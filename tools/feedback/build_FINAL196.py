#!/usr/bin/env python3
"""FINAL196 on FINAL195. The decision bar of the request screen shows for any administrator viewing a Processing request
(from the Review queue, Request Management or a dashboard), and the decision returns to where the request was opened from."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV57', 'newV58'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def sub(t, old, new, n=1):
    assert t.count(old) == n, (old[:70], t.count(old)); return t.replace(old, new)
def edit(screen, ctl, prop, fn):
    t = app.rule(screen, ctl, prop); n = fn(t); assert n != t, (screen, ctl, prop)
    app.set(screen, ctl, prop, n, expect=t)
RS = 'RequesDetailScreen'
OLD = 'Coalesce(locFromReview, false) And varUserRole = "ADMINISTRATOR" And Coalesce(varCurrentRequest.Status.Value, "") = "Processing"'
NEWC = 'varUserRole = "ADMINISTRATOR" And Coalesce(varCurrentRequest.ID, 0) > 0 And Coalesce(varCurrentRequest.Status.Value, "") = "Processing"'
for c in ('RS_DecBar', 'RS_DecComment', 'RS_DecApprove', 'RS_DecPending', 'RS_DecReject', 'Label12_6'):
    edit(RS, c, 'Visible', lambda t: sub(t, OLD, NEWC))
edit(RS, 'RS_DecApprove', 'DisplayMode', lambda t: sub(t, OLD, NEWC))
for c in ('RS_DecPending', 'RS_DecReject'):
    edit(RS, c, 'DisplayMode', lambda t: sub(t, OLD, NEWC))
BACK = ('// back to where the request was opened from: the Review queue, else Request Management (the dashboards reload on entry)\n'
        '    If(Coalesce(locFromReview, false), Navigate(ReviewScreen, ScreenTransition.UnCover), Navigate(RequestManagementScreen, ScreenTransition.UnCover)),')
for c in ('RS_DecApprove', 'RS_DecPending', 'RS_DecReject'):
    edit(RS, c, 'OnSelect', lambda t: sub(t, '// back to the Review queue\n    Navigate(ReviewScreen, ScreenTransition.UnCover),', BACK))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL196 built')
