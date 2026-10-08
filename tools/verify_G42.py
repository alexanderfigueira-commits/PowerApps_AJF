#!/usr/bin/env python3
"""Checks for FINAL52 against FINAL51: Beluga filter visible to all roles; RS_ThTitle_1 below the type pop-up."""
import json, sys, zipfile
def load(p):
    z = zipfile.ZipFile(p); out = {}; ref = {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            t = json.loads(z.read(i).decode('utf-8-sig'))['TopParent']
            def w(c):
                out[(t['Name'], c['Name'])] = {r['Property']: r['InvariantScript'] for r in c['Rules']}
                for k in c.get('Children', []): w(k)
            w(t)
        elif f.startswith('References/'): ref[f] = z.read(i)
    return out, ref
(n, nr), (o, orf) = load(sys.argv[1]), load(sys.argv[2])
fails = []
if nr != orf: fails.append('data sources changed')
if set(n) != set(o): fails.append('controls differ')
ch = sorted((k, p) for k in n if k in o for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p))
exp = sorted([(('RequestManagementScreen', 'HomeLblBeluga'), 'Visible'), (('RequestManagementScreen', 'HomeFilterBeluga'), 'Visible'), (('RequesDetailScreen', 'RS_ThTitle_1'), 'ZIndex')])
if ch != exp: fails.append(f'unexpected changes {ch}')
for c in ('HomeLblBeluga', 'HomeFilterBeluga'):
    if n[('RequestManagementScreen', c)]['Visible'] != 'locShowFilters': fails.append(c)
S = 'RequesDetailScreen'
z = int(n[(S, 'RS_ThTitle_1')]['ZIndex'])
popup = [int(n[(S, c)]['ZIndex']) for (s, c) in n if s == S and c.startswith('RS_TypePicker') or (s == S and c in ('Rectangle1', 'RS_CardPhoto', 'RS_CardVideoBtn', 'RS_CardPodcastBtn'))]
if not (z < min(popup) and z > int(n[(S, 'RS_ChildrenHeader')]['ZIndex'])): fails.append(f'z {z} vs popup {min(popup)}')
print('FAIL' if fails else 'PASS'); [print(' -', f) for f in fails]; sys.exit(1 if fails else 0)
