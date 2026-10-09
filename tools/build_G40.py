#!/usr/bin/env python3
"""FINAL50 on FINAL49: the same spacing between ALL navigation buttons, on every screen.

Before: Dashboard -> Requests had a 9 px gap, but Requests / Review / Export / Help overlapped by 4-7 px. Now the five 83 px buttons sit at a
92 px pitch (the Dashboard -> Requests rhythm): 
  administrator : panel 621-1110 (X 621, width 489); Dashboard 640, Requests 732, Review 824, Export 916, Help 1008
  everyone else : the Review slot is closed; panel 713-1110 (X 713, width 397); Dashboard 732, Requests 824, Export 916, Help 1008
The right edge of the panel (1110) is unchanged; the extra width is taken on the left, where the role tag ends at X 602.
Applied to all 15 screens (the 12 screens of FINAL43, ReviewScreen, and the two operational dashboards; the Requestor dashboard's menu copy
also gets the Dashboard button inside its panel, Review 83 wide).
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG39', 'newG40'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
A = 'varUserRole = "ADMINISTRATOR"'
GEOM = {  # item -> (property -> value)
    'Panel': {'X': f'If({A}, 621, 713)', 'Width': f'If({A}, 489, 397)'},
    'Dashboard': {'X': f'If({A}, 640, 732)'},
    'Requests': {'X': f'If({A}, 732, 824)'},
    'Review': {'X': '824', 'Width': '83'},
    'Export': {'X': '916'},
    'Help': {'X': '1008'},
}
screens = 0
for s in list(app.map):
    if s == 'App':
        continue
    names = []
    def collect(c):
        names.append(c['Name'])
        for k in c.get('Children', []):
            collect(k)
    collect(app.doc(s)['TopParent'])
    found = {}
    for n in names:
        m = re.match(r'^(\w+?)_Menu_(Panel|Dashboard|Requests|Review|Export|Help)(_1)?$', n)
        if m:
            found[m.group(2)] = n
    if not found:
        continue
    if set(found) != set(GEOM):
        sys.exit(f'! {s}: menu items {sorted(found)}')
    for item, props in GEOM.items():
        for p, v in props.items():
            old = app.rule(s, found[item], p)
            app.set(s, found[item], p, v, expect=old)
    screens += 1
print('menus adjusted on', screens, 'screens')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL50 built')
