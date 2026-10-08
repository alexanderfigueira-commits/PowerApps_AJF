#!/usr/bin/env python3
"""FINAL72 on FINAL71: RS_Trk3 tooltip uses the dashboards' 'Partially approved' rule. 'Partially approved' is not a status: an Approved
request whose media files are only partly ticked (RS_CRowApproved, MediaApproved in colArchives) says 'Partially Approved Request.'"""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG61', 'newG62'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
new = '''// "Partially approved" is not a status: an Approved request whose media files are only partly ticked (RS_CRowApproved) says so here
With(
    {
        st: Coalesce(varCurrentRequest.Status.Value, "Draft"),
        n: CountRows(colArchives),
        ok: CountRows(Filter(colArchives, MediaApproved = true))
    },
    If(
        st = "Partially approved" Or (st = "Approved" And ok > 0 And ok < n),
        "Partially Approved Request.",
        Switch(
            st,
            "Approved", "Approved: the request was approved by Central Deposit.",
            "Published", "Approved: the request was approved by Central Deposit.",
            "Rejected", "Rejected: the request was rejected, see the reviewer comment.",
            "Pending", "Pending: information needed, the request was sent back to the requestor.",
            "Approval: Central Deposit decides on the request."
        )
    )
)'''
app.set(S, 'RS_Trk3', 'Tooltip', new, expect=app.rule(S, 'RS_Trk3', 'Tooltip'))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL72 built')
