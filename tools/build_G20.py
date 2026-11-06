#!/usr/bin/env python3
"""FINAL30 on the user's FINAL_3: the media item's SharePoint ID is never lost, so a file attached after Save Media is sent.

Symptom: after Save Media (no file yet) the user opens the item again, attaches a file, saves, and the id that CL_DCAttach (CL_FormAttach)
needs is empty (spId = 0): the attachments are not sent.
Causes fixed:
* the ID was resolved with Coalesce(), which treats 0 as a value: a stale 0 in the media list (colArchives) hid the real id kept in
  varCurrentChildSPId. Now a 0 never wins over a real id (when the list is written and when Save reads it back).
* when a tab opens with varCurrentChildSPId empty, it is restored from the media list before the attachments record is read.
* when Save has the id but the attachments panel is not loaded for that item, the user is told instead of the file being dropped silently.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'up3', 'newG20'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)


def nl(t):
    return t.replace('\r\n', '\n')


def like(o, t):
    return t.replace('\n', '\r\n') if '\r\n' in o else t


# ---------------------------------------------------------------- 1. Save Media
S, N = 'ChildValidScreen', 'CV_BtnSaveArchive'
t = app.rule(S, N, 'OnSelect')
n = nl(t)
a = 'SPId: Coalesce(existingRec.SPId, varCurrentChildSPId, 0),'
if n.count(a) != 1:
    sys.exit('! SPId write not found')
n = n.replace(a, 'SPId: If(Coalesce(existingRec.SPId, 0) > 0, existingRec.SPId, Coalesce(varCurrentChildSPId, 0)),')
b = '{spId: Coalesce(LookUp(colArchives, ArchiveId = varCurrentChildId).SPId, 0)},'
if n.count(b) != 1:
    sys.exit('! spId read not found')
n = n.replace(b, '''{
                              // the item's SharePoint ID: from the media list, else from varCurrentChildSPId (a 0 never hides a real id)
                              spId: If(
                                  Coalesce(LookUp(colArchives, ArchiveId = varCurrentChildId).SPId, 0) > 0,
                                  LookUp(colArchives, ArchiveId = varCurrentChildId).SPId,
                                  Coalesce(varCurrentChildSPId, 0)
                              )
                          },''')
c = re.compile(r'( *)// The item was only just created: the form was disabled, nothing to send\.\n *Notify\("Media saved to SharePoint\.", NotificationType\.Success\);')
m = c.findall(n)
if len(m) != 1:
    sys.exit('! else branch not found')
def rep(mo):
    i = mo.group(1)
    return (f'{i}// Otherwise the item was only just created (the form was disabled, nothing to send), or its attachments\n'
            f'{i}// panel is not loaded for this item: say so, so a file is never dropped silently.\n'
            f'{i}If(\n{i}    spId > 0,\n'
            f'{i}    Notify("Media saved, but its attachments panel was not loaded, so no file was sent. Open the media item again and attach the file.", NotificationType.Warning),\n'
            f'{i}    Notify("Media saved to SharePoint.", NotificationType.Success)\n{i});')
n = c.sub(rep, n)
app.set(S, N, 'OnSelect', like(t, n), expect=t)

# ---------------------------------------------------------------- 2. every media tab restores the id before reading the attachments record
anchor = 'If(\n    Coalesce(varAttachRecord.ID, 0) <> Coalesce(varCurrentChildSPId, 0),'
fix = '''// the item's SharePoint ID: if the variable lost it, take it back from the media list
If(
    Coalesce(varCurrentChildSPId, 0) = 0 And Coalesce(LookUp(colArchives, ArchiveId = varCurrentChildId).SPId, 0) > 0,
    Set(varCurrentChildSPId, LookUp(colArchives, ArchiveId = varCurrentChildId).SPId)
);
'''
for scr in ('ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen'):
    t = app.rule(scr, None, 'OnVisible')
    n = nl(t)
    if n.count(anchor) != 1:
        sys.exit(f'! {scr}: anchor not found')
    n = n.replace(anchor, fix + anchor)
    app.set(scr, None, 'OnVisible', like(t, n), expect=t)
app.save()

h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL30 built')
