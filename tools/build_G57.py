#!/usr/bin/env python3
"""FINAL67 on FINAL66: PPD_BtnPrint hides every control of the PPD_Menu group (panel + the five buttons; a group has no YAML block of its own, so each member carries the rule) while printing (locPrinting), so the menu is not on
the printout. The app is already landscape 1366 x 768 with scale-to-fit, and the page content (gallery rows, '+ n more' note, footer at 744)
stays inside the 768 px screen, i.e. one landscape page."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG56', 'newG57'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'PrintPhotoDetailScreen'
for n in ('Panel', 'Requests', 'Export', 'Dashboard', 'Help'):
    c = f'PPD_Menu_{n}'; app.set(S, c, 'Visible', 'Not(locPrinting)', expect=app.rule(S, c, 'Visible'))
c = 'PPD_Menu_Review'; app.set(S, c, 'Visible', 'varUserRole = "ADMINISTRATOR" And Not(locPrinting)', expect=app.rule(S, c, 'Visible'))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL67 built')
