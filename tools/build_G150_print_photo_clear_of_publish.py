#!/usr/bin/env python3
"""FINAL161 on FINAL160: in a Studio print the Studio's own "Publish" pill lands on the right end of the page, over the header photo of the
compact layout (photo X 899..960). In compact mode only, the header photo and the user name move 90 px to the left (photo 809..870, user name
593..809), clear of the pill. The full-size layout (published app) is untouched."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV22', 'newV23'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
PRE = 'If(locPrinting And Coalesce(varCompactPrint, false), '
for screen, P in (('PrintVideoDetailScreen', 'PVD'), ('PrintPhotoDetailScreen', 'PPD'), ('PrintPodcastDetailScreen', 'PPoD')):
    for ctl, old, new in ((f'{P}_Header_Photo', 899, 809), (f'{P}_Header_UserName', 683, 593)):
        t = app.rule(screen, ctl, 'X')
        assert t == f'{PRE}{old}, {1305 if "Photo" in ctl else 1089})', (ctl, t)
        app.set(screen, ctl, 'X', t.replace(f', {old},', f', {new},'), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL161 built')
