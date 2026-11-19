#!/usr/bin/env python3
"""FINAL82 on FINAL81: with contract case 1 selected, in reading mode (varRequestorLocked: view-only or a request the user cannot edit) the
two mandatory contracts CL_ChkFramework and CL_ChkSpecific count as confirmed: varDocFramework / varDocSpecific are set true when the Legal & Docs
and Validations screens open, so the checkboxes show ticked and the 'Case 1: both mandatory contracts confirmed' check passes."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG71', 'newG72'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
ANCHOR = 'Set(varNavArm, "");\n'
ADD = ('// reading mode with contract case 1: the framework and specific contracts count as confirmed\n'
       'If(\n    varRequestorLocked And Left(varChildContractCase, 6) = "Case 1",\n    Set(varDocFramework, true);\n    Set(varDocSpecific, true)\n);\n')
for s in ('ChildLegalScreen', 'ChildValidScreen'):
    t = app.rule(s, None, 'OnVisible'); eol = '\r\n' if '\r\n' in t else '\n'
    n = t.replace('\r\n', '\n'); assert n.count(ANCHOR) == 1, s
    app.set(s, None, 'OnVisible', n.replace(ANCHOR, ANCHOR + ADD).replace('\n', eol), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL82 built')
