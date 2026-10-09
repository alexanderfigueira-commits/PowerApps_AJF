#!/usr/bin/env python3
"""FINAL78 on FINAL77: every text on HomePrintScreen is at least size 11 (the nav buttons, the header subtitle and the footer were 10)."""
import datetime, json, os, re, shutil
from payaml import App
SRC, NEW = 'newG67out', 'newG68'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'HomePrintScreen'
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
n = 0
for c in list(walk(app.doc(S)['TopParent'])):
    r = {x['Property']: x['InvariantScript'] for x in c['Rules']}
    if c['Template']['Name'] in ('label', 'button', 'text', 'dropdown', 'combobox', 'datepicker') and r.get('Size', '').isdigit() and int(r['Size']) < 11:
        app.set(S, c['Name'], 'Size', '11'); n += 1
print('texts raised to 11:', n)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL78 built')
