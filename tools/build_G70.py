#!/usr/bin/env python3
"""FINAL80 on FINAL79: SaveButton has a yellow border until it is clicked once, then a blue one (locSaveClicked, reset when the screen opens);
Icon2 (the arrow above it) is deleted."""
import datetime, json, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG69', 'newG70'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
app.set(S, 'SaveButton', 'BorderColor', 'If(locSaveClicked, RGBA(0, 18, 107, 1), RGBA(255, 204, 0, 1))', expect='RGBA(0, 18, 107, 1)')
app.set(S, 'SaveButton', 'BorderThickness', 'If(locSaveClicked, 2, 3)', expect='0')
o = app.rule(S, 'SaveButton', 'OnSelect')
app.set(S, 'SaveButton', 'OnSelect', 'UpdateContext({locSaveClicked: true});\r\n' + o, expect=o)
t = app.rule(S, None, 'OnVisible')
m = re.search(r'([ \t]*)locOwnerNoMatch: false,', t); assert m
app.set(S, None, 'OnVisible', t.replace(m.group(0), f'{m.group(1)}locSaveClicked: false,\r\n{m.group(0)}', 1), expect=t)
app.save()
# delete Icon2 (JSON + YAML)
jp = [os.path.join(NEW, 'Controls', f) for f in os.listdir(f'{NEW}/Controls') if '"RequesDetailScreen"' in open(os.path.join(NEW, 'Controls', f), encoding='utf-8-sig').read()[:400]][0]
raw = open(jp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); crlf = b'\r\n' in raw
d = json.loads(raw.decode('utf-8-sig')); top = d['TopParent']
n0 = len(top['Children']); top['Children'] = [c for c in top['Children'] if c['Name'] != 'Icon2']; assert n0 - len(top['Children']) == 1
out = json.dumps(d, ensure_ascii=False, indent=2)
open(jp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out.replace('\n', '\r\n') if crlf else out)
yp = f'{NEW}/Src/RequesDetailScreen.pa.yaml'
y = open(yp, 'rb').read().decode('utf-8'); L = y.split('\n')
i = [k for k, l in enumerate(L) if l.rstrip('\r') == '      - Icon2:'][0]; j = i + 1
while j < len(L) and (L[j].strip() == '' or len(L[j]) - len(L[j].lstrip()) > 6): j += 1
del L[i:j]; open(yp, 'wb').write('\n'.join(L).encode('utf-8'))
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL80 built')
