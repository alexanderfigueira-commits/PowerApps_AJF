#!/usr/bin/env python3
"""FINAL215 on FINAL214. Request screen, media section:
1. The two icons become labelled buttons side by side on the "Media files" line: "💾 Save draft" (white, amber border while
   unsaved, as the icon) and "➕ Add media file" (blue). Same names (SaveButton, addMediaItem), same formulas.
2. After a successful Save draft on a request without media files, a pop-up says "Draft saved" and offers "➕ Add media file"
   or "Later" (not shown when the save comes from the leave pop-up).
3. The empty media table shows a "➕ Add the first media file" button."""
import datetime, os, re, shutil
from payaml import App, find
from hp_common import Builder
SRC, NEW = 'newV76', 'newV77'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
RS = 'RequesDetailScreen'
def setp(ctl, prop, val):
    t = app.rule(RS, ctl, prop); assert t is not None, (ctl, prop)
    if t.strip() != val.strip(): app.set(RS, ctl, prop, val, expect=t)
keep = {c: {p: app.rule(RS, c, p) for p in ('OnSelect', 'DisplayMode', 'Tooltip', 'Visible', 'BorderColor', 'BorderThickness')} for c in ('SaveButton', 'addMediaItem')}
# 2. pop-up flag set by a successful Save draft when the request has no media file yet (and not from the leave pop-up)
OK = 'Set(varDraftOK, true); Notify("Draft saved.", NotificationType.Success),'
assert keep['SaveButton']['OnSelect'].count(OK) == 1
keep['SaveButton']['OnSelect'] = keep['SaveButton']['OnSelect'].replace(OK,
    'Set(varDraftOK, true); Notify("Draft saved.", NotificationType.Success);\n'
    '        // first save of a request without media files: suggest the next step\n'
    '        If(Not(Coalesce(varLeaveAsk, false)) And CountRows(colArchives) = 0, UpdateContext({locAddMediaPrompt: true})),')
b = Builder(app, RS)
b.swap('SaveButton', RS, 'RS_LeaveDiscard', {
    'Text': '"💾  Save draft"', 'X': '1006', 'Y': '406', 'Width': '160', 'Height': '36', 'Size': '11',
    'OnSelect': keep['SaveButton']['OnSelect'], 'DisplayMode': keep['SaveButton']['DisplayMode'], 'Tooltip': keep['SaveButton']['Tooltip'],
    'Visible': keep['SaveButton']['Visible'], 'BorderColor': keep['SaveButton']['BorderColor'], 'BorderThickness': keep['SaveButton']['BorderThickness']})
b.swap('addMediaItem', RS, 'RS_LeaveSave', {
    'Text': '"➕  Add media file"', 'X': '1174', 'Y': '406', 'Width': '156', 'Height': '36', 'Size': '11',
    'OnSelect': keep['addMediaItem']['OnSelect'], 'DisplayMode': keep['addMediaItem']['DisplayMode'], 'Tooltip': keep['addMediaItem']['Tooltip'],
    'Visible': keep['addMediaItem']['Visible']})
P = 'Coalesce(locAddMediaPrompt, false)'
CAN_ADD = 'If(addMediaItem.DisplayMode = DisplayMode.Edit, DisplayMode.Edit, DisplayMode.Disabled)'
b.clone('RS_AddMShade', RS, 'RS_LeaveShade', {'Visible': P})
b.clone('RS_AddMPanel', RS, 'RS_LeavePanel', {'Visible': P})
b.clone('RS_AddMText', RS, 'RS_LeaveText', {'Visible': P, 'Height': '84', 'Text': (
    '"✓  Draft saved" & Char(10) & "Request " & Coalesce(varCurrentRequest.RequestNumber, "") & " is saved as a draft." & Char(10) & '
    '"Next step: add the media files of this request."')})
b.clone('RS_AddMLater', RS, 'RS_LeaveBack', {'Visible': P, 'Text': '"Later"', 'X': '507', 'Width': '140',
        'OnSelect': 'UpdateContext({locAddMediaPrompt: false})'})
b.clone('RS_AddMGo', RS, 'RS_LeaveSave', {'Visible': P, 'Text': '"➕  Add media file"', 'X': '667', 'Width': '236', 'DisplayMode': CAN_ADD,
        'OnSelect': 'UpdateContext({locAddMediaPrompt: false});\nSelect(addMediaItem)'})
# 3. empty table: message + button
b.clone('RS_BtnAddFirst', RS, 'RS_LeaveSave', {'Text': '"➕  Add the first media file"', 'X': '553', 'Y': '624', 'Width': '260', 'Height': '42',
        'Size': '12', 'Visible': app.rule(RS, 'RS_ChildrenEmpty', 'Visible'), 'DisplayMode': CAN_ADD, 'OnSelect': 'Select(addMediaItem)',
        'Tooltip': '"Add the first media file of this request"'})
b.save()
setp('RS_ChildrenEmpty', 'Text', '"No media files yet."')
setp('RS_ChildrenEmpty', 'Y', '584')
# pop-up above everything
tp = app.doc(RS)['TopParent']
z = lambda n: int(([x['InvariantScript'] for x in n['Rules'] if x['Property'] == 'ZIndex'] or ['0'])[0])
def deep(n):
    yield n
    for c in n.get('Children', []): yield from deep(c)
NEWC = ['RS_AddMShade', 'RS_AddMPanel', 'RS_AddMText', 'RS_AddMLater', 'RS_AddMGo']
mx = max(z(n) for n in deep(tp) if n['Name'] not in NEWC)
for k, nm in enumerate(NEWC): [x for x in find(tp, nm)['Rules'] if x['Property'] == 'ZIndex'][0]['InvariantScript'] = str(mx + 1 + k)
app.save()
p_ = f'{NEW}/Properties.json'
raw = open(p_, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
for k, d in (('icon', -2), ('button', 2 + 3), ('rectangle', 2), ('label', 1)):
    t = re.sub(r'("%s"\s*:\s*)(\d+)' % k, lambda mm: mm.group(1) + str(int(mm.group(2)) + d), t, count=1)
open(p_, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL215 built')
