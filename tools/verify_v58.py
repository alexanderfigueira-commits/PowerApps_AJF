#!/usr/bin/env python3
"""Static checks for v58 against v57: print screens fit one sheet."""
import json, re, sys, zipfile
import yaml
from paload import PaLoader

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v58-print-one-sheet.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-v57-dashboard-nav.msapp'
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


# ---- v58: print screens fit one sheet ----
PR = {'PVD': 'PrintVideoDetailScreen', 'PPoD': 'PrintPodcastDetailScreen', 'PPD': 'PrintPhotoDetailScreen'}
check(changed == sorted(PR.values()), f'changed: {changed}')
for p, scr in PR.items():
    nc = {c['Name']: c for c in walk(new[scr])}
    oc = {c['Name']: c for c in walk(old[scr])}
    check(set(nc) - set(oc) == {f'{p}_More'} and not set(oc) - set(nc), f'{scr} controls added/removed')
    for k in ('BtnPrint', 'BtnBack'):
        for q in ('OnSelect', 'Visible'):
            check(rule(nc[f'{p}_{k}'], q) == rule(oc[f'{p}_{k}'], q), f'{p}_{k}.{q} changed')
    g = nc[f'{p}_Gallery']
    ts = int(rule(g, 'TemplateSize'))
    gy = int(rule(g, 'Y'))
    fit = (740 - gy) // ts
    check(fit >= 3, f'{p}: only {fit} row(s) fit')
    check(gy + fit * ts <= 740 < int(rule(nc[f'{p}_Footer'], 'Y')), f'{p} gallery over the footer')
    kids = {k['Name']: k for k in g['Children'] if k['Template']['Name'] != 'galleryTemplate'}
    ys = {}
    def yof(k, d=0):
        if k in ys:
            return ys[k]
        t = rule(kids[k], 'Y').strip()
        if t.lstrip('-').isdigit():
            v = int(t)
        else:
            m = re.fullmatch(r'(\w+)\.Y(?: \+ If\(\1\.Visible, \1\.Height, 0\))?', t)
            check(m is not None and d < 40, f'{p} {k}.Y: {t}')
            v = yof(m.group(1), d + 1) + (int(rule(kids[m.group(1)], 'Height')) if '+' in t else 0)
        ys[k] = v
        return v
    for k, c in kids.items():
        x, w, h = int(rule(c, 'X')), int(rule(c, 'Width')), int(rule(c, 'Height'))
        check(x + w <= 1302, f'{k} wider than the row')
        if not k.endswith('RowRule'):
            check(yof(k) + h <= ts, f'{k} below its row ({yof(k)}+{h} > {ts})')
        mm = re.fullmatch(p + r'_(Lbl|Val)(\d+)', k)
        if mm and mm.group(1) == 'Lbl':
            check(rule(c, 'Visible') == f'{p}_Val{mm.group(2)}.Visible' and rule(c, 'Y') == f'{p}_Val{mm.group(2)}.Y', f'{k} not tied to its value')
        if mm and mm.group(1) == 'Val':
            check(rule(c, 'Text') == rule(oc[k], 'Text'), f'{k}.Text changed')
            check(rule(c, 'PaddingTop') == '0' and rule(c, 'PaddingBottom') == '0', f'{k} padding')
    # no two fields overlap (worst case: all visible)
    fields = [k for k in kids if re.fullmatch(p + r'_(Lbl\d+|Val\d+|Sec\d+|RowCaption)', k)]
    for i, a1 in enumerate(fields):
        for b1 in fields[i + 1:]:
            x1, w1, h1 = int(rule(kids[a1], 'X')), int(rule(kids[a1], 'Width')), int(rule(kids[a1], 'Height'))
            x2, w2, h2 = int(rule(kids[b1], 'X')), int(rule(kids[b1], 'Width')), int(rule(kids[b1], 'Height'))
            y1, y2 = yof(a1), yof(b1)
            check(not (x1 < x2 + w2 and x2 < x1 + w1 and y1 < y2 + h2 and y2 < y1 + h1), f'{a1} overlaps {b1}')
    for c in new[scr]['Children']:
        if c.get('IsGroupControl'):
            continue
        try:
            x, y, w, h = (int(rule(c, q)) for q in ('X', 'Y', 'Width', 'Height'))
        except (TypeError, ValueError):
            continue
        check(x + w <= 1366 and y + h <= 768, f'{c["Name"]} off screen')

print(f'{n - len(fails)}/{n} checks passed')
for f in fails[:40]:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
