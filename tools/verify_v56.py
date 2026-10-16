#!/usr/bin/env python3
"""Static checks for v56 against v55: role dashboards and start screen."""
import json, re, sys, zipfile
import yaml
from paload import PaLoader

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v56-role-dashboards.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-v55-notes-popups.msapp'
fails, n = [], 0


def check(ok, msg):
    global n
    n += 1
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


# ---- v56: role dashboards ----
NEWS = {'Dashboard-Ope-Requestor': 'DOR', 'Dashboard-Ope-Administrator': 'DOA'}
check(changed == ['App', 'Dashboard-Ope-Administrator', 'Dashboard-Ope-Requestor'], f'changed: {changed}')
idx = sorted(tp['Index'] for nm, tp in new.items() if nm != 'App')
check(idx == list(range(len(idx))), f'screen indexes {idx}')
es = ny['_EditorState']
check('    - Dashboard-Ope-Requestor\n    - Dashboard-Ope-Administrator' in es, 'ScreensOrder')
st = rule(new['App'], 'StartScreen')
check("'Dashboard-Ope-Administrator'" in st and "'Dashboard-Ope-Requestor'" in st and 'RolesPermissionsList' in st,
      'StartScreen by role')
check('StartScreen' in ny['App'], 'StartScreen in App.pa.yaml')
for scr, P in NEWS.items():
    nc = {c['Name']: c for c in walk(new[scr])}
    check(all(k.startswith(P + '_') for k in nc if k != scr), f'{scr}: control without {P}_ prefix')
    for g in new[scr]['Children']:
        if g.get('IsGroupControl'):
            check(set(g['GroupedControlsKey']) <= set(nc), f'{g["Name"]} groups missing controls')
    ov = rule(new[scr], 'OnVisible')
    check('Set(varUserRole' in ov and 'colOpeReqs' in ov, f'{scr} OnVisible')
    items = [rule(nc[f'{P}_List{i}Gallery'], 'Items') for i in (1, 2, 3)]
    first, second = ('Pending', 'Draft') if P == 'DOR' else ('Pending', 'Processing')
    check(items[0].index(f'"{first}"') < items[0].index(f'"{second}"') and items[0].count('SortOrder.Ascending') == 2
          and 'Ungroup(' in items[0], f'{P} list 1')
    want2 = '["Draft", "Pending"]' if P == 'DOR' else '["Pending", "Processing"]'
    check(want2 in items[1] and 'SortOrder.Descending' in items[1], f'{P} list 2')
    check('["Published", "Approved", "Partially approved", "Rejected"]' in items[2] and 'SortOrder.Descending' in items[2],
          f'{P} list 3')
    if P == 'DOA':
        check('Status.Value <> "Draft"' in ov, 'admin excludes drafts')
    else:
        check("'Created By'.Email = User().Email" in ov, 'requestor own requests')
    for i in (1, 2, 3):
        g = nc[f'{P}_List{i}Gallery']
        kids = sorted(k['Name'] for k in g['Children'] if k['Template']['Name'] != 'galleryTemplate')
        check(kids == sorted(f'{P}_List{i}Row{k}' for k in ('Select', 'Title', 'Meta', 'Badge', 'Divider')), f'{P} list {i} rows')
        sel = rule(nc[f'{P}_List{i}RowSelect'], 'OnSelect')
        check('Navigate(RequesDetailScreen' in sel and cat(nc[f'{P}_List{i}RowSelect'], 'OnSelect') == 'Behavior', f'{P} row open')
        x = int(rule(nc[f'{P}_List{i}Card'], 'X'))
        check(x + int(rule(nc[f'{P}_List{i}Card'], 'Width')) <= 1366, f'{P} card {i} off screen')
    for c in nc.values():
        for r in c['Rules']:
            t = r['InvariantScript']
            check(t.count('(') == t.count(')'), f'{c["Name"]}.{r["Property"]} brackets')

print(f'{n - len(fails)}/{n} checks passed')
for f in fails[:40]:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
