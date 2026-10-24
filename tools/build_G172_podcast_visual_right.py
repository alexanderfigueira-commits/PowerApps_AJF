#!/usr/bin/env python3
"""FINAL183 on TEST_17 (= FINAL182 + the user's layout edits, all kept). Podcast only: the 'Podcast visual' block (label, hint, upload button, view button) moves from the
bottom of the Info tab to the free column on the right, under 'Copy from previous Podcast', aligned with that button (X 1011, width 300). Nothing else is touched."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newT17', 'newV45'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
I = 'ChildInfoScreen'
NEWGEO = {   # control: (X, Y, Width, Height), in the media form's coordinates (the gallery CI_Gallery that scrolls)
    'CI_LblPodcastVisual':  (1011, 119, 300, 22),    # level with 'Title of the podcast *'
    'CI_HintPodcastVisual': (1011, 143, 300, 48),    # three lines of the 11 pt hint
    'CI_BtnOpenAttach':     (1011, 198, 300, 64),    # the text of this button is long: two or three lines
    'CI_BtnViewVisual':     (1011, 274, 300, 48),
}
OLD = {'CI_LblPodcastVisual': (51, 634, 800, 22), 'CI_HintPodcastVisual': (51, 655, 900, 20), 'CI_BtnOpenAttach': (51, 677, 900, 48), 'CI_BtnViewVisual': (976, 678, 300, 48)}
for ctl, geo in NEWGEO.items():
    for prop, new, old in zip(('X', 'Y', 'Width', 'Height'), geo, OLD[ctl]):
        t = app.rule(I, ctl, prop)
        assert t.strip() == str(old), (ctl, prop, t)
        app.set(I, ctl, prop, str(new), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL183 built')
