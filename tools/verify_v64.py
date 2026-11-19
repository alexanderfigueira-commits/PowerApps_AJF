#!/usr/bin/env python3
"""Static checks for v64 against v63: ChildMetaScreen podcast grid, episode visual upload + preview."""
import json, re, sys, zipfile
import yaml
from paload import PaLoader

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v64-episode-visual.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-v63-visual-preview.msapp'
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


# ---- v64 ----
check(changed == ['ChildInfoScreen', 'ChildLegalScreen', 'ChildMetaScreen', 'ChildValidScreen'], f'changed: {changed}')
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


# other media types: layout untouched
for mt in ('Photo', 'Video', ''):
    o, nn = geo(old[CM], mt), geo(new[CM], mt)
    check(o == nn, f'{mt or "no type"} layout changed: {sorted(k for k in set(o) | set(nn) if o.get(k) != nn.get(k))}')

P = geo(new[CM], 'Podcast')
card = P['CM_Card']
check(card[0] == 32 and card[2] == 1302, 'card')
BG = {'CM_Card', 'CM_PodcastNote', 'CM_AIWarning'}
for k, (x, y, w, h) in P.items():
    if k == 'CM_Card':
        continue
    check(x >= card[0] + 16 and x + w <= card[0] + card[2] - 16, f'{k} outside the card width ({x}+{w})')
    check(y >= card[1] and y + h <= card[1] + card[3] - 16, f'{k} outside the card height ({y}+{h} > {card[1] + card[3]})')
check(card[1] + card[3] <= ev(rule(nc['CM_Gallery'], 'TemplateSize'), 'Podcast'), 'card taller than the row')
items = [(k, v) for k, v in P.items() if k not in BG and k not in ('CM_PodcastNoteText', 'CM_AIWarningText')]
for i, (a, (ax, ay, aw, ah)) in enumerate(items):
    for bn, (bx, by, bw, bh) in items[i + 1:]:
        check(ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay, f'podcast: {a} overlaps {bn}')
# the grid: fields start on a column and end on a column edge
COLS = {56, 367, 678, 989}
EDGES = {351, 662, 973, 1284, 1286}
FIELDS = ['CM_SeasonNumber', 'CM_EpisodeNumber', 'CM_EpisodeTitleP', 'CM_EpisodeSummary', 'CM_Language', 'CM_ShootDate',
          'CM_ProdEnd', 'CM_PubStartV', 'CM_PubEndV', 'CM_PlacePhoto', 'CM_LinksPhoto', 'CM_TagsPhoto', 'CM_Producer',
          'CM_ExecProducer', 'CM_Credits', 'CM_BtnOpenEpisodeVisual', 'CM_BtnViewEpisodeVisual', 'CM_BtnOpenAttach']
for f in FIELDS:
    x, y, w, h = P[f]
    if f != 'CM_EpisodeNumber':
        check(x in COLS, f'{f} X {x} off the grid')
    if f != 'CM_SeasonNumber':     # season + episode share column 1
        check(x + w in EDGES, f'{f} right edge {x + w} off the grid')
    lbl = {'CM_SeasonNumber': 'CM_LblSeasonNumber', 'CM_EpisodeNumber': 'CM_LblEpisodeNumber',
           'CM_EpisodeTitleP': 'CM_LblEpisodeTitleP', 'CM_EpisodeSummary': 'CM_LblEpisodeSummary',
           'CM_Language': 'CM_LblLanguage', 'CM_ShootDate': 'CM_LblShootDate', 'CM_ProdEnd': 'CM_LblProdEnd',
           'CM_PubStartV': 'CM_LblPubStartV', 'CM_PubEndV': 'CM_LblPubEndV', 'CM_PlacePhoto': 'CM_LblPlacePhoto',
           'CM_LinksPhoto': 'CM_LblLinksPhoto', 'CM_TagsPhoto': 'CM_LblTagsPhoto', 'CM_Producer': 'CM_LblProducer',
           'CM_ExecProducer': 'CM_LblExecProducer', 'CM_Credits': 'CM_LblCredits'}.get(f)
    if lbl:
        lx, ly, lw, lh = P[lbl]
        check(lx == x and ly + 26 == y, f'{lbl} not above {f} ({lx},{ly}) vs ({x},{y})')
rows = {}
for f in FIELDS:
    rows.setdefault(P[f][1], []).append(f)
for y, fs in rows.items():
    check(len({P[f][3] for f in fs}) == 1, f'row {y}: heights differ {fs}')
check(P['CM_SeasonNumber'][0] + P['CM_SeasonNumber'][2] + 17 == P['CM_EpisodeNumber'][0], 'season / episode gap')

# episode visual form
f = nc['CM_FormEpisodeVisual']; fa = nc['CM_FormAudioFiles']
check(f['Parent'] == CM and f['Template']['Name'] == 'form', 'form placement')
for p in ('DataSource', 'Item', 'DefaultMode', 'OnSuccess', 'OnFailure'):
    check(rule(f, p) == rule(fa, p), f'form {p} differs from CM_FormAudioFiles')
v = nc['CM_EpisodeVisual']
check(v['Template']['Name'] == 'attachments' and v['Parent'] == 'CM_DCEpisodeVisual' and nc['CM_DCEpisodeVisual']['Parent'] == 'CM_FormEpisodeVisual', 'CM_EpisodeVisual placement')
check(rule(nc['CM_DCEpisodeVisual'], 'Update') == 'CM_EpisodeVisual.Attachments', 'card Update')
check(rule(nc['CM_DCEpisodeVisual'], 'DataField') == '"{Attachments}"', 'card DataField')
code = re.sub(r'//.*', '', rule(v, 'Items'))
check('Filter(varAttachRecord.Attachments, StartsWith(DisplayName, "EpisodeVisual_") And (' in code and 'Parent.Default' not in code, 'EV Items')
check(rule(v, 'MaxAttachments') == '1', 'EV max 1')
check('CM_AudioFiles' not in json.dumps(f), 'EV form still names the audio box')
VIS = 'locShowEpisodeVisual And varChildMediaType = "Podcast"'
for n in ('CM_EVAttachShade', 'CM_EVAttachPanel', 'CM_LblEVAttachPanel', 'CM_EVAttachFor', 'CM_EVAttachHint', 'CM_FormEpisodeVisual', 'CM_EVAttachClose'):
    check(rule(nc[n], 'Visible') == VIS, f'{n}.Visible')
check(rule(nc['CM_EVAttachNeedSave'], 'Visible') == f'IsBlank(varAttachRecord) And {VIS}', 'need-save visible')
for n in ('CM_EVAttachShade', 'CM_EVAttachClose'):
    check(rule(nc[n], 'OnSelect') == 'UpdateContext({locShowEpisodeVisual: false})', f'{n} closes')
bo = nc['CM_BtnOpenEpisodeVisual']; bv = nc['CM_BtnViewEpisodeVisual']
check(bo['Parent'] == 'CM_Gallery' and rule(bo, 'OnSelect') == 'UpdateContext({locShowEpisodeVisual: true})', 'upload button')
check(bv['Parent'] == 'CM_Gallery' and rule(bv, 'OnSelect') == 'UpdateContext({locShowEpVisualPreview: true})', 'view button')
check('DisplayMode.Disabled' in rule(bv, 'DisplayMode'), 'view disabled without image')
PV = 'locShowEpVisualPreview And varChildMediaType = "Podcast"'
PREV = ['CM_EpVisualShade', 'CM_EpVisualPanel', 'CM_LblEpVisualPanel', 'CM_EpVisualFile', 'CM_EpVisualImage', 'CM_EpVisualClose']
for n in PREV:
    check(rule(nc[n], 'Visible') == PV, f'{n}.Visible')
im = nc['CM_EpVisualImage']
check(rule(im, 'Image') == 'Last(Filter(CM_EpisodeVisual.Attachments, EndsWith(Lower(Name), ".jpg") Or EndsWith(Lower(Name), ".jpeg") Or EndsWith(Lower(Name), ".png"))).Value', 'preview image')
check(rule(im, 'CalculateOriginalDimensions') == 'true', 'dimensions')
t = rule(nc['CM_EpVisualFile'], 'Text')
check('CM_EpVisualImage.OriginalWidth' in t and 'w = 1280 And h = 720' in t, 'format check')
ov = rule(new[CM], 'OnVisible')
check(ov.startswith(rule(old[CM], 'OnVisible')) and ov.rstrip().endswith('UpdateContext({locShowEpisodeVisual: false, locShowEpVisualPreview: false})'), 'OnVisible')
top = [c for c in new[CM]['Children'] if not c.get('IsGroupControl')]
zs = {c['Name']: int(rule(c, 'ZIndex')) for c in top}
UP = ['CM_EVAttachShade', 'CM_EVAttachPanel', 'CM_LblEVAttachPanel', 'CM_EVAttachFor', 'CM_EVAttachHint',
      'CM_FormEpisodeVisual', 'CM_EVAttachNeedSave', 'CM_EVAttachClose']
rest = [z for k, z in zs.items() if k not in UP + PREV]
check(min(zs[k] for k in UP) > max(rest), 'upload pop-up under other controls')
check(min(zs[k] for k in PREV) > max(zs[k] for k in UP), 'preview under the upload pop-up')
for k in UP + PREV:
    check(list(zs.values()).count(zs[k]) == 1, f'{k} shares its ZIndex')
for n in PREV + UP + ['CM_BtnOpenEpisodeVisual', 'CM_BtnViewEpisodeVisual']:
    for c in walk(nc[n]):
        for r in c['Rules']:
            s = r['InvariantScript']
            check(s.count('(') == s.count(')'), f'{c["Name"]}.{r["Property"]} brackets')
            check(' + "' not in s and '" + ' not in s, f'{c["Name"]}.{r["Property"]} + on text')
# only the podcast branch of shared formulas changed
for n, c in nc.items():
    if n not in oc or c['Parent'] not in ('CM_Gallery', CM):
        continue
    if rule(c, 'Visible') == 'varChildMediaType = "Podcast"':
        continue    # podcast-only: hidden for the other types
    for r in c['Rules']:
        o = rule(oc[n], r['Property'])
        if o is None or o == r['InvariantScript'] or r['Property'] not in ('X', 'Y', 'Width', 'Height'):
            continue
        for mt in ('Photo', 'Video', ''):
            check(ev(o, mt) == ev(r['InvariantScript'], mt), f'{n}.{r["Property"]} changed for {mt}')

# Info tab: podcast visual leaves episode visuals out
ci = {c['Name']: c for c in walk(new['ChildInfoScreen'])}
code = re.sub(r'//.*', '', rule(ci['CI_PodcastVisual'], 'Items'))
check('Filter(varAttachRecord.Attachments, Not(StartsWith(DisplayName, "EpisodeVisual_")) And (' in code, 'CI Items')
check('episode' not in rule(ci['CI_DCPodcastVisualKey'], 'Text').lower(), 'CI key text')
# the merge
u = rule({c['Name']: c for c in walk(new['ChildLegalScreen'])}['CL_DCAttach'], 'Update')
code = re.sub(r'//.*', '', u)
check(code.count('(') == code.count(')') and code.count('{') == code.count('}'), 'merge brackets')
for need in ('Name in CM_EpisodeVisual.Attachments.Name', 'pre: "EpisodeVisual_", files: Filter(', 'DisplayName: f.pre & f.Name',
             'f.pre & f.Name)', 'Not(("EpisodeVisual_" & Name) in saved)', 'CI_PodcastVisual.Attachments', 'CM_AudioFiles.Attachments'):
    check(need in code, f'merge misses {need}')
check(code.count('pre: ""') == 3, 'merge: three unprefixed sources')
# validations
cv = {c['Name']: c for c in walk(new['ChildValidScreen'])}
for n, p in (('CV_BtnRefresh', 'OnSelect'), ('ChildValidScreen', 'OnVisible')):
    s = rule(cv[n], p)
    check(s.count('CountRows(Filter(CM_EpisodeVisual.Attachments, EndsWith(Lower(Name), ".gif")') == 1, f'{n} format check')
    check(s.count('(') == s.count(')'), f'{n} brackets')

print(f'{cnt - len(fails)}/{cnt} checks passed')
for f_ in fails[:60]:
    print('  FAIL', f_)
sys.exit(1 if fails else 0)
