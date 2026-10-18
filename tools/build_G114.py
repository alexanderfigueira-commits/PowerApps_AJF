#!/usr/bin/env python3
"""FINAL124 on FINAL123: step 2 of the status flow reads "Pending" when the request is Pending (otherwise "Analysis"); step 3 stays "Approval"."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newQ7', 'newQ8'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
D = 'RequesDetailScreen'
t = app.rule(D, 'RS_TrkLbl2', 'Text'); assert t == '"Analysis"'
app.set(D, 'RS_TrkLbl2', 'Text', 'If(Coalesce(varCurrentRequest.Status.Value, "Draft") = "Pending", "Pending", "Analysis")', expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL124 built')
