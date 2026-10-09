#!/usr/bin/env python3
"""Static checks for v73 against v72b: 5 latest rows in DOA/DOR List2 and List3 galleries."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v73-dash-last5.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-v72b-v3-dashboards.msapp'
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, ys = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('Src/'):
            ys[f[4:-8]] = z.read(i).decode('utf-8')
    return js, ys


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


new, ny = load(PKG)
old, _ = load(BASE)
flat = lambda t: ' '.join(t.split())
diff = []
for s in new:
    oc = {c['Name']: c for c in walk(old[s])}
    for c in walk(new[s]):
        check(c['Name'] in oc, f'{s}: {c["Name"]} added')
        if c['Name'] not in oc:
            continue
        a = {r['Property']: r['InvariantScript'] for r in c['Rules']}
        b = {r['Property']: r['InvariantScript'] for r in oc[c['Name']]['Rules']}
        diff += [(s, c['Name'], p) for p in set(a) | set(b) if a.get(p) != b.get(p)]
        strip = lambda x: {k: v for k, v in x.items() if k not in ('Rules', 'Children')}
        check(strip(c) == strip(oc[c['Name']]), f'{s}: {c["Name"]} metadata changed')
want = []
for S, P in (('Dashboard-Ope-Administrator', 'DOA'), ('Dashboard-Ope-Requestor', 'DOR')):
    nc = {c['Name']: c for c in walk(new[S])}; oc = {c['Name']: c for c in walk(old[S])}
    r = lambda d, n, p: next(x['InvariantScript'] for x in d[n]['Rules'] if x['Property'] == p)
    for i in (2, 3):
        g, sub = f'{P}_List{i}Gallery', f'{P}_List{i}Sub'
        want += [(S, g, 'Items'), (S, sub, 'Text')]
        it, ot = r(nc, g, 'Items'), r(oc, g, 'Items')
        code = re.sub(r'//.*', '', it)
        check(flat(code).startswith('FirstN( Sort(') and flat(code).endswith(', 5 )'), f'{g}: not FirstN(..., 5)')
        check(flat(ot) in flat(code), f'{g}: the Sort changed')
        check(code.count('(') == code.count(')'), f'{g}: brackets')
        flt = re.search(r'Filter\(colOpeReqs, [^\n]+?\]\)', ot).group(0)
        st = r(nc, sub, 'Text')
        check(f'Text(CountRows({flt}))' in st and 'the 5 latest of' in st, f'{sub}: count text')
        check(st.count('(') == st.count(')') and ' + ' not in st, f'{sub}: formula')
        check(f'{P}_List{i}Info' in nc and r(nc, f'{P}_List{i}Info', 'Tooltip') == f'{sub}.Text', f'{P}{i}: info tooltip')
        check('FirstN(' in ny[S].split(f'- {g}:')[1][:600], f'{g}: YAML')
    for i in (1,):
        g = 'Todo List Gallery' if P == 'DOA' else f'{P}_List1Gallery'
        check(r(nc, g, 'Items') == r(oc, g, 'Items'), f'{g}: list 1 changed')
check(sorted(diff) == sorted(want), f'changed rules: {sorted(diff)}')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
