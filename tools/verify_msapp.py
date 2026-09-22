#!/usr/bin/env python3
"""Static verification of everything shipped so far, read back out of the .msapp.

This is not a runtime test -- nothing here proves Power Fx compiles or that
SharePoint accepts a write. It proves that each change is actually present and
wired the way it was described, which is the part that can be checked without
Studio. Anything depending on data or on a SharePoint column is listed in the
manual matrix instead.
"""
import io, json, sys, zipfile
import yaml
from paload import PaLoader

MSAPP = sys.argv[1] if len(sys.argv) > 1 else \
    '/home/user/PowerApps_AJF/msapp-versions/AV-CD-v12-section2.msapp'
z = zipfile.ZipFile(MSAPP)
S, R = {}, {}
for n in [i.filename for i in z.infolist()]:
    if n.startswith('Controls\\'):
        d = json.loads(z.read(n).decode('utf-8'))
        tp = d['TopParent']
        S[tp['Name']] = tp

        def walk(c, scr):
            R[(scr, c['Name'])] = {r['Property']: r['InvariantScript'] for r in c['Rules']}
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
