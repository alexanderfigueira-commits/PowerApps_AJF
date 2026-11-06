#!/usr/bin/env python3
"""Checks for FINAL35 against FINAL34: Beluga reference below FTP, admin-only, optional; Notes moves for Video/Podcast."""
import json, re, sys, zipfile
PKG, BASE = sys.argv[1], sys.argv[2]
fails, cnt = [], 0
def check(ok, msg):
    global cnt
    cnt += 1
    if not ok: fails.append(msg)
def load(p):
    z = zipfile.ZipFile(p); js, ref = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('References/'): ref[f] = z.read(i)
    return js, ref
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
(new, nref), (old, oref) = load(PKG), load(BASE)
check(nref == oref, 'data sources unchanged')
flat = lambda js: {(s, c['Name']): {r['Property']: r['InvariantScript'] for r in c['Rules'] if r['Property'] != 'ZIndex'} for s, t in js.items() for c in walk(t)}
n, o = flat(new), flat(old)
ch = sorted((k, p) for k in n for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p))
S = 'ChildInfoScreen'
exp = sorted([((S, 'CI_LblBeluga'), 'Visible'), ((S, 'CI_BelugaRef'), 'Visible'), ((S, 'CI_LblBeluga'), 'Y'), ((S, 'CI_BelugaRef'), 'Y'), ((S, 'CI_LblNotes'), 'Y'), ((S, 'CI_Notes'), 'Y')])
check(ch == exp, f'only the 6 expected rules changed: {ch}')
check(n[(S, 'CI_BelugaRef')]['Visible'] == 'varUserRole = "ADMINISTRATOR"', 'admin only, any status')
check('If(varChildMediaType = "Photo", 392, 471)' == n[(S, 'CI_LblBeluga')]['Y'] and 'If(varChildMediaType = "Photo", 418, 497)' == n[(S, 'CI_BelugaRef')]['Y'], 'Beluga position')
ftp = n[(S, 'CI_FTPPath')]; fb = float(ftp['Y']) + float(ftp['Height'])
check(fb < 392, 'Photo: Beluga label is below the FTP box')
check(float(n[(S, 'CI_Language')]['Y']) + float(n[(S, 'CI_Language')]['Height']) < 471, 'Video: Beluga below Language')
check(float(n[(S, 'CI_BtnOpenAttach')]['Y']) + float(n[(S, 'CI_BtnOpenAttach')]['Height']) < 471, 'Podcast: Beluga below the visual button')
check(580 + float(n[(S, 'CI_Notes')]['Height']) < 712, 'Notes stay above the bottom bar (712)')
check('255, 204, 0' not in n[(S, 'CI_BelugaRef')]['BorderColor'] and '*' not in n[(S, 'CI_LblBeluga')]['Text'], 'optional: no yellow, no *')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
