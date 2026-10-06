#!/usr/bin/env python3
"""Checks for FINAL15 against FINAL14: only RS_CRowBadge changed - it links to the AV portal for approved media."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL15-badge-colours.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL14-beluga-link.msapp'
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, ref = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('References/'):
            ref[f] = z.read(i)
    return js, ref


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
new, nref = load(PKG); old, oref = load(BASE)
check(nref == oref, 'data sources changed')
check(all(json.dumps(new[s], sort_keys=True) == json.dumps(old[s], sort_keys=True) for s in new if s != 'RequesDetailScreen'), 'another screen changed')
N = {c['Name']: c for c in walk(new['RequesDetailScreen'])}; O = {c['Name']: c for c in walk(old['RequesDetailScreen'])}
check(set(N) == set(O), 'controls added or removed')
ch = {n: sorted(p for p in set(rd(c)) | set(rd(O[n])) if rd(c).get(p) != rd(O[n]).get(p)) for n, c in N.items()}
check({k: v for k, v in ch.items() if v} == {'RS_CRowBadge': ['Color', 'DisplayMode', 'Fill', 'HoverFill', 'OnSelect', 'Text', 'Tooltip']}, 'only RS_CRowBadge changed')
r = rd(N['RS_CRowBadge'])
for p in ('Color', 'DisplayMode', 'Fill', 'HoverFill', 'OnSelect', 'Text', 'Tooltip'):
    v = re.sub(r'(?m)^\s*//[^\n]*', '', r[p]); v = re.sub(r'"[^"\n]*"', '""', v)
    check(v.count('(') == v.count(')') and v.count('{') == v.count('}'), f'{p}: brackets')
    check('mode: If(' in r[p] and 'Coalesce(varRequestArchivedOnly, false)' in r[p] and 'ThisItem.BelugaReference' in r[p] and 'Coalesce(ThisItem.MediaApproved, false)' in r[p], f'{p}: same three-way rule')
check('RGBA(236, 238, 242, 1)' in r['Fill'] and 'RGBA(96, 104, 116, 1)' in r['Fill'] and 'RGBA(22, 128, 80, 1)' in r['Fill'], 'light grey / dark grey / green')
check('"archive", RGBA(96' in r['Fill'] and '"link", RGBA(22' in r['Fill'], 'dark grey = archive, green = link')
check('If(mode = "link", Launch(url))' in r['OnSelect'] and 'If(mode = "link", DisplayMode.Edit, DisplayMode.View)' in r['DisplayMode'], 'only the green badge is clickable')
check('"none", "No Beluga ID"' in r['Text'] and '"archive", "Archive' in r['Text'] and '"link", "' in r['Text'], 'texts')
check('"Podcast", "podcast"' in r['Text'] and '"Video", "video"' in r['Text'] and '"Photo", "photo"' in r['Text'] and 'https://audiovisual.ec.europa.eu/en/media/' in r['OnSelect'], 'portal paths')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
