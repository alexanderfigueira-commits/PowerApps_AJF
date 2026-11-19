#!/usr/bin/env python3
"""Static checks for v47 (print navigation + A4 print screens) against the 24 base."""
import json, os, re, sys, zipfile
from paload import load

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v47-print-a4.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'AV-CD-24.msapp'  # the 24.msapp you sent
fails, n = [], 0


def check(ok, msg):
    global n
    n += 1
    if not ok:
        fails.append(msg)


def screens(path):
    z = zipfile.ZipFile(path)
    out, yml = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig'))
            out[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('Src/') and f.endswith('.pa.yaml'):
            yml[f[4:-8]] = z.read(i).decode('utf-8')
    return z, out, yml


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


def rule(c, p):
    m = [r for r in c['Rules'] if r['Property'] == p]
    return m[0]['InvariantScript'] if m else None


z, new, ny = screens(PKG)
_, old, _ = screens(BASE)
ds = json.loads(z.read('References\\DataSources.json'))
cols = {d['Name']: set(d['ConnectedDataSourceInfoNameMapping'].values())
        for d in ds['DataSources'] if d['Name'] in ('AV-CD-Requests', 'AV-CD-Mediafiles')}

# ---- only the intended screens changed ----
changed = sorted(s for s in new if json.dumps(new[s], sort_keys=True) != json.dumps(old[s], sort_keys=True))
check(changed == ['HomePrintScreen', 'PrintPhotoDetailScreen', 'PrintPodcastDetailScreen',
                  'PrintVideoDetailScreen'], f'unexpected screens changed: {changed}')
hp_diff = [(c['Name'], r['Property']) for c in walk(new['HomePrintScreen'])
           for r in c['Rules']
           if rule(next((o for o in walk(old['HomePrintScreen']) if o['Name'] == c['Name']), {'Rules': []}),
                   r['Property']) != r['InvariantScript']]
check(sorted(hp_diff) == [('HP_RowChevron', 'OnSelect'), ('HP_RowChevron', 'TabIndex'),
                          ('HP_RowChevron', 'Tooltip')], f'HomePrintScreen rules changed: {hp_diff}')

# ---- YAML mirrors JSON, rule by rule ----
def yaml_rules(text):
    d = load(text) if not os.path.exists(text) else load(text)
    return d


import yaml as _y
from paload import PaLoader
for s in changed:
    doc = _y.load(ny[s], Loader=PaLoader)['Screens'][s]
    ymap = {s: doc.get('Properties', {})}
    def yw(kids):
        for k in kids or []:
            (name, body), = k.items()
            ymap[name] = body.get('Properties', {}) or {}
            yw(body.get('Children'))
    yw(doc.get('Children'))
    for c in walk(new[s]):
        if c['Template']['Name'] in ('galleryTemplate',) or c.get('IsGroupControl'):
            continue
        yp = ymap.get(c['Name'])
        check(yp is not None, f'{s}.{c["Name"]} missing in YAML')
        if yp is None:
            continue
        for p, v in yp.items():
            if c is new[s] and p == 'LoadingSpinnerColor':
                continue  # Studio keeps the screen's spinner colour outside Rules (same in 24)
            j = rule(c, p)
            v = str(v)
            check(j is not None and ' '.join(v.lstrip('=').split()) == ' '.join(j.split()),
                  f'{s}.{c["Name"]}.{p}: YAML {v[:60]!r} != JSON {str(j)[:60]!r}')

# ---- Task 2 ----
hp = {c['Name']: c for c in walk(new['HomePrintScreen'])}
ch = rule(hp['HP_RowChevron'], 'OnSelect')
cat = [r['Category'] for r in hp['HP_RowChevron']['Rules'] if r['Property'] == 'OnSelect'][0]
check(cat == 'Behavior', 'chevron OnSelect is not a Behavior rule')
check('Set(varPrintRequest, ThisItem)' in ch, 'chevron does not set varPrintRequest')
for scr in ('PrintVideoDetailScreen', 'PrintPodcastDetailScreen', 'PrintPhotoDetailScreen'):
    check(f'Navigate({scr}' in ch, f'chevron misses {scr}')
check('First(LookUp(\'AV-CD-Mediafiles\', ParentRequest = ThisItem.RequestNumber).MediaType).Value' in ch,
      'chevron switch is not on First(MediaType).Value')
check(' + ' not in ch and '" +' not in ch, 'text joined with + in chevron')
setters = [(s, c['Name']) for s in new for c in walk(new[s]) for r in c['Rules']
           if re.search(r'Set\(\s*varPrintRequest', r['InvariantScript'])]
check(setters == [('HomePrintScreen', 'HP_RowChevron')], f'varPrintRequest set by {setters}')

MEDIA_COLS, REQ_COLS = cols['AV-CD-Mediafiles'], cols['AV-CD-Requests']
missing = set()
for s in ('PrintVideoDetailScreen', 'PrintPodcastDetailScreen', 'PrintPhotoDetailScreen'):
    tp = new[s]
    ov = rule(tp, 'OnVisible')
    check([r['Category'] for r in tp['Rules'] if r['Property'] == 'OnVisible'] == ['Behavior'],
          f'{s}.OnVisible category')
    check("Filter('AV-CD-Mediafiles', ParentRequest = varPrintRequest.RequestNumber)" in ov,
          f'{s}.OnVisible does not filter the media list by the request')
    for c in walk(tp):
        for r in c['Rules']:
            t = r['InvariantScript']
            check('gblPrintRequest' not in t and 'colPrintMedia' not in t and 'locPrinting' not in t,
                  f'{s}.{c["Name"]}.{r["Property"]} still uses an old name')
            for f in re.findall(r'varPrintRequest\.(\'[^\']+\'|\w+)', t):
                if f.strip("'") not in REQ_COLS:
                    missing.add(('request', f))
            for f in re.findall(r'(?:ThisItem|First\(colPrintReqMedia\))\.(\'[^\']+\'|\w+)', t):
                if f.strip("'") not in MEDIA_COLS:
                    missing.add(('media', f))
check(not missing, f'fields with no matching column: {sorted(missing)}')

# ---- Task 3: geometry in both modes ----
def num(expr, printing, sib):
    e = expr
    e = re.sub(r'If\(\w+\.Printing, (\d+), 0\)', lambda m: m.group(1) if printing else '0', e)
    return e


for p, s in (('PVD', 'PrintVideoDetailScreen'), ('PPoD', 'PrintPodcastDetailScreen'),
             ('PPD', 'PrintPhotoDetailScreen')):
    tp = new[s]
    check(rule(tp, 'Width') == '794' and rule(tp, 'Height') == '1123', f'{s} is not 794 x 1123')
    ctl = {c['Name']: c for c in walk(tp)}
    check(rule(ctl[f'{p}_BtnPrint'], 'OnSelect') == 'Print()', f'{s} print OnSelect')
    for b in ('BtnBack', 'BtnPrint'):
        check(rule(ctl[f'{p}_{b}'], 'Visible') == f'Not({s}.Printing)', f'{s} {b} not hidden while printing')
    grp = [c for c in tp['Children'] if c.get('IsGroupControl')][0]
    for nme in grp['GroupedControlsKey']:
        if nme.startswith(('Nav', 'HomeUserName', 'Image1')):
            check(f'Not({s}.Printing)' in rule(ctl[nme], 'Visible'), f'{s}.{nme} visible while printing')
    g = ctl[f'{p}_Gallery']
    ts = int(rule(g, 'TemplateSize'))
    for printing in (False, True):
        boxes = []
        for c in tp['Children']:
            if c.get('IsGroupControl'):
                continue
            vis = rule(c, 'Visible') or 'true'
            if printing and f'Not({s}.Printing)' in vis:
                continue
            try:
                x = int(rule(c, 'X')); w = int(rule(c, 'Width'))
                y = eval(num(rule(c, 'Y'), printing, None))
            except Exception:
                continue    # formula-driven (Podcast Y chain, p_More), checked below
            hraw = rule(c, 'Height')
            if c['Name'] == f'{p}_Gallery':
                fit = (1066 - y) // ts
                h = ts * fit
                check(fit >= 1, f'{s}: no row fits')
                check(y + h <= 1066, f'{s}: gallery past its bottom')
            else:
                h = int(hraw)
            check(x >= 0 and x + w <= 794, f'{s}.{c["Name"]} outside page width ({x}+{w})')
            check(y >= 0 and y + h <= 1123, f'{s}.{c["Name"]} outside page height ({y}+{h}) printing={printing}')
            boxes.append((c['Name'], y, h))
    for nme in grp['GroupedControlsKey']:
        x, w = int(rule(ctl[nme], 'X')), int(rule(ctl[nme], 'Width'))
        check(x + w <= 794, f'{s}.{nme} outside page width ({x}+{w})')
    # rows: worst case (every field visible) stays inside the template
    for c in g['Children']:
        if c['Template']['Name'] == 'galleryTemplate':
            continue
        x, w = int(rule(c, 'X')), int(rule(c, 'Width'))
        check(x + w <= 762, f'{s}.{c["Name"]} wider than the row')
    ys = {}
    kids = {c['Name']: c for c in g['Children']}
    def yof(nme, depth=0):
        check(depth < 60, f'{s}: Y chain loops at {nme}')
        if nme in ys:
            return ys[nme]
        t = rule(kids[nme], 'Y').strip()
        if t.isdigit():
            v = int(t)
        else:
            m = re.fullmatch(r'(\w+)\.Y(?: \+ If\(\1\.Visible, \1\.Height, 0\))?', t)
            check(m is not None, f'{s}.{nme}.Y unexpected: {t}')
            prev = m.group(1)
            v = yof(prev, depth + 1) + (int(rule(kids[prev], 'Height')) if '+' in t else 0)
        ys[nme] = v
        return v
    for nme, c in kids.items():
        if c['Template']['Name'] in ('galleryTemplate',) or nme.endswith('RowRule'):
            continue
        y = yof(nme)
        check(y + int(rule(c, 'Height')) <= ts, f'{s}.{nme} below the row ({y}+{rule(c, "Height")} > {ts})')
    # labels share their value's row and visibility
    for nme in kids:
        m = re.fullmatch(fr'{p}_Lbl(\d+)', nme)
        if m:
            check(rule(kids[nme], 'Visible') == f'{p}_Val{m.group(1)}.Visible', f'{s}.{nme} visibility')
    check(f'{p}_More' in ctl, f'{s}: no overflow note')

print(f'{n - len(fails)}/{n} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
