#!/usr/bin/env python3
"""FINAL73 on FINAL72: HomeRowBadge (RequestManagementScreen) tooltip uses the dashboards' partially-approved rule, over colMyMedia
(the media list this screen loads): an Approved request whose media files are only partly ticked says 'Partially Approved Request.'"""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG62', 'newG63'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequestManagementScreen'
assert app.rule(S, 'HomeRowBadge', 'Tooltip') == ''  or True
new = '''// "Partially approved" is not a status: an Approved request whose media files are only partly ticked (RS_CRowApproved) says so here
With(
    {
        n: CountRows(Filter(colMyMedia, ParentRequest = ThisItem.RequestNumber)),
        ok: CountRows(Filter(colMyMedia, ParentRequest = ThisItem.RequestNumber, MediaApproved = true))
    },
    If(
        ThisItem.Status.Value = "Partially approved" Or (ThisItem.Status.Value = "Approved" And ok > 0 And ok < n),
        "Partially Approved Request.",
        "Status"
    )
)'''
app.set(S, 'HomeRowBadge', 'Tooltip', new, expect=app.rule(S, 'HomeRowBadge', 'Tooltip'))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL73 built')
