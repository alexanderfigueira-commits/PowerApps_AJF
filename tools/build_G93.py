#!/usr/bin/env python3
"""FINAL103 on FINAL102: Message Center: NT_ReadReceipt sits right under Title1, whatever its (auto) height."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newJ3', 'newJ4'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
app.set('RequesDetailScreen', 'NT_ReadReceipt', 'Y', 'Title1.Y + Title1.Height + 3', expect='92')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL103 built')
