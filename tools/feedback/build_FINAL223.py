#!/usr/bin/env python3
"""FINAL223 on FINAL222. The dd-mm-yyyy labels under the Request Management date filters (HomeFilterStart_Txt,
HomeFilterEnd_Txt, added in FINAL217) copied the picker's BorderColor with Self.SelectedDate; a label has no SelectedDate
(6 errors). They now name the pickers."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV84', 'newV85'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
S = 'RequestManagementScreen'
for lbl, pick in (('HomeFilterStart_Txt', 'HomeFilterStart'), ('HomeFilterEnd_Txt', 'HomeFilterEnd')):
    t = app.rule(S, lbl, 'BorderColor'); assert t.count('Self.SelectedDate') == 2, (lbl, t)
    app.set(S, lbl, 'BorderColor', t.replace('Self.SelectedDate', f'{pick}.SelectedDate'), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL223 built')
