#!/usr/bin/env python3
"""FINAL108 on FINAL107: an Administrator cannot delete the media files of a request created by someone else.
RS_CRowDelete is disabled (with an explaining tooltip) and RS_DelYes refuses as well."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newJ8', 'newJ9'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
# someone else's request, seen by an administrator
OTHERS = '(varUserRole = "ADMINISTRATOR" And Coalesce(varCurrentRequest.ID, 0) > 0 And Lower(Coalesce(varCurrentRequest.\'Created By\'.Email, "")) <> Lower(User().Email))'
MSG = 'Administrators cannot delete media files of requests created by other users.'
app.set(S, 'RS_CRowDelete', 'DisplayMode', 'If(varRequestorLocked Or ' + OTHERS + ', DisplayMode.Disabled, DisplayMode.Edit)',
        expect='If(varRequestorLocked, DisplayMode.Disabled, DisplayMode.Edit)')
app.set(S, 'RS_CRowDelete', 'Tooltip', 'If(' + OTHERS + ', "' + MSG + '", "")', expect='""')
t = app.rule(S, 'RS_DelYes', 'OnSelect'); eol = '\r\n' if '\r\n' in t else '\n'; n = t.replace('\r\n', '\n')
tail = ');\nUpdateContext({locShowDelConfirm: false, locDelItem: Blank()})'
assert n.endswith(tail) and n.startswith('IfError(')
body = n[:-len(tail)] + ')'
ind = '\n'.join('    ' + l if l else l for l in body.split('\n'))
new = 'If(\n    ' + OTHERS + ',\n    Notify("' + MSG + '", NotificationType.Warning),\n' + ind + '\n' + tail
app.set(S, 'RS_DelYes', 'OnSelect', new.replace('\n', eol), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL108 built')
