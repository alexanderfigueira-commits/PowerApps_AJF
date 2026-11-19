#!/usr/bin/env python3
"""FINAL180 on FINAL179 - accessibility, part 2 of 3: the controls a person really operates get a tab stop and a visible focus.
Help links (6 labels with Launch), the six refresh icons of the dashboards, Save draft / Add media / Back to the review queue (icons without a TabIndex), the review queue row
icon (Icon1): TabIndex 0. The same labels and refresh icons, and the print list's row chevron: FocusedBorderThickness 2 (it was 0, so keyboard focus was invisible).
Left as they are (reported by the checker, deliberately): pop-up shades and the template / list rows' helper controls (a second tab stop per row or one for a click-away layer
would make keyboard use worse), the 15 empty 'Menu_Panel' buttons (panel backgrounds), galleries (their rows hold the controls that take focus)."""
import datetime, os, re, shutil
from payaml import App
from acc_common import *
SRC, NEW = 'newV41', 'newV42'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
TAB_FOCUS = [('HelpScreen', c) for c in ('HL_Link1', 'HL_Link2', 'HL_Link3', 'HL_Link3_1', 'HL_SupportMail', 'HL_SupportVideo')] + \
            [('Dashboard-Ope-Administrator', f'DOA_List{i}Refresh') for i in (1, 2, 3)] + \
            [('Dashboard-Ope-Requestor', f'DOR_List{i}Refresh') for i in (1, 2, 3)]
TAB_ONLY = [('RequesDetailScreen', c) for c in ('BackButton_ReviewScreen', 'SaveButton', 'addMediaItem')] + [('ReviewScreen', 'Icon1')]
FOCUS_ONLY = [('HomePrintScreen', 'HP_RowChevron')]
for scr, ctl in TAB_FOCUS + TAB_ONLY:
    old = put_rule(app, scr, ctl, 'TabIndex', '0')
    assert old.strip() in ('', '-1'), (ctl, old)
for scr, ctl in TAB_FOCUS + FOCUS_ONLY:
    node = find(app.doc(scr)['TopParent'], ctl)
    old = [r['InvariantScript'] for r in node['Rules'] if r['Property'] == 'FocusedBorderThickness']
    assert old and old[0].strip() == '0', (ctl, old)
    put_rule(app, scr, ctl, 'FocusedBorderThickness', '2')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL180 built:', len(TAB_FOCUS + TAB_ONLY), 'tab stops,', len(TAB_FOCUS + FOCUS_ONLY), 'focus borders')
