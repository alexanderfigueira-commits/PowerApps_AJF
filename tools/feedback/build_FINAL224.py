#!/usr/bin/env python3
"""FINAL224 on FINAL223. The 12 modern date pickers are drawn opaque like the other fields: white (light grey in reading mode,
as every other field), black text, and the border (yellow while a mandatory date is empty) that their dd-mm-yyyy label carried.
The labels under the pickers (FINAL217) are hidden: a transparent modern picker is not reliable, and an opaque one covers them.
The picker shows the date in its own short format (from the user's language settings)."""
import datetime, json, os, re, shutil, glob
from payaml import App
SRC, NEW = 'newV85', 'newV86'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))


def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)


def walk(n):
    yield n
    for c in n.get('Children', []): yield from walk(c)


done = []
for f in sorted(glob.glob(f'{NEW}/Controls/*.json')):
    top = json.load(open(f, encoding='utf-8'))['TopParent']
    for n in walk(top):
        if n['Template']['Name'] != 'modernDatePicker': continue
        scr, p, l = top['Name'], n['Name'], n['Name'] + '_Txt'
        lab_fill = app.rule(scr, l, 'Fill'); lab_bc = app.rule(scr, l, 'BorderColor'); lab_bt = app.rule(scr, l, 'BorderThickness')
        assert 'Self.' not in lab_fill + lab_bc + lab_bt, (scr, l)
        setp(scr, p, 'Fill', lab_fill)
        setp(scr, p, 'Color', 'RGBA(0, 0, 0, 1)')
        setp(scr, p, 'BorderColor', lab_bc)
        setp(scr, p, 'BorderThickness', lab_bt)
        setp(scr, p, 'Placeholder', '"Select a date"')
        setp(scr, l, 'Visible', '// FINAL224: the opaque date picker above shows the date itself\nfalse')
        done.append(f'{scr}.{p}')
assert len(done) == 12, done
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL224 built:', ', '.join(done))
