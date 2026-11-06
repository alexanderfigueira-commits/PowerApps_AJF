#!/usr/bin/env python3
"""FINAL16 on FINAL15: the administrator can approve a request as "archive only" (ReviewScreen).

* RV_ArchiveOnly (administrators): "Archive only: the conditions for publication are not met". Shows what is saved
  (ArchivedOnly of the request, ticked by the requestor or not) and can be changed before approving.
* Approve saves ArchivedOnly with the decision. When the administrator turns it ON, a reason is required
  (RV_Comment): it is saved in ReviewerComments and added to AV-CD-Notes as an Administrator note, so the requestor
  sees it in the app, and the "request approved, archive only" email is sent by the notification flow
  (flow spec in the hand-over message): Status = Approved / Partially approved AND ArchivedOnly = Yes.
* RV_RejectHint tells the administrator that the reason is needed.
"""
import datetime, os, re, shutil, sys
from payaml import App, find
from hp_common import Builder

SRC, NEW = 'newG5', 'newG6'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RV = 'ReviewScreen'
NEWARCH = 'RV_ArchiveOnly.Value And Not(Coalesce(varReviewProject.ArchivedOnly, false))'

# ---- the checkbox (a clone of the Archiving-only checkbox of the request screen: same look)
b = Builder(app, RV)
ck = b.clone('RV_ArchiveOnly', 'RequesDetailScreen', 'RS_Archive', {
    'Text': '"Archive only: the conditions for publication are not met"',
    'Default': 'Coalesce(varReviewProject.ArchivedOnly, false)',
    'DisplayMode': 'If(varUserRole = "ADMINISTRATOR" And Coalesce(varReviewProject.Status.Value, "") = "Processing", DisplayMode.Edit, DisplayMode.View)',
    'OnCheck': 'false', 'OnUncheck': 'false',
    'Visible': 'Not(IsBlank(varReviewProject)) And varUserRole = "ADMINISTRATOR"',
    'X': '870', 'Y': '506', 'Width': '470', 'Height': '48',
})
b.save()
# stacking: same level as the assignee box (JSON only, as in Studio's own YAML there is no ZIndex line)
z = int(app.rule(RV, 'RV_Assignee', 'ZIndex'))
ckc = find(app.doc(RV)['TopParent'], 'RV_ArchiveOnly')
[r for r in ckc['Rules'] if r['Property'] == 'ZIndex'][0]['InvariantScript'] = str(z)
for e in ckc.get('ControlPropertyState', []):
    if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString'):
        e['AutoRuleBindingString'] = str(z)
app.save()

# ---- reason hint
ht, hv = app.rule(RV, 'RV_RejectHint', 'Text'), app.rule(RV, 'RV_RejectHint', 'Visible')
app.set(RV, 'RV_RejectHint', 'Text', f'If({NEWARCH}, "A reason is required for archive-only: it is sent to the requestor.", {ht})', expect=ht)

# ---- Approve
dm = app.rule(RV, 'RV_BtnApprove', 'DisplayMode')
old_dm = '''If(
    Not(IsBlank(varReviewProject)) And varUserRole = "ADMINISTRATOR"
    And varReviewProject.Status.Value = "Processing",
    DisplayMode.Edit,
    DisplayMode.Disabled
)'''
if ' '.join(dm.split()) != ' '.join(old_dm.split()):
    sys.exit('! Approve DisplayMode changed')
app.set(RV, 'RV_BtnApprove', 'DisplayMode', '''If(
    Not(IsBlank(varReviewProject)) And varUserRole = "ADMINISTRATOR"
    And varReviewProject.Status.Value = "Processing"
    // turning archive-only ON needs a reason (it goes to the requestor)
    And Not(%s And IsBlank(Trim(varReviewComment))),
    DisplayMode.Edit,
    DisplayMode.Disabled
)''' % NEWARCH, expect=dm)
tx = app.rule(RV, 'RV_BtnApprove', 'Text')
app.set(RV, 'RV_BtnApprove', 'Text', 'If(RV_ArchiveOnly.Value, "✓  Approve · Archive", "✓  Approve")', expect=tx)

t = app.rule(RV, 'RV_BtnApprove', 'OnSelect')
m = re.search(r'\n( *)ReviewedDate: Now\(\)\n', t)
if not m or t.count('ReviewedDate: Now()') != 1:
    sys.exit('! Approve: ReviewedDate not found')
ind = m.group(1)
fields = (f'\n{ind}ReviewedDate: Now(),\n'
          f'{ind}// "archive only": saved with the decision; the reason (RV_Comment) goes to ReviewerComments for the email\n'
          f'{ind}ArchivedOnly: RV_ArchiveOnly.Value,\n'
          f'{ind}ReviewerComments: If({NEWARCH}, Trim(varReviewComment), varReviewProject.ReviewerComments)\n')
n = t[:m.start()] + fields + t[m.end():]
# the reason also becomes a note the requestor reads in the app
NOTE = '''    // archive-only decision: the reason is also a note of the request (AV-CD-Notes), the email comes from the notification flow
    If(
        %s,
        IfError(
            Patch(
                'AV-CD-Notes',
                Defaults('AV-CD-Notes'),
                {
                    Title: varReviewProject.RequestNumber,
                    ParentRequest: varReviewProject.RequestNumber,
                    NoteText: "<b>Approved - archive only</b> · " & Substitute(Trim(varReviewComment), Char(10), "<br>"),
                    AuthorRole: {Value: "Administrator"},
                    AuthorName: User().FullName,
                    AuthorEmail: User().Email,
                    NoteDate: Now()
                }
            ),
            Notify("The reason could not be added to the notes: " & FirstError.Message, NotificationType.Warning)
        )
    );
''' % NEWARCH
i = n.index('\n    Notify(\n        If(With(')
n = n[:i] + '\n' + NOTE.rstrip('\n') + n[i:]
old_notify = '"Request partially approved: only the ticked media files are approved.", "Request approved.")'
if n.count(old_notify) != 1:
    sys.exit('! Approve: notify text changed')
n = n.replace(old_notify, old_notify[:-1] + ')')  # no-op guard
n = n.replace('''        If(With(
                {n: CountRows(RV_ChildrenGallery.AllItems), ok: CountRows(Filter(RV_ChildrenGallery.AllItems, MediaApproved = true))},
                ok > 0 And ok < n
            ), "Request partially approved: only the ticked media files are approved.", "Request approved."),''',
              '''        If(
            %s,
            "Approved as archive only. The reason is added to the notes and the requestor is notified.",
            If(With(
                {n: CountRows(RV_ChildrenGallery.AllItems), ok: CountRows(Filter(RV_ChildrenGallery.AllItems, MediaApproved = true))},
                ok > 0 And ok < n
            ), "Request partially approved: only the ticked media files are approved.", "Request approved.")
        ),''' % NEWARCH)
if 'Approved as archive only' not in n:
    sys.exit('! Approve: notify not replaced')
app.set(RV, 'RV_BtnApprove', 'OnSelect', n, expect=t)
app.save()

h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
from collections import Counter


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


cnt = Counter(c['Template']['Name'] for s in app.map if s != 'App' for c in walk(app.doc(s)['TopParent']))
p = open(f'{NEW}/Properties.json', encoding='utf-8').read()
for k, v in cnt.items():
    p = re.sub(rf'("{k}": )\d+', rf'\g<1>{v}', p, count=1)
open(f'{NEW}/Properties.json', 'w', encoding='utf-8', newline='').write(p)
print('FINAL16 built')
