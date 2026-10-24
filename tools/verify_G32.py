#!/usr/bin/env python3
"""Checks for FINAL42 against FINAL41: Remove asks for confirmation."""
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
def bal(t):
    v = re.sub(r'(?m)^\s*//[^\n]*', '', t); v = re.sub(r'"[^"\n]*"', '""', v)
    return v.count('(') == v.count(')') and v.count('{') == v.count('}')
(new, nref), (old, oref) = load(PKG), load(BASE)
check(nref == oref, 'data sources unchanged')
flat = lambda js: {(s, c['Name']): {r['Property']: r['InvariantScript'] for r in c['Rules']} for s, t in js.items() for c in walk(t)}
n, o = flat(new), flat(old)
RS = 'RequesDetailScreen'
added = sorted(set(n) - set(o))
check(added == sorted((RS, x) for x in ('RS_DelBackdrop', 'RS_DelPanel', 'RS_DelTitle', 'RS_DelText', 'RS_DelNo', 'RS_DelYes')), f'six new controls only: {added}')
check(not (set(o) - set(n)), 'nothing removed')
ch = sorted((k, p) for k in n if k in o for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p))
check(ch == sorted([((RS, RS), 'OnVisible'), ((RS, 'RS_CRowDelete'), 'OnSelect')]), f'only OnVisible and RS_CRowDelete.OnSelect changed: {ch}')
check(n[(RS, 'RS_CRowDelete')]['OnSelect'] == 'UpdateContext({locDelItem: ThisItem, locShowDelConfirm: true})', 'Remove only opens the pop-up')
yes = n[(RS, 'RS_DelYes')]['OnSelect']
oldlogic = o[(RS, 'RS_CRowDelete')]['OnSelect'].replace('ThisItem', 'locDelItem')
check(oldlogic in yes, 'Yes runs the same deletion as before')
check('locShowDelConfirm: false' in n[(RS, 'RS_DelNo')]['OnSelect'] and 'Remove(' not in n[(RS, 'RS_DelNo')]['OnSelect'], 'No deletes nothing')
check(all(n[(RS, x)]['Visible'] == 'locShowDelConfirm' for x in ('RS_DelBackdrop', 'RS_DelPanel', 'RS_DelTitle', 'RS_DelText', 'RS_DelNo', 'RS_DelYes')), 'pop-up visibility')
z = {c['Name']: int(next(r['InvariantScript'] for r in c['Rules'] if r['Property'] == 'ZIndex')) for c in walk(new[RS]) if any(r['Property'] == 'ZIndex' for r in c['Rules'])}
top_old = max(v for k, v in z.items() if not k.startswith('RS_Del'))
dz = [z[x] for x in ('RS_DelBackdrop', 'RS_DelPanel', 'RS_DelTitle', 'RS_DelText', 'RS_DelNo', 'RS_DelYes')]
check(dz == sorted(dz) and min(dz) > top_old and len(set(dz)) == 6, f'pop-up above everything: {dz} > {top_old}')
check('locShowDelConfirm: false' in n[(RS, RS)]['OnVisible'], 'pop-up closed when the screen opens')
check('Are you sure you want to delete the media file' in n[(RS, 'RS_DelText')]['Text'], 'confirmation text')
check(all(bal(n[k][p]) for k, p in ch) and all(bal(v) for k in n if k[1].startswith('RS_Del') for v in n[k].values()), 'brackets')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
