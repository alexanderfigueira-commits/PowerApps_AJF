#!/usr/bin/env python3
"""FINAL200 on FINAL199. PDF(): the orientation enum is PaperOrientation (PageOrientation does not exist; Studio reported 5 errors per print sheet)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = os.environ.get('SRC', 'newV61'), os.environ.get('NEW', 'newV62')
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
for scr, p in (('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD'), ('PrintPhotoDetailScreen', 'PPD')):
    t = app.rule(scr, f'{p}_PdfTimer', 'OnTimerEnd')
    assert t.count('Orientation: PageOrientation.Landscape') == 1
    app.set(scr, f'{p}_PdfTimer', 'OnTimerEnd', t.replace('Orientation: PageOrientation.Landscape', 'Orientation: PaperOrientation.Landscape'), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL200 built')
