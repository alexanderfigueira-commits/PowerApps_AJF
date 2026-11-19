#!/usr/bin/env python3
"""FINAL105 on FINAL104: the REF badge of each media row (RS_ChildrenGallery) has the tooltip 'Open Media File'."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newJ5', 'newJ6'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
app.set('RequesDetailScreen', 'DOA_List1RowBadge_8', 'Tooltip', '"Open Media File"', expect='')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL105 built')
