#!/usr/bin/env python3
"""FINAL135 on FINAL134: the print screens fit an A4 landscape page.
The print came out cut on the right: Print() puts the screen on the page at 100 %, an A4 landscape page is 1123 px wide (at 96 dpi) and the screens are 1366 px wide, so the last 240 px of every
line (Submitted, Place, Links, Legal & Documents ...) were lost. Photo, Video and Podcast print screens are now laid out in 1090 px: every X and Width x 0.798, font sizes x 0.798 (rows, header,
footer), images keep their proportions. Heights and row heights are unchanged, so rows per page and the paging stay. A grey band shows, on screen only, what lies outside the printed page."""
import datetime, os, re, shutil
from payaml import App, find
from hp_common import Builder
SRC, NEW = 'newU1', 'newU2'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
PAGE_W = 1090
F = PAGE_W / 1366
NUM = re.compile(r'^-?\d+(\.\d+)?$')
LIT = re.compile(r'(?<![\w."\'])(\d+)(?![\w"\'])')
walk = lambda n: [n] + [x for c in n.get('Children', []) for x in walk(c)]
warn = []
for screen in ('PrintPhotoDetailScreen', 'PrintVideoDetailScreen', 'PrintPodcastDetailScreen'):
    tp = app.doc(screen)['TopParent']
    for c in walk(tp)[1:]:
        kind = c['Template']['Name']
        if kind in ('galleryTemplate',) or c['Name'].endswith('template') or c['Name'].endswith('template1'):
            continue
        rules = {r['Property']: r['InvariantScript'] for r in c['Rules']}
        w = rules.get('Width')
        if w is not None and NUM.match(w.strip()) and float(w) <= 5:
            continue                                         # the groups
        for prop in ('X', 'Width', 'Size'):
            v = rules.get(prop)
            if v is None or not v.strip():
                continue
            if prop == 'Width' and kind == 'image':
                continue                                     # a logo keeps its proportions
            if prop == 'Size' and not NUM.match(v.strip()):
                continue
            if NUM.match(v.strip()):
                x = float(v)
                new = max(7, round(x * F)) if prop == 'Size' else round(x * F)
                if prop == 'Size' and x >= 18: new = max(new, 14)
            elif prop in ('X', 'Width') and not re.search(r'[A-Za-z_]+\.(X|Y|Width|Height)', v):
                new = LIT.sub(lambda m: str(round(int(m.group(1)) * F)), v)
            else:
                warn.append((screen, c['Name'], prop, v[:60])); continue
            if str(new) != v.strip():
                app.set(screen, c['Name'], prop, str(new), expect=v)
        # the right-hand photo of the header sits at the right edge of the (now narrower) top bar
        if kind == 'image' and rules.get('X') and NUM.match(rules['X'].strip()) and float(rules['X']) > 1200:
            app.set(screen, c['Name'], 'X', str(PAGE_W - int(rules['Width'])))
app.save()
print('left as they were (formulas that refer to other controls):', warn)

class NB(Builder):
    def grouped(self, tp): return set()
for screen, P in (('PrintPhotoDetailScreen', 'PPD'), ('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD')):
    b = NB(app, screen)
    b.clone(f'{P}_PageEdge', screen, f'{P}_HeaderCard', {
        'X': str(PAGE_W), 'Y': '0', 'Width': str(1366 - PAGE_W), 'Height': '768',
        'Fill': 'RGBA(228, 231, 237, 1)', 'Visible': 'Not(locPrinting)'})
    b.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL135 built')
