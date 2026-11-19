#!/usr/bin/env python3
"""FINAL235 on FINAL234.
1. Print sheets: while the preview (or the save) is being prepared the shade is solid (opacity 0.65 -> 1), so the pages laid out
   for the PDF, with their header, are not seen on the screen: the header is only seen in the PDF preview. The shade is outside
   the gallery that PDF() prints, so the PDF is unchanged.
2. PDF page header a bit higher and tighter under the brand block: header band 36 -> 34 (52 -> 50 high), request title 38 -> 35,
   created by / DG / dates 65 -> 60; the first media file of the page 92 -> 86."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV96', 'newV97'
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


for scr, p in (('PrintPhotoDetailScreen', 'PPD'), ('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD')):
    setp(scr, f'{p}_LoadShade', 'Fill', 'RGBA(0, 18, 107, 1)', 'RGBA(0, 18, 107, 0.65)')
    setp(scr, f'{p}_PgHdrBg', 'Y', '34', '36')
    setp(scr, f'{p}_PgHdrBg', 'Height', '50', '52')
    setp(scr, f'{p}_PgHdrTitle', 'Y', '35', '38')
    setp(scr, f'{p}_PgHdrInfo', 'Y', '60', '65')
    rep(scr, f'{p}_RowCaption', 'Y', 'Mod(ThisItem.PdfRowNo, 2) = 1), 92, 0)', 'Mod(ThisItem.PdfRowNo, 2) = 1), 86, 0)')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL235 built')
