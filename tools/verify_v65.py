#!/usr/bin/env python3
"""Static checks for v65 against v64: ChildMetaScreen Photo / Video on the 4-column grid."""
import json, re, sys, zipfile
import yaml
from paload import PaLoader

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v65-meta-grid.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-v64-episode-visual.msapp'
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


# ---- v65 ----
check(changed == ['ChildMetaScreen'], f'changed: {changed}')
CM = 'ChildMetaScreen'
nc = {c['Name']: c for c in walk(new[CM])}
oc = {c['Name']: c for c in walk(old[CM])}


def ev(expr, mt):
    e = expr.strip()
    e = e.replace('<>', '!=')
    e = re.sub(r'(?<![<>!=])=(?!=)', '==', e)
    e = e.replace('varChildMediaType', 'MT').replace(' And ', ' and ').replace(' Or ', ' or ')
    e = re.sub(r'\bNot\(', 'not (', e)
    e = re.sub(r'\btrue\b', 'True', e); e = re.sub(r'\bfalse\b', 'False', e)
    e = re.sub(r'\bIf\(', 'IF(', e); e = re.sub(r'\bSwitch\(', 'SW(', e)
    def IF(*a):
        for i in range(0, len(a) - 1, 2):
            if a[i]:
                return a[i + 1]
        return a[-1] if len(a) % 2 else None
    def SW(v, *a):
        for i in range(0, len(a) - 1, 2):
            if v == a[i]:
                return a[i + 1]
        return a[-1] if len(a) % 2 else None
    return eval(e, {'IF': IF, 'SW': SW, 'MT': mt, 'varChildAIVoiceover': True, 'locShowEpisodeVisual': False,
                    'locShowAudioFiles': False, 'locShowEpVisualPreview': False})


def geo(tree, mt):
    g = {c['Name']: c for c in walk(tree)}['CM_Gallery']
    out = {}
    for c in g['Children']:
        if c['Template']['Name'] == 'galleryTemplate':
            continue
        if not ev(rule(c, 'Visible') or 'true', mt):
            continue
        out[c['Name']] = tuple(ev(rule(c, p), mt) for p in ('X', 'Y', 'Width', 'Height'))
    return out



# podcast and no type: untouched
for mt in ('Podcast', ''):
    o, nn = geo(old[CM], mt), geo(new[CM], mt)
    check(o == nn, f'{mt or "no type"} layout changed: {sorted(k for k in set(o) | set(nn) if o.get(k) != nn.get(k))}')
# only geometry of gallery controls changed
diff = [(c['Name'], r['Property']) for c in walk(new[CM]) for r in c['Rules']
        if rule(oc[c['Name']], r['Property']) != r['InvariantScript']]
check(set(nc) == set(oc), 'controls added / removed')
check(all(p in ('X', 'Y', 'Width') for _, p in diff) and all(nc[n]['Parent'] == 'CM_Gallery' for n, _ in diff), f'unexpected changes: {diff}')

COLS = {56, 367, 678, 989}
EDGES = {351, 662, 973, 1284, 1286}
LBL = {'CM_ShootDate': 'CM_LblShootDate', 'CM_PlacePhoto': 'CM_LblPlacePhoto', 'CM_Authority': 'CM_LblAuthority',
       'CM_Credits': 'CM_LblCredits', 'CM_Caption': 'CM_LblCaptions', 'CM_LinksPhoto': 'CM_LblLinksPhoto',
       'CM_TagsPhoto': 'CM_LblTagsPhoto', 'CM_ProdEnd': 'CM_LblProdEnd', 'CM_PubStartV': 'CM_LblPubStartV',
       'CM_PubEndV': 'CM_LblPubEndV', 'CM_Script': 'CM_LblScript', 'CM_Producer': 'CM_LblProducer',
       'CM_ExecProducer': 'CM_LblExecProducer'}
EXPECT = {'Photo': [['CM_ShootDate', 'CM_PlacePhoto', 'CM_Authority', 'CM_Credits'], ['CM_Caption'],
                    ['CM_LinksPhoto', 'CM_TagsPhoto']],
          'Video': [['CM_ShootDate', 'CM_ProdEnd', 'CM_PubStartV', 'CM_PubEndV'], ['CM_PlacePhoto', 'CM_LinksPhoto', 'CM_TagsPhoto'],
                    ['CM_Script'], ['CM_Producer', 'CM_ExecProducer', 'CM_Credits']]}
for mt, rows_ in EXPECT.items():
    P = geo(new[CM], mt)
    card = P['CM_Card']
    for k, (x, y, w, h) in P.items():
        if k == 'CM_Card':
            continue
        check(x >= card[0] + 16 and x + w <= card[0] + card[2] - 16, f'{mt}: {k} outside the card width')
        check(y >= card[1] and y + h <= card[1] + card[3] - 16, f'{mt}: {k} outside the card height')
    check(card[1] + card[3] <= ev(rule(nc['CM_Gallery'], 'TemplateSize'), mt), f'{mt}: card taller than the row')
    BG = {'CM_Card', 'CM_PodcastNote', 'CM_PhotoNotice', 'CM_AIWarning'}
    items = [(k, v) for k, v in P.items() if k not in BG and k not in ('CM_PhotoNoticeText', 'CM_AIWarningText')]
    for i, (a, (ax, ay, aw, ah)) in enumerate(items):
        for bn, (bx, by, bw, bh) in items[i + 1:]:
            check(ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay, f'{mt}: {a} overlaps {bn}')
    # the AI warning under every field
    ai = P['CM_AIWarning']
    for k, (x, y, w, h) in items:
        if k not in ('CM_TypeBadge', 'CM_SectionHeader'):
            check(y + h <= ai[1], f'{mt}: AI warning over {k}')
    check(P['CM_AIWarningText'][1] == ai[1], f'{mt}: AI text / box')
    prev_bottom = 0
    for row in rows_:
        ys = {P[f][1] for f in row}
        check(len(ys) == 1, f'{mt}: row {row} not on one line')
        check(len({P[f][3] for f in row}) == 1, f'{mt}: row {row} heights differ')
        check(min(ys) > prev_bottom, f'{mt}: row {row} order')
        prev_bottom = max(P[f][1] + P[f][3] for f in row)
        xs = sorted((P[f][0], P[f][0] + P[f][2]) for f in row)
        check(xs[0][0] == 56 and xs[-1][1] in (1284, 1286), f'{mt}: row {row} does not fill the width {xs}')
        for (a0, a1), (b0, b1) in zip(xs, xs[1:]):
            check(b0 - a1 == 16, f'{mt}: row {row} gap {b0 - a1}')
        for f in row:
            x, y, w, h = P[f]
            check(x in COLS and x + w in EDGES, f'{mt}: {f} off the grid ({x}, {x + w})')
            lx, ly, lw, lh = P[LBL[f]]
            check(lx == x and ly + 26 == y and lw <= max(w, 800), f'{mt}: {LBL[f]} not above {f}')
    shown = {f for row in rows_ for f in row}
    for f in LBL:
        if f in P and f not in shown:
            check(False, f'{mt}: {f} shown but not placed')

for c in walk(new[CM]):
    for r in c['Rules']:
        if r['Property'] in ('X', 'Y', 'Width'):
            s = r['InvariantScript']
            check(s.count('(') == s.count(')'), f'{c["Name"]}.{r["Property"]} brackets')

print(f'{cnt - len(fails)}/{cnt} checks passed')
for f_ in fails[:60]:
    print('  FAIL', f_)
sys.exit(1 if fails else 0)
