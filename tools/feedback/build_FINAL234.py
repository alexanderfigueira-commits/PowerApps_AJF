#!/usr/bin/env python3
"""FINAL234 on FINAL233.
1. PDF page header: the brand block is two thirds of its size (450 x 50 -> 300 x 34; logo 124 x 32, badge 20, "Central Deposit"
   10 pt, "Ticket System" 7 pt); the header lines and the first media file move up again by 16 px (shift 36 instead of 52).
2. Print sheets: the shade behind "Preparing the preview" / the save message is much darker (opacity 0.20 -> 0.65), so the page
   being prepared underneath no longer shows through."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV95', 'newV96'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))


def setp(scr, ctl, prop, val, old=None):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if old is not None: assert t.strip() == old, (scr, ctl, prop, t)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)


def rep(scr, ctl, prop, old, new, count=1):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    assert t.count(old) == count, (scr, ctl, prop, t.count(old), old[:80])
    app.set(scr, ctl, prop, t.replace(old, new), expect=t)


BW, BH, SHIFT = 300, 34, 36
L = f'(Parent.TemplateWidth - {BW}) / 2'
for scr, p in (('PrintPhotoDetailScreen', 'PPD'), ('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD')):
    setp(scr, f'{p}_PdfBrandBg', 'X', L); setp(scr, f'{p}_PdfBrandBg', 'Width', str(BW)); setp(scr, f'{p}_PdfBrandBg', 'Height', str(BH))
    for c, x, y, w, h in ((f'{p}_PdfBrandLogoEC', 3, 1, 124, 32), (f'{p}_PdfBrandLogoCD', 139, 7, 20, 20),
                          (f'{p}_PdfBrandTitle', 161, 0, 136, 22), (f'{p}_PdfBrandSub', 176, 16, 118, 16)):
        setp(scr, c, 'X', f'{L} + {x}'); setp(scr, c, 'Y', str(y)); setp(scr, c, 'Width', str(w)); setp(scr, c, 'Height', str(h))
    setp(scr, f'{p}_PdfBrandLogoEC', 'PaddingLeft', '7', '10')
    setp(scr, f'{p}_PdfBrandTitle', 'Size', '10', '14')
    setp(scr, f'{p}_PdfBrandTitle', 'PaddingLeft', '3')
    setp(scr, f'{p}_PdfBrandSub', 'Size', '7', '10')
    setp(scr, f'{p}_PdfBrandSub', 'PaddingLeft', '3')
    setp(scr, f'{p}_PgHdrBg', 'Y', str(SHIFT), '52')
    setp(scr, f'{p}_PgHdrTitle', 'Y', str(2 + SHIFT), '54')
    setp(scr, f'{p}_PgHdrInfo', 'Y', str(29 + SHIFT), '81')
    rep(scr, f'{p}_RowCaption', 'Y', 'Mod(ThisItem.PdfRowNo, 2) = 1), 108, 0)', f'Mod(ThisItem.PdfRowNo, 2) = 1), {56 + SHIFT}, 0)')
    setp(scr, f'{p}_LoadShade', 'Fill', 'RGBA(0, 18, 107, 0.65)', 'RGBA(0, 18, 107, 0.20)')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL234 built')
