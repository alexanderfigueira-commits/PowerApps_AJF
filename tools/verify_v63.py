#!/usr/bin/env python3
"""Static checks for v63 against v62: ChildInfoScreen podcast visual preview pop-up."""
import json, re, sys, zipfile
import yaml
from paload import PaLoader

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v63-visual-preview.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-v62-podcast-filter.msapp'
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


# ---- v63: podcast visual preview ----
check(changed == ['ChildInfoScreen'], f'changed: {changed}')
S = 'ChildInfoScreen'
oc = {c['Name']: c for c in walk(old[S])}
nc = {c['Name']: c for c in walk(new[S])}
NEWC = ['CI_BtnViewVisual', 'CI_VisualShade', 'CI_VisualPanel', 'CI_LblVisualPanel', 'CI_VisualFile',
        'CI_VisualImage', 'CI_VisualClose']
check(sorted(set(nc) - set(oc)) == sorted(NEWC), f'added: {sorted(set(nc) - set(oc))}')
check(not set(oc) - set(nc), 'controls removed')
diff = [(c['Name'], r['Property']) for c in walk(new[S]) if c['Name'] in oc
        for r in c['Rules'] if rule(oc[c['Name']], r['Property']) != r['InvariantScript']]
check(diff == [('ChildInfoScreen', 'OnVisible')], f'changed rules: {diff}')
ov = rule(new[S], 'OnVisible')
check(ov.startswith(rule(old[S], 'OnVisible')) and ov.rstrip().endswith('UpdateContext({locShowVisualPreview: false})'), 'OnVisible')
tpl = {'CI_BtnViewVisual': 'button', 'CI_VisualShade': 'rectangle', 'CI_VisualPanel': 'rectangle',
       'CI_LblVisualPanel': 'label', 'CI_VisualFile': 'label', 'CI_VisualImage': 'image', 'CI_VisualClose': 'button'}
for k, t in tpl.items():
    check(nc[k]['Template']['Name'] == t, f'{k} template')
    for r in nc[k]['Rules']:
        check(r['InvariantScript'].count('(') == r['InvariantScript'].count(')'), f'{k}.{r["Property"]} brackets')
        check(' + "' not in r['InvariantScript'] and '" + ' not in r['InvariantScript'], f'{k}.{r["Property"]} uses + for text')
bt = nc['CI_BtnViewVisual']
check(bt['Parent'] == 'CI_Gallery', 'view button not in the gallery row')
check(rule(bt, 'Visible') == 'varChildMediaType = "Podcast"', 'view button visibility')
check(rule(bt, 'OnSelect') == 'UpdateContext({locShowVisualPreview: true})', 'view button OnSelect')
check('DisplayMode.Disabled' in rule(bt, 'DisplayMode'), 'view button disabled without image')
up = nc['CI_BtnOpenAttach']
check(rule(bt, 'Y') == rule(up, 'Y') and rule(bt, 'Height') == rule(up, 'Height'), 'view button not on the upload row')
check(int(rule(bt, 'X')) >= int(rule(up, 'X')) + int(rule(up, 'Width')) + 10, 'view button overlaps upload')
check(int(rule(bt, 'X')) + int(rule(bt, 'Width')) <= 32 + 1302 - 20, 'view button outside the card')
for k in NEWC[1:]:
    check(nc[k]['Parent'] == S, f'{k} not on the screen')
    check(rule(nc[k], 'Visible') == 'locShowVisualPreview And varChildMediaType = "Podcast"', f'{k} Visible')
for k in ('CI_VisualShade', 'CI_VisualClose'):
    check(rule(nc[k], 'OnSelect') == 'UpdateContext({locShowVisualPreview: false})', f'{k} closes')
im = nc['CI_VisualImage']
check(rule(im, 'Image') == 'Last(Filter(CI_PodcastVisual.Attachments, EndsWith(Lower(Name), ".jpg") Or EndsWith(Lower(Name), ".jpeg") Or EndsWith(Lower(Name), ".png"))).Value', 'image source')
check(rule(im, 'ImagePosition') == 'ImagePosition.Fit' and rule(im, 'CalculateOriginalDimensions') == 'true', 'image fit / dimensions')
check('CI_VisualImage.OriginalWidth' in rule(nc['CI_VisualFile'], 'Text'), 'file label size')
# pop-up above everything else, inside the panel
top = [c for c in new[S]['Children'] if not c.get('IsGroupControl')]
zs = {c['Name']: int(rule(c, 'ZIndex')) for c in top}
check(min(zs[k] for k in NEWC[1:]) > max(z for k, z in zs.items() if k not in NEWC), 'pop-up under other controls')
check([zs[k] for k in NEWC[1:]] == sorted(zs[k] for k in NEWC[1:]), 'pop-up z order')
px, py, pw, ph = (int(rule(nc['CI_VisualPanel'], p)) for p in ('X', 'Y', 'Width', 'Height'))
check(px >= 0 and py >= 0 and px + pw <= 1366 and py + ph <= 768, 'panel off screen')
for k in ('CI_LblVisualPanel', 'CI_VisualFile', 'CI_VisualImage', 'CI_VisualClose'):
    x, y, w, h = (int(rule(nc[k], p)) for p in ('X', 'Y', 'Width', 'Height'))
    check(x >= px and y >= py and x + w <= px + pw and y + h <= py + ph, f'{k} outside the panel')
for a, bb in (('CI_LblVisualPanel', 'CI_VisualFile'), ('CI_VisualFile', 'CI_VisualImage')):
    check(int(rule(nc[a], 'Y')) + int(rule(nc[a], 'Height')) <= int(rule(nc[bb], 'Y')), f'{a} overlaps {bb}')
x, w = int(rule(nc['CI_LblVisualPanel'], 'X')), int(rule(nc['CI_LblVisualPanel'], 'Width'))
check(x + w <= int(rule(nc['CI_VisualClose'], 'X')), 'title under the close button')

print(f'{n - len(fails)}/{n} checks passed')
for f in fails[:40]:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
