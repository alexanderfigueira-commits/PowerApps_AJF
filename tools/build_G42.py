#!/usr/bin/env python3
"""FINAL52 on FINAL51: Beluga filter visible to requestors; RS_ThTitle_1 ('REF') sits behind the production-type pop-up."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG41', 'newG42'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RM, RS = 'RequestManagementScreen', 'RequesDetailScreen'
for c in ('HomeLblBeluga', 'HomeFilterBeluga'):
    app.set(RM, c, 'Visible', 'locShowFilters', expect='locShowFilters And varUserRole = "ADMINISTRATOR"')
app.save()
import json
p = f'{NEW}/Controls/463.json'
d = json.load(open(p, encoding='utf-8-sig'))
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
c = [x for x in walk(d['TopParent']) if x['Name'] == 'RS_ThTitle_1'][0]
r = [x for x in c['Rules'] if x['Property'] == 'ZIndex'][0]
assert r['InvariantScript'] == '128'
r['InvariantScript'] = '105'   # below the pop-up overlay (106+), above the header strip (35)
for e in c.get('ControlPropertyState', []):
    if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString'):
        e['AutoRuleBindingString'] = '105'
raw = open(p, 'rb').read()
bom = raw.startswith(b'\xef\xbb\xbf')
open(p, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(json.dumps(d, ensure_ascii=False, indent=2).replace('\n', '\r\n'))
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL52 built')
