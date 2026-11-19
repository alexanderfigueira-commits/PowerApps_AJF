#!/usr/bin/env python3
"""FINAL138 on FINAL137: the footer (and the bottom of the page) reaches the paper.
The footer sat at Y=744 of the 768 px screen; the browser prints the screen at the window's app scale (~1.1), so only ~710 design px of height reach an A4 landscape page and the footer was cut off.
While printing, the part of the screen under the top bar is now scaled in height like it already is in width and font (x 0.703, pivot = bottom of the top bar): rows, header card, labels, gallery rows and footer move up
and shrink, the footer lands at Y~540. Still full size on screen (every changed Y / Height / TemplateSize is If(locPrinting, <print>, <as before>)). Rows per page do not change."""
import datetime, os, re, shutil
from payaml import App, find
SRC, NEW = 'newU4', 'newU5'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
F = 960 / 1366
PIVOT = 56
NUM = re.compile(r'^-?\d+(\.\d+)?$')
changed = 0
def setp(screen, name, prop, v, new):
    global changed
    if str(new) != v.strip():
        app.set(screen, name, prop, f'If(locPrinting, {new}, {v.strip()})', expect=v); changed += 1
for screen, P in (('PrintPhotoDetailScreen', 'PPD'), ('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD')):
    tp = app.doc(screen)['TopParent']
    skip = {f'{P}_BtnBack', f'{P}_BtnPrint', f'{P}_BtnPrevPage', f'{P}_BtnNextPage', f'{P}_PageLbl', f'{P}_PrintHint'}
    for c in tp['Children']:
        name, kind = c['Name'], c['Template']['Name']
        if name in skip or name.startswith((f'{P}_Header_', f'{P}_TopBar', f'{P}_Menu', f'{P}_RoleTag')) or kind in ('group', 'image'):
            continue
        rules = {r['Property']: r['InvariantScript'] for r in c['Rules']}
        y, h = rules.get('Y'), rules.get('Height')
        if kind == 'gallery':
            R = int(rules['TemplateSize']); Rp = round(R * F)
            yv = y.strip(); assert NUM.match(yv), (screen, yv)
            setp(screen, name, 'Y', yv, round(PIVOT + (float(yv) - PIVOT) * F))
            setp(screen, name, 'TemplateSize', rules['TemplateSize'], Rp)
            hh = rules['Height']
            assert f'{R} * Min(' in hh, (screen, hh)
            app.set(screen, name, 'Height', hh.replace(f'{R} * Min(', f'If(locPrinting, {Rp}, {R}) * Min(', 1), expect=hh); changed += 1
            for k in c['Children']:
                if k['Name'].endswith('template') or k['Name'].endswith('template1'):
                    continue
                kr = {r['Property']: r['InvariantScript'] for r in k['Rules']}
                ky, kh = kr.get('Y'), kr.get('Height')
                if ky is not None and NUM.match(ky.strip()):
                    setp(screen, k['Name'], 'Y', ky, round(float(ky) * F))
                if kh is not None and NUM.match(kh.strip()):
                    setp(screen, k['Name'], 'Height', kh, max(1, round(float(kh) * F)))
            continue
        if y is not None and NUM.match(y.strip()) and float(y) >= PIVOT:
            setp(screen, name, 'Y', y, round(PIVOT + (float(y) - PIVOT) * F))
        if h is not None and NUM.match(h.strip()):
            setp(screen, name, 'Height', h, max(1, round(float(h) * F)))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('rules changed:', changed)
print('FINAL138 built')
