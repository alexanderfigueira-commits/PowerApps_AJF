#!/usr/bin/env python3
"""FINAL110 on DEV: HomeRowUserAction ('User action ->') stays visible for Pending requests but is only active for the Requestor; an Administrator sees it inactive."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newL1', 'newL2'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, C = 'RequestManagementScreen', 'HomeRowUserAction'
app.set(S, C, 'DisplayMode', 'If(varUserRole = "ADMINISTRATOR", DisplayMode.Disabled, DisplayMode.Edit)', expect='DisplayMode.Edit')
app.set(S, C, 'Tooltip', 'If(varUserRole = "ADMINISTRATOR", "Waiting for the requestor: only the requestor can act here", "Open in review queue to approve or reject")', expect='"Open in review queue to approve or reject"')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL110 built')
