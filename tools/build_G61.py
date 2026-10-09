#!/usr/bin/env python3
"""FINAL71 on FINAL70: RS_Trk3 tooltip says so when the request is Partially approved."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG60', 'newG61'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
o = app.rule(S, 'RS_Trk3', 'Tooltip')
old = '"Partially approved", "Approved: the request was approved by Central Deposit."'
assert old in o
app.set(S, 'RS_Trk3', 'Tooltip', o.replace(old, '"Partially approved", "Partially approved: only part of the request was approved by Central Deposit."'), expect=o)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL71 built')
