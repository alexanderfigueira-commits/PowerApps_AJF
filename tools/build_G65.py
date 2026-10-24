#!/usr/bin/env python3
"""FINAL75 on FINAL74: who edits what.
  requestor     : Draft and Pending only (unchanged); 'Resubmit for review' no longer shows on Rejected, because the request is locked.
  administrator : Processing, Rejected, and their own Drafts (before: always unlocked); Approved / Pending / other users' Drafts are read-only.
varRequestorLocked (OnVisible of the five request / media screens) carries the rule. The controls that bypassed it now follow it:
Draft Save (visible only in status Draft), Submit, Resubmit, Add media, Remove,
and the production-type picker."""
import datetime, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG64', 'newG65'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RS = 'RequesDetailScreen'
OLD = ('varViewOnly\n    Or (\n        varUserRole <> "ADMINISTRATOR"\n        And Not(Coalesce(varCurrentRequest.Status.Value, "Draft") in ["Draft", "Pending"])\n    )')
NEWL = ('varViewOnly\n    Or With(\n        {\n            st: Coalesce(varCurrentRequest.Status.Value, "Draft"),\n'
        '            mine: Coalesce(varCurrentRequest.ID, 0) <= 0 Or Lower(Coalesce(varCurrentRequest.\'Created By\'.Email, "")) = Lower(User().Email)\n        },\n'
        '        If(\n            varUserRole = "ADMINISTRATOR",\n'
        '            // an administrator edits Processing and Rejected requests and their own drafts\n'
        '            Not(st in ["Processing", "Rejected"] Or (st = "Draft" And mine)),\n'
        '            // a requestor edits Draft and Pending requests\n'
        '            Not(st in ["Draft", "Pending"])\n        )\n    )')
for s in (RS, 'ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen'):
    t = app.rule(s, None, 'OnVisible'); eol = '\r\n' if '\r\n' in t else '\n'
    n = t.replace('\r\n', '\n')
    assert n.count(OLD) == 1, s
    app.set(s, None, 'OnVisible', n.replace(OLD, NEWL).replace('\n', eol), expect=t)
def edit(ctl, prop, fn):
    t = app.rule(RS, ctl, prop); n = fn(t)
    assert n != t, (ctl, prop)
    app.set(RS, ctl, prop, n, expect=t)
# Draft Save shows only while the request is a Draft (or new) that the user may edit
edit('RS_BtnDraftSave', 'Visible', lambda t: t.replace('Not(varViewOnly) And (!locShowTypePicker)',
     'Not(varViewOnly) And Not(varRequestorLocked) And (!locShowTypePicker) And (IsBlank(varCurrentRequest) Or Coalesce(varCurrentRequest.ID, 0) <= 0 Or Coalesce(varCurrentRequest.Status.Value, "Draft") = "Draft")', 1))
edit('RS_BtnSubmitRequest', 'Visible', lambda t: t.replace('Not(varViewOnly) And (', 'Not(varViewOnly) And Not(varRequestorLocked) And (', 1))
edit('RS_BtnResubmitRequest', 'Visible', lambda t: t.replace('Not(varViewOnly) And (', 'Not(varViewOnly) And Not(varRequestorLocked) And (', 1))
edit('Add_media_icon', 'DisplayMode', lambda t: t.replace('If(varViewOnly, DisplayMode.Disabled', 'If(varViewOnly Or varRequestorLocked, DisplayMode.Disabled', 1))
edit('RS_TypeIconBtn', 'DisplayMode', lambda t: t.replace('If(varViewOnly, DisplayMode.Disabled', 'If(varViewOnly Or varRequestorLocked, DisplayMode.Disabled', 1))
app.set(RS, 'RS_CRowDelete', 'DisplayMode', 'If(varRequestorLocked, DisplayMode.Disabled, DisplayMode.Edit)', expect=app.rule(RS, 'RS_CRowDelete', 'DisplayMode'))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL75 built')
