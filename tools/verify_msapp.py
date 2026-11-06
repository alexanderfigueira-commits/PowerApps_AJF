#!/usr/bin/env python3
"""Static verification of everything shipped so far, read back out of the .msapp.

This is not a runtime test -- nothing here proves Power Fx compiles or that
SharePoint accepts a write. It proves that each change is actually present and
wired the way it was described, which is the part that can be checked without
Studio. Anything depending on data or on a SharePoint column is listed in the
manual matrix instead.
"""
import io, json, re, sys, zipfile
import yaml
from paload import PaLoader

MSAPP = sys.argv[1] if len(sys.argv) > 1 else \
    '/home/user/PowerApps_AJF/msapp-versions/AV-CD-v46-visual-check.msapp'
z = zipfile.ZipFile(MSAPP)
S, R = {}, {}
for n in [i.filename for i in z.infolist()]:
    if n.startswith('Controls\\'):
        d = json.loads(z.read(n).decode('utf-8'))
        tp = d['TopParent']
        S[tp['Name']] = tp

        RAW = globals().setdefault('RAW', {})

        def walk(c, scr):
            R[(scr, c['Name'])] = {r['Property']: r['InvariantScript'] for r in c['Rules']}
            RAW[(scr, c['Name'])] = c['Rules']
            for k in c.get('Children', []):
                walk(k, scr)
        walk(tp, tp['Name'])

results = []


def check(section, name, ok, detail=''):
    results.append((section, name, bool(ok), detail))


def rule(scr, ctl, prop):
    return R.get((scr, ctl), {}).get(prop)


def has(scr, ctl, prop, *needles):
    v = rule(scr, ctl, prop)
    return v is not None and all(x in v for x in needles)


# the two screens were renamed in Studio on 22-09
MR, RQ, RV, DS = 'RequestManagementScreen', 'RequesDetailtScreen', 'ReviewScreen', 'DashboardScreen'

# ---------------- Section 1: status model ----------------
check('1', 'Submit writes Processing', has(RQ, 'RS_BtnSubmitRequest', 'OnSelect', 'Status: {Value: "Processing"}'))
check('1', 'Resubmit writes Processing', has(RQ, 'RS_BtnResubmitRequest', 'OnSelect', 'Status: {Value: "Processing"}'))
check('1', 'Resubmit offered for Pending as well as Rejected',
      has(RQ, 'RS_BtnResubmitRequest', 'Visible', '"Rejected"', '"Pending"'))
check('1', 'Need-info action exists and writes Pending',
      has(RV, 'RV_BtnNeedInfo', 'OnSelect', 'Status: {Value: "Pending"}'))
check('1', 'Need-info is admin-only and requires a comment',
      has(RV, 'RV_BtnNeedInfo', 'DisplayMode', 'varUserRole = "ADMINISTRATOR"', 'varReviewComment <> ""'))
check('1', 'Need-info stores the reviewer comment', has(RV, 'RV_BtnNeedInfo', 'OnSelect', 'ReviewerComments'))
check('1', 'Review queue lists both Processing and Pending',
      has(RV, 'RV_QueueGallery', 'Items', 'Status.Value = "Processing"', 'Status.Value = "Pending"'))
check('1', 'The dead If(x, same, same) status clause is gone',
      'If(varReviewQueueMine, Status.Value' not in (rule(RV, 'RV_QueueGallery', 'Items') or ''))
for _rvbtn in ('RV_BtnApprove', 'RV_BtnReject', 'RV_BtnNeedInfo'):
    check('1', f'{_rvbtn} requires Processing, so a listed Pending row is visible but not actionable',
          'varReviewProject.Status.Value = "Processing"' in (rule(RV, _rvbtn, 'DisplayMode') or ''))
check('1', 'Row Review button: Processing + admin only',
      has(MR, 'HomeRowReview', 'Visible', '"Processing"', 'varUserRole = "ADMINISTRATOR"'))
check('1', 'Publish button retired', (rule(RQ, 'RS_BtnPublish', 'Visible') or '').strip() == 'false')
check('1', 'No "Published" left in the dashboard KPIs', '"Published"' not in (rule(DS, DS, 'OnVisible') or 'x'))
check('1', 'No PublishedDate left in the dashboard KPIs', 'PublishedDate' not in (rule(DS, DS, 'OnVisible') or 'x'))
# the success-rate pair was replaced in Studio by varKpiPublishedTotal /
# varKpiApprovedTotal, so what matters now is that the Published one was
# repointed rather than left counting a retired status
check('1', 'Published KPIs repointed to Approved',
      (rule(DS, DS, 'OnVisible') or '').count('Status.Value = "Approved"') >= 2)
check('1', 'Trend / avg days key off ReviewedDate', has(DS, DS, 'OnVisible', 'ReviewedDate'))
check('1', 'Validation card counts Processing',
      (rule(DS, DS, 'OnVisible') or '').count('Status.Value = "Processing"') >= 2)
check('1', 'Validation card captions updated',
      has(DS, 'Pending_CardTitle', 'Text', 'TO VALIDATE'))
check('1', 'varUserRole yields the SharePoint Role.Value',
      has(MR, MR, 'OnVisible', 'Role.Value', '"REQUESTOR"') and '"USER"' not in (rule(MR, MR, 'OnVisible') or ''))
check('1', 'Requestor filter locked for non-admins',
      has(MR, 'cmbFilterRequestor', 'DisplayMode', 'varUserRole = "ADMINISTRATOR"', 'DisplayMode.Disabled'))
for ctl in ('RS_BtnDraftSave', 'RS_BtnDraftSave_1', 'RS_CRowDelete'):
    check('1', f'{ctl} editable while Pending', has(RQ, ctl, 'DisplayMode', '"Pending"'))
check('1', 'Reviewer comment surfaced for Pending too',
      has(RQ, RQ, 'OnVisible', 'ReviewerComments', '"Pending"'))

# chips
CHIPS = ('HomeChipAll', 'HomeChipDraft', 'HomeChipSubmitted', 'HomeChipApproved',
         'HomeChipRejected', 'HomeChipPublished', 'HomeTypeAll', 'HomeTypePhoto',
         'HomeTypeVideo', 'HomeTypePodcast')
check('1', 'A Processing chip exists', has(MR, 'HomeChipPublished', 'Text', 'Processing'))
check('1', 'No chip still says Published',
      not any('Published' in (rule(MR, c, 'Text') or '') for c in CHIPS))
order = [(int(rule(MR, c, 'X')), c) for c in
         ('HomeChipAll', 'HomeChipDraft', 'HomeChipPublished', 'HomeChipSubmitted',
          'HomeChipApproved', 'HomeChipRejected')]
check('1', 'Chips read All, Draft, Processing, Pending, Approved, Rejected left to right',
      order == sorted(order), ' '.join(c for _, c in sorted(order)))
check('1', 'All 10 chip counts share the requestor clause',
      all('cmbFilterRequestor.SelectedItems' in (rule(MR, c, 'Text') or '') for c in CHIPS))
check('1', 'All 10 chip counts share the assignee clause',
      all('cmbFilterAssignee_1.SelectedItems' in (rule(MR, c, 'Text') or '') for c in CHIPS))
check('1', 'Status chips drop their own status clause',
      not any('varFilter = "All" Or Status.Value = varFilter' in (rule(MR, c, 'Text') or '')
              for c in CHIPS[:6]))
check('1', 'Type chips drop their own type clause',
      not any('locProdTypeFilter' in (rule(MR, c, 'Text') or '') for c in CHIPS[6:]))

# ---------------- Section 2 ----------------
check('2', 'Save always visible',
      (rule(RQ, 'RS_BtnDraftSave', 'Visible') or '').strip().startswith('true'))
check('2', 'Save gated on title + DG while editable',
      has(RQ, 'RS_BtnDraftSave', 'DisplayMode', 'RS_Title.Text',
          'HomeFilterDG.Selected.Value', '"Draft"', '"Pending"'))
STYLE = ('Fill', 'HoverFill', 'PressedFill', 'DisabledFill', 'Color', 'HoverColor',
         'PressedColor', 'DisabledColor', 'BorderColor', 'BorderThickness', 'BorderStyle',
         'RadiusTopLeft', 'RadiusTopRight', 'RadiusBottomLeft', 'RadiusBottomRight',
         'Font', 'Size', 'FontWeight', 'PaddingTop', 'PaddingBottom', 'PaddingLeft', 'PaddingRight')
# 2b: the pair was rebuilt in Studio and already matches each other
# P1-26 (v45): the Media button takes the Submit colours; the rest of its style still matches Save
bad = [p for p in STYLE if p not in ('Fill', 'HoverFill') and rule(RQ, 'RS_BtnDraftSave_1', p) != rule(RQ, 'RS_BtnDraftSave', p)]
check('2', f'Media matches Save on the {len(STYLE) - 2} non-colour style properties', not bad, ','.join(bad))
check('2', 'P1-26: Media button uses the Submit colours',
      all(rule(RQ, 'RS_BtnDraftSave_1', p) == rule(RQ, 'RS_BtnSubmitRequest', p) for p in ('Fill', 'HoverFill')))
check('2', 'Media keeps its own caption and position',
      rule(RQ, 'RS_BtnDraftSave_1', 'Text') != rule(RQ, 'RS_BtnDraftSave', 'Text')
      and rule(RQ, 'RS_BtnDraftSave_1', 'X') != rule(RQ, 'RS_BtnDraftSave', 'X'))

# ---------------- carried forward from v4-v10 ----------------
# v40: ReviewScreen is admin-only, so the author exclusion was dropped on request.
check('prior', 'Approve is admin-only on ReviewScreen',
      has(RV, 'RV_BtnApprove', 'DisplayMode', 'varUserRole = "ADMINISTRATOR"'))
# Superseded: the queue used to exclude the author, which hid a Processing request
# from the person who submitted it. Visibility and permission are now separate --
# the queue shows it, the three actions refuse it.
check('prior', 'Review queue no longer hides your own requests',
      "Lower('Created By'.Email) <> Lower(User().Email)"
      not in (rule(RV, 'RV_QueueGallery', 'Items') or ''))
check('prior', 'All three review actions: ADMINISTRATOR + Processing, no author exclusion (v40)',
      all(all(x in (rule(RV, c_, 'DisplayMode') or '')
              for x in ('varUserRole = "ADMINISTRATOR"', 'varReviewProject.Status.Value = "Processing"'))
          and "'Created By'" not in (rule(RV, c_, 'DisplayMode') or '')
          for c_ in ('RV_BtnApprove', 'RV_BtnReject', 'RV_BtnNeedInfo')))
_qi = ' '.join((rule(RV, 'RV_QueueGallery', 'Items') or '').split())
check('prior', 'RV_QueueGallery: admin sees Processing + Pending, anyone else only their own Pending (v40)',
      'If( varUserRole = "ADMINISTRATOR", Status.Value = "Processing" Or Status.Value = "Pending", '
      'Status.Value = "Pending" And Lower(\'Created By\'.Email) = Lower(User().Email) )' in _qi)
check('prior', 'The review queue keeps its mine-only narrowing',
      has(RV, 'RV_QueueGallery', 'Items', 'varReviewQueueMine', 'DG_Agency_Contact'))
check('prior', 'The review queue is read fresh, not from the connector cache',
      (lambda o: "Refresh('AV-CD-Requests')" in o
       and o.index("Refresh('AV-CD-Requests')") < o.index('ClearCollect(colRevReqs'))
      (rule(RV, RV, 'OnVisible') or 'xClearCollect(colRevReqs'))
check('prior', 'Approve no longer overwrites DG_Agency_Contact',
      'DG_Agency_Contact' not in (rule(RV, 'RV_BtnApprove', 'OnSelect') or 'x'))
check('prior', 'Approve writes the single-person Assignee',
      has(RV, 'RV_BtnApprove', 'OnSelect', 'Assignee: If('))
check('prior', 'Gallery filters on Assignee',
      has(MR, 'HomeGallery', 'Items', 'Assignee.DisplayName in cmbFilterAssignee_1.SelectedItems.Value'))
check('prior', 'Gallery shows the Assignee column', has(MR, 'HomeRowAssignee', 'Text', 'Assignee.DisplayName'))
check('prior', 'Inverted date range is refused, not committed',
      (rule(MR, 'HomeFilterStart', 'OnChange') or '').index('Notify(') <
      (rule(MR, 'HomeFilterStart', 'OnChange') or 'Notify( Set(').index('Set(varFilterStartDate'))
check('prior', 'Date labels flag an inverted range', has(MR, 'HomeLblFilterStart', 'Text', 'FROM IS AFTER TO'))
check('prior', 'Clear clears both date variables',
      has(MR, 'HomeBtnClear', 'OnSelect', 'Set(varFilterStartDate, Blank())',
          'Set(varFilterEndDate, Blank())'))
check('prior', 'Contact popup present (8 controls)',
      sum(1 for (s, c) in R if s == RQ and 'Contact' in c and c.startswith('RS_')) >= 8)

# ---------------- Section 3a: Processing is view-only for a requestor, bar Notes ----------------
LOCKVAR = 'varRequestorLocked'
LOCKED_SCREENS = ['RequesDetailtScreen', 'ChildInfoScreen', 'ChildMetaScreen',
                  'ChildLegalScreen', 'ChildValidScreen']
import re as _re3
_setter = _re3.compile(r'Set\(\s*' + LOCKVAR + r'\s*,\s*varUserRole <> "ADMINISTRATOR"\s*'
                       r'And Coalesce\(varCurrentRequest\.Status\.Value, ""\) = "Processing"\s*\)')
missing = [scr for scr in LOCKED_SCREENS
           if not _setter.search(' '.join((rule(scr, scr, 'OnVisible') or '').split()))]
check('3a', 'All 5 request screens compute the lock identically', not missing, ','.join(missing))

INPUT_T = {'text', 'checkbox', 'combobox', 'datepicker', 'dropdown', 'attachments'}
_tmpl = {}
for _sn, _stp in S.items():
    def _wt(c, sn):
        _tmpl[(sn, c['Name'])] = c['Template']['Name']
        for k in c.get('Children', []):
            _wt(k, sn)
    _wt(_stp, _sn)
unlocked = []
nlocked = 0
for scr in LOCKED_SCREENS:
    for (s_, c_) in R:
        if s_ != scr or _tmpl.get((s_, c_)) not in INPUT_T:
            continue
        dm = rule(scr, c_, 'DisplayMode') or ''
        # CL_DCAttachValue (inside CL_FormAttach) doesn't reference the lock in
        # its OWN DisplayMode -- it's 'Parent.DisplayMode', inherited from the
        # form's DefaultMode = If(varRequestorLocked, FormMode.View, FormMode.Edit).
        # Verified directly, not by string match, since the lock's real here.
        if c_ == 'CL_DCAttachValue' and dm.strip() == 'Parent.DisplayMode':
            nlocked += 1
            continue
        if LOCKVAR in dm:
            nlocked += 1
        elif not (c_ in ('CI_Notes', 'RS_RequestorNotes') or 'varUserRole' in dm or c_ == 'CI_TplSearch'
                  or (c_ in ('CI_PodcastVisual', 'CM_EpisodeVisual', 'CL_VTTUpload', 'CM_AudioFiles')
                      and dm.strip() == 'DisplayMode.View')):
            unlocked.append(c_)
check('3a', f'Every request input carries the lock ({nlocked} of them)',
      not unlocked, ','.join(unlocked))
check('3a', 'Notes is the one editable field',
      (rule('ChildInfoScreen', 'CI_Notes', 'DisplayMode') or '').strip() == 'DisplayMode.Edit')
check('3a', 'Notes persists by itself, not via the archive save',
      '{Notes: Self.Text}' in (rule('ChildInfoScreen', 'CI_Notes', 'OnChange') or ''))
check('3a', 'The Notes save is not itself gated by the lock',
      LOCKVAR not in (rule('ChildInfoScreen', 'CI_Notes', 'OnChange') or ''))
for _c in ('CI_TplConfirmOK',):
    check('3a', f'{_c} cannot overwrite fields while locked',
          LOCKVAR in (rule('ChildInfoScreen', _c, 'DisplayMode') or ''))
check('3a', 'RS_btnSaveContact gated by the lock',
      LOCKVAR in (rule(RQ, 'RS_btnSaveContact', 'DisplayMode') or ''))
check('3a', 'CV_BtnSaveArchive gated by the lock',
      LOCKVAR in (rule('ChildValidScreen', 'CV_BtnSaveArchive', 'DisplayMode') or ''))
# no button that writes request data is reachable by a locked requestor
open_btns = []
for scr in LOCKED_SCREENS:
    for (s_, c_) in R:
        if s_ != scr or _tmpl.get((s_, c_)) != 'button':
            continue
        g = R[(s_, c_)]
        if not _re3.search(r'Set\(\s*varChild|Patch\(', g.get('OnSelect', '')):
            continue
        vis = ' '.join(g.get('Visible', 'true').split())
        dm = ' '.join(g.get('DisplayMode', '').split())
        if not (LOCKVAR in dm or _re3.search(r'"Draft"|"Pending"|"Rejected"', dm + vis)
                or vis == 'false'):
            open_btns.append(f'{scr}.{c_}')
check('3a', 'No data-writing button is open to a locked requestor',
      not open_btns, ','.join(open_btns))
check('3a', 'Submit offered only on blank status or Draft',
      '"Draft"' in (rule(RQ, 'RS_BtnSubmitRequest', 'Visible') or '')
      and '"Processing"' not in (rule(RQ, 'RS_BtnSubmitRequest', 'Visible') or ''))
check('3a', 'Resubmit still covers Rejected and Pending',
      all(x in (rule(RQ, 'RS_BtnResubmitRequest', 'Visible') or '')
          for x in ('"Rejected"', '"Pending"')))

# ---------------- attachments: one Edit Form, CL_FormAttach (v32) ----------------
CI2, CM2, CL2, CV2 = 'ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen'


def code_only(script):
    return '\n'.join(l for l in (script or '').split('\n') if not l.strip().startswith('//'))


def _node(scr, name):
    st = [S[scr]]
    while st:
        c = st.pop()
        if c['Name'] == name:
            return c
        st.extend(c.get('Children', []))


_all_rules = [(s_, c_, p_, v_) for (s_, c_), g in R.items() for p_, v_ in g.items()]
check('attach', 'CL_Annex is deleted and nothing anywhere still reads it',
      (CL2, 'CL_Annex') not in R and not any('CL_Annex' in v_ for (*_, v_) in _all_rules))
_form = _node(CL2, 'CL_FormAttach')
check('attach', 'CL_FormAttach exists once, on the screen itself (a form cannot live in a gallery)',
      _form is not None and _form['Parent'] == CL2
      and [c for (s_, c) in R if c == 'CL_FormAttach'] == ['CL_FormAttach'])
_tj = json.loads(z.read('References\\Templates.json').decode('utf-8'))
check('attach', 'The form template is registered in References/Templates.json',
      any(t['Name'] == 'form' and t['Version'] == '2.4.4' for t in _tj['UsedTemplates']))
check('attach', "CL_FormAttach edits the media items list ('AV-CD-Mediafiles' = AV-CD-MediaItems)",
      (rule(CL2, 'CL_FormAttach', 'DataSource') or '').strip() == "'AV-CD-Mediafiles'")
check('attach', 'CL_FormAttach.Item is the open media item, Defaults() only when none exists',
      all(x in (rule(CL2, 'CL_FormAttach', 'Item') or '')
          for x in ('varAttachRecord', "Defaults('AV-CD-Mediafiles')")))
check('attach', 'CL_FormAttach.DefaultMode respects the Processing lock',
      (rule(CL2, 'CL_FormAttach', 'DefaultMode') or '') ==
      'If(varRequestorLocked, FormMode.View, FormMode.Edit)')
_cards = [k['Name'] for k in (_form or {}).get('Children', [])]
check('attach', 'Exactly two cards: CL_DCId then CL_DCAttach', _cards == ['CL_DCId', 'CL_DCAttach'])
_idc = _node(CL2, 'CL_DCId') or {}
check('attach', 'CL_DCId is a custom card with no DataField/Update, so the read-only ID is never written',
      _idc.get('VariantName') == 'blankCard'
      and not any(p_ in R.get((CL2, 'CL_DCId'), {}) for p_ in ('DataField', 'Update', 'Default')))
check('attach', 'CL_DCIdValue shows ThisItem.ID', 'ThisItem.ID' in (rule(CL2, 'CL_DCIdValue', 'Text') or ''))
check('attach', 'CL_DCAttach is the standard attachments card, written from its own box',
      (rule(CL2, 'CL_DCAttach', 'DataField') or '') == '"{Attachments}"'
      and (rule(CL2, 'CL_DCAttach', 'Update') or '') == 'CL_DCAttachValue.Attachments'
      and (_node(CL2, 'CL_DCAttach') or {}).get('VariantName') == 'attachmentsEditCard')
check('attach', 'CL_DCAttach is disabled while the media item has no SharePoint record',
      has(CL2, 'CL_DCAttach', 'DisplayMode', 'IsBlank(varAttachRecord)', 'DisplayMode.Disabled',
          'Parent.DisplayMode'))
check('attach', 'The "save first" message shows exactly when there is no record',
      (rule(CL2, 'CL_AttachNeedSave', 'Visible') or '') == 'IsBlank(varAttachRecord)'
      and 'Save the media item first' in (rule(CL2, 'CL_AttachNeedSave', 'Text') or ''))
check('attach', 'The panel header names the media item the form refers to',
      has(CL2, 'CL_AttachFor', 'Text', 'varChildTitle1', 'CD_MediaNumber'))
for _scr in (CL2, CV2):
    _ov = rule(_scr, _scr, 'OnVisible') or ''
    check('attach', f'{_scr}.OnVisible re-reads the snapshot only when a different item is open',
          'Coalesce(varAttachRecord.ID, 0) <> Coalesce(varCurrentChildSPId, 0)' in _ov
          and "LookUp('AV-CD-Mediafiles', ID = Coalesce(varCurrentChildSPId, 0))" in _ov)
_cvov = code_only(rule(CV2, CV2, 'OnVisible'))
check('attach', 'ChildValidScreen takes the snapshot before building the checklist',
      _cvov.index('Set(varAttachRecord') < _cvov.index('ClearCollect(colValidations'))
_save = code_only(rule(CV2, 'CV_BtnSaveArchive', 'OnSelect'))
check('attach', 'Save: SubmitForm(CL_FormAttach) exactly once, after the Patch of the other fields',
      _save.count('SubmitForm(CL_FormAttach)') == 1
      and _save.index('savedMedia: Patch(') < _save.index('SubmitForm(CL_FormAttach)'))
check('attach', 'Save submits only for an item that already had an ID and is loaded in the form',
      'spId > 0 And Coalesce(varAttachRecord.ID, 0) = spId' in _save)
check('attach', 'Save without attachments to send still finishes exactly as before',
      _save.count('Navigate(RequesDetailtScreen') == 2 and _save.count('Set(varRequestMediaType, "")') == 2)
_ok = code_only(rule(CL2, 'CL_FormAttach', 'OnSuccess'))
check('attach', 'OnSuccess: success notification, refresh, then the usual finish',
      all(x in _ok for x in ('NotificationType.Success', "Refresh('AV-CD-Mediafiles')",
                             'Set(varRequestMediaType, "")', 'Navigate(RequesDetailtScreen'))
      and _ok.index("Refresh(") < _ok.index('Navigate('))
_ko = code_only(rule(CL2, 'CL_FormAttach', 'OnFailure'))
check('attach', 'OnFailure: shows the form error and does not continue',
      'CL_FormAttach.Error' in _ko and 'NotificationType.Error' in _ko and 'Navigate(' not in _ko)
for _scr, _ctl, _prop in ((CV2, CV2, 'OnVisible'), (CV2, 'CV_BtnRefresh', 'OnSelect'),
                          (CL2, 'CL_LblMissing', 'Text')):
    _v = rule(_scr, _ctl, _prop) or ''
    check('attach', f'{_ctl}.{_prop}: VTT/SRT checks read the form\'s attachments box',
          'CL_DCAttachValue.Attachments' in _v and 'CL_VTTUpload.Attachments' not in _v)
check('attach', 'CL_VTTUpload is a read-only list of the .vtt files in the form',
      (rule(CL2, 'CL_VTTUpload', 'DisplayMode') or '').strip() == 'DisplayMode.View'
      and 'CL_DCAttachValue.Attachments' in (rule(CL2, 'CL_VTTUpload', 'Items') or '')
      and not any(p_ in R.get((CL2, 'CL_VTTUpload'), {})
                  for p_ in ('OnAddFile', 'OnRemoveFile', 'OnUndoRemoveFile')))
check('attach', 'CL_VTTUpload name map matches the rows it now lists (Name/Value)',
      [r for r in RAW[(CL2, 'CL_VTTUpload')] if r['Property'] == 'Items'][0].get('NameMap')
      == '{"Name":"Name","Value":"Value"}')
check('attach', 'Nothing on ChildLegalScreen Patches {Attachments: ...} any more',
      not any(s_ == CL2 and '{Attachments:' in v_ for (s_, c_, p_, v_) in _all_rules))
for _s, _c, _flt in ((CI2, 'CI_PodcastVisual', '.png'), (CM2, 'CM_EpisodeVisual', '.png'), (CM2, 'CM_AudioFiles', '.mp3')):
    _g = R.get((_s, _c), {})
    check('attach', f'{_c} is a read-only list of the files in the attachments form (v45, no Patch)',
          _g.get('DisplayMode') == 'DisplayMode.View' and 'CL_DCAttachValue.Attachments' in _g.get('Items', '')
          and _flt in _g.get('Items', '') and not any(p_ in _g for p_ in ('OnAddFile', 'OnRemoveFile', 'OnUndoRemoveFile')))


def _geo(scr, ctl):
    g = R[(scr, ctl)]
    return tuple(int(g[p_]) for p_ in ('X', 'Y', 'Width', 'Height'))


_gx, _gy, _gw, _gh = _geo(CL2, 'CL_Gallery')
_px, _py, _pw, _ph = _geo(CL2, 'CL_AttachPanel')
check('attach', 'Gallery and attachments panel sit side by side without overlapping',
      _gx + _gw <= _px and _px + _pw <= 1366)
check('attach', 'Gallery and panel end above the bottom bar (Y 712)',
      _gy + _gh <= 712 and _py + _ph <= 712)
_fx, _fw, _fh = (int(rule(CL2, 'CL_FormAttach', p_)) for p_ in ('X', 'Width', 'Height'))
check('attach', 'CL_FormAttach fits inside the panel in both positions',
      _px <= _fx and _fx + _fw <= _px + _pw
      and all(y_ + _fh <= _py + _ph for y_ in (250, 278))
      and (rule(CL2, 'CL_FormAttach', 'Y') or '') == 'If(IsBlank(varAttachRecord), 278, 250)')
check('attach', 'Both cards fit inside the form',
      int(rule(CL2, 'CL_DCId', 'Height')) + int(rule(CL2, 'CL_DCAttach', 'Height')) <= _fh
      and int(rule(CL2, 'CL_DCAttachValue', 'Y')) + int(rule(CL2, 'CL_DCAttachValue', 'Height'))
      <= int(rule(CL2, 'CL_DCAttach', 'Height')) - 20)

# ChildLegalScreen's scroll panel now flows: every Y is chained to the control
# above it, and hidden rows take no space. Evaluate it for every combination of
# the variables that show or hide rows.
import itertools as _it


def _cl_layout(env):
    kids = {k['Name']: {r['Property']: r['InvariantScript'] for r in k['Rules']}
            for k in _node(CL2, 'CL_Gallery')['Children'] if k['Template']['Name'] != 'galleryTemplate'}
    memo = {}

    def ev(expr):
        t = code_only(expr)
        t = re.sub(r'\b(CL_\w+)\.(Y|Height|Visible|X|Width)\b', r'val("\1","\2")', t)
        t = t.replace('Left(varChildContractCase, 6) = "Case 1"', repr(env['case1']))
        t = t.replace('Left(varChildContractCase, 6) <> "Case 1"', repr(not env['case1']))
        t = t.replace('varChildMediaType', repr(env['mt']))
        for v_ in ('varChildModelRelease', 'varChildMusicUsed', 'varChildPreexisting',
                   'varChildSubtitlesProvided', 'varDocFramework', 'varDocSpecific'):
            t = re.sub(r'\b' + v_ + r'\b', repr(env.get(v_, False)), t)
        t = t.replace('<>', '!=')
        t = re.sub(r'(?<![!<>=])=(?!=)', '==', t)
        t = re.sub(r'\bAnd\b', ' and ', re.sub(r'\bOr\b', ' or ', t))
        t = re.sub(r'\bNot\(', 'not_(', t).replace('true', 'True').replace('false', 'False')
        t = ' '.join(t.split())
        return eval(t, {'If': lambda c, a, b=0: a if c else b, 'not_': lambda x: not x,
                        'val': val})

    def val(c, p_):
        if (c, p_) not in memo:
            memo[(c, p_)] = ev(kids[c].get(p_, 'true' if p_ == 'Visible' else '0'))
        return memo[(c, p_)]

    ts = ev(R[(CL2, 'CL_Gallery')]['TemplateSize'])
    boxes = [(c, val(c, 'X'), val(c, 'Y'), val(c, 'Width'), val(c, 'Height'))
             for c in kids if val(c, 'Visible')]
    return ts, boxes


_bad = []
_worst_gap = 0
for mt, c1, mr, mu, pe, sb in _it.product(('Photo', 'Video', 'Podcast'), *[(False, True)] * 5):
    env = {'mt': mt, 'case1': c1, 'varChildModelRelease': mr, 'varChildMusicUsed': mu,
           'varChildPreexisting': pe, 'varChildSubtitlesProvided': sb}
    try:
        ts, boxes = _cl_layout(env)
    except Exception as ex:
        _bad.append(f'eval {env}: {ex}')
        break
    bottom = max(y + h for (_c, x, y, w, h) in boxes)
    if bottom > ts:
        _bad.append(f'{mt} case1={c1} mr={mr} mu={mu} pe={pe} sb={sb}: content {bottom} > {ts}')
    _worst_gap = max(_worst_gap, ts - bottom)
    for (a, ax, ay, aw, ah), (b_, bx, by, bw, bh) in _it.combinations(boxes, 2):
        if {a, b_} == {'CL_Banner', 'CL_BannerText'}:
            continue
        if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
            _bad.append(f'{mt}: {a} overlaps {b_}')
    if any(x + w > _gw for (_c, x, y, w, h) in boxes):
        _bad.append(f'{mt}: a control is wider than the gallery')
check('attach', 'ChildLegalScreen flows: no clipping, no overlap, fits the width, in all 96 variable combinations',
      not _bad, '; '.join(sorted(set(_bad))[:5]))
check('attach', f'ChildLegalScreen stays compact: at most 40px of empty space under the content (worst {_worst_gap})',
      _worst_gap <= 40)


# ---------------- layout: nothing clipped, nothing stranded outside its scroll panel ----------------
def _ev(expr, mt):
    if expr is None:
        return None
    def If(c, a, b=False):
        return a if c else b
    def Switch(v, *args):
        pairs = args[:len(args) - len(args) % 2]
        for i in range(0, len(pairs) - 1, 2):
            if v == pairs[i]:
                return pairs[i + 1]
        return args[-1] if len(args) % 2 else 0
    import re as _re
    t = expr.replace('varChildMediaType', repr(mt)).replace('<>', '!=')
    t = _re.sub(r'(?<![!<>=])=(?!=)', '==', t)
    t = _re.sub(r'\bAnd\b', 'and', _re.sub(r'\bOr\b', 'or', t))
    t = _re.sub(r'\bNot\(', 'not_(', t).replace('true', 'True').replace('false', 'False')
    try:
        return eval(t, {'If': If, 'Switch': Switch, 'not_': lambda x: not x})
    except Exception:
        return None

clipped, stranded = [], []
for sname, stp in S.items():
    for gal in stp.get('Children', []):
        gr = {r['Property']: r['InvariantScript'] for r in gal['Rules']}
        if gal['Template']['Name'] != 'gallery' or gr.get('Items', '').strip() != '[{id: 1}]':
            continue  # only the one-row galleries used as scroll panels
        for mt in ('Photo', 'Video', 'Podcast', 'Other'):
            ts = _ev(gr.get('TemplateSize'), mt)
            if not isinstance(ts, int):
                continue
            for k in gal.get('Children', []):
                g = {r['Property']: r['InvariantScript'] for r in k['Rules']}
                if _ev(g.get('Visible', 'true'), mt) is not True:
                    continue
                y, h = _ev(g.get('Y'), mt), _ev(g.get('Height'), mt)
                if isinstance(y, int) and isinstance(h, int) and y + h > ts:
                    clipped.append(f'{k["Name"]}@{mt} {y + h}>{ts}')
        # a control positioned like the panel's contents but parented to the screen
        # would float instead of scrolling -- the bug that stranded three controls
        names = {k['Name'] for k in gal.get('Children', [])}
        for sib in stp.get('Children', []):
            if sib['Name'] == gal['Name'] or sib.get('IsGroupControl'):
                continue
            sg = {r['Property']: r['InvariantScript'] for r in sib['Rules']}
            try:
                sy = int(sg['Y'])
            except (ValueError, KeyError):
                continue
            gy, gh = _ev(gr.get('Y'), 'Other'), _ev(gr.get('Height'), 'Other')
            if isinstance(gy, int) and isinstance(gh, int) and gy < sy < gy + gh \
                    and sib['Name'] not in names and sib['Name'].endswith(('Notes', 'NoThirdParty')):
                stranded.append(f'{sname}.{sib["Name"]}')
check('layout', 'Nothing inside a scroll panel is clipped by TemplateSize',
      not clipped, '; '.join(sorted(set(clipped))[:6]))
check('layout', 'No field control stranded outside its scroll panel',
      not stranded, ','.join(stranded))
for scr, ctl, par in (('ChildLegalScreen', 'CL_ChkNoThirdParty', 'CL_Gallery'),
                      ('ChildInfoScreen', 'CI_LblNotes', 'CI_Gallery'),
                      ('ChildInfoScreen', 'CI_Notes', 'CI_Gallery')):
    gal = [c for c in S[scr]['Children'] if c['Name'] == par][0]
    check('layout', f'{ctl} lives inside {par}',
          any(k['Name'] == ctl and k.get('Parent') == par for k in gal.get('Children', [])))

# ---------------- HomePrintScreen: filters, navigation, detail screens ----------------
HPS = 'HomePrintScreen'
PHOTO_S, VIDEO_S, POD_S = ('PrintPhotoDetailScreen', 'PrintVideoDetailScreen',
                           'PrintPodcastDetailScreen')
for _s in (PHOTO_S, VIDEO_S, POD_S):
    check('print', f'{_s} exists', _s in S)
_hp_items = rule(HPS, 'HP_Gallery', 'Items') or ''
check('print', 'Gallery still filters colPrintData, so role logic is kept',
      'colPrintData' in _hp_items)
for _n, _needle in (('production type', 'First(MediaType).Value = locHPProductionType'),
                    ('status', 'Status.Value = locHPStatus'),
                    ('title (StartsWith)', 'StartsWith(RequestTitle, HP_TxtTitle.Text)'),
                    ('request id (numeric)', 'ID = Value(HP_TxtRequestID.Text)')):
    check('print', f'Gallery filters on {_n}', _needle in _hp_items)
check('print', 'Blank/All filters are skipped rather than applied',
      _hp_items.count('IsBlank(') >= 2 and 'locHPProductionType = "All" Or' in _hp_items)
_ov = rule(HPS, HPS, 'OnVisible') or ''
check('print', 'Both filter variables initialise to All',
      'locHPProductionType: "All"' in _ov and 'locHPStatus: "All"' in _ov)
check('print', 'OnVisible still builds colPrintMedia', 'colPrintMedia' in _ov)
_CHIPS = ['HP_BtnAllMedia', 'HP_BtnPhoto', 'HP_BtnVideo', 'HP_BtnPodcast',
          'HP_BtnStatusAll', 'HP_BtnStatusDraft', 'HP_BtnStatusProcessing',
          'HP_BtnStatusPending', 'HP_BtnStatusApproved', 'HP_BtnStatusRejected']
check('print', f'All {len(_CHIPS)} chips exist', all((HPS, c) in R for c in _CHIPS))
check('print', 'Every chip shows a live count',
      all('CountRows(' in (rule(HPS, c, 'Text') or '') for c in _CHIPS))
_selfapplied = [c for c in _CHIPS[:4] if 'locHPProductionType' in (rule(HPS, c, 'Text') or '')] \
    + [c for c in _CHIPS[4:] if 'locHPStatus' in (rule(HPS, c, 'Text') or '')]
check('print', 'Each chip count drops its own dimension', not _selfapplied,
      ','.join(_selfapplied))
check('print', 'No chip offers the retired Published status',
      not any('Published' in (rule(HPS, c, 'Text') or '') for c in _CHIPS))
check('print', 'Clear resets both variables and both inputs',
      all(x in (rule(HPS, 'HP_BtnClear', 'OnSelect') or '')
          for x in ('locHPProductionType: "All"', 'locHPStatus: "All"',
                    'Reset(HP_TxtTitle)', 'Reset(HP_TxtRequestID)')))
check('print', 'Empty state reads as a filter message',
      'match these filters' in (rule(HPS, 'HP_EmptyState', 'Text') or ''))
_nav = rule(HPS, 'HP_Gallery', 'OnSelect')
# Studio has now dropped this rule on export twice while keeping its siblings
# (HoverFill/PressedFill/Transition/Selectable), so its absence is reported as
# one finding instead of three.
check('print', 'LINEAGE NOTE: HP_Gallery.OnSelect present (print rows clickable)',
      _nav is not None, 'absent in this export -- Studio dropped it again')
if _nav is not None:
    check('print', 'Row select stores the request', 'Set(gblPrintRequest, ThisItem)' in _nav)
    check('print', 'Row select routes to all three detail screens',
          all(f'Navigate({x}, ScreenTransition.None)' in _nav for x in (PHOTO_S, VIDEO_S, POD_S)))
    check('print', 'Mixed/untyped requests are told, not silently ignored',
          'NotificationType.Warning' in _nav)
check('print', 'Row has a hover cue distinct from its fill',
      (rule(HPS, 'HP_Gallery', 'HoverFill') or '') != (rule(HPS, 'HP_Gallery', 'Fill') or 'x'))
check('print', 'Row has a chevron', (HPS, 'HP_RowChevron') in R)
for _s, _p in ((PHOTO_S, 'PPD'), (VIDEO_S, 'PVD'), (POD_S, 'PPoD')):
    check('print', f'{_p}: Back and Print hide while printing',
          (rule(_s, f'{_p}_BtnBack', 'Visible') or '').strip() == 'Not(locPrinting)'
          and (rule(_s, f'{_p}_BtnPrint', 'Visible') or '').strip() == 'Not(locPrinting)')
    check('print', f'{_p}: Print toggles locPrinting around Print()',
          all(x in (rule(_s, f'{_p}_BtnPrint', 'OnSelect') or '')
              for x in ('locPrinting: true', 'Print()', 'locPrinting: false')))
    check('print', f'{_p}: reads gblPrintRequest',
          'gblPrintRequest' in (rule(_s, f'{_p}_Title', 'Text') or ''))
    check('print', f'{_p}: media gallery is scoped to the request',
          'ParentRequest = gblPrintRequest.RequestNumber' in (rule(_s, f'{_p}_Gallery', 'Items') or ''))
    _vals = [c for (sc, c) in R if sc == _s and c.startswith(f'{_p}_Val')]
    check('print', f'{_p}: {len(_vals)} field values, all with a Not provided fallback',
          _vals and all('Not provided' in (rule(_s, v, 'Text') or '')
                        or 'Yes' in (rule(_s, v, 'Text') or '') for v in _vals))
    check('print', f'{_p}: blank values are greyed, not left looking filled',
          all('If(' in (rule(_s, v, 'Color') or '') for v in _vals))
    _edit = [c for (sc, c) in R if sc == _s
             and any(p in R[(sc, c)] for p in ('HintText', 'OnCheck', 'SelectedDate'))]
    check('print', f'{_p}: no editable controls on a read-only print view',
          not _edit, ','.join(_edit))
check('print', 'Podcast episodes come from the media list',
      'colPrintMedia' in (rule(POD_S, 'PPoD_Gallery', 'Items') or ''))
check('print', 'Video screen carries the legal section',
      any('Legal & Documents' in (rule(VIDEO_S, c, 'Text') or '')
          for (sc, c) in R if sc == VIDEO_S))
# every screen ScreensOrder names must exist and vice versa
_es = z.read('Src\\_EditorState.pa.yaml').decode('utf-8')
_listed = set(re.findall(r'^\s*- (\w+)\s*$', _es, re.M)) if 're' in dir() else set()
check('print', 'New screens are registered in ScreensOrder',
      all(x in _es for x in (PHOTO_S, VIDEO_S, POD_S)))

# behaviour properties must not be filed as data, or ";" chaining is invalid
_BEH = ('OnSelect', 'OnVisible', 'OnChange', 'OnAddFile', 'OnRemoveFile',
        'OnUndoRemoveFile', 'OnCheck', 'OnUncheck', 'OnStart')
_miscat = []
for (_sc, _cn), _rules in RAW.items():
    for _r in _rules:
        if _r['Property'] in _BEH and _r.get('Category') != 'Behavior':
            _miscat.append(f"{_sc}.{_cn}.{_r['Property']}={_r.get('Category')}")
check('print', 'Every behaviour rule is filed as Behavior', not _miscat, ','.join(_miscat[:5]))

# ---------------- production-type picker: only from "New request" (v33) ----------------
_ov_rq = rule(RQ, RQ, 'OnVisible') or ''
_navs = []
for (_s, _c), _g in R.items():
    for _p, _v in _g.items():
        for _m in re.finditer(r'Navigate\(\s*RequesDetailtScreen[^)]*\)', _v):
            _navs.append((_s, _c, _p, _m.group(0)))
check('picker', f'Every Navigate into RequesDetailtScreen passes locShowTypePicker ({len(_navs)} found)',
      len(_navs) == 7 and all('locShowTypePicker' in n_[3] for n_ in _navs),
      ','.join(n_[1] for n_ in _navs if 'locShowTypePicker' not in n_[3]))
check('picker', 'Only HomeBtnNew passes true',
      [n_[1] for n_ in _navs if 'locShowTypePicker: true' in n_[3]] == ['HomeBtnNew'])
check('picker', 'HomeRowSelect (gallery row: edit and view) passes false',
      any(n_[1] == 'HomeRowSelect' and 'locShowTypePicker: false' in n_[3] for n_ in _navs))
check('picker', 'Returns from the media tabs and the save paths pass false',
      all('locShowTypePicker: false' in n_[3] for n_ in _navs
          if n_[1] in ('CM_BtnPrev_1', 'CM_Back', 'CV_BtnSaveArchive', 'CL_FormAttach')))
check('picker', 'HomeBtnNew keeps its new-request setup before navigating',
      all(x in (rule(MR, 'HomeBtnNew', 'OnSelect') or '')
          for x in ("Set(varCurrentRequest, Defaults('AV-CD-Requests'))", 'Set(varRequestMediaType, "")')))
check('picker', 'OnVisible never assigns locShowTypePicker, so the value passed in survives',
      re.search(r'locShowTypePicker\s*:', _ov_rq) is None and 'Set(locShowTypePicker' not in _ov_rq)
check('picker', 'The old global varShowTypeConfirm is gone from the whole app',
      not any('varShowTypeConfirm' in v_ for g_ in R.values() for v_ in g_.values()))
_grp = [c for c in S[RQ]['Children'] if c['Name'] == 'grpProductionTypePicker']
check('picker', 'grpProductionTypePicker exists', len(_grp) == 1)
if _grp:
    check('picker', 'The group is still a classic group with no Visible of its own',
          not any(r['Property'] == 'Visible' for r in _grp[0]['Rules']))
    _mem = (_grp[0]['GroupedControlsKey'] or []) + ['RS_TypePickerRestart']
    _off = [m for m in _mem if (rule(RQ, m, 'Visible') or '').strip() != 'locShowTypePicker']
    check('picker', f'RS_TypePickerPanel and all {len(_mem) - 1} other picker controls follow locShowTypePicker',
          not _off and 'RS_TypePickerPanel' in _mem, ','.join(_off))
for _c, _want in (('RS_TypePickerClose', 'false'), ('RS_TypePickerOverlay', 'false'),
                  ('RS_CardPhotoBtn', 'false'), ('RS_CardVideoBtn', 'false'),
                  ('RS_CardPodcastBtn', 'false'), ('RS_TypeIconBtn', 'true'),
                  ('RS_TypePickerRestart', 'true')):
    check('picker', f'{_c} sets it {_want} with UpdateContext',
          f'UpdateContext({{locShowTypePicker: {_want}}})' in (rule(RQ, _c, 'OnSelect') or ''))
for _c, _t in (('RS_CardPhotoBtn', 'Photo'), ('RS_CardVideoBtn', 'Video'), ('RS_CardPodcastBtn', 'Podcast')):
    check('picker', f'{_c} keeps its selection logic',
          all(x in (rule(RQ, _c, 'OnSelect') or '')
              for x in (f'Set(varRequestMediaType, "{_t}")', 'Set(varConfirmed, true)')))
check('picker', 'RS_LblMissing follows the locShowDetails collapse idiom',
      (rule(RQ, 'RS_LblMissing', 'Y') or '') == 'If(locShowDetails,403,110)')

# ---------------- Draft Save / Submit write the opened request's real values (v35) ----------------
_hr = rule(MR, 'HomeRowSelect', 'OnSelect') or ''
check('save', 'Opening a request fills the variables the screen and saves read',
      'Set(varRequestTitle, Coalesce(ThisItem.RequestTitle' in _hr
      and 'Set(varRequestDescription, Coalesce(ThisItem.Description' in _hr)
check('save', 'RS_Title and RS_Description show the variables that are saved',
      rule(RQ, 'RS_Title', 'Default') == 'varRequestTitle'
      and rule(RQ, 'RS_Description', 'Default') == 'varRequestDescription')
check('save', 'HomeFilterDG shows and updates the request DG',
      rule(RQ, 'HomeFilterDG', 'Default') == 'varRequestDG'
      and 'Set(varRequestDG, Self.Selected.Value)' in (rule(RQ, 'HomeFilterDG', 'OnChange') or '')
      and 'Value = varRequestDG' in (rule(RQ, 'HomeFilterDG', 'Items') or ''))
check('save', 'OnVisible no longer overwrites an opened request DG',
      'IsBlank(varRequestDG) Or varRequestDG = ""' in _ov_rq)
for _cb, _col in (('RS_Owner', 'DG_Agency_Contact'), ('RS_Contractor', 'Contractor_Contact')):
    check('save', f'{_cb} pre-selects the saved {_col} people',
          f'varCurrentRequest.{_col} As p' in (rule(RQ, _cb, 'DefaultSelectedItems') or ''))
for _b in ('RS_BtnDraftSave', 'RS_BtnSubmitRequest', 'RS_BtnResubmitRequest'):
    _t = code_only(rule(RQ, _b, 'OnSelect'))
    check('save', f'{_b} saves what is on screen',
          _t.startswith('Set(varRequestTitle, RS_Title.Text)') and 'Set(varRequestDG, HomeFilterDG.Selected.Value)' in _t)
    check('save', f'{_b} writes only resolvable users to the Person columns',
          _t.count('DisplayName <> Mail) As u') == 2 and 'SelectedItems As u' not in _t)
    check('save', f'{_b} marks the management list for reload after success',
          'Set(varReqDataLoaded, false)' in _t)

# ---------------- manual contacts persist in their own text columns (v36) ----------------
for _k, _cb, _col in (('DG/Agency', 'RS_Owner', 'Manual_DG_Agency_Contact'),
                      ('Contractor', 'RS_Contractor', 'Manual_Contractor_Contact')):
    for _p in ('Items', 'DefaultSelectedItems'):
        check('manual', f'{_cb}.{_p} falls back to the saved {_col}',
              f'varCurrentRequest.{_col}' in (rule(RQ, _cb, _p) or ''))
    for _b in ('RS_BtnDraftSave', 'RS_BtnSubmitRequest', 'RS_BtnResubmitRequest'):
        check('manual', f'{_b} writes {_col} from the manual picks in {_cb}',
              f'{_col}: Concat(Filter({_cb}.SelectedItems, Not(IsBlank(Mail)) And DisplayName = Mail), Mail, "; ")'
              in (rule(RQ, _b, 'OnSelect') or ''))
for _b in ('RS_BtnDraftSave', 'RS_BtnSubmitRequest', 'RS_BtnResubmitRequest'):
    _t = code_only(rule(RQ, _b, 'OnSelect'))
    check('manual', f'{_b} hands over to the saved column only after the Patch',
          _t.index('Patch(') < _t.index('RemoveIf(colManualContacts, ParentRequest = varCurrentRequest.RequestNumber)'))

# ---------------- rich-text columns shown as plain text (v37) ----------------
for _col in ('Notes', 'PhotoCaption'):
    check('plain', f'colArchives.{_col} is loaded as plain text (feeds CI_Notes / CM_Caption)',
          f'{_col}: PlainText(Coalesce(' in _ov_rq)
check('plain', 'RV_CRowNotes shows plain text, and its save icon compares the same value',
      rule(RV, 'RV_CRowNotes', 'Default') == 'PlainText(Coalesce(ThisItem.Notes, ""))'
      and 'RV_CRowNotes.Text <> PlainText(Coalesce(ThisItem.Notes, ""))' in (rule(RV, 'RV_CRowNotesSave', 'DisplayMode') or ''))

# ---------------- current Power Fx syntax (v38) ----------------
_bad_ug = [f'{s_}.{c_}.{p_}' for (s_, c_), g in R.items() for p_, v_ in g.items()
           if re.search(r'Ungroup\([\s\S]*,\s*"[A-Za-z_]+"\s*\)', v_)]
check('syntax', 'No Ungroup passes its column as a quoted string', not _bad_ug, ','.join(_bad_ug))
_odata = [f'{s_}.{c_}.{p_}' for (s_, c_), g in R.items() for p_, v_ in g.items() if "'@odata.type'" in v_]
check('syntax', "Person values carry no legacy '@odata.type' field", not _odata, ','.join(_odata))

# ---------------- review queue reloads after each action (v41) ----------------
for _b in ('RV_BtnApprove', 'RV_BtnReject', 'RV_BtnNeedInfo'):
    _t = rule(RV, _b, 'OnSelect') or ''
    _ok = _t[:_t.rfind('Notify(')]          # success branch: everything before the failure Notify
    check('rv-reload', f'{_b} reloads the queue after a successful Patch',
          all(x in _ok for x in ("Refresh('AV-CD-Requests')", "ClearCollect(colRevReqs, 'AV-CD-Requests')",
                                 'Set(varReqDataLoaded, false)'))
          and _ok.index('Patch(') < _ok.index('ClearCollect(colRevReqs'))

# ---------------- HomeGallery status actions (v42) ----------------
for _c, _vis, _extra in (('HomeRowUserAction', 'ThisItem.Status.Value = "Pending"', '"User action'),
                         ('HomeRowContinue', 'IsBlank(ThisItem.Status.Value) Or ThisItem.Status.Value = "Draft"', 'Icon.Edit'),
                         ('HomeRowApproved', 'ThisItem.Status.Value = "Approved" Or ThisItem.Status.Value = "Partially approved"', 'Icon.Check')):
    _g = R.get((MR, _c), {})
    check('row-actions', f'{_c} shows only for its status and opens the row like a click',
          _g.get('Visible') == _vis and 'Select(HomeRowSelect)' in _g.get('OnSelect', '')
          and (_extra in _g.get('Text', '') or _g.get('Icon') == _extra)
          and _g.get('DisplayMode', 'DisplayMode.Edit') == 'DisplayMode.Edit')
check('row-actions', 'The check is green for Approved, amber for Partially approved',
      R.get((MR, 'HomeRowApproved'), {}).get('Color') == 'If(ThisItem.Status.Value = "Partially approved", RGBA(184, 134, 11, 1), RGBA(22, 128, 80, 1))')

# ---------------- administrator notes = ReviewerComments (v43) ----------------
check('admin-notes', 'RS_AdminNotes shows ReviewerComments, read-only placeholder for others',
      'varCurrentRequest.ReviewerComments' in (rule(RQ, 'RS_AdminNotes', 'Default') or '')
      and 'No notes from the administrator' in (rule(RQ, 'RS_AdminNotes', 'Default') or '')
      and 'varCurrentRequest.Notes' not in (rule(RQ, 'RS_AdminNotes', 'Default') or ''))
check('admin-notes', 'RS_AdminNotes saves ReviewerComments (SharePoint and the list cache)',
      (rule(RQ, 'RS_AdminNotes', 'OnChange') or '').count('{ReviewerComments: Self.Text, AdminNotesUpdatedOn: Now()}') == 2)
for _b in ('RS_BtnDraftSave', 'RS_BtnDraftSave_1', 'RS_BtnSubmitRequest', 'RS_BtnResubmitRequest'):
    _t = rule(RQ, _b, 'OnSelect') or ''
    check('admin-notes', f'{_b} keeps ReviewerComments (admin text, or the stored value for others)',
          'ReviewerComments: If(varUserRole = "ADMINISTRATOR", RS_AdminNotes.Text' in _t and 'Notes: If(' in _t.replace('ReviewerComments: If(', '')
          and 'AdminNotesUpdatedOn: If(' in _t and 'RequestorNotesUpdatedOn: If(' in _t)

# ---------------- Rejected vs Pending (Need info) (v44) ----------------
check('reject', 'Reject writes Rejected, Need info writes Pending, Approve writes Approved',
      'Status: {Value: "Rejected"}' in (rule(RV, 'RV_BtnReject', 'OnSelect') or '')
      and 'Status: {Value: "Pending"}' in (rule(RV, 'RV_BtnNeedInfo', 'OnSelect') or '')
      and '"Partially approved",' in (rule(RV, 'RV_BtnApprove', 'OnSelect') or '')
      and '"Approved"' in (rule(RV, 'RV_BtnApprove', 'OnSelect') or ''))
check('reject', 'The request screen announces Rejected and Pending differently',
      '"Rejected by "' in _ov_rq and '"More information requested by "' in _ov_rq)
check('reject', 'The rejection banner shows the reviewer comment',
      'varCurrentRequest.ReviewerComments' in (rule(RQ, 'RS_RejectionComment', 'Text') or ''))

# ---------------- v45: requestor notes, per-media approval, podcast channel ----------------
_rn = R.get((RQ, 'RS_RequestorNotes'), {})
check('v45', 'RS_RequestorNotes: owner edits (also while Processing), others read-only with a placeholder',
      'DisplayMode.Edit' in _rn.get('DisplayMode', '') and "'Created By'.Email" in _rn.get('DisplayMode', '')
      and 'No notes from the requestor' in _rn.get('Default', ''))
check('v45', 'RS_RequestorNotes saves Notes + RequestorNotesUpdatedOn (SharePoint and list cache)',
      _rn.get('OnChange', '').count('{Notes: Self.Text, RequestorNotesUpdatedOn: Now()}') == 2)
for _c, _col in (('RS_AdminNotesUpdated', 'AdminNotesUpdatedOn'), ('RS_RequestorNotesUpdated', 'RequestorNotesUpdatedOn')):
    check('v45', f'{_c} shows "Last updated on" from {_col}',
          f'varCurrentRequest.{_col}' in (rule(RQ, _c, 'Text') or '') and 'Last updated on' in (rule(RQ, _c, 'Text') or ''))
for _b in ('RV_BtnReject', 'RV_BtnNeedInfo'):
    check('v45', f'{_b} stamps AdminNotesUpdatedOn with the comment', 'AdminNotesUpdatedOn: Now()' in (rule(RV, _b, 'OnSelect') or ''))
_ap = R.get((RQ, 'RS_CRowApproved'), {})
check('v45', 'RS_CRowApproved: admin-only checkbox in RS_ChildrenGallery that saves MediaApproved',
      'varUserRole = "ADMINISTRATOR"' in _ap.get('DisplayMode', '') and 'MediaApproved: true' in _ap.get('OnCheck', '')
      and 'MediaApproved: false' in _ap.get('OnUncheck', '')
      and any(k['Name'] == 'RS_CRowApproved' for c in S[RQ]['Children'] if c['Name'] == 'RS_ChildrenGallery' for k in c['Children']))
check('v45', 'colArchives loads MediaApproved and PublicationChannel',
      'MediaApproved: Coalesce(MediaApproved, false)' in _ov_rq and 'PublicationChannel: Concat(PublicationChannel, Value, ";")' in _ov_rq)
_sv = rule('ChildValidScreen', 'CV_BtnSaveArchive', 'OnSelect') or ''
check('v45', 'Save Media writes PublicationChannel (Beluga / Spotify)',
      'PublicationChannel: ForAll(Filter(' in _sv and 'varChildPubSpotify' in _sv)
check('v45', 'Opening a media item loads the channel; a new one clears it',
      'Set(varChildPubSpotify, "Spotify" in' in (rule(RQ, 'RS_CRowSelect', 'OnSelect') or '')
      and 'Set(varChildPubSpotify, false)' in (rule(RQ, 'RS_BtnDraftSave_1', 'OnSelect') or ''))
for _scr in ('ChildInfoScreen', 'ChildMetaScreen'):
    check('v45', f'{_scr} takes the attachments snapshot so its file lists show the open item',
          'Set(varAttachRecord' in (rule(_scr, _scr, 'OnVisible') or ''))
check('v45', 'P1-21: Request Management opens with the filter sections expanded',
      'locShowFilters: true' in (rule(MR, MR, 'OnVisible') or ''))

# ---------------- v46: podcast image size alerts (flow result columns) ----------------
for _s, _c, _col in (('ChildInfoScreen', 'CI_PodcastVisualCheck', 'PodcastVisualCheck'),
                     ('ChildMetaScreen', 'CM_EpisodeVisualCheck', 'EpisodeVisualCheck')):
    _t = rule(_s, _c, 'Text') or ''
    check('v46', f'{_c} shows pending / OK / the flow message from {_col}',
          f'.{_col}' in _t and 'pending' in _t and '"⚠ " & r' in _t and rule(_s, _c, 'Visible') == 'varChildMediaType = "Podcast"')
check('v46', 'colArchives loads both check columns',
      'PodcastVisualCheck: Coalesce(PodcastVisualCheck, "")' in _ov_rq and 'EpisodeVisualCheck: Coalesce(EpisodeVisualCheck, "")' in _ov_rq)
for _b in ('RS_BtnSubmitRequest', 'RS_BtnResubmitRequest'):
    _d = rule(RQ, _b, 'DisplayMode') or ''
    check('v46', f'{_b} is blocked only by a known failure, never by a pending check',
          'Not(IsBlank(PodcastVisualCheck)) And PodcastVisualCheck <> "OK"' in _d
          and 'Not(IsBlank(EpisodeVisualCheck)) And EpisodeVisualCheck <> "OK"' in _d)
for _s, _c in ((RQ, 'RS_CRowValid'), (RV, 'RV_CRowValid')):
    check('v46', f'{_c} flags a failed image check', 'ThisItem.PodcastVisualCheck' in (rule(_s, _c, 'Text') or '') and 'Image size' in (rule(_s, _c, 'Text') or ''))
check('v46', 'RS_LblMissing lists failed podcast image sizes', 'Podcast image sizes' in (rule(RQ, 'RS_LblMissing', 'Text') or ''))

# ---------------- after a media save: back to the request, type restored, no picker ----------------
_save = rule('ChildValidScreen', 'CV_BtnSaveArchive', 'OnSelect') or ''
_navc = _save.count('Navigate(RequesDetailtScreen')
check('save-return', 'Save has exactly 2 direct success paths, both navigating back', _navc == 2, str(_navc))
check('save-return', 'Both clear the saved type', _save.count('Set(varRequestMediaType, "")') == 2)
_FAIL = 'Notify("Save failed: " & FirstError.Message, NotificationType.Error)'
check('save-return', 'The failure path is untouched and does not reset the form', _save.count(_FAIL) == 1)
check('save-return', 'OnVisible restores the type from the saved media, so no picker is needed',
      'Set(\n        varRequestMediaType,\n        First(colArchives).MediaType\n    )' in _ov_rq
      and _ov_rq.index('Clear(colArchives)') < _ov_rq.index('First(colArchives).MediaType'))
check('save-return', 'Cards unlock once the type is cleared (unchanged precondition)',
      all('varRequestMediaType <> ""' in (rule(RQ, c, 'DisplayMode') or '')
          for c in ('RS_CardPhotoBtn', 'RS_CardVideoBtn', 'RS_CardPodcastBtn')))

# ---------------- contact "+" buttons follow their own combo box (v33) ----------------
for _b, _cb in (('RS_DetailsToggle_contrator_1', 'RS_Owner'), ('RS_DetailsToggle_contrator', 'RS_Contractor')):
    _dm = code_only(rule(RQ, _b, 'DisplayMode'))
    _other = 'RS_Contractor' if _cb == 'RS_Owner' else 'RS_Owner'
    check('contact+', f'{_b} is enabled while {_cb} is empty, and only its own combo box counts',
          f'IsEmpty({_cb}.SelectedItems)' in _dm and _other not in _dm)
    check('contact+', f'{_b} stays disabled in view mode', 'Not(varRequestorLocked)' in _dm)
check('contact+', 'The pairing matches the popup type each button opens',
      '"DG/Agency"' in (rule(RQ, 'RS_DetailsToggle_contrator_1', 'OnSelect') or '')
      and '"Contractor"' in (rule(RQ, 'RS_DetailsToggle_contrator', 'OnSelect') or ''))
for _cb, _k in (('RS_Owner', 'DG/Agency'), ('RS_Contractor', 'Contractor')):
    check('contact+', f'{_cb} still pre-selects its manual email (so it counts as filled)',
          f'ContactType = "{_k}"' in (rule(RQ, _cb, 'DefaultSelectedItems') or ''))
check('contact+', 'Only the management-screen entries reset the contact pickers',
      sorted(n_[1] for n_ in _navs if 'locResetContacts: true' in n_[3]) == ['HomeBtnNew', 'HomeRowSelect']
      and all('locResetContacts' in n_[3] for n_ in _navs))
check('contact+', 'OnVisible resets both combo boxes on that flag, then clears it',
      all(x in _ov_rq for x in ('locResetContacts,', 'Reset(RS_Owner)', 'Reset(RS_Contractor)',
                                'UpdateContext({locResetContacts: false})')))
for _c in ('RS_BtnDraftSave', 'RS_BtnDraftSave_1'):
    _t = rule(RQ, _c, 'OnSelect') or ''
    check('contact+', f'{_c} moves manual contacts onto the request number it just created',
          'UpdateIf(\n' in _t and 'colManualContacts' in _t
          and _t.index('Set(varCurrentRequest') < _t.index('colManualContacts'))
_hn = rule(MR, 'HomeBtnNew', 'OnSelect') or ''
check('contact+', 'New request drops manual contacts left by an abandoned new request',
      'RemoveIf(colManualContacts, IsBlank(ParentRequest)' in _hn
      and _hn.index('RemoveIf(colManualContacts') < _hn.index('Navigate('))

# ---------------- fresh read of colMyReqs/colMyMedia on RequestManagementScreen ----------------
_mr_ov = rule(MR, MR, 'OnVisible') or ''
check('refresh', "Requests are refreshed before the ClearCollect that feeds the gallery",
      "Refresh('AV-CD-Requests')" in _mr_ov
      and _mr_ov.find("Refresh('AV-CD-Requests')") < _mr_ov.find("ClearCollect(colMyReqs"))
check('refresh', "Media files are refreshed before their ClearCollect",
      "Refresh('AV-CD-Mediafiles')" in _mr_ov
      and _mr_ov.find("Refresh('AV-CD-Mediafiles')") < _mr_ov.find("ClearCollect(colMyMedia"))
check('refresh', "Neither refresh is duplicated",
      _mr_ov.count("Refresh('AV-CD-Requests')") == 1
      and _mr_ov.count("Refresh('AV-CD-Mediafiles')") == 1)

# ---------------- Section 1: management screen row data + no reset ----------------
_arch = rule(MR, 'HomeRowArchives', 'Text') or ''
check('mgmt', '1.1 HomeRowArchives counts the row\'s media files',
      'CountRows(' in _arch and 'colMyMedia' in _arch and 'RequestTitle' not in _arch)
check('mgmt', '1.1 counts the local collection, so no delegation warning',
      "'AV-CD-Mediafiles'" not in _arch)
_rr = rule(MR, 'HomeRowRequest', 'Text') or ''
check('mgmt', '1.2 Per-row icon when no production-type filter is applied',
      'IsBlank(locProdTypeFilter)' in _rr and 'colMyMedia' in _rr)
check('mgmt', '1.2 Keeps the filter-based icon when a type is selected',
      _rr.count('ThisItem.RequestNumber') >= 8)
check('mgmt', '1.2 Does not reference a ProductionType column that does not exist',
      'ProductionType' not in _rr)
_ov = ' '.join((rule(MR, MR, 'OnVisible') or '').split())
check('mgmt', '1.3 Data loads once per session, self-healing when empty',
      'Not(varReqDataLoaded) Or IsEmpty(colMyReqs)' in _ov)
check('mgmt', '1.3 Filters initialise once, so they survive navigating away',
      'Not(varReqFiltersInit)' in _ov)
check('mgmt', '1.3 varUserRole is set outside the load gate',
      'Set( varUserRole,' in _ov
      and _ov.index('Set( varUserRole,') < _ov.index('Not(varReqDataLoaded)'))
check('mgmt', '1.3 A dashboard status jump still applies every visit',
      'Not(IsBlank(varNavFilter))' in _ov and 'Set(varNavFilter, Blank())' in _ov)
check('mgmt', '1.3 All five collections are still built',
      all(c in _ov for c in ('colDGOptions', 'colAssignees', 'colMyReqs',
                             'colMyMedia', 'colRequestorOptions')))
check('mgmt', '1.3 The 2000-row ceiling warning survives', '2000' in _ov)
_rf = rule(MR, 'HomeBtnRefresh', 'OnSelect') or ''
check('mgmt', '1.3 Explicit reload button reloads both lists and clears the gate',
      all(x in _rf for x in ("Refresh('AV-CD-Requests')", 'ClearCollect(colMyReqs',
                             'Set(varReqDataLoaded, true)')))
check('mgmt', '1.3 Reload button clear of its neighbours in the action row',
      (lambda x, w: x >= 648 and x + w <= 1059)
      (int(rule(MR, 'HomeBtnRefresh', 'X')), int(rule(MR, 'HomeBtnRefresh', 'Width'))))

# ---------------- Section 2: contact popup + manual email ----------------
_pw, _ph = int(rule(RQ, 'RS_ContactPopup', 'Width')), int(rule(RQ, 'RS_ContactPopup', 'Height'))
_px, _py = int(rule(RQ, 'RS_ContactPopup', 'X')), int(rule(RQ, 'RS_ContactPopup', 'Y'))
check('contact', '2.1 Popup is 70-80% of the screen on both axes',
      0.70 <= _pw / 1366 <= 0.80 and 0.70 <= _ph / 768 <= 0.80,
      f'{_pw / 1366:.0%} x {_ph / 768:.0%}')
check('contact', '2.1 Popup is centred',
      abs(_px - (1366 - _pw) / 2) <= 1 and abs(_py - (768 - _ph) / 2) <= 1)
check('contact', '2.1 Overlay still follows the popup flag',
      (rule(RQ, 'RS_ContactBackdrop', 'Visible') or '').strip() == 'locShowContactPopup')
_POPUP_KIDS = ['RS_LblContactType', 'RS_drpContactType', 'RS_LblEmailContact',
               'RS_txtEmailContact', 'RS_btnSaveContact', 'RS_btnCancelContact',
               'RS_ContactTitle', 'RS_LblSavedHead', 'RS_SavedCardContractor',
               'RS_SavedTypeContractor', 'RS_SavedEmailContractor',
               'RS_SavedCardDGAgency', 'RS_SavedTypeDGAgency', 'RS_SavedEmailDGAgency']
_out = []
for _c in _POPUP_KIDS:
    try:
        _cx, _cy = int(rule(RQ, _c, 'X')), int(rule(RQ, _c, 'Y'))
        _cw, _ch = int(rule(RQ, _c, 'Width')), int(rule(RQ, _c, 'Height'))
    except (TypeError, ValueError):
        _out.append(f'{_c}:unreadable')
        continue
    if _cx < _px or _cy < _py or _cx + _cw > _px + _pw or _cy + _ch > _py + _ph:
        _out.append(_c)
check('contact', f'2.1 All {len(_POPUP_KIDS)} popup controls sit inside the popup',
      not _out, ','.join(_out))
check('contact', '2.1 Every popup control is tied to locShowContactPopup',
      all((rule(RQ, _c, 'Visible') or '').strip() == 'locShowContactPopup'
          for _c in _POPUP_KIDS))
for _slug, _kind, _other in (('Contractor', 'Contractor', 'DG/Agency'),
                             ('DGAgency', 'DG/Agency', 'Contractor')):
    _t = rule(RQ, f'RS_SavedEmail{_slug}', 'Text') or ''
    check('contact', f'2.1 {_kind} row reads only its own type, newest first',
          f'ContactType = "{_kind}"' in _t and f'ContactType = "{_other}"' not in _t
          and 'Last(' in _t)
    check('contact', f'2.1 {_kind} row falls back to a placeholder',
          'Not defined' in _t)
    check('contact', f'2.1 {_kind} row greys the placeholder',
          'IsBlank(' in (rule(RQ, f'RS_SavedEmail{_slug}', 'Color') or ''))
for _ctl, _kind in (('RS_Owner', 'DG/Agency'), ('RS_Contractor', 'Contractor')):
    _it = rule(RQ, _ctl, 'Items') or ''
    check('contact', f'2.2 {_ctl} unions the directory with its {_kind} manual email',
          all(x in _it for x in ('SearchUserV2', 'colManualContacts', 'Ungroup(',
                                 f'ContactType = "{_kind}"')))
    check('contact', f'2.2 {_ctl} projects both sides to one schema so the types unify',
          '{DisplayName: o.DisplayName, Mail: o.Mail}' in _it
          and '{DisplayName: locManual, Mail: locManual}' in _it)
    check('contact', f'2.2 {_ctl} pre-selects the manual email when there is one',
          'colManualContacts' in (rule(RQ, _ctl, 'DefaultSelectedItems') or ''))
    check('contact', f'2.2 {_ctl} still displays and searches on DisplayName',
          (rule(RQ, _ctl, 'DisplayFields') or '').strip() == '["DisplayName"]'
          and (rule(RQ, _ctl, 'SearchFields') or '').strip() == '["DisplayName"]')

# ---------------- package integrity ----------------
total, missing = 0, []
for n in [i.filename for i in z.infolist()]:
    if n.startswith('Controls\\'):
        d = json.loads(z.read(n).decode('utf-8'))

        def chk(c):
            global total
            total += 1
            if 'Children' not in c:
                missing.append(c['Name'])
            for k in c.get('Children', []):
                chk(k)
        chk(d['TopParent'])
check('pkg', f'All {total} controls carry "Children"', not missing, ','.join(missing[:5]))
check('pkg', 'No invented identifiers remain',
      not any(b in z.read(n).decode('utf-8', 'replace')
              for n in [i.filename for i in z.infolist()] if n.endswith(('.json', '.pa.yaml'))
              for b in ('SearchFn', 'varFilterProductionType', "'Assigned To'", 'AssignedTo')))

# ---------------- report ----------------
w = max(len(n) for _, n, _, _ in results)
cur = None
npass = 0
for sec, name, ok, detail in results:
    if sec != cur:
        cur = sec
        print(f'\n--- {"Section " + sec if sec.isdigit() else sec} ---')
    npass += ok
    print(f'  [{"PASS" if ok else "FAIL"}] {name:{w}s}' + (f'  {detail}' if detail and not ok else ''))
print(f'\n{npass}/{len(results)} static checks passed')
sys.exit(0 if npass == len(results) else 1)
