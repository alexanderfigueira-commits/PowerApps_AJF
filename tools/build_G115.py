#!/usr/bin/env python3
"""FINAL125 on FINAL124: ReviewScreen DOA_List1RowBadge_4 (the status badge) shows only once a request is selected in the queue (Icon1 / RV_QRowBg set varReviewProject).
It followed varCurrentRequest (the last request opened anywhere) for Visible and Fill while its text came from varReviewProject; all three now follow the selected request."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newQ8', 'newQ9'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
R, B = 'ReviewScreen', 'DOA_List1RowBadge_4'
t = app.rule(R, B, 'Visible'); assert t == 'Coalesce(varCurrentRequest.ID, 0) > 0'
app.set(R, B, 'Visible', 'Not(IsBlank(varReviewProject))', expect=t)
t = app.rule(R, B, 'Fill'); assert 'varCurrentRequest' in t and 'varReviewProject' not in t
app.set(R, B, 'Fill', t.replace('varCurrentRequest', 'varReviewProject'), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL125 built')
