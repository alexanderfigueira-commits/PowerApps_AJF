#!/usr/bin/env python3
"""FINAL107 on FINAL106: Message Center: the 'Add a note:' label (NT_Hint) is deleted, the input's hint reads 'Write a message...' and the two 'Last updated on' labels read 'Last message sent on'."""
import datetime, os, re, shutil
from payaml import App
from jio import jwrite
SRC, NEW = 'newJ7', 'newJ8'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
app.set(S, 'NT_Input', 'HintText', '"Write a message..."', expect='"Write a note..."')
for c, w0, w1 in (('NT_ReqUpdated', '230', '285'), ('NT_AdmUpdated', '243', '285')):
    t = app.rule(S, c, 'Text'); eol = '\r\n' if '\r\n' in t else '\n'; n = t.replace('\r\n', '\n')
    a = 'If(IsBlank(last), "Last updated on: -", "Last updated on " & Text(last, DateTimeFormat.ShortDateTime))'
    assert n.count(a) == 1
    app.set(S, c, 'Text', n.replace(a, 'If(IsBlank(last), "Last message sent on: -", "Last message sent on " & Text(last, DateTimeFormat.ShortDateTime))').replace('\n', eol), expect=t)
    app.set(S, c, 'Width', w1, expect=w0)
doc = app.doc(S); tp = doc['TopParent']
n0 = len(tp['Children']); tp['Children'] = [c for c in tp['Children'] if c['Name'] != 'NT_Hint']; assert n0 - len(tp['Children']) == 1
g = [c for c in tp['Children'] if c['Name'] == 'Group3'][0]
assert g['GroupedControlsKey'].count('NT_Hint') == 1; g['GroupedControlsKey'].remove('NT_Hint')
jwrite(doc, app.map[S])
yp = f'{NEW}/Src/{S}.pa.yaml'
Y = open(yp, encoding='utf-8').read().split('\n')
i = [k for k, l in enumerate(Y) if l.rstrip('\r') == '      - NT_Hint:']; assert len(i) == 1
i = i[0]; j = i + 1
while j < len(Y) and (Y[j].strip() == '' or len(Y[j]) - len(Y[j].lstrip()) > 6): j += 1
del Y[i:j]; open(yp, 'w', encoding='utf-8').write('\n'.join(Y))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL107 built')
