#!/usr/bin/env python3
"""Static checks for v69 against v68: DOA_menu_2 copied to every screen, old menus deleted."""
import json, os, re, sys, zipfile
import yaml
from paload import PaLoader

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v69-menu-all-screens.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-v68-dashboard-sections-v2.msapp'
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


# ---- v69 ----
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from menu_map import menu, ROLES
DOA = 'Dashboard-Ope-Administrator'
PREFIX = {'ChildInfoScreen': 'CI', 'ChildLegalScreen': 'CL', 'ChildMetaScreen': 'CM', 'ChildValidScreen': 'CV',
          'Dashboard-Ope-Requestor': 'DOR', 'DashboardScreen': 'DB', 'HelpScreen': 'HL', 'HomePrintScreen': 'HP',
          'PrintPhotoDetailScreen': 'PPD', 'PrintPodcastDetailScreen': 'PPoD', 'PrintVideoDetailScreen': 'PVD',
          'RequesDetailScreen': 'RS', 'RequestManagementScreen': 'RM', 'ReviewScreen': 'RV'}
check(changed == sorted(PREFIX), f'changed: {changed}')
check(json.dumps(new[DOA], sort_keys=True) == json.dumps(old[DOA], sort_keys=True), 'DOA changed')
rd = lambda c: {x['Property']: x['InvariantScript'] for x in c['Rules']}
dm = menu(new[DOA])
dg = next(c for c in new[DOA]['Children'] if c['Name'] == 'DOA_menu_2')
ztop = lambda tp: {c['Name']: int(rule(c, 'ZIndex')) for c in tp['Children'] if not c.get('IsGroupControl') and (rule(c, 'ZIndex') or '').isdigit()}
for S, P in PREFIX.items():
    om, nm = menu(old[S]), menu(new[S])
    oldn = {c['Name'] for c in om.values()}
    ns = {c['Name']: c for c in walk(new[S])}; os_ = {c['Name']: c for c in walk(old[S])}
    for n in oldn:
        if n not in {f'{P}_' + d['Name'][4:] for d in dm.values()}:
            check(n not in ns, f'{S}: old {n} still there')
    check(sorted(nm) == sorted(ROLES), f'{S}: menu roles {sorted(nm)}')
    for k in ROLES:
        c, d = nm[k], dm[k]
        check(c['Name'] == f'{P}_' + d['Name'][4:], f'{S}: {k} named {c["Name"]}')
        check(c['Parent'] == S, f'{c["Name"]} parent')
        a, b = rd(c), rd(d)
        check({p: v for p, v in a.items() if p != 'ZIndex'} == {p: v for p, v in b.items() if p != 'ZIndex'}, f'{c["Name"]} differs from {d["Name"]}')
        strip = lambda x: {kk: vv for kk, vv in x.items() if kk not in ('Name', 'ControlUniqueId', 'PublishOrderIndex', 'Parent', 'Rules', 'ControlPropertyState')}
        check(strip(c) == strip(d), f'{c["Name"]} metadata differs')
    # z: the new menu sits where the old one did, in DOA's internal order
    oz = sorted(int(rule(c, 'ZIndex')) for c in om.values())
    nz = [int(rule(nm[k], 'ZIndex')) for k in sorted(ROLES, key=lambda k: int(rule(dm[k], 'ZIndex')))]
    check(nz == oz, f'{S}: menu ZIndex {nz} vs old {oz}')
    # group
    g = [c for c in new[S]['Children'] if c.get('IsGroupControl') and c['Name'] == f'{P}_menu_2']
    check(len(g) == 1, f'{S}: group')
    if g:
        check(g[0]['GroupedControlsKey'] == [f'{P}_' + n[4:] for n in dg['GroupedControlsKey']], f'{S}: group members')
        check(rd(g[0]) == rd(dg), f'{S}: group rules')
    for gg in [c for c in new[S]['Children'] if c.get('IsGroupControl')]:
        for n in gg['GroupedControlsKey']:
            check(n in ns, f'{S}: group {gg["Name"]} lists missing {n}')
        check(len(gg['GroupedControlsKey']) > 0, f'{S}: empty group {gg["Name"]}')
    # other groups keep their other members
    for og in [c for c in old[S]['Children'] if c.get('IsGroupControl')]:
        rest = [n for n in og['GroupedControlsKey'] if n not in oldn]
        ng = [c for c in new[S]['Children'] if c.get('IsGroupControl') and c['Name'] == og['Name']]
        if rest:
            check(ng and ng[0]['GroupedControlsKey'] == rest, f'{S}: group {og["Name"]} lost members')
    # every other control unchanged
    for n, c in os_.items():
        if n in oldn or c.get('IsGroupControl'):
            continue
        if n == S:
            check(rd(ns[n]) == rd(c), f'{S}: screen properties changed')
            continue
        check(n in ns and json.dumps(ns[n], sort_keys=True) == json.dumps(c, sort_keys=True), f'{S}: {n} changed')
    # YAML Group line
    y = ny[S]
    for k in ROLES:
        blk = y[y.index(f'- {nm[k]["Name"]}:'):]
        check(f'Group: {P}_menu_2' in blk[:blk.index('Properties:')], f'{S}: {nm[k]["Name"]} YAML group')
    for n in oldn - {c['Name'] for c in nm.values()}:
        check(f'- {n}:' not in y, f'{S}: {n} still in YAML')
names = [c['Name'] for s in new for c in walk(new[s])]
check(len(names) == len(set(names)), 'duplicate names')

print(f'{cnt - len(fails)}/{cnt} checks passed')
for f_ in fails[:60]:
    print('  FAIL', f_)
sys.exit(1 if fails else 0)
