#!/usr/bin/env python3
"""FINAL146 on FINAL145: the notification after a submission carries the request number
("Request 26-0012 submitted successfully." / "Request 26-0012 resubmitted for review.")."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV5', 'newV6'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
for ctl, old, new in (
    ('RS_BtnSubmitRequest', 'Notify("Request submitted successfully.", NotificationType.Success)',
     'Notify("Request " & savedReq.RequestNumber & " submitted successfully.", NotificationType.Success)'),
    ('RS_BtnResubmitRequest', 'Notify("Request resubmitted for review.", NotificationType.Success)',
     'Notify("Request " & savedReq.RequestNumber & " resubmitted for review.", NotificationType.Success)')):
    t = app.rule(S, ctl, 'OnSelect'); assert t.count(old) == 1 and 'savedReq:' in t, ctl
    app.set(S, ctl, 'OnSelect', t.replace(old, new), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL146 built')
