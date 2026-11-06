#!/usr/bin/env python3
"""Checks for FINAL54 against FINAL53: CI_LblBeluga / CI_BelugaRef moved inside CI_Gallery, same screen position."""
import json, re, sys, zipfile
def load(p):
    z = zipfile.ZipFile(p); out = {}; par = {}; ref = {}; yaml = {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            t = json.loads(z.read(i).decode('utf-8-sig'))['TopParent']
            def w(c, p):
                out[(t['Name'], c['Name'])] = {r['Property']: r['InvariantScript'] for r in c['Rules']}
                par[(t['Name'], c['Name'])] = (p, c.get('Parent'))
                for k in c.get('Children', []): w(k, c['Name'])
            w(t, None)
        elif f.startswith('References/'): ref[f] = z.read(i)
        elif f.endswith('ChildInfoScreen.pa.yaml'): yaml = z.read(i).decode('utf-8')
    return out, par, ref, yaml
(n, np_, nr, ny), (o, op, orf, oy) = load(sys.argv[1]), load(sys.argv[2])
S = 'ChildInfoScreen'; fails = []
if nr != orf: fails.append('data sources changed')
if set(n) != set(o): fails.append('controls differ')
ch = sorted((k, p) for k in n if k in o for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p))
exp = sorted([((S, c), 'Y') for c in ('CI_LblBeluga', 'CI_BelugaRef')])
if ch != exp: fails.append(f'unexpected changes {ch}')
for c in ('CI_LblBeluga', 'CI_BelugaRef'):
    if np_[(S, c)] != ('CI_Gallery', 'CI_Gallery'): fails.append(f'{c} parent {np_[(S, c)]}')
    if int(n[(S, c)]['Y']) + int(n[(S, 'CI_Gallery')]['Y']) != int(o[(S, c)]['Y']): fails.append(f'{c} moved on screen')
    if not re.search(r'^            - ' + c + ':', ny, re.M) or re.search(r'^      - ' + c + ':', ny, re.M): fails.append(f'{c} yaml nesting')
print('FAIL' if fails else 'PASS'); [print(' -', x) for x in fails]; sys.exit(1 if fails else 0)
