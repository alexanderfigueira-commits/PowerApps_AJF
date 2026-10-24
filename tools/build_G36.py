#!/usr/bin/env python3
"""FINAL46 on FINAL45: the two "+" buttons that open the Contact Extra pop-up (RS_DetailsToggle_contrator_1 for the DG/Agency contact,
RS_DetailsToggle_contrator for the contractor) are hidden in view mode (varRequestorLocked: a request opened from a dashboard ID, or locked
for a requestor while Processing). They were already disabled there; now they are not shown at all.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG35', 'newG36'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
for c in ('RS_DetailsToggle_contrator_1', 'RS_DetailsToggle_contrator'):
    app.set('RequesDetailScreen', c, 'Visible', 'Not(locDetailsCollapsed) And Not(varRequestorLocked)', expect='Not(locDetailsCollapsed)')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL46 built')
