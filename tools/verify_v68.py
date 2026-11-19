#!/usr/bin/env python3
"""Static checks for v68 against 28-9-v2.msapp: every dashboard section in the TODO section layout."""
import json, re, sys, zipfile
import yaml
from paload import PaLoader

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v68-dashboard-sections-v2.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else '/root/.claude/uploads/4d44a760-ee6e-5284-adba-c35ebdee79f5/33867a14-28-9-v2.msapp'
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(path):
    z = zipfile.ZipFile(path)
    js, ys = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig'))
            js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('Src/') and f.endswith('.pa.yaml'):
            ys[f[4:-8]] = z.read(i).decode('utf-8')
    return js, ys


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


def rule(c, p):
    m = [r for r in c['Rules'] if r['Property'] == p]
    return m[0]['InvariantScript'] if m else None


def cat(c, p):
    m = [r['Category'] for r in c['Rules'] if r['Property'] == p]
    return m[0] if m else None


def flat(t):
    return ' '.join((t or '').split())


new, ny = load(PKG)
old, _ = load(BASE)
ctl = {}
for s, tp in new.items():
    for c in walk(tp):
        ctl.setdefault(c['Name'], []).append((s, c))

# ---- package integrity ----
dups = [k for k, v in ctl.items() if len(v) > 1]
check(not dups, f'control names used twice: {dups}')
uids = [c['ControlUniqueId'] for tp in new.values() for c in walk(tp)]
check(len(uids) == len(set(uids)), 'duplicate ControlUniqueId')
for s, tp in new.items():
    for c in walk(tp):
        for k in c.get('Children', []):
            check(k['Parent'] == c['Name'], f'{s}.{k["Name"]} Parent is {k["Parent"]}, not {c["Name"]}')
        check('Children' in c, f'{s}.{c["Name"]} has no Children key')
        for r in c['Rules']:
            if r['Property'].startswith('On'):
                check(r['Category'] == 'Behavior', f'{s}.{c["Name"]}.{r["Property"]} not Behavior')

PRINT_SCREENS = ['PrintPhotoDetailScreen', 'PrintPodcastDetailScreen', 'PrintVideoDetailScreen']
changed = sorted(s for s in new if s not in old or json.dumps(new[s], sort_keys=True) != json.dumps(old[s], sort_keys=True))


# ---- YAML mirrors JSON: no mismatch that the 24 base does not already have ----
def yaml_issues(js, ys, screen):
    out = set()
    y = yaml.load(ys[screen], Loader=PaLoader)
    doc = y['App'] if screen == 'App' else y['Screens'][screen]
    if screen == 'App':
        for p, v in (doc.get('Properties') or {}).items():
            j = rule(js['App'], p)
            if j is None or flat(str(v).lstrip('=')) != flat(j):
                out.add(f'App.{p}: YAML differs from JSON')
        return out
    ymap, ykids = {screen: doc.get('Properties', {})}, {screen: []}

    def yw(parent, kids):
        for k in kids or []:
            (name, body), = k.items()
            ymap[name] = body.get('Properties', {}) or {}
            ykids.setdefault(parent, []).append(name)
            ykids.setdefault(name, [])
            yw(name, body.get('Children'))
    yw(screen, doc.get('Children'))
    for c in walk(js[screen]):
        if c['Template']['Name'] == 'galleryTemplate' or c.get('IsGroupControl'):
            continue
        if c['Name'] not in ymap:
            out.add(f'{c["Name"]} missing in YAML')
            continue
        jk = sorted(k['Name'] for k in c.get('Children', [])
                    if k['Template']['Name'] != 'galleryTemplate' and not k.get('IsGroupControl'))
        if c is not js[screen] and jk != sorted(ykids.get(c['Name'], [])):
            out.add(f'{c["Name"]}: YAML children differ')
        for p, v in ymap[c['Name']].items():
            j = rule(c, p)
            if j is None or flat(str(v).lstrip('=')) != flat(j):
                out.add(f'{c["Name"]}.{p}: YAML differs from JSON')
    return out


_, oy = load(BASE)
for s_ in changed:
    base = yaml_issues(old, oy, s_) if s_ in oy else set()
    for issue in sorted(yaml_issues(new, ny, s_) - base):
        check(False, f'{s_}: {issue}')
    check(True, f'{s_} yaml')


# ---- v67 ----
A, R = 'Dashboard-Ope-Administrator', 'Dashboard-Ope-Requestor'
check(changed == [A, R], f'changed: {changed}')
na = {c['Name']: c for c in walk(new[A])}; nr = {c['Name']: c for c in walk(new[R])}
oa = {c['Name']: c for c in walk(old[A])}; orr = {c['Name']: c for c in walk(old[R])}
rd = lambda c: {x['Property']: x['InvariantScript'] for x in c['Rules']}
REF = {'Card': 'DOA_List1Card', 'Accent': 'DOA_List1Accent', 'Title': 'DOA_List1Title', 'Sub': 'DOA_List1Sub',
       'Empty': 'DOA_List1Empty', 'Gallery': 'Todo List Gallery', 'RowSelect': 'DOA_List1RowSelect',
       'RowTitle': 'Label2', 'RowMeta': 'DOA_List1RowMeta', 'RowBadge': 'DOA_List1RowBadge',
       'RowDivider': 'DOA_List1RowDivider', 'RowNumber': 'DOA_List1RowBadge_1', 'RowDate': 'Label1'}
# the reference section is untouched
for k, n in REF.items():
    check(json.dumps(na[n], sort_keys=True) == json.dumps(oa[n], sort_keys=True), f'reference {n} changed')
# names: nothing renamed or removed; exactly the number pill and the date added per section
SECTIONS = [(A, 'DOA', 2, na, oa), (A, 'DOA', 3, na, oa), (R, 'DOR', 1, nr, orr), (R, 'DOR', 2, nr, orr), (R, 'DOR', 3, nr, orr)]
added = sorted(set(na) - set(oa)) + sorted(set(nr) - set(orr))
check(sorted(added) == sorted(f'{P}_List{i}{s}' for _, P, i, _, _ in SECTIONS for s in ('RowNumber', 'RowDate')), f'added: {added}')
check(not (set(oa) - set(na)) and not (set(orr) - set(nr)), 'controls removed')
CONTENT = {'Text', 'Items', 'OnSelect', 'Visible', 'Tooltip', 'AccessibleLabel', 'Default'}
ref_card = (int(rule(na['DOA_List1Card'], 'X')), int(rule(na['DOA_List1Card'], 'Y')))
for S, P, i, nc, oc in SECTIONS:
    L = f'{P}_List{i}'
    cx, cy = int(rule(nc[f'{L}Card'], 'X')), int(rule(nc[f'{L}Card'], 'Y'))
    check((cx, cy) == (int(rule(oc[f'{L}Card'], 'X')), int(rule(oc[f'{L}Card'], 'Y'))), f'{L} card moved')
    for suf, rn in REF.items():
        t, r_ = rd(nc[f'{L}{suf}']), rd(na[rn])
        check(nc[f'{L}{suf}']['Template']['Name'] == na[rn]['Template']['Name'], f'{L}{suf} template')
        header = suf in ('Card', 'Accent', 'Title', 'Sub', 'Empty', 'Gallery')
        for p, v in r_.items():
            if p in CONTENT and not (not header and p in ('OnSelect', 'Tooltip')):
                continue
            if header and p in ('X', 'Y', 'ZIndex'):
                continue
            if suf == 'Accent' and p == 'Fill':
                continue
            if suf in ('RowNumber',) and p == 'OnSelect':
                continue
            if P == 'DOR' and suf == 'RowMeta' and p == 'Tooltip':
                continue
            check(t.get(p) == v, f'{L}{suf}.{p}: {str(t.get(p))[:50]!r} != reference {v[:50]!r}')
        if header:
            for p, d in (('X', cx - ref_card[0]), ('Y', cy - ref_card[1])):
                check(int(t[p]) == int(r_[p]) + d, f'{L}{suf}.{p} offset')
    # content kept
    old_sel = rule(oc[f'{L}RowSelect'], 'OnSelect')
    check('Navigate(RequesDetailScreen' in old_sel, f'{L} open formula')
    check(rule(nc[f'{L}RowNumber'], 'OnSelect') == old_sel, f'{L}RowNumber does not open the request')
    check(rule(nc[f'{L}RowSelect'], 'OnSelect') == '', f'{L}RowSelect still opens')
    check(nc[f'{L}RowNumber']['Parent'] == f'{L}Gallery' and nc[f'{L}RowDate']['Parent'] == f'{L}Gallery', f'{L} new controls placement')
    for suf, p in (('Gallery', 'Items'), ('Title', 'Text'), ('Sub', 'Text'), ('Empty', 'Text'), ('Empty', 'Visible'),
                   ('Accent', 'Fill'), ('RowBadge', 'Text')):
        check(rule(nc[f'{L}{suf}'], p) == rule(oc[f'{L}{suf}'], p), f'{L}{suf}.{p} changed')
    if P == 'DOA':
        check(rule(nc[f'{L}RowTitle'], 'Text') == rule(na['Label2'], 'Text'), f'{L} title text')
        check(rule(nc[f'{L}RowMeta'], 'Text') == rule(na['DOA_List1RowMeta'], 'Text'), f'{L} meta text')
    else:
        check(rule(nc[f'{L}RowTitle'], 'Text') == rule(oc[f'{L}RowTitle'], 'Text'), f'{L} title text kept')
        check("'Modified By'.DisplayName" in rule(nc[f'{L}RowMeta'], 'Text'), f'{L} meta text')
    # row controls inside the 86 px row and the 400 px width
    ts = int(rule(nc[f'{L}Gallery'], 'TemplateSize'))
    for c in nc[f'{L}Gallery']['Children']:
        if c['Template']['Name'] == 'galleryTemplate':
            continue
        x, y, w, h = (int(rule(c, p)) for p in ('X', 'Y', 'Width', 'Height'))
        check(x >= 0 and x + w <= 400 and y >= 0 and y + h <= ts, f'{c["Name"]} outside the row')
    # gallery inside the card
    gx, gy, gw, gh = (int(rule(nc[f'{L}Gallery'], p)) for p in ('X', 'Y', 'Width', 'Height'))
    check(gx >= cx and gx + gw <= cx + 416 and gy + gh <= cy + int(rule(nc[f'{L}Card'], 'Height')), f'{L} gallery outside its card')
    check(gy >= int(rule(nc[f'{L}Sub'], 'Y')) + int(rule(nc[f'{L}Sub'], 'Height')), f'{L} gallery under the sub-title')
# the three sections of a screen stay on one line
for S, P, nc in ((A, 'DOA', na), (R, 'DOR', nr)):
    for suf in ('Card', 'Title', 'Sub', 'Empty'):
        check(len({rule(nc[f'{P}_List{i}{suf}'], 'Y') for i in (1, 2, 3)}) == 1, f'{P} {suf} not aligned')
    gy = {rule(nc['Todo List Gallery' if (P, i) == ('DOA', 1) else f'{P}_List{i}Gallery'], 'Y') for i in (1, 2, 3)}
    check(len(gy) == 1, f'{P} galleries not aligned: {gy}')
for c in list(walk(new[A])) + list(walk(new[R])):
    for r in c['Rules']:
        s = r['InvariantScript']
        check(s.count('(') == s.count(')'), f'{c["Name"]}.{r["Property"]} brackets')

print(f'{cnt - len(fails)}/{cnt} checks passed')
for f_ in fails[:60]:
    print('  FAIL', f_)
sys.exit(1 if fails else 0)
