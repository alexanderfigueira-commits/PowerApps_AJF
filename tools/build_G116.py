#!/usr/bin/env python3
"""FINAL126 on FINAL125 (ReviewScreen): RV_LblOwnerAssign and RV_ArchiveOnly at size 11; RV_LblComment reads "Message to the requestor"; RV_RejectHint deleted."""
import datetime, os, re, shutil
from payaml import App
from jio import jwrite
SRC, NEW = 'newQ9', 'newQ10'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
R = 'ReviewScreen'
t = app.rule(R, 'RV_LblOwnerAssign', 'Size'); assert t == '13'; app.set(R, 'RV_LblOwnerAssign', 'Size', '11', expect=t)
t = app.rule(R, 'RV_ArchiveOnly', 'Size'); assert t == '10'; app.set(R, 'RV_ArchiveOnly', 'Size', '11', expect=t)
t = app.rule(R, 'RV_LblComment', 'Text')
assert t == '"Message to the requestor  (required to send back or reject; it is added to the Message Center of the request)"'
app.set(R, 'RV_LblComment', 'Text', '"Message to the requestor"', expect=t)
# delete RV_RejectHint (JSON + YAML); nothing refers to it and it is in no group
doc = app.doc(R); tp = doc['TopParent']
n0 = len(tp['Children']); tp['Children'] = [c for c in tp['Children'] if c['Name'] != 'RV_RejectHint']; assert n0 - len(tp['Children']) == 1
app.save()
yp = f'{NEW}/Src/{R}.pa.yaml'; Y = open(yp, encoding='utf-8').read().split('\n')
i = [k for k, l in enumerate(Y) if l.rstrip('\r') == '      - RV_RejectHint:']; assert len(i) == 1
i = i[0]; j = i + 1
while j < len(Y) and (Y[j].strip() == '' or len(Y[j]) - len(Y[j].lstrip()) > 6): j += 1
del Y[i:j]; open(yp, 'w', encoding='utf-8', newline='').write('\n'.join(Y))
assert 'RV_RejectHint' not in open(yp, encoding='utf-8').read()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL126 built')
