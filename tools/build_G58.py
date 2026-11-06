#!/usr/bin/env python3
"""FINAL68 on FINAL67: cmbFilterRequestor accepts only one value (keeps 'All', as cmbFilterAssignee_1 in FINAL63)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG57', 'newG58'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
app.set('RequestManagementScreen', 'cmbFilterRequestor', 'SelectMultiple', 'false', expect='true')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL68 built')
