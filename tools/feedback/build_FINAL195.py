#!/usr/bin/env python3
"""FINAL195 on FINAL194. Admin evaluation feedback.
1. Review page: hint sentence above the message box; Pending / Rejected become active while typing (live RV_Comment.Text,
   no need to click outside); the decision formulas take the text straight from the box.
2. Request screen: an administrator who opened a Processing request from the Review queue gets a decision bar at the bottom
   (message box + Approved / Pending / Rejected, same logic as the Review page, no archive-only) and lands back on the queue."""
import datetime, os, re, shutil
from payaml import App, find
from hp_common import Builder
SRC, NEW = 'newV56', 'newV57'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def sub(t, old, new, n=1):
    assert t.count(old) == n, (old[:70], t.count(old)); return t.replace(old, new)
def edit(screen, ctl, prop, fn):
    t = app.rule(screen, ctl, prop); n = fn(t); assert n != t, (screen, ctl, prop)
    app.set(screen, ctl, prop, n, expect=t)
RV, RS = 'ReviewScreen', 'RequesDetailScreen'
# ---------- 1. Review page
edit(RV, 'RV_LblComment', 'Text', lambda t: '"Message to the requestor  -  if the request still needs further clarification or is rejected, please write the justification below"')
edit(RV, 'RV_LblComment', 'Width', lambda t: '880')
LIVE_OLD = 'And Not(IsBlank(varReviewComment)) And varReviewComment <> "",'
for c in ('RV_BtnNeedInfo', 'RV_BtnReject'):
    edit(RV, c, 'DisplayMode', lambda t: sub(t, LIVE_OLD, '// active while typing: the box is read live, no need to leave it\n    And Not(IsBlank(Trim(RV_Comment.Text))),'))
edit(RV, 'RV_BtnApprove', 'DisplayMode', lambda t: sub(t, 'IsBlank(Trim(varReviewComment))', 'IsBlank(Trim(RV_Comment.Text))'))
for c in ('RV_BtnApprove', 'RV_BtnNeedInfo', 'RV_BtnReject'):
    edit(RV, c, 'OnSelect', lambda t: '// the box is the source of truth (its OnChange may not have fired yet)\nSet(varReviewComment, RV_Comment.Text);\n' + t)
# ---------- 2. decision bar on the request screen
DEC = 'Coalesce(locFromReview, false) And varUserRole = "ADMINISTRATOR" And Coalesce(varCurrentRequest.Status.Value, "") = "Processing"'
def adapt(t, approve=False):
    t = sub(t, '// the box is the source of truth (its OnChange may not have fired yet)\nSet(varReviewComment, RV_Comment.Text);\n', '')
    t = t.replace('varReviewProject', 'varCurrentRequest').replace('varReviewComment', 'RS_DecComment.Text')
    if approve:
        t = sub(t, 'If(RV_ArchiveOnly.Value And Not(Coalesce(varCurrentRequest.ArchivedOnly, false)), "Approved - archive only", "Approved")', '"Approved"')
        t = sub(t, 'ArchivedOnly: RV_ArchiveOnly.Value,', 'ArchivedOnly: Coalesce(varCurrentRequest.ArchivedOnly, false),')
        i = t.index('    Notify(\n        If(\n            RV_ArchiveOnly.Value'); j = t.index('NotificationType.Success\n    );', i) + len('NotificationType.Success\n    );')
        t = t[:i] + '    Notify("Request approved." & If(noAssignee, " You are now the assignee.", ""), NotificationType.Success);' + t[j:]
    assert 'RV_' not in t, re.findall(r'RV_\w+', t)
    t = sub(t, 'Set(varCurrentRequest, Blank());\n    Set(RS_DecComment.Text, "");', 'Set(varReviewProject, Blank());\n    Set(varReviewComment, "");\n    Set(varReviewFromRow, false);\n    Reset(RS_DecComment);')
    t = sub(t, '    Set(varReqDataLoaded, false),', '    Set(varReqDataLoaded, false);\n    // back to the Review queue\n    Navigate(ReviewScreen, ScreenTransition.UnCover),')
    return t
APPROVE = adapt(app.rule(RV, 'RV_BtnApprove', 'OnSelect'), True)
PENDING = adapt(app.rule(RV, 'RV_BtnNeedInfo', 'OnSelect'))
REJECT = adapt(app.rule(RV, 'RV_BtnReject', 'OnSelect'))
b = Builder(app, RS)
b.clone('RS_DecBar', RS, 'RS_LeavePanel', {'X': '26', 'Y': '712', 'Width': '1296', 'Height': '56', 'Fill': 'RGBA(247, 248, 250, 1)',
        'BorderThickness': '0', 'Visible': DEC})
b.clone('RS_DecComment', RV, 'RV_Comment', {'X': '260', 'Y': '719', 'Width': '510', 'Height': '43', 'Mode': 'TextMode.SingleLine', 'Size': '11',
        'Default': '""', 'OnChange': 'false', 'Visible': DEC, 'DisplayMode': 'DisplayMode.Edit',
        'HintText': '"Message to the requestor  -  required for Pending / Rejected"', 'AccessibleLabel': '"Message to the requestor"',
        'Tooltip': '"If the request still needs further clarification or is rejected, please write the justification here"'})
NEED = f'If({DEC} And Not(IsBlank(Trim(RS_DecComment.Text))), DisplayMode.Edit, DisplayMode.Disabled)'
b.clone('RS_DecApprove', RV, 'RV_BtnApprove', {'X': '782', 'Y': '719', 'Width': '130', 'Height': '43', 'Size': '11', 'Text': '"✓  Approved"',
        'Visible': DEC, 'DisplayMode': f'If({DEC}, DisplayMode.Edit, DisplayMode.Disabled)', 'OnSelect': APPROVE,
        'Tooltip': '"Approve this request (the message, if any, goes to its Message Center)"'})
b.clone('RS_DecPending', RV, 'RV_BtnNeedInfo', {'X': '920', 'Y': '719', 'Width': '120', 'Height': '43', 'Size': '11',
        'Visible': DEC, 'DisplayMode': NEED, 'OnSelect': PENDING, 'Tooltip': '"Send back to the requestor: write the justification first"'})
b.clone('RS_DecReject', RV, 'RV_BtnReject', {'X': '1048', 'Y': '719', 'Width': '120', 'Height': '43', 'Size': '11',
        'Visible': DEC, 'DisplayMode': NEED, 'OnSelect': REJECT, 'Tooltip': '"Reject this request: write the justification first"'})
b.save()
edit(RS, 'Label12_6', 'Visible', lambda t: f'Not({DEC})')
# z-order: the bar sits above everything (it is the last block in the YAML too)
tp = app.doc(RS)['TopParent']
def z(n):
    v = [x for x in n['Rules'] if x['Property'] == 'ZIndex']; return int(v[0]['InvariantScript']) if v else 0
def deep(n):
    yield n
    for c in n.get('Children', []): yield from deep(c)
NEWC = ['RS_DecBar', 'RS_DecComment', 'RS_DecApprove', 'RS_DecPending', 'RS_DecReject']
mx = max(z(n) for n in deep(tp) if n['Name'] not in NEWC)
for i, nm in enumerate(NEWC):
    [x for x in find(tp, nm)['Rules'] if x['Property'] == 'ZIndex'][0]['InvariantScript'] = str(mx + 1 + i)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL195 built')
