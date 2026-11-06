#!/usr/bin/env python3
"""FINAL31 on FINAL30: the attachments control CL_DCAttachValue (Legal & Docs) has a yellow border whenever it holds no file.

Yellow while the panel is empty (not for a requestor whose request is locked, who cannot add files) and, as before, while a mandatory
VTT file is missing; red on a form error. Nothing else changes.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG20', 'newG21'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, C = 'ChildLegalScreen', 'CL_DCAttachValue'
VTT = 'CL_LblVTT.Visible And CountRows(Filter(CL_DCAttachValue.Attachments, EndsWith(Lower(Name), ".vtt"))) = 0'
EMPTY = 'CountRows(CL_DCAttachValue.Attachments) = 0 And Not(varRequestorLocked)'
bc, bt = app.rule(S, C, 'BorderColor'), app.rule(S, C, 'BorderThickness')
if f'RGBA(255, 204, 0, 1), Parent.BorderColor)' not in bc or bt != f'If({VTT}, 3, 2)':
    sys.exit('! attachment border rules changed')
app.set(S, C, 'BorderColor',
        '// yellow while no file is attached or a mandatory VTT file is missing; red on a form error\n'
        f'If(Not(IsBlank(Parent.Error)), Color.Red, ({EMPTY}) Or ({VTT}), RGBA(255, 204, 0, 1), Parent.BorderColor)', expect=bc)
app.set(S, C, 'BorderThickness', f'If(({EMPTY}) Or ({VTT}), 3, 2)', expect=bt)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL31 built')
