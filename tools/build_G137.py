#!/usr/bin/env python3
"""FINAL148 on FINAL147: ChildLegalScreen, whole "Rights & declarations" section at size 11
(its heading, the six rights checkboxes with their sub-checkboxes, and the VTT line)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV7', 'newV8'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'ChildLegalScreen'
for c in ('CL_LblRights', 'CL_ChkNoThirdParty', 'CL_ChkModel', 'CL_ChkModelProvided', 'CL_ChkMusic', 'CL_ChkMusicProvided',
          'CL_ChkPreexisting', 'CL_ChkPreexistingProvided', 'CL_ChkSubtitles', 'CL_LblVTT'):
    t = app.rule(S, c, 'Size'); assert t in ('11', '13', '14'), (c, t)
    if t != '11': app.set(S, c, 'Size', '11', expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL148 built')
