#!/usr/bin/env python3
"""FINAL130 on FINAL129: Approve (ReviewScreen) on a request nobody is assigned to sets the approving administrator as the Assignee, in the same save as the Approved status.
An existing assignee is kept (rewritten as it is); the confirmation says when the reviewer became the assignee."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newQ13', 'newQ14'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
R, B = 'ReviewScreen', 'RV_BtnApprove'
t = app.rule(R, B, 'OnSelect')
eol = '\r\n' if '\r\n' in t else '\n'
u = t.replace('\r\n', '\n')
assert u.startswith('IfError(\n') and u.endswith('Notify("Approve failed: " & FirstError.Message, NotificationType.Error)\n)')
# 1. assignee in the same Patch as the status
old = '            ReviewedDate: Now(),\n            ArchivedOnly: RV_ArchiveOnly.Value,\n'
assert u.count(old) == 1
u = u.replace(old, '            ReviewedDate: Now(),\n'
    '            // nobody assigned: the administrator who approves is the assignee; an assignee already set is kept\n'
    '            Assignee: With(\n'
    '                {cur: LookUp(\'AV-CD-Requests\', ID = varReviewProject.ID).Assignee},\n'
    '                If(\n'
    '                    noAssignee,\n'
    '                    {Claims: "i:0#.f|membership|" & Lower(User().Email), DisplayName: User().FullName, Email: User().Email, Department: "", JobTitle: "", Picture: ""},\n'
    '                    {Claims: "i:0#.f|membership|" & Lower(cur.Email), DisplayName: cur.DisplayName, Email: cur.Email, Department: "", JobTitle: "", Picture: ""}\n'
    '                )\n'
    '            ),\n'
    '            ArchivedOnly: RV_ArchiveOnly.Value,\n')
# 2. the confirmation says it
old = '"Request approved.")\n        ),\n        NotificationType.Success'
assert u.count(old) == 1
u = u.replace(old, '"Request approved.")\n        ) & If(noAssignee, " You are now the assignee.", ""),\n        NotificationType.Success')
# 3. the flag, computed once before anything is saved
u = ('With(\n    {noAssignee: IsBlank(LookUp(\'AV-CD-Requests\', ID = varReviewProject.ID).Assignee.Email)},\n'
     + u + '\n)')
app.set(R, B, 'OnSelect', u.replace('\n', eol), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL130 built')
