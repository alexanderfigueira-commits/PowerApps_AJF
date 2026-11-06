#!/usr/bin/env python3
"""FINAL35 on FINAL34: the Beluga reference field on ChildInfoScreen sits below the FTP field and is shown to the administrator on every request.

CI_LblBeluga / CI_BelugaRef already existed at the bottom of the screen, but only for an ADMINISTRATOR on an Approved request. Now:
* visible for an ADMINISTRATOR whatever the status (a requestor still does not see it); optional: no * and no yellow border;
* Photo: right below the FTP field (label Y 392, box Y 418); Video / Podcast, which have no FTP field: right below their last field
  (label Y 471, box Y 497) and the Notes box moves down to make room (label Y 548, box Y 580). Photo keeps Notes where it was.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG24', 'newG25'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'ChildInfoScreen'
PH = 'varChildMediaType = "Photo"'
OLDV = 'Coalesce(varCurrentRequest.Status.Value, "") = "Approved" And varUserRole = "ADMINISTRATOR"'
for c in ('CI_LblBeluga', 'CI_BelugaRef'):
    app.set(S, c, 'Visible', 'varUserRole = "ADMINISTRATOR"', expect=OLDV)
app.set(S, 'CI_LblBeluga', 'Y', f'If({PH}, 392, 471)', expect='560')
app.set(S, 'CI_BelugaRef', 'Y', f'If({PH}, 418, 497)', expect='584')
app.set(S, 'CI_LblNotes', 'Y', f'If({PH}, 471, 548)', expect='471')
app.set(S, 'CI_Notes', 'Y', f'If({PH}, 503, 580)', expect='503')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL35 built')
