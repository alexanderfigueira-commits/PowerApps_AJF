#!/usr/bin/env python3
"""FINAL39 on FINAL38: "All Status" on the Requests screen lists drafts first (by creation date), then every other status by modification date.

Both parts newest first (the order All Status already used). A single status chip keeps its order (creation date, oldest first).
The sort key is one number: drafts get a large offset plus their creation time, the others their modification time; sorted descending.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG28', 'newG29'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RM = 'RequestManagementScreen'
t = app.rule(RM, 'HomeGallery', 'Items')
n = t.replace('\r\n', '\n')
ALL = 'Coalesce(varFilter, If(varUserRole = "ADMINISTRATOR", "Processing", "Pending")) = "All"'
old = f'''    Created,
    // one status: oldest first (waiting longest on top); All Status: newest first
    If({ALL}, SortOrder.Descending, SortOrder.Ascending)
)'''
if n.count(old) != 1:
    sys.exit('! sort block not found')
new = f'''    If(
        {ALL},
        // All Status: drafts first, by creation date; every other status by modification date (newest first in both)
        If(Status.Value = "Draft", 10000000000, 0)
            + DateDiff(DateTime(2000, 1, 1, 0, 0, 0), If(Status.Value = "Draft", Created, Modified), TimeUnit.Seconds),
        // one status: by creation date
        DateDiff(DateTime(2000, 1, 1, 0, 0, 0), Created, TimeUnit.Seconds)
    ),
    // one status: oldest first (waiting longest on top); All Status: newest first
    If({ALL}, SortOrder.Descending, SortOrder.Ascending)
)'''
n2 = n.replace(old, new)
app.set(RM, 'HomeGallery', 'Items', n2.replace('\n', '\r\n') if '\r\n' in t else n2, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL39 built')
