#!/usr/bin/env python3
"""FINAL133 on FINAL132: Rejected and Pending (Reject / Need info buttons of ReviewScreen) do what Approve does: a request nobody is assigned to gets the administrator who decides as its
assignee first, verified, before the message and the status; a failure stops the decision."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newT9', 'newT10'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
R = 'ReviewScreen'
STEP = ('    // nobody is assigned: the administrator who decides becomes the assignee first, before the message and the status (an assignee already set is never touched)\n'
        '    If(\n'
        '        noAssignee,\n'
        '        Patch(\n'
        '            \'AV-CD-Requests\',\n'
        '            LookUp(\'AV-CD-Requests\', ID = varReviewProject.ID),\n'
        '            {Assignee: {Claims: "i:0#.f|membership|" & Lower(User().Email), DisplayName: User().FullName, Email: User().Email, Department: "", JobTitle: "", Picture: ""}}\n'
        '        );\n'
        '        // checked in what SharePoint returns: without an assignee the decision is not taken\n'
        '        If(\n'
        '            IsBlank(LookUp(\'AV-CD-Requests\', ID = varReviewProject.ID).Assignee.Email),\n'
        '            Error({Kind: ErrorKind.Custom, Message: "you could not be set as the assignee, so the decision was not taken"})\n'
        '        )\n'
        '    );\n')
for ctl, ok_old in (('RV_BtnReject', 'Notify("Request rejected. Your message is in the Message Center of the request.", NotificationType.Warning);'),
                    ('RV_BtnNeedInfo', 'Notify("Sent back to the requestor. Your message is in the Message Center of the request.", NotificationType.Success);')):
    t = app.rule(R, ctl, 'OnSelect')
    eol = '\r\n' if '\r\n' in t else '\n'
    u = t.replace('\r\n', '\n')
    assert u.startswith('IfError(\n    // the message is a note of the request (Message Center)')
    u = u.replace('IfError(\n', 'IfError(\n' + STEP, 1)
    assert u.count(ok_old) == 1
    kind = ok_old[ok_old.index(', NotificationType'):]
    msg = ok_old[len('Notify('):ok_old.index(', NotificationType')]
    u = u.replace(ok_old, 'Notify(' + msg + ' & If(noAssignee, " You are now the assignee.", "")' + kind)
    u = ('With(\n    {noAssignee: IsBlank(LookUp(\'AV-CD-Requests\', ID = varReviewProject.ID).Assignee.Email)},\n' + u + '\n)')
    app.set(R, ctl, 'OnSelect', u.replace('\n', eol), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL133 built')
