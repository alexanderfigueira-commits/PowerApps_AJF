#!/usr/bin/env python3
"""FINAL171 on FINAL170. "With Archive only ticked, Submit does not leave the request in Processing."
Reading the app: Submit writes Status = Processing and ArchivedOnly = the tick, with no branch on Archive only, so the app itself cannot treat the two cases differently.
What can: something outside the app moving the status again (a flow, a list rule), or the request being opened view-only (opened from a dashboard ID: Submit is hidden).
Submit now reads the request back from SharePoint after the media files were updated and says what it holds instead of "submitted successfully" when the status is not Processing."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV32', 'newV33'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
D = 'RequesDetailScreen'
t = app.rule(D, 'RS_BtnSubmitRequest', 'OnSelect')
old = 'Notify("Request " & savedReq.RequestNumber & " submitted successfully.", NotificationType.Success);'
assert t.count(old) == 1
new = '''// what SharePoint holds now: if something outside the app (a flow, a list rule) moved the status again, that is said instead of "submitted"
        Refresh('AV-CD-Requests');
        With(
            {chk: LookUp('AV-CD-Requests', ID = savedReq.ID)},
            If(
                chk.Status.Value = "Processing",
                Notify("Request " & savedReq.RequestNumber & " submitted successfully.", NotificationType.Success),
                Notify("Request " & savedReq.RequestNumber & " was saved, but SharePoint shows its status as " & Char(34) & Coalesce(chk.Status.Value, "empty") & Char(34) & " (Archive only: " & If(Coalesce(chk.ArchivedOnly, false), "yes", "no") & "), not Processing: something outside the app changed it back. Check the flows and list rules on AV-CD-Requests.", NotificationType.Warning)
            )
        );'''
app.set(D, 'RS_BtnSubmitRequest', 'OnSelect', t.replace(old, new), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL171 built')
