#!/usr/bin/env python3
"""FINAL149 on FINAL148: an administrator who is not the creator of a request only views it, whatever the status.
The lock (varRequestorLocked, set on RequesDetailScreen and on the four media tabs) is now
  ADMINISTRATOR: editable only when the administrator created the request and it is Draft / Processing / Rejected
  requestor:     unchanged (Draft / Pending)
CI_BelugaRef follows the lock too (the Save Media button was already disabled while locked, so an edit there was never stored)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV8', 'newV9'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
PAT = re.compile(r'// an administrator edits Processing and Rejected requests and their own drafts(\r*\n\s*)'
                 r'Not\(st in \["Processing", "Rejected"\] Or \(st = "Draft" And mine\)\),')
for screen in ('RequesDetailScreen', 'ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen'):
    t = app.rule(screen, None, 'OnVisible')
    assert len(PAT.findall(t)) == 1, screen
    u = PAT.sub(lambda m: '// an administrator who is not the creator only views; the creator edits their own Draft, Processing and Rejected requests'
                + m.group(1) + 'Not(mine And st in ["Draft", "Processing", "Rejected"]),', t)
    app.set(screen, None, 'OnVisible', u, expect=t)

t = app.rule('ChildInfoScreen', 'CI_BelugaRef', 'DisplayMode')
assert t == 'If(varViewOnly Or varUserRole <> "ADMINISTRATOR", DisplayMode.View, DisplayMode.Edit)', t
app.set('ChildInfoScreen', 'CI_BelugaRef', 'DisplayMode',
        'If(varViewOnly Or varRequestorLocked Or varUserRole <> "ADMINISTRATOR", DisplayMode.View, DisplayMode.Edit)', expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL149 built')
