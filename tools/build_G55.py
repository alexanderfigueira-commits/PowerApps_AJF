#!/usr/bin/env python3
"""FINAL65 on FINAL64: the Track flow status stepper on RequesDetailScreen becomes dynamic with only three steps:
  Draft - Processing - (Approval | Approved | Rejected | Pending)
The current step takes the colour of the status badge (Processing SlateBlue, Pending DarkKhaki, Approved DarkGreen, Rejected #F08080,
Draft grey); everything behind it is grey, what is still ahead is pale. The check mark shows only on Approved (a cross on Rejected).
Pending is shown as the outcome step (Draft - Processing - Pending). The fourth step, its label and the third connector are removed."""
import datetime, json, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG54', 'newG55'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
ST = 'Coalesce(varCurrentRequest.Status.Value, "Draft")'
CUR = f'Switch({ST}, "Processing", 2, "Pending", 3, "Rejected", 3, "Approved", 3, "Partially approved", 3, "Published", 3, 1)'
APPROVED = f'{ST} in ["Approved", "Partially approved", "Published"]'
GREY, LIGHT = 'RGBA(150, 155, 165, 1)', 'RGBA(215, 223, 240, 1)'
STCOL = (f'Switch({ST}, "Processing", RGBA(106, 90, 205, 1), "Pending", RGBA(189, 183, 107, 1), "Approved", RGBA(0, 100, 0, 1), '
         f'"Partially approved", RGBA(0, 100, 0, 1), "Published", RGBA(0, 100, 0, 1), "Rejected", RGBA(240, 128, 128, 1), {GREY})')
TIP = {1: '"Draft: the requestor prepares the request and adds the media files."',
       2: '"Processing: submitted and under review by Central Deposit."',
       3: f'Switch({ST}, "Approved", "Approved: the request was approved by Central Deposit.", "Partially approved", "Approved: the request was approved by Central Deposit.", "Published", "Approved: the request was approved by Central Deposit.", '
          f'"Rejected", "Rejected: the request was rejected, see the reviewer comment.", "Pending", "Pending: information needed, the request was sent back to the requestor.", "Approval: Central Deposit decides on the request.")'}
LBL3 = f'Switch({ST}, "Approved", "Approved", "Partially approved", "Approved", "Published", "Approved", "Rejected", "Rejected", "Pending", "Pending", "Approval")'
XT = {1: 563, 2: 658, 3: 753}       # circles (24 wide), centres 575 / 670 / 765
for i in (1, 2, 3):
    t = f'RS_Trk{i}'
    glyph = {1: '"1"', 2: '"2"', 3: f'If({CUR} = 3, If({APPROVED}, "✓", {ST} = "Rejected", "✕", "3"), "3")'}[i]
    app.set(S, t, 'Text', glyph, expect=app.rule(S, t, 'Text'))
    app.set(S, t, 'Fill', f'If({i} < {CUR}, {GREY}, {i} = {CUR}, {STCOL}, {LIGHT})', expect=app.rule(S, t, 'Fill'))
    app.set(S, t, 'Color', f'If({i} > {CUR}, RGBA(96, 104, 120, 1), RGBA(255, 255, 255, 1))', expect=app.rule(S, t, 'Color'))
    app.set(S, t, 'Tooltip', TIP[i], expect=app.rule(S, t, 'Tooltip'))
    app.set(S, t, 'X', str(XT[i]), expect=app.rule(S, t, 'X'))
    l = f'RS_TrkLbl{i}'
    app.set(S, l, 'Text', {1: '"Draft"', 2: '"Processing"', 3: LBL3}[i], expect=app.rule(S, l, 'Text'))
    app.set(S, l, 'Color', f'If({i} = {CUR}, RGBA(0, 18, 107, 1), RGBA(96, 104, 120, 1))', expect=app.rule(S, l, 'Color'))
    app.set(S, l, 'FontWeight', f'If({i} = {CUR}, FontWeight.Bold, FontWeight.Semibold)', expect=app.rule(S, l, 'FontWeight'))
    app.set(S, l, 'X', str(XT[i] + 12 - 47), expect=app.rule(S, l, 'X'))   # 95 wide, centred on the circle (+0.5 px)
for i, x in ((1, 591), (2, 686)):
    n = f'RS_TrkLine{i}'
    app.set(S, n, 'Fill', f'If({i} < {CUR}, {GREY}, {LIGHT})', expect=app.rule(S, n, 'Fill'))
    app.set(S, n, 'X', str(x), expect=app.rule(S, n, 'X'))
app.save()
# remove the fourth step, its label and the third connector (JSON + YAML mirror)
GONE = ('RS_Trk4', 'RS_TrkLbl4', 'RS_TrkLine3')
jp = [os.path.join(NEW, 'Controls', f) for f in os.listdir(f'{NEW}/Controls') if '"RequesDetailScreen"' in open(os.path.join(NEW, 'Controls', f), encoding='utf-8-sig').read()[:400]][0]
raw = open(jp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); crlf = b'\r\n' in raw
d = json.loads(raw.decode('utf-8-sig')); top = d['TopParent']
before = len(top['Children'])
top['Children'] = [c for c in top['Children'] if c['Name'] not in GONE]
assert before - len(top['Children']) == 3
out = json.dumps(d, ensure_ascii=False, indent=2)
open(jp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out.replace('\n', '\r\n') if crlf else out)
yp = f'{NEW}/Src/RequesDetailScreen.pa.yaml'
y = open(yp, 'rb').read().decode('utf-8'); eol = '\r\n' if '\r\n' in y else '\n'
L = y.split(eol)
for n in GONE:
    i = [k for k, l in enumerate(L) if l == f'      - {n}:'][0]
    j = i + 1
    while j < len(L) and (L[j].strip() == '' or len(L[j]) - len(L[j].lstrip()) > 6): j += 1
    del L[i:j]
open(yp, 'wb').write(eol.join(L).encode('utf-8'))
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL65 built')
