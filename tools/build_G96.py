#!/usr/bin/env python3
"""FINAL106 on FINAL105: the 'Media item removed.' message names the media item (its ID, as shown in the REF column)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newJ6', 'newJ7'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, C = 'RequesDetailScreen', 'RS_DelYes'
t = app.rule(S, C, 'OnSelect'); eol = '\r\n' if '\r\n' in t else '\n'; n = t.replace('\r\n', '\n')
old = 'Notify("Media item removed.", NotificationType.Success)'
assert n.count(old) == 1
new = 'Notify("Media item " & Coalesce(locDelItem.Title, locDelItem.ProductionTitle, "") & " removed.", NotificationType.Success)'
app.set(S, C, 'OnSelect', n.replace(old, new).replace('\n', eol), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL106 built')
