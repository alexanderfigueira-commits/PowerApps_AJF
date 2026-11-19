#!/usr/bin/env python3
"""FINAL178 on FINAL177. Studio: "Unused data sources (1): SuspensionDates". The data source is removed from the app: its entry in References/DataSources.json
and its mentions in the connection reference of Properties.json (the list itself in SharePoint is not touched). No formula uses it."""
import datetime, json, os, re, shutil
from jio import jdump, jwrite
SRC, NEW = 'newV39', 'newV40'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
# nothing in a formula may use it
for root, _, files in os.walk(NEW):
    for f in files:
        if f.endswith('.json') and root.endswith('Controls') or f.endswith('.pa.yaml'):
            assert 'SuspensionDates' not in open(os.path.join(root, f), encoding='utf-8').read(), f

# the writer must reproduce the files byte for byte before anything is changed
for rel in ('References/DataSources.json', 'Properties.json'):
    raw = open(f'{NEW}/{rel}', 'rb').read()
    assert jdump(json.loads(raw.decode('utf-8'))).encode('utf-8') == raw, rel

p = f'{NEW}/References/DataSources.json'
d = json.load(open(p, encoding='utf-8'))
n0 = len(d['DataSources'])
d['DataSources'] = [x for x in d['DataSources'] if x.get('Name') != 'SuspensionDates']
assert len(d['DataSources']) == n0 - 1
jwrite(d, p)

p = f'{NEW}/Properties.json'
d = json.load(open(p, encoding='utf-8'))
ref = json.loads(d['LocalConnectionReferences'])
k = 0
for cid, c in ref.items():
    if 'SuspensionDates' in c.get('dataSources', []):
        c['dataSources'].remove('SuspensionDates'); k += 1
    for ds, v in c.get('datasets', {}).items():
        if 'SuspensionDates' in v.get('dataSources', {}):
            del v['dataSources']['SuspensionDates']; k += 1
assert k == 2, k
d['LocalConnectionReferences'] = json.dumps(ref, separators=(',', ':'), ensure_ascii=False)
jwrite(d, p)

for root, _, files in os.walk(NEW):
    for f in files:
        try:
            assert 'SuspensionDates' not in open(os.path.join(root, f), encoding='utf-8').read(), os.path.join(root, f)
        except UnicodeDecodeError:
            pass
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL178 built: data sources', n0, '->', n0 - 1)
