#!/usr/bin/env python3
"""FINAL54 on FINAL53: CI_LblBeluga and CI_BelugaRef move inside CI_Gallery (same place on screen: gallery Y is 102)."""
import datetime, json, os, re, shutil, sys
SRC, NEW = 'newG43', 'newG44'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
NAMES = ('CI_LblBeluga', 'CI_BelugaRef')
jp = f'{NEW}/Controls/4.json'
raw = open(jp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); crlf = b'\r\n' in raw
d = json.loads(raw.decode('utf-8-sig')); top = d['TopParent']
def rule(c, p): return [r for r in c['Rules'] if r['Property'] == p][0]
gal = [c for c in top['Children'] if c['Name'] == 'CI_Gallery'][0]
GY = int(rule(gal, 'Y')['InvariantScript']); assert (GY, int(rule(gal, 'X')['InvariantScript'])) == (102, 0)
moved = []
for n in NAMES:
    c = [k for k in top['Children'] if k['Name'] == n][0]
    top['Children'].remove(c)
    c['Parent'] = 'CI_Gallery'
    y = rule(c, 'Y'); y['InvariantScript'] = str(int(y['InvariantScript']) - GY)
    for e in c.get('ControlPropertyState', []):
        if isinstance(e, dict) and e.get('InvariantPropertyName') == 'Y' and e.get('AutoRuleBindingString'):
            e['AutoRuleBindingString'] = y['InvariantScript']
    gal['Children'].append(c); moved.append(n)
s = json.dumps(d, ensure_ascii=False, indent=2)
open(jp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(s.replace('\n', '\r\n') if crlf else s)
# YAML mirror
yp = f'{NEW}/Src/ChildInfoScreen.pa.yaml'
raw = open(yp, 'rb').read().decode('utf-8'); eol = '\r\n' if '\r\n' in raw else '\n'
L = raw.split(eol)
def block(name, indent):
    i = [k for k, l in enumerate(L) if l == ' ' * indent + f'- {name}:'][0]
    j = i + 1
    while j < len(L) and (L[j].strip() == '' or len(L[j]) - len(L[j].lstrip()) > indent): j += 1
    return i, j
blocks = []
for n in NAMES:
    i, j = block(n, 6); b = L[i:j]; del L[i:j]
    b = ['      ' + l if l.strip() else l for l in b]          # 6 -> 12
    assert b[0].startswith('            - ' + n)
    # Y relative to the gallery
    for k, l in enumerate(b):
        m = re.match(r'^(\s+)Y: =(\d+)$', l)
        if m: b[k] = f'{m.group(1)}Y: ={int(m.group(2)) - 102}'
    blocks += b
i, j = block('CI_Tags', 12)
L[j:j] = blocks
open(yp, 'wb').write(eol.join(L).encode('utf-8'))
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL54 built', moved)
