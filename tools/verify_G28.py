#!/usr/bin/env python3
"""Checks for FINAL38 against FINAL37: today's requests are inside the default date range."""
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
flat = lambda js: {(s, c['Name']): {r['Property']: r['InvariantScript'] for r in c['Rules'] if r['Property'] != 'ZIndex'} for s, t in js.items() for c in walk(t)}
n, o = flat(new), flat(old)
ch = sorted((k, p) for k in n for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p))
exp = sorted([(('App', 'App'), 'OnStart'), (('RequestManagementScreen', 'RequestManagementScreen'), 'OnVisible'), (('RequesDetailScreen', 'Add_media_icon'), 'OnSelect')])
check(ch == exp, f'only the 3 expected rules changed: {ch}')
ov = n[('RequestManagementScreen', 'RequestManagementScreen')]['OnVisible']
check('Set(varFilterEndDate, Today() + Time(23, 59, 59))' in ov and 'Set(varFilterEndDate, Today());' not in ov, 'default To = end of today')
check('varFilterDay <> Today()' in ov and 'Reset(HomeFilterStart)' in ov and 'Reset(HomeFilterEnd)' in ov, 'new-day re-initialisation')
check('Set(varFilterDay, Today());' in n[('App', 'App')]['OnStart'], 'varFilterDay initialised in OnStart')
check('Set(varReqDataLoaded, false)' in n[('RequesDetailScreen', 'Add_media_icon')]['OnSelect'], 'Add media marks the list stale')
check(all(bal(n[k][p]) for k, p in ch), 'brackets')
# the list filter itself is unchanged and keeps Created <= varFilterEndDate: with To = 23:59:59 a request created today at 10:30 passes
check(sum(v.get('Items', '').count('Created <= varFilterEndDate') for v in n.values()) >= 1, 'filter still uses Created <= varFilterEndDate')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
