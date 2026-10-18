#!/usr/bin/env python3
"""FINAL123 on FINAL122: the status flow at the top of the request (RS_Trk1..3 / RS_TrkLbl1..3).
Step 2 is called "Analysis" and covers both Processing and Pending (Pending was shown under step 3, Approval). Its tooltip (circle and label) gives the real status.
Step 3 is Approval for Approved / Rejected only."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newQ6', 'newQ7'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
D = 'RequesDetailScreen'
eol = lambda t: '\r\n' if '\r\n' in t else '\n'
walk = lambda n: [n] + [x for c in n.get('Children', []) for x in walk(c)]
MAP_OLD = '"Processing", 2, "Pending", 3,'
MAP_NEW = '"Processing", 2, "Pending", 2,'
n = 0
for c in walk(app.doc(D)['TopParent']):
    if not c['Name'].startswith(('RS_Trk',)): continue
    for r in c['Rules']:
        t = r['InvariantScript']
        if MAP_OLD in t:
            app.set(D, c['Name'], r['Property'], t.replace(MAP_OLD, MAP_NEW), expect=t); n += 1
assert n == 15, n
t = app.rule(D, 'RS_TrkLbl2', 'Text'); assert t == '"Processing"'
app.set(D, 'RS_TrkLbl2', 'Text', '"Analysis"', expect=t)
TIP = '''With(
    {st: Coalesce(varCurrentRequest.Status.Value, "Draft")},
    Switch(
        st,
        "Processing", "Analysis · status: Processing. Submitted and under review by Central Deposit.",
        "Pending", "Analysis · status: Pending. Information needed, the request was sent back to the requestor.",
        "Analysis: Central Deposit reviews the request (status Processing) or asks the requestor for information (status Pending)."
    )
)'''
for ctl in ('RS_Trk2', 'RS_TrkLbl2'):
    t = app.rule(D, ctl, 'Tooltip')
    app.set(D, ctl, 'Tooltip', TIP.replace('\n', eol(t)), expect=t)
# step 3: Approval is for Approved / Rejected; Pending belongs to step 2
t = app.rule(D, 'RS_Trk3', 'Tooltip')
old = '            "Pending", "Pending: information needed, the request was sent back to the requestor.",\n'
assert t.count(old.replace('\n', eol(t))) == 1
app.set(D, 'RS_Trk3', 'Tooltip', t.replace(old.replace('\n', eol(t)), ''), expect=t)
t = app.rule(D, 'RS_TrkLbl3', 'Text'); old = '"Rejected", "Rejected", "Pending", "Pending", "Approval")'
assert t.count(old) == 1
app.set(D, 'RS_TrkLbl3', 'Text', t.replace(old, '"Rejected", "Rejected", "Approval")'), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL123 built')
