#!/usr/bin/env python3
"""Static checks for v70 against v69: info icon with the sub-title as tooltip on every dashboard section."""
import json, os, re, sys, zipfile
import yaml
from paload import PaLoader

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v70-section-info-icons.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-v69-menu-all-screens.msapp'
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


# ---- v70 ----
A, R = 'Dashboard-Ope-Administrator', 'Dashboard-Ope-Requestor'
check(changed == [A, R], f'changed: {changed}')
rd = lambda c: {x['Property']: x['InvariantScript'] for x in c['Rules']}
donor = next(c for c in walk(old[A]) if c['Name'] == 'DOA_NoInternetIcon_4')
OVR = {'Icon', 'Tooltip', 'AccessibleLabel', 'Color', 'Visible', 'X', 'Y', 'Width', 'Height', 'ZIndex',
       'PaddingTop', 'PaddingRight', 'PaddingBottom', 'PaddingLeft'}
for S, P in ((A, 'DOA'), (R, 'DOR')):
    ns = {c['Name']: c for c in walk(new[S])}; os_ = {c['Name']: c for c in walk(old[S])}
    check(sorted(set(ns) - set(os_)) == [f'{P}_List{i}Info' for i in (1, 2, 3)], f'{S}: added {sorted(set(ns) - set(os_))}')
    check(not set(os_) - set(ns), f'{S}: removed')
    for n, c in os_.items():
        if n == S or c.get('IsGroupControl'):
            continue
        a, b = rd(ns[n]), rd(c)
        if n.endswith('Sub') and n.startswith(f'{P}_List'):
            check(a['Visible'] == 'false' and {k: v for k, v in a.items() if k != 'Visible'} == {k: v for k, v in b.items() if k != 'Visible'}, f'{n}')
        else:
            check(a == b, f'{S}: {n} changed')
    tops = {c['Name']: int(rule(c, 'ZIndex')) for c in new[S]['Children'] if not c.get('IsGroupControl') and (rule(c, 'ZIndex') or '').isdigit()}
    for i in (1, 2, 3):
        ic = ns[f'{P}_List{i}Info']
        check(ic['Parent'] == S and ic['Template']['Name'] == 'icon', f'{P}{i} icon placement')
        a, b = rd(ic), rd(donor)
        check({k: v for k, v in a.items() if k not in OVR} == {k: v for k, v in b.items() if k not in OVR}, f'{P}{i} icon style')
        check(a['Icon'] == 'Icon.Information' and a['Tooltip'] == f'{P}_List{i}Sub.Text' and a['Visible'] == 'true', f'{P}{i} icon props')
        t, card = ns[f'{P}_List{i}Title'], ns[f'{P}_List{i}Card']
        x, y, w, h = (int(a[p]) for p in ('X', 'Y', 'Width', 'Height'))
        tx, ty, tw_, th = (int(rule(t, p)) for p in ('X', 'Y', 'Width', 'Height'))
        cx, cw = int(rule(card, 'X')), int(rule(card, 'Width'))
        check(ty <= y and y + h <= ty + th, f'{P}{i} icon not on the title line')
        check(x > tx + tw_ / 2 and x + w <= cx + cw - 8, f'{P}{i} icon outside the card / left of centre')
        check(tops[ic['Name']] > max(tops[f'{P}_List{i}{s}'] for s in ('Card', 'Accent', 'Title')), f'{P}{i} icon under the card')
        check(f'{P}_List{i}Info' in ny[S], f'{P}{i} icon in YAML')

print(f'{cnt - len(fails)}/{cnt} checks passed')
for f_ in fails[:60]:
    print('  FAIL', f_)
sys.exit(1 if fails else 0)
