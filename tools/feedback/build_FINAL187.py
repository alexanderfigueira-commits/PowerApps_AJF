#!/usr/bin/env python3
"""FINAL187 on FINAL186. FB-09: the six contract cases carry the names of the metadata documents (one list for all production types). The stored text keeps the 'Case n' prefix the logic reads."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV48', 'newV49'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
L = 'ChildLegalScreen'
OLD = ['Case 1 - framework / direct service contract', 'Case 2 - specific service contract', 'Case 3 - co-production agreement',
       'Case 4 - acquisition of existing material', 'Case 5 - internal EU production', 'Case 6 - donation / free licence']
NEWN = ['Case 1: Media produced via a direct or framework service contract', 'Case 2: Media produced via a direct service contract',
        'Case 3: Media produced within a low value contract', 'Case 4: Media from a third party with exclusive rights',
        'Case 5: Media from a third party with non-exclusive rights', 'Case 6: Media produced in-house by an official or contractual agent']
def swap(t):
    for o, n in zip(OLD, NEWN):
        assert o in t, o
        t = t.replace(o, n)
    return t
t = app.rule(L, 'CL_Case', 'Items'); app.set(L, 'CL_Case', 'Items', swap(t), expect=t)
t = app.rule(L, None, 'OnVisible')
assert t.count(OLD[0]) == 1
app.set(L, None, 'OnVisible', t.replace(OLD[0], NEWN[0]), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL187 built'); print(*NEWN, sep='\n')
