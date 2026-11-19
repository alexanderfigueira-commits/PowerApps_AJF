#!/usr/bin/env python3
"""FINAL74 on FINAL73: a requestor can edit a request only while it is Draft or Pending (option A). varRequestorLocked, set on the
OnVisible of the five request / media screens, was true only for Processing (and view-only); it is now true for every status other
than Draft / Pending (a new request counts as Draft). Administrators and the view-only rule are unchanged."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG63', 'newG64'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
OLD = 'And Coalesce(varCurrentRequest.Status.Value, "") = "Processing"'
NEWC = 'And Not(Coalesce(varCurrentRequest.Status.Value, "Draft") in ["Draft", "Pending"])'
for s in ('RequesDetailScreen', 'ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen'):
    t = app.rule(s, None, 'OnVisible')
    assert t.count(OLD) == 1, s
    app.set(s, None, 'OnVisible', t.replace(OLD, NEWC).replace('// view-only (a request opened from a dashboard ID) locks everything, whatever the role',
            '// view-only (a request opened from a dashboard ID) locks everything, whatever the role; a requestor edits only in Draft / Pending'), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL74 built')
