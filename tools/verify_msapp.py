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
    '/home/user/PowerApps_AJF/msapp-versions/AV-CD-v24-printdetails.msapp'
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
check('1', 'Need-info is admin-only, author-excluded, requires a comment',
      has(RV, 'RV_BtnNeedInfo', 'DisplayMode', 'varUserRole = "ADMINISTRATOR"',
          "<> Lower(User().Email)", 'varReviewComment <> ""'))
check('1', 'Need-info stores the reviewer comment', has(RV, 'RV_BtnNeedInfo', 'OnSelect', 'ReviewerComments'))
check('1', 'Review queue lists Processing, not Pending',
      has(RV, 'RV_QueueGallery', 'Items', '"Processing"') and '"Pending"' not in (rule(RV, 'RV_QueueGallery', 'Items') or ''))
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
bad = [p for p in STYLE if rule(RQ, 'RS_BtnDraftSave_1', p) != rule(RQ, 'RS_BtnDraftSave', p)]
check('2', f'Media matches Save on all {len(STYLE)} style properties', not bad, ','.join(bad))
check('2', 'Media keeps its own caption and position',
      rule(RQ, 'RS_BtnDraftSave_1', 'Text') != rule(RQ, 'RS_BtnDraftSave', 'Text')
      and rule(RQ, 'RS_BtnDraftSave_1', 'X') != rule(RQ, 'RS_BtnDraftSave', 'X'))

# ---------------- carried forward from v4-v10 ----------------
check('prior', 'Self-approval closed on ReviewScreen',
      has(RV, 'RV_BtnApprove', 'DisplayMode', 'varUserRole = "ADMINISTRATOR"', '<> Lower(User().Email)'))
check('prior', 'Review queue excludes your own requests',
      has(RV, 'RV_QueueGallery', 'Items', "Lower('Created By'.Email) <> Lower(User().Email)"))
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
        if LOCKVAR in dm:
            nlocked += 1
        elif not (c_ == 'CI_Notes' or 'varUserRole' in dm or c_ == 'CI_TplSearch'):
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

# ---------------- attachments ----------------
CI2, CM2, CL2, CV2 = 'ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen'
BOXES = [(CI2, 'CI_PodcastVisual'), (CM2, 'CM_EpisodeVisual'),
         (CL2, 'CL_Annex'), (CL2, 'CL_VTTUpload')]
REC = "LookUp('AV-CD-Mediafiles', ID = Coalesce(varCurrentChildSPId, 0))"
for scr, ctl in BOXES:
    check('attach', f'{ctl} loads the item\'s attachments',
          (rule(scr, ctl, 'Items') or '') == f'{REC}.Attachments')
    check('attach', f'{ctl} persists add/remove/undo',
          all(f'{{Attachments: {ctl}.Attachments}}' in (rule(scr, ctl, p) or '')
              and 'IfError(' in (rule(scr, ctl, p) or '')
              for p in ('OnAddFile', 'OnRemoveFile', 'OnUndoRemoveFile')))
    check('attach', f'{ctl} still locked while Processing',
          'varRequestorLocked' in (rule(scr, ctl, 'DisplayMode') or ''))
# every box writes only its own output, never a sibling's
crossed = []
for scr, ctl in BOXES:
    for p in ('OnAddFile', 'OnRemoveFile', 'OnUndoRemoveFile'):
        v = rule(scr, ctl, p) or ''
        crossed += [f'{ctl}.{p}->{o}' for _, o in BOXES if o != ctl and o in v]
check('attach', 'No box overwrites another box\'s output', not crossed, ','.join(crossed))
# a shared bag makes an unfiltered CountRows meaningless, so none may remain
vacuous = []
for scr, ctl, prop in ((CV2, CV2, 'OnVisible'), (CV2, 'CV_BtnRefresh', 'OnSelect'),
                       (CI2, 'CI_LblMissing', 'Text'), (CL2, 'CL_LblMissing', 'Text')):
    v = rule(scr, ctl, prop) or ''
    for _, box in BOXES:
        if f'CountRows({box}.Attachments)' in v:
            vacuous.append(f'{ctl}.{prop}:{box}')
check('attach', 'No rule counts the whole shared bag unfiltered', not vacuous, ','.join(vacuous))

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
_nav = rule(HPS, 'HP_Gallery', 'OnSelect') or ''
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
