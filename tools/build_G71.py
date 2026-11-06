#!/usr/bin/env python3
"""FINAL81 on FINAL80: RS_BtnDraftSave deleted from RequesDetailScreen (nothing referenced it by name)."""
import datetime, json, os, re, shutil
SRC, NEW = 'newG70', 'newG71'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
GONE = 'RS_BtnDraftSave'
jp = [os.path.join(NEW, 'Controls', f) for f in os.listdir(f'{NEW}/Controls') if '"RequesDetailScreen"' in open(os.path.join(NEW, 'Controls', f), encoding='utf-8-sig').read()[:400]][0]
raw = open(jp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); crlf = b'\r\n' in raw
d = json.loads(raw.decode('utf-8-sig')); top = d['TopParent']
n0 = len(top['Children']); top['Children'] = [c for c in top['Children'] if c['Name'] != GONE]; assert n0 - len(top['Children']) == 1
out = json.dumps(d, ensure_ascii=False, indent=2)
open(jp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out.replace('\n', '\r\n') if crlf else out)
yp = f'{NEW}/Src/RequesDetailScreen.pa.yaml'
L = open(yp, 'rb').read().decode('utf-8').split('\n')
i = [k for k, l in enumerate(L) if l.rstrip('\r') == f'      - {GONE}:'][0]; j = i + 1
while j < len(L) and (L[j].strip() == '' or len(L[j]) - len(L[j].lstrip()) > 6): j += 1
del L[i:j]; open(yp, 'wb').write('\n'.join(L).encode('utf-8'))
for f in os.listdir(f'{NEW}/Src'):
    assert GONE not in open(os.path.join(NEW, 'Src', f), encoding='utf-8').read(), f
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL81 built')
