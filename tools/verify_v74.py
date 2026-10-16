#!/usr/bin/env python3
"""Static checks for v74 against v73: bell with days left in both TODO galleries."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v74-todo-bell.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-v73-dash-last5.msapp'
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
    return js, ys, json.loads(z.read('Properties.json').decode('utf-8-sig'))


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


new, ny, props = load(PKG)
old, _, _ = load(BASE)
rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
A, R = 'Dashboard-Ope-Administrator', 'Dashboard-Ope-Requestor'
for s in new:
    nc = {c['Name']: c for c in walk(new[s])}; oc = {c['Name']: c for c in walk(old[s])}
    added = sorted(set(nc) - set(oc))
    want = {A: ['DOA_List1RowBell'], R: ['DOR_List1RowBell']}.get(s, [])
    check(added == want and not set(oc) - set(nc), f'{s}: added {added}')
    for n, c in oc.items():
        a, b = rd(nc[n]), rd(c)
        if n == s and s in (A, R):
            check(a.pop('OnVisible').startswith(b.pop('OnVisible')), f'{s}: OnVisible not appended')
        check(a == b, f'{s}: {n} rules changed')
for S, P, g in ((A, 'DOA', 'Todo List Gallery'), (R, 'DOR', 'DOR_List1Gallery')):
    nc = {c['Name']: c for c in walk(new[S])}
    bell, notes = nc[f'{P}_List1RowBell'], nc[f'{P}_List1RowNotes']
    check(bell['Parent'] == g and bell['Template']['Name'] == 'icon', f'{P}: bell not in {g}')
    a, b = rd(bell), rd(notes)
    same = {k for k in b if k not in ('Icon', 'Tooltip', 'AccessibleLabel', 'Color', 'X', 'ZIndex')}
    check({k: a[k] for k in same} == {k: b[k] for k in same}, f'{P}: bell style differs from the notes icon')
    check(a['Icon'] == 'Icon.Bell', f'{P}: icon')
    t = re.sub(r'//[^\n]*', '', a['Tooltip'])
    for need in ('ParentRequest = ThisItem.RequestNumber', 'CaptureDate >= Today()', 'DateDiff(Today(), m.CaptureDate, TimeUnit.Days)',
                 '"Photo", "Shooting day"', '"Video", "Filming date"', '"Capture date"', 'days left', 'days ago', 'Last(dated)'):
        check(need in t, f'{P}: tooltip misses {need}')
    check(t.count('(') == t.count(')') and t.count('{') == t.count('}'), f'{P}: tooltip brackets')
    check(' + ' not in t.replace('" & "', ''), f'{P}: + in text')
    col = re.sub(r'//[^\n]*', '', a['Color'])
    check('DateDiff(Today(), m.CaptureDate, TimeUnit.Days) < 7, Color.Red' in col and 'IsBlank(m), RGBA(166, 166, 166, 1)' in col
          and 'RGBA(0, 18, 107, 1)' in col, f'{P}: colour rule')
    check(col.count('(') == col.count(')'), f'{P}: colour brackets')
    # the colour picks the same date as the tooltip
    pick = lambda x: re.sub(r'\s+', '', x[x.index('m: If('):x.index('},', x.index('m: If('))])
    check(pick(col) == pick(t), f'{P}: colour and tooltip use different dates')
    x, w = int(a['X']), int(a['Width'])
    check(x >= int(b['X']) + int(b['Width']) and a['Y'] == b['Y'], f'{P}: bell not after the notes icon')
    for k in nc[g]['Children']:
        if k is bell or k['Template']['Name'] == 'galleryTemplate' or k['Name'].endswith(('RowSelect', 'RowDivider')):
            continue
        kr = rd(k)
        kx, ky, kw, kh = (int(kr[p]) for p in ('X', 'Y', 'Width', 'Height'))
        y, h = int(a['Y']), int(a['Height'])
        check(x + w <= kx or kx + kw <= x or y + h <= ky or ky + kh <= y, f'{P}: bell overlaps {k["Name"]}')
    ov = rd(new[S])['OnVisible']
    check(ov.count('ClearCollect(colOpeMedia') == 1, f'{S}: colOpeMedia load')
    if P == 'DOR':
        check("Filter('AV-CD-Mediafiles', 'Created By'.Email = User().Email)" in ov, 'DOR media filter')
    check(f'- {P}_List1RowBell:' in ny[S], f'{P}: YAML')
cc = props['ControlCount']
total = {}
for tp in new.values():
    if tp['Name'] != 'App':
        for c in walk(tp):
            total[c['Template']['Name']] = total.get(c['Template']['Name'], 0) + 1
check(all(cc[k] == total.get(k) for k in cc), 'ControlCount stale')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
