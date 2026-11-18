#!/usr/bin/env python3
"""FINAL231 on FINAL230.
1. Request page, Message Center: the panel ends at 697 instead of 737, so the administrator's decision bar under it (message to
   the requestor, Approved / Pending / Rejected, from 712) stays clear while the Message Center is open: panel 680 -> 640 px,
   messages 444 -> 434 px, the message box and its send button 30 px higher.
2. Request Management: the notes icon's tooltip is the one of the dashboards: "No notes" when the request has none,
   "New notes to check" / "Notes sent" otherwise, with the last message (author, role, date, text)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV92', 'newV93'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))


def setp(scr, ctl, prop, val, old=None):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if old is not None: assert t.strip() == old, (scr, ctl, prop, t)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)


RS = 'RequesDetailScreen'
setp(RS, 'NT_Panel', 'Height', '640', '680')
setp(RS, 'MessageCenter', 'Height', '434', '444')
setp(RS, 'NT_Input', 'Y', '592', '622')
setp(RS, 'NT_BtnAdd', 'Y', '637', '667')
tip = app.rule('Dashboard-Ope-Administrator', 'Label1_3', 'Tooltip')
assert '"No notes"' in tip and 'Last message' in tip
setp('RequestManagementScreen', 'Label1', 'Tooltip', tip)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL231 built')
