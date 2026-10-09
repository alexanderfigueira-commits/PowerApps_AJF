#!/usr/bin/env python3
"""FINAL37 on FINAL36: clicking a request ID on a dashboard opens the request details in VIEW-ONLY mode; Beluga reference visible.

* new global flag varViewOnly: set true by the six ID links on the two dashboards (DOR_/DOA_ List1-3 RowNumber), set false when the
  Request Management or Review screen opens (every other way into the request) and in App.OnStart;
* varRequestorLocked (which already locks every field of the request and of the four media tabs, Save Media, attachments, template)
  now also is true while varViewOnly is true;
* the request screen controls that were not covered by that lock are covered: production type, Add media, administrator / requestor notes
  (box and Save), Message Center input, per-file approval tick, delete media, Draft Save / Submit / Resubmit (hidden);
  on the Info tab the Notes and the Beluga reference boxes. The card title says "view only".
* Beluga reference (ChildInfoScreen, below the FTP field / last field): visible for every role, editable only by an ADMINISTRATOR (and
  not in view-only mode). It was visible for administrators only.
"""
import datetime, os, re, shutil, sys
from payaml import App, find

SRC, NEW = 'newG26', 'newG27'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RS = 'RequesDetailScreen'


def nl(t):
    return t.replace('\r\n', '\n')


def like(o, t):
    return t.replace('\n', '\r\n') if '\r\n' in o else t


def edit(s, c, p, fn, must):
    t = app.rule(s, c, p)
    if t is None:
        sys.exit(f'! {s}.{c}.{p} missing')
    n = fn(nl(t))
    if must not in n or n == nl(t):
        sys.exit(f'! {s}.{c}.{p}: edit did not apply')
    app.set(s, c, p, like(t, n), expect=t)


# 1. flag
edit('App', None, 'OnStart', lambda t: 'Set(varViewOnly, false);\n' + t, 'varViewOnly')
OLDLOCK = '''Set(
    varRequestorLocked,
    varUserRole <> "ADMINISTRATOR"
    And Coalesce(varCurrentRequest.Status.Value, "") = "Processing"
);'''
NEWLOCK = '''Set(
    varRequestorLocked,
    // view-only (a request opened from a dashboard ID) locks everything, whatever the role
    varViewOnly
    Or (
        varUserRole <> "ADMINISTRATOR"
        And Coalesce(varCurrentRequest.Status.Value, "") = "Processing"
    )
);'''
for s in (RS, 'ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen'):
    edit(s, None, 'OnVisible', lambda t: t.replace(OLDLOCK, NEWLOCK, 1) if t.count(OLDLOCK) == 1 else t, 'varViewOnly')
edit('RequestManagementScreen', None, 'OnVisible', lambda t: 'Set(varViewOnly, false);\n' + t, 'varViewOnly')
edit('ReviewScreen', None, 'OnVisible', lambda t: 'Set(varViewOnly, false);\n' + t, 'varViewOnly')

# 2. the six dashboard ID links
for s, cs in (('Dashboard-Ope-Requestor', ('DOR_List1RowNumber', 'DOR_List2RowNumber', 'DOR_List3RowNumber')),
              ('Dashboard-Ope-Administrator', ('DOA_List1RowNumber', 'DOA_List2RowNumber', 'DOA_List3RowNumber'))):
    for c in cs:
        edit(s, c, 'OnSelect', lambda t: t.replace('    Set(varCurrentRequest, req);', '    // opened from a dashboard: details are shown in view-only mode\n    Set(varViewOnly, true);\n    Set(varCurrentRequest, req);', 1), 'varViewOnly, true')

# 3. request screen: controls not covered by the lock
def wrap_dm(mode):
    return lambda t: f'If(varViewOnly, DisplayMode.{mode}, {t})' if not t.lstrip().startswith('//') else t.replace(t.split('\n', 1)[1], f'If(varViewOnly, DisplayMode.{mode}, {t.split(chr(10), 1)[1]})', 1)


for c, mode in (('RS_TypeIconBtn', 'Disabled'), ('Add_media_icon', 'Disabled'), ('RS_AdminNotes', 'View'), ('RS_RequestorNotes', 'View'),
                ('NT_Input', 'View'), ('NT_BtnAdd', 'Disabled'), ('RS_CRowApproved', 'View'), ('RS_CRowDelete', 'Disabled')):
    edit(RS, c, 'DisplayMode', wrap_dm(mode), 'varViewOnly')
for c in ('RS_BtnDraftSave', 'RS_BtnSubmitRequest', 'RS_BtnResubmitRequest', 'RS_AdminNotesSave', 'RS_RequestorNotesSave'):
    edit(RS, c, 'Visible', lambda t: f'Not(varViewOnly) And ({t.strip()})', 'varViewOnly')
edit(RS, 'RS_CardTitle', 'Text', lambda t: f'If(varViewOnly, "Request Details  ·  view only", {t})', 'view only')

# 4. media tabs: Notes and Beluga reference; Beluga visible for everyone
CI = 'ChildInfoScreen'
app.set(CI, 'CI_Notes', 'DisplayMode', 'If(varViewOnly, DisplayMode.View, DisplayMode.Edit)', expect='DisplayMode.Edit')
app.set(CI, 'CI_BelugaRef', 'DisplayMode', 'If(varViewOnly Or varUserRole <> "ADMINISTRATOR", DisplayMode.View, DisplayMode.Edit)',
        expect='If(varUserRole = "ADMINISTRATOR", DisplayMode.Edit, DisplayMode.View)')
for c in ('CI_LblBeluga', 'CI_BelugaRef'):
    app.set(CI, c, 'Visible', 'true', expect='varUserRole = "ADMINISTRATOR"')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL37 built')
