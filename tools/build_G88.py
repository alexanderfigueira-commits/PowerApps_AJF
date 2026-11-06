#!/usr/bin/env python3
"""FINAL98 on FINAL97: varAppLink = the real address of the app (environment, app id, tenant). The portal's session parameters (hint, sourcetime, source) are left out."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG87', 'newG88'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
t = app.rule('App', None, 'OnStart')
old = 'Set(varAppLink, "https://apps.powerapps.com/play/e/ENVIRONMENT-ID/a/APP-ID?tenantId=TENANT-ID");'
assert t.count(old) == 1
new = 'Set(varAppLink, "https://apps.powerapps.com/play/e/487b2992-105a-eb44-aa4b-296dae01044b/a/ba2698a5-2c73-4939-83cc-dd3c5120277d?tenantId=b24c8b06-522c-46fe-9080-70926f8dddb1");'
app.set('App', None, 'OnStart', t.replace(old, new).replace('(replace the placeholders)', '(real address of the app)'), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL98 built')
