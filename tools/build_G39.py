#!/usr/bin/env python3
"""FINAL49 on FINAL48: Dashboard-Ope-Administrator navigation: all five buttons inside DOA_Menu_Panel for an administrator.

Before: panel X 769 / width 341 (769-1110) with Review 798, Requests 868, Export 951, Help 1030, but Dashboard at X 579, outside the panel,
and Review only 70 wide. Now the same layout as the other screens: for an ADMINISTRATOR the panel is 686-1110 and holds Dashboard 705,
Requests 797, Review 875 (83 wide), Export 951, Help 1030, so every button, Review included, sits inside it. For anyone else the Review slot
is closed as on the other screens (panel 762, width 348; Dashboard 781, Requests 873).
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG38', 'newG39'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'Dashboard-Ope-Administrator'
A = 'varUserRole = "ADMINISTRATOR"'
chk = {('DOA_Menu_Panel', 'X'): f'If({A},769,820)', ('DOA_Menu_Panel', 'Width'): f'If({A},341,300)', ('DOA_Menu_Dashboard', 'X'): '579',
       ('DOA_Menu_Requests', 'X'): '868', ('DOA_Menu_Review', 'X'): '798', ('DOA_Menu_Review', 'Width'): '70'}
for (c, p), v in chk.items():
    if app.rule(S, c, p).replace(' ', '') != v.replace(' ', ''):
        sys.exit(f'! {c}.{p} is {app.rule(S, c, p)!r}, expected {v!r}')
app.set(S, 'DOA_Menu_Panel', 'X', f'If({A}, 686, 762)', expect=chk[('DOA_Menu_Panel', 'X')])
app.set(S, 'DOA_Menu_Panel', 'Width', f'If({A}, 424, 348)', expect=chk[('DOA_Menu_Panel', 'Width')])
app.set(S, 'DOA_Menu_Dashboard', 'X', f'If({A}, 705, 781)', expect='579')
app.set(S, 'DOA_Menu_Requests', 'X', f'If({A}, 797, 873)', expect='868')
app.set(S, 'DOA_Menu_Review', 'X', '875', expect='798')
app.set(S, 'DOA_Menu_Review', 'Width', '83', expect='70')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL49 built')
