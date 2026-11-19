#!/usr/bin/env python3
"""FINAL236 on FINAL235. Metadata tab: the Shooting date picker (CM_ShootDate; Filming / Recording date for Video / Podcast)
shows its date in size 13 (was 11), the size of its label."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV97', 'newV98'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
t = app.rule('ChildMetaScreen', 'CM_ShootDate', 'Size'); assert t.strip() == '11', t
app.set('ChildMetaScreen', 'CM_ShootDate', 'Size', '13', expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL236 built')
