#!/usr/bin/env python3
"""FINAL128 on FINAL127: RS_RejectionComment (RequesDetailScreen) deleted. It was a member of Group1; nothing else refers to it."""
import datetime, os, re, shutil
from payaml import App, find
SRC, NEW = 'newQ11', 'newQ12'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
tp = app.doc(S)['TopParent']
g = find(tp, 'Group1'); assert g['GroupedControlsKey'].count('RS_RejectionComment') == 1
g['GroupedControlsKey'].remove('RS_RejectionComment')
n0 = len(tp['Children']); tp['Children'] = [c for c in tp['Children'] if c['Name'] != 'RS_RejectionComment']; assert n0 - len(tp['Children']) == 1
app.save()
yp = f'{NEW}/Src/{S}.pa.yaml'; Y = open(yp, encoding='utf-8').read().split('\n')
i = [k for k, l in enumerate(Y) if l.rstrip('\r') == '      - RS_RejectionComment:']; assert len(i) == 1
i = i[0]; j = i + 1
while j < len(Y) and (Y[j].strip() == '' or len(Y[j]) - len(Y[j].lstrip()) > 6): j += 1
del Y[i:j]; open(yp, 'w', encoding='utf-8', newline='').write('\n'.join(Y))
assert 'RS_RejectionComment' not in open(yp, encoding='utf-8').read()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL128 built')
