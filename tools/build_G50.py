#!/usr/bin/env python3
"""FINAL60 on FINAL59: ChildValidScreen gets a validation row 'Legal annexes and supporting documents attached' that fails while
CL_DCAttachValue has no file, so Save Media names it in its error message instead of failing later on the required id."""
import datetime, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG49out', 'newG50'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
CV = 'ChildValidScreen'
MSG = 'Legal annexes and supporting documents is empty. Attach at least one file on the Legal & Docs tab.'
anchor = 'Case 1: both mandatory contracts confirmed", Pass: Left(varChildContractCase, 6) <> "Case 1" Or (varDocFramework And varDocSpecific), Note: "Confirm the signed framework and specific contracts on the Legal & Docs tab."},'
anchor_ml = None
doc = app.doc(CV)
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
hits = 0
for c in list(walk(doc['TopParent'])):
    for r in c['Rules']:
        s = r['InvariantScript']
        if 'Case 1: both mandatory contracts confirmed' not in s: continue
        n = s.replace('\r\n', '\n')
        m = re.search(r'(\{Check: "Case 1: both mandatory contracts confirmed",\s*Pass: [^\n]*?(?:\n\s*Note: "[^"]*"|, Note: "[^"]*")\},)', n)
        if not m: sys.exit('! anchor row not found in ' + c['Name'])
        row = m.group(1)
        sep = '\n' + re.match(r'[ \t]*', n[n.rfind('\n', 0, m.start()) + 1:m.start()]).group(0) if '\n' in row else ' '
        new_row = '{Check: "Legal annexes and supporting documents attached", Pass: CountRows(CL_DCAttachValue.Attachments) > 0, Note: "' + MSG + '"},'
        n = n.replace(row, row + sep + new_row, 1)
        app.set(CV, c['Name'] if c['Name'] != CV else None, r['Property'], n.replace('\n', '\r\n') if '\r\n' in s else n, expect=s)
        hits += 1
print('rows added:', hits); assert hits == 2
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL60 built')
