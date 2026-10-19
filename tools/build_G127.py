#!/usr/bin/env python3
"""FINAL137 on FINAL134 (like FINAL136, narrower): the print preview of FINAL136 still lost the right-hand columns. The browser prints the screen at the scale the app has in the window (about 1.1 here), so only the first
~990 design px of a line reach the page. The compact print geometry is now 960 px wide (FINAL136: 1090). Still full size on screen: every X / Width / font Size of what is printed is If(locPrinting, ...).
FINAL135 shrank the layout for good: on screen the text was tiny, the header logos overlapped and a grey band took the right of the screen. Now every X / Width / font Size of what is printed is
If(locPrinting, <fits 1090 px>, <as before>): locPrinting is already true while Print() runs (it hides the menus and buttons). Header: the top bar is 1090 wide while printing, the user name and the photo
move left of the page edge, logos and titles do not move."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newU1', 'newU4'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
PAGE_W = 960
F = PAGE_W / 1366
NUM = re.compile(r'^-?\d+(\.\d+)?$')
walk = lambda n: [n] + [x for c in n.get('Children', []) for x in walk(c)]
changed = 0
for screen, P in (('PrintPhotoDetailScreen', 'PPD'), ('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD')):
    tp = app.doc(screen)['TopParent']
    hidden_when_printing = {f'{P}_BtnBack', f'{P}_BtnPrint', f'{P}_BtnPrevPage', f'{P}_BtnNextPage', f'{P}_PageLbl'}
    special = {f'{P}_TopBar': {'Width': (PAGE_W, 1366)}, f'{P}_Header_Photo': {'X': (PAGE_W - 61, 1305)}, f'{P}_Header_UserName': {'X': (PAGE_W - 61 - 216, 1089)}}
    for c in walk(tp)[1:]:
        name, kind = c['Name'], c['Template']['Name']
        if kind == 'galleryTemplate' or name.endswith('template') or name.endswith('template1') or name in hidden_when_printing:
            continue
        rules = {r['Property']: r['InvariantScript'] for r in c['Rules']}
        w = rules.get('Width')
        if w is not None and NUM.match(w.strip()) and float(w) <= 5:
            continue                                                         # the groups
        header = name.startswith((f'{P}_Header_', f'{P}_TopBar', f'{P}_Menu', f'{P}_RoleTag'))
        for prop in ('X', 'Width', 'Size'):
            v = rules.get(prop)
            if v is None or not NUM.match(v.strip()):
                continue
            orig = float(v)
            if name in special and prop in special[name]:
                new_print, new_screen = special[name][prop]
            elif header:
                continue
            elif prop == 'Width' and kind == 'image':
                continue
            else:
                new_screen = int(orig) if orig == int(orig) else orig
                new_print = max(7, round(orig * F)) if prop == 'Size' else round(orig * F)
                if prop == 'Size' and orig >= 18: new_print = max(new_print, 14)
            if new_print != new_screen:
                app.set(screen, name, prop, f'If(locPrinting, {new_print}, {new_screen})', expect=v); changed += 1
app.save()
from hp_common import Builder
class NB(Builder):
    def grouped(self, tp): return set()
for screen, P in (('PrintPhotoDetailScreen', 'PPD'), ('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD')):
    b = NB(app, screen)
    b.clone(f'{P}_PrintHint', screen, f'{P}_Footer', {
        'Text': '"Print dialog: A4 · Landscape · Margins: None · Scale: Fit to page"', 'X': '1012', 'Y': '70', 'Width': '186', 'Height': '36',
        'Size': '9', 'Visible': 'Not(locPrinting)'})
    b.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('rules changed:', changed)
print('FINAL137 built')
