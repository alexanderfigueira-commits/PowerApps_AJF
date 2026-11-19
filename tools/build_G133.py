#!/usr/bin/env python3
"""FINAL144 on FINAL143: printing from the published app and from Studio need different print geometry.
 * Published player: Print() fits the whole 1366 px screen to the page width, so the compact 960 px layout (made for Studio prints, which come out enlarged by the window's scale) used only 70 % of the page.
 * Studio edit mode: the page gets the screen enlarged ~1.1x, so the layout has to be compact to fit.
Default now = full-size layout (what the published app needs). A checkbox "Compact (Studio)" on the three print screens (global varCompactPrint, shown on screen only) switches the compact geometry on for prints made from Studio.
Every compact value stays If(locPrinting And Coalesce(varCompactPrint, false), <compact>, <full>)."""
import datetime, os, re, shutil
from payaml import App
from hp_common import Builder
SRC, NEW = 'newV3', 'newV4'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
walk = lambda n: [n] + [x for c in n.get('Children', []) for x in walk(c)]
n = 0
for screen, P in (('PrintPhotoDetailScreen', 'PPD'), ('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD')):
    for c in walk(app.doc(screen)['TopParent'])[1:]:
        for r in c['Rules']:
            if r['Property'] in ('X', 'Width', 'Size') and r['InvariantScript'].startswith('If(locPrinting, '):
                t = r['InvariantScript']
                app.set(screen, c['Name'], r['Property'], 'If(locPrinting And Coalesce(varCompactPrint, false), ' + t[len('If(locPrinting, '):], expect=t); n += 1
    t = app.rule(screen, f'{P}_PrintHint', 'Text')
    app.set(screen, f'{P}_PrintHint', 'Text', '"Print dialog: A4 · Landscape · Margins: None · Background graphics: on"', expect=t)
app.save()
print('geometry rules switched to the compact checkbox:', n)

class NB(Builder):
    def grouped(self, tp): return set()
for screen, P in (('PrintPhotoDetailScreen', 'PPD'), ('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD')):
    b = NB(app, screen)
    b.clone(f'{P}_ChkCompact', 'ReviewScreen', 'RV_ArchiveOnly', {
        'Text': '"Compact (Studio)"', 'X': '644', 'Y': '76', 'Width': '138', 'Height': '28', 'Size': '10',
        'Default': 'Coalesce(varCompactPrint, false)',
        'DisplayMode': 'DisplayMode.Edit',
        'Visible': 'Not(locPrinting)',
        'OnCheck': 'Set(varCompactPrint, true)',
        'OnUncheck': 'Set(varCompactPrint, false)'})
    b.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL144 built')
