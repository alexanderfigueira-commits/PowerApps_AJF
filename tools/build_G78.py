#!/usr/bin/env python3
"""FINAL88 on FINAL87: CI_TplSearch also searches by Beluga ID: new hint, and CI_TplGallery matches the text against BelugaReference."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG77', 'newG78'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'ChildInfoScreen'
app.set(S, 'CI_TplSearch', 'HintText', '"Search by title, media ID or Beluga ID..."', expect='"Search by title or media ID..."')
t = app.rule(S, 'CI_TplGallery', 'Items'); n = t.replace('\r\n', '\n')
a = '            Or varTplSearch in ProductionTitle\n'
assert n.count(a) == 1
app.set(S, 'CI_TplGallery', 'Items', n.replace(a, a + '            Or varTplSearch in BelugaReference\n').replace('\n', '\r\n') if '\r\n' in t else n.replace(a, a + '            Or varTplSearch in BelugaReference\n'), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL88 built')
