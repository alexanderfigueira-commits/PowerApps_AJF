#!/usr/bin/env python3
"""FINAL62 on FINAL61: cmbFilterAssignee_1 (RequestManagementScreen) selects one assignee only and no longer offers 'All'."""
import datetime, json, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG51out', 'newG52'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, C = 'RequestManagementScreen', 'cmbFilterAssignee_1'
o = app.rule(S, C, 'Items'); assert o == 'colAssignees'
app.set(S, C, 'Items', 'Filter(colAssignees, Value <> "All")', expect=o)
o = app.rule(S, C, 'DefaultSelectedItems')
app.set(S, C, 'DefaultSelectedItems', 'Filter(colAssignees, false)', expect=o)   # nothing picked until the user chooses
o = app.rule(S, C, 'SelectMultiple'); assert o == 'true'
app.set(S, C, 'SelectMultiple', 'false', expect=o)
app.save()
# keep the Items binding string in step (Studio stores the column it shows)
jp = f'{NEW}/Controls/754.json'
raw = open(jp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); crlf = b'\r\n' in raw
d = json.loads(raw.decode('utf-8-sig'))
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
c = [x for x in walk(d['TopParent']) if x['Name'] == C][0]
for e in c.get('ControlPropertyState', []):
    if isinstance(e, dict) and e.get('InvariantPropertyName') == 'Items' and e.get('AutoRuleBindingString'):
        e['AutoRuleBindingString'] = 'Filter(colAssignees, Value <> "All")'
out = json.dumps(d, ensure_ascii=False, indent=2)
open(jp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out.replace('\n', '\r\n') if crlf else out)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL62 built')
