#!/usr/bin/env python3
"""FINAL44 on FINAL43:
1. RequesDetailScreen header: a "Track flow status" stepper between the message badge and the status badge (X 480-860, Y 62-104), four steps
   Draft > Processing > Decision > Published, driven by varCurrentRequest.Status:
     Draft / new      step 1 current (blue)
     Pending          step 1 current in amber, label "Info needed" (sent back to the requestor)
     Processing       step 1 done, step 2 current
     Approved         steps 1-2 done, step 3 green "Approved"   (old "Partially approved" shows as Approved)
     Rejected         steps 1-2 done, step 3 red "Rejected"
     Published        all done
   Each circle has a tooltip; the connector between two steps is green once the earlier step is done.
2. Legal & Docs: the key text of the attachments card (CL_DCAttachKey) ends with " *" (the attachments are mandatory: yellow border while empty).
"""
import datetime, os, re, shutil, sys
from collections import Counter
from payaml import App, find
from hp_common import Builder

SRC, NEW = 'newG33', 'newG34'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RS = 'RequesDetailScreen'
b = Builder(app, RS)

S = 'Coalesce(varCurrentRequest.Status.Value, "Draft")'
RANK = f'Switch({S}, "Pending", 1, "Processing", 2, "Rejected", 3, "Approved", 3, "Partially approved", 3, "Published", 4, 1)'
TERM = f'{S} in ["Approved", "Partially approved", "Published"]'
GREEN, BLUE, AMBER, RED, TODO, GREY, NAVY, WHITE = ('RGBA(22, 128, 80, 1)', 'RGBA(56, 96, 178, 1)', 'RGBA(200, 140, 0, 1)', 'RGBA(192, 57, 43, 1)',
                                                    'RGBA(215, 223, 240, 1)', 'RGBA(96, 104, 120, 1)', 'RGBA(0, 18, 107, 1)', 'RGBA(255, 255, 255, 1)')
TIP = {
    1: f'If({S} = "Pending", "Information needed: the request was sent back to the requestor.", "Draft: the requestor prepares the request and adds the media files.")',
    2: '"Processing: submitted and under review by Central Deposit."',
    3: f'Switch({S}, "Approved", "Approved by Central Deposit.", "Partially approved", "Approved by Central Deposit.", "Rejected", "Rejected: see the reviewer comment.", "Decision: approved or rejected by Central Deposit.")',
    4: '"Published: the media is published on the portal."',
}
LAB = {
    1: f'If({S} = "Pending", "Info needed", "Draft")',
    2: '"Processing"',
    3: f'Switch({S}, "Approved", "Approved", "Partially approved", "Approved", "Rejected", "Rejected", "Decision")',
    4: '"Published"',
}
X0, PITCH, D, YC, YL = 480, 95, 24, 62, 87
made = []
for i in (1, 2, 3, 4):
    cx = X0 + PITCH / 2 + PITCH * (i - 1)
    fill = f'If({S} = "Rejected" And {i} = 3, {RED}, {i} < {RANK}, {GREEN}, {i} = {RANK}, If({TERM}, {GREEN}, If({S} = "Pending", {AMBER}, {BLUE})), {TODO})'
    txt = f'If({S} = "Rejected" And {i} = 3, "✕", {i} < {RANK} Or ({i} = {RANK} And {TERM}), "✓", "{i}")'
    col = f'If({i} > {RANK}, {GREY}, {WHITE})'
    made.append(b.clone(f'RS_Trk{i}', RS, 'DOA_List1RowBadge_3', {
        'X': str(int(cx - D / 2)), 'Y': str(YC), 'Width': str(D), 'Height': str(D), 'Text': txt, 'Fill': fill, 'Color': col, 'Tooltip': TIP[i], 'OnSelect': 'false',
        'DisplayMode': 'DisplayMode.View', 'Visible': 'true', 'Size': '11', 'FontWeight': 'FontWeight.Bold', 'BorderColor': 'RGBA(0, 0, 0, 0)', 'BorderThickness': '0',
        'RadiusTopLeft': str(D // 2), 'RadiusTopRight': str(D // 2), 'RadiusBottomLeft': str(D // 2), 'RadiusBottomRight': str(D // 2),
        'PaddingLeft': '0', 'PaddingRight': '0', 'PaddingTop': '0', 'PaddingBottom': '0', 'Align': 'Align.Center'}, parent=None))
    made.append(b.clone(f'RS_TrkLbl{i}', RS, 'RS_LblDescription', {
        'X': str(int(cx - PITCH / 2)), 'Y': str(YL), 'Width': str(PITCH), 'Height': '17', 'Text': LAB[i], 'Align': 'Align.Center', 'Size': '11',
        'Color': f'If({i} > {RANK}, {GREY}, {NAVY})', 'FontWeight': f'If({i} = {RANK}, FontWeight.Bold, FontWeight.Semibold)', 'Visible': 'true'}, parent=None))
    if i < 4:
        made.append(b.clone(f'RS_TrkLine{i}', RS, 'RS_DetailsDivider', {
            'X': str(int(cx + D / 2 + 4)), 'Y': str(YC + D // 2 - 1), 'Width': str(PITCH - D - 8), 'Height': '3', 'Visible': 'true',
            'Fill': f'If({i} < {RANK}, {GREEN}, {TODO})'}, parent=None))
b.save()
# stacking: below every pop-up backdrop (lowest 64), above the card; the controls do not overlap each other
tp = b.tp
for i, c in enumerate(made):
    r = [x for x in c['Rules'] if x['Property'] == 'ZIndex'][0]
    z = 46 if c['Name'].startswith('RS_Trk') and not c['Name'].startswith(('RS_TrkLbl', 'RS_TrkLine')) else (51 if c['Name'].startswith('RS_TrkLbl') else 37)
    r['InvariantScript'] = str(z)
    for e in c.get('ControlPropertyState', []):
        if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString'):
            e['AutoRuleBindingString'] = str(z)
# nothing else may sit in the tracker area
def rect(c):
    r = {x['Property']: x['InvariantScript'] for x in c['Rules']}
    try:
        return float(r['X']), float(r['Y']), float(r['X']) + float(r['Width']), float(r['Y']) + float(r['Height'])
    except (KeyError, ValueError):
        return None
AREA = (X0, 60, X0 + 4 * PITCH, 106)
clash = []
def scan(c):
    for k in c.get('Children', []):
        if not k['Name'].startswith('RS_Trk'):
            q = rect(k)
            if q and not (q[2] <= AREA[0] or q[0] >= AREA[2] or q[3] <= AREA[1] or q[1] >= AREA[3]) and (q[2] - q[0]) < 1300:
                clash.append((k['Name'], q))
        scan(k)
scan(tp)
print('controls overlapping the tracker area:', clash)
app.save()
# attachments card key: mandatory marker
L = 'ChildLegalScreen'
app.set(L, 'CL_DCAttachKey', 'Text', 'Parent.DisplayName & " *"', expect='Parent.DisplayName')
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
print('FINAL44 built; new controls:', len(made))
