#!/usr/bin/env python3
"""FINAL237 on FINAL236. Metadata tab: every date picker in size 13 - Production end date (CM_ProdEnd), Publication start date
(CM_PubStartV) and Publication end date (CM_PubEndV) 11 -> 13, like the Shooting / Filming / Recording date (FINAL236)."""
import datetime, json, glob, os, re, shutil
from payaml import App
SRC, NEW = 'newV98', 'newV99'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)


def walk(n):
    yield n
    for c in n.get('Children', []): yield from walk(c)


pickers = [n['Name'] for n in walk(app.doc('ChildMetaScreen')['TopParent']) if n['Template']['Name'] == 'modernDatePicker']
assert sorted(pickers) == ['CM_ProdEnd', 'CM_PubEndV', 'CM_PubStartV', 'CM_ShootDate'], pickers
for c in pickers:
    t = app.rule('ChildMetaScreen', c, 'Size')
    if t.strip() != '13': app.set('ChildMetaScreen', c, 'Size', '13', expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL237 built')
