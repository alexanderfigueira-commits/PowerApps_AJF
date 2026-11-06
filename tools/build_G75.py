#!/usr/bin/env python3
"""FINAL85 on FINAL84: reading mode is visible. On the request, Info, Metadata and Legal screens every text input, dropdown, combobox and date
picker that follows varRequestorLocked gets a very light grey fill (RGBA 244, 245, 248) while locked, and its yellow 'mandatory and empty' border
is replaced by the normal blue one. Editable fields are unchanged. The Rights & declarations checkboxes get the same grey behind their row."""
import datetime, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG74', 'newG75'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
GREY, BLUE = 'RGBA(244, 245, 248, 1)', 'RGBA(0, 18, 107, 1)'
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
tot = {'fill': 0, 'color': 0, 'thick': 0, 'check': 0}
for s in ('RequesDetailScreen', 'ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen'):
    for c in list(walk(app.doc(s)['TopParent'])):
        r = {x['Property']: x['InvariantScript'] for x in c['Rules']}
        if c['Template']['Name'] == 'checkbox':          # Rights & declarations: grey row while locked
            if 'varRequestorLocked' in (r.get('DisplayMode') or '') and r.get('Fill') == 'RGBA(0, 0, 0, 0)':
                app.set(s, c['Name'], 'Fill', f'If(varRequestorLocked, {GREY}, RGBA(0, 0, 0, 0))'); tot['check'] += 1
            continue
        if c['Template']['Name'] not in ('text', 'dropdown', 'combobox', 'datepicker'): continue
        if 'varRequestorLocked' not in (r.get('DisplayMode') or ''): continue
        n = c['Name']
        if r.get('Fill') == 'RGBA(255, 255, 255, 1)':
            app.set(s, n, 'Fill', f'If(varRequestorLocked, {GREY}, RGBA(255, 255, 255, 1))'); tot['fill'] += 1
        bc = r.get('BorderColor') or ''
        if '255, 204, 0' in bc:
            app.set(s, n, 'BorderColor', f'If(varRequestorLocked, {BLUE},\n{bc}\n)'); tot['color'] += 1
            bt = r.get('BorderThickness') or ''
            if bt and bt != '2' and 'varRequestorLocked' not in bt:
                app.set(s, n, 'BorderThickness', f'If(varRequestorLocked, 2, {bt})'); tot['thick'] += 1
print(tot)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL85 built')
