#!/usr/bin/env python3
"""FINAL63 on FINAL62: cmbFilterAssignee_1 keeps the 'All' option (selected by default) but accepts only one value."""
import datetime, json, os, re, shutil
from payaml import App
SRC, NEW = 'newG52', 'newG53'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, C = 'RequestManagementScreen', 'cmbFilterAssignee_1'
o = app.rule(S, C, 'Items'); assert o == 'Filter(colAssignees, Value <> "All")'
app.set(S, C, 'Items', 'colAssignees', expect=o)
o = app.rule(S, C, 'DefaultSelectedItems'); assert o == 'Filter(colAssignees, false)'
app.set(S, C, 'DefaultSelectedItems', 'Table({Value: "All"})', expect=o)
app.save()
jp = f'{NEW}/Controls/754.json'
raw = open(jp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); crlf = b'\r\n' in raw
d = json.loads(raw.decode('utf-8-sig'))
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
c = [x for x in walk(d['TopParent']) if x['Name'] == C][0]
for e in c.get('ControlPropertyState', []):
    if isinstance(e, dict) and e.get('InvariantPropertyName') == 'Items' and e.get('AutoRuleBindingString'):
        e['AutoRuleBindingString'] = 'colAssignees.Value'
out = json.dumps(d, ensure_ascii=False, indent=2)
open(jp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out.replace('\n', '\r\n') if crlf else out)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL63 built')
