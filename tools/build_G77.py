#!/usr/bin/env python3
"""FINAL87 on FINAL86: CI_TplGallery (template picker on ChildInfoScreen) lists only the user's own media files for a requestor; administrators see everyone's."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG76', 'newG77'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'ChildInfoScreen'
t = app.rule(S, 'CI_TplGallery', 'Items')
a = '        varChildMediaType in MediaType.Value,\n'
n = t.replace('\r\n', '\n'); assert n.count(a) == 1
n = n.replace(a, a + '        // a requestor sees only the media files they created; an administrator sees all\n        varUserRole = "ADMINISTRATOR" Or Lower(\'Created By\'.Email) = Lower(User().Email),\n')
app.set(S, 'CI_TplGallery', 'Items', n.replace('\n', '\r\n') if '\r\n' in t else n, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL87 built')
