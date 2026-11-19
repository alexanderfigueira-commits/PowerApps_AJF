#!/usr/bin/env python3
"""FINAL42 on FINAL41: "Remove" on the media files list (RS_ChildrenGallery > RS_CRowDelete) asks for confirmation first.

Remove no longer deletes at once. It opens a confirmation pop-up on RequesDetailScreen:
  "Remove media file?  Are you sure you want to delete the media file "<title>"? This cannot be undone."   [No, keep it] [Yes, delete]
* Yes: the same deletion as before (the SharePoint item when it has an id, then the row of the list), then the pop-up closes;
* No (or opening the screen again): nothing is deleted and the pop-up closes.
The pop-up is built from the screen's own Contact Extra pop-up controls (backdrop, title) and the notes pop-up buttons (the panel is a white clone of the backdrop) so it looks the same.
locDelItem keeps the row that was clicked; locShowDelConfirm shows the pop-up.
"""
import datetime, os, re, shutil, sys
from collections import Counter
from payaml import App, find
from hp_common import Builder

SRC, NEW = 'newG31', 'newG32'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RS = 'RequesDetailScreen'
b = Builder(app, RS)
tp = b.tp
mx = 0
def zs(c):
    global mx
    for r in c['Rules']:
        if r['Property'] == 'ZIndex':
            mx = max(mx, int(r['InvariantScript']))
    for k in c.get('Children', []):
        zs(k)
zs(tp)
S = 'locShowDelConfirm'
TITLE = 'Coalesce(locDelItem.ProductionTitle, "")'
DELETE = '''IfError(
    If(
        Coalesce(locDelItem.SPId, 0) > 0,
        Remove('AV-CD-Mediafiles', LookUp('AV-CD-Mediafiles', ID = locDelItem.SPId))
    );
    RemoveIf(colArchives, ArchiveId = locDelItem.ArchiveId);
    Notify("Media item removed.", NotificationType.Success),
    Notify("Could not delete the media item: " & FirstError.Message, NotificationType.Error)
);
UpdateContext({locShowDelConfirm: false, locDelItem: Blank()})'''
back = b.clone('RS_DelBackdrop', RS, 'RS_ContactBackdrop', {'Visible': S}, parent=None)
panel = b.clone('RS_DelPanel', RS, 'RS_ContactBackdrop', {'X': '433', 'Y': '270', 'Width': '500', 'Height': '230', 'Visible': S, 'Fill': 'RGBA(255, 255, 255, 1)', 'BorderColor': 'RGBA(0, 18, 107, 1)', 'BorderThickness': '2'}, parent=None)
title = b.clone('RS_DelTitle', RS, 'RS_ContactTitle', {'X': '463', 'Y': '292', 'Width': '440', 'Height': '34', 'Visible': S, 'Text': '"Remove media file?"', 'Align': 'Align.Left'}, parent=None)
msg = b.clone('RS_DelText', RS, 'RS_ContactTitle', {'X': '463', 'Y': '338', 'Width': '440', 'Height': '84', 'Visible': S,
                                                     'Text': f'"Are you sure you want to delete the media file " & Char(34) & {TITLE} & Char(34) & "? This cannot be undone."',
                                                     'Align': 'Align.Left', 'FontWeight': 'FontWeight.Normal'}, parent=None)
no = b.clone('RS_DelNo', RS, 'RS_AdminNotesCancel', {'X': '463', 'Y': '440', 'Width': '200', 'Height': '44', 'Visible': S, 'Text': '"No, keep it"',
                                                      'OnSelect': 'UpdateContext({locShowDelConfirm: false, locDelItem: Blank()})'}, parent=None)
yes = b.clone('RS_DelYes', RS, 'RS_AdminNotesSave', {'X': '703', 'Y': '440', 'Width': '200', 'Height': '44', 'Visible': S, 'Text': '"Yes, delete"', 'OnSelect': DELETE,
                                                      'Fill': 'RGBA(192, 57, 43, 1)', 'HoverFill': 'RGBA(150, 40, 30, 1)', 'DisplayMode': 'DisplayMode.Edit'}, parent=None)
b.save()
# stacking above everything (set after b.save() so the ZIndex stays out of the YAML mirror)
def set_z(c, z):
    r = [x for x in c['Rules'] if x['Property'] == 'ZIndex'][0]
    r['InvariantScript'] = str(z)
    for e in c.get('ControlPropertyState', []):
        if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString'):
            e['AutoRuleBindingString'] = str(z)
for i, c in enumerate((back, panel, title, msg, no, yes)):
    set_z(c, mx + 1 + i)
app.save()
# the Remove button asks first
t = app.rule(RS, 'RS_CRowDelete', 'OnSelect')
app.set(RS, 'RS_CRowDelete', 'OnSelect', 'UpdateContext({locDelItem: ThisItem, locShowDelConfirm: true})', expect=t)
# the pop-up never stays open when the screen is entered
t = app.rule(RS, None, 'OnVisible')
n = t.replace('\r\n', '\n')
a = 'locShowAdminNotes: false,'
if n.count(a) != 1:
    sys.exit('! OnVisible context block not found')
app.set(RS, None, 'OnVisible', (n.replace(a, a + '\n        locShowDelConfirm: false,')).replace('\n', '\r\n') if '\r\n' in t else n.replace(a, a + '\n        locShowDelConfirm: false,'), expect=t)
app.save()

def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)
app = App(NEW)
cnt = Counter(c['Template']['Name'] for s in app.map if s != 'App' for c in walk(app.doc(s)['TopParent']))
p = open(f'{NEW}/Properties.json', encoding='utf-8').read()
for k, v in cnt.items():
    p = re.sub(rf'("{k}": )\d+', rf'\g<1>{v}', p, count=1)
open(f'{NEW}/Properties.json', 'w', encoding='utf-8', newline='').write(p)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL42 built; top ZIndex', mx + 6)
