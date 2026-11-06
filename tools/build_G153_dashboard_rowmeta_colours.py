#!/usr/bin/env python3
"""FINAL164 on FINAL163: the administrators' colour theme on the dashboards' row labels DOA_List1/2/3RowMeta (created by) and
DOR_List1/2/3RowMeta (last updated by): the name takes the colour its owner has in the roles list (column Colour); a person without a colour
(a requestor, an unknown colour) keeps the dark grey the labels already have. colAdminColours is also loaded when each dashboard opens and by
its refresh icons, so a colour changed in the list shows up without restarting the app."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV25', 'newV26'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
ADM, REQ = 'Dashboard-Ope-Administrator', 'Dashboard-Ope-Requestor'

t = app.rule('RequestManagementScreen', None, 'OnVisible')
LOAD = t[t.index('// one colour per administrator'):]
assert LOAD.rstrip().endswith(')') and LOAD.count('ClearCollect(') == 1

GREY = 'RGBA(32, 31, 30, 1)'
for S, P, who in ((ADM, 'DOA', "'Created By'"), (REQ, 'DOR', "'Modified By'")):
    for i in (1, 2, 3):
        c = f'{P}_List{i}RowMeta'
        t = app.rule(S, c, 'Color'); assert t == GREY, (c, t)
        app.set(S, c, 'Color', f'Coalesce(LookUp(colAdminColours, Mail = Lower(ThisItem.{who}.Email)).Color, {GREY})', expect=t)
    # the colours are read again when the dashboard opens ...
    t = app.rule(S, None, 'OnVisible'); assert 'colAdminColours' not in t
    app.set(S, None, 'OnVisible', t.rstrip().rstrip(';') + ';\n' + LOAD, expect=t)
    # ... and by its three refresh icons
    for i in (1, 2, 3):
        c = f'{P}_List{i}Refresh'
        t = app.rule(S, c, 'OnSelect'); assert 'colAdminColours' not in t
        anchor = 'If(\n        CountRows(colOpeAll) >= 2000,' if P == 'DOA' else 'Notify("Lists refreshed.", NotificationType.Success),'
        assert t.count(anchor) == 1, c
        app.set(S, c, 'OnSelect', t.replace(anchor, LOAD + ';\n    ' + anchor), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL164 built')
