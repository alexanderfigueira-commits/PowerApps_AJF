#!/usr/bin/env python3
"""FINAL132 on TEST_8: Approve (ReviewScreen) on a request nobody is assigned to makes the approving administrator the assignee FIRST, and checks it was saved, before the status becomes Approved.
(FINAL130 wrote the assignee in the same save as the status; now the assignment is its own save, verified, and a failure stops the approval so a request is never Approved without an assignee.)"""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newT8', 'newT9'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
R, B = 'ReviewScreen', 'RV_BtnApprove'
t = app.rule(R, B, 'OnSelect')
eol = '\r\n' if '\r\n' in t else '\n'
u = t.replace('\r\n', '\n')
# 1. the assignee leaves the status save
old = ('            // nobody assigned: the administrator who approves is the assignee; an assignee already set is kept\n'
       '            Assignee: With(\n'
       '                {cur: LookUp(\'AV-CD-Requests\', ID = varReviewProject.ID).Assignee},\n'
       '                If(\n'
       '                    noAssignee,\n'
       '                    {Claims: "i:0#.f|membership|" & Lower(User().Email), DisplayName: User().FullName, Email: User().Email, Department: "", JobTitle: "", Picture: ""},\n'
       '                    {Claims: "i:0#.f|membership|" & Lower(cur.Email), DisplayName: cur.DisplayName, Email: cur.Email, Department: "", JobTitle: "", Picture: ""}\n'
       '                )\n'
       '            ),\n')
assert u.count(old) == 1
u = u.replace(old, '')
# 2. its own save, before the decision, checked
anchor = "    // the message (if any) is added to the request's Message Center first, so the notification e-mail finds it\n"
assert u.count(anchor) == 1
new = ('    // nobody is assigned: the administrator who approves becomes the assignee first, before the message and the status (an assignee already set is never touched)\n'
       '    If(\n'
       '        noAssignee,\n'
       '        Patch(\n'
       '            \'AV-CD-Requests\',\n'
       '            LookUp(\'AV-CD-Requests\', ID = varReviewProject.ID),\n'
       '            {Assignee: {Claims: "i:0#.f|membership|" & Lower(User().Email), DisplayName: User().FullName, Email: User().Email, Department: "", JobTitle: "", Picture: ""}}\n'
       '        );\n'
       '        // checked in what SharePoint returns: without an assignee the request is not approved\n'
       '        If(\n'
       '            IsBlank(LookUp(\'AV-CD-Requests\', ID = varReviewProject.ID).Assignee.Email),\n'
       '            Error({Kind: ErrorKind.Custom, Message: "you could not be set as the assignee, so the request was not approved"})\n'
       '        )\n'
       '    );\n')
u = u.replace(anchor, new + anchor)
app.set(R, B, 'OnSelect', u.replace('\n', eol), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL132 built')
