#!/usr/bin/env python3
"""FINAL218 on FINAL217. Media list of the request: the APPROVED box can only be ticked when the media file is "Ready"
(same rule as the VALIDATION column); an incomplete media file shows the box empty and disabled, with a tooltip."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV79', 'newV80'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
RS = 'RequesDetailScreen'
def setp(ctl, prop, val):
    t = app.rule(RS, ctl, prop); assert t is not None, (ctl, prop)
    if t.strip() != val.strip(): app.set(RS, ctl, prop, val, expect=t)
v = app.rule(RS, 'RS_CRowValid', 'Text')
m = re.match(r'\s*If\(\s*(.*?),\s*"✓  Ready"', v, re.S); assert m, v[:200]
READY = '(' + ' '.join(m.group(1).split()) + ')'
setp('RS_CRowApproved', 'Default', f'// ticked only when the media file is complete (VALIDATION = Ready)\nCoalesce(ThisItem.MediaApproved, false) And {READY}')
setp('RS_CRowApproved', 'DisplayMode', (
    '// administrators approve per media file, and only a complete one; everyone else sees the state\n'
    'If(\n    varViewOnly,\n    DisplayMode.View,\n'
    '    varUserRole = "ADMINISTRATOR" And Coalesce(ThisItem.SPId, 0) > 0,\n'
    f'    If({READY}, DisplayMode.Edit, DisplayMode.Disabled),\n    DisplayMode.View\n)'))
setp('RS_CRowApproved', 'Tooltip', f'If({READY}, "", "Complete the media file before approving it (VALIDATION must be Ready)")')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('READY =', READY); print('FINAL218 built')
