#!/usr/bin/env python3
"""FINAL127 on FINAL126: the status chips of RequestManagementScreen (HomeChip*) have the same gap (10) between them, from All (X=619) to Rejected (ends at 1332)."""
import datetime, os, re, shutil
from payaml import App, find
SRC, NEW = 'newQ10', 'newQ11'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequestManagementScreen'
GAP = 10
# left to right, as they appear: All, Draft, Processing, Pending, Approved, Rejected
order = ['HomeChipAll', 'HomeChipDraft', 'HomeChipPublished', 'HomeChipSubmitted', 'HomeChipApproved', 'HomeChipRejected']
tp = app.doc(S)['TopParent']
x = int(app.rule(S, order[0], 'X'))
for nm in order:
    w = int(app.rule(S, nm, 'Width'))
    old = app.rule(S, nm, 'X')
    if old != str(x): app.set(S, nm, 'X', str(x), expect=old)
    print(f'{nm:20} X {old:>5} -> {x:>5}  (W {w}, ends {x + w})')
    x += w + GAP
assert x - GAP == 1332, x - GAP
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL127 built')
