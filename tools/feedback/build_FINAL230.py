#!/usr/bin/env python3
"""FINAL230 on FINAL229. DG / Agency of a NEW request, the way the user asked: the DG choice that STARTS WITH the department
code is selected, else nothing (blank, to choose). The code is the department up to its first "." ("COMM.A.4.007" -> COMM, the
same text the header shows), so COMM and COMP are told apart; when that finds nothing, the first 3 characters are tried ("COM").
The dropdown's Default works it out itself from varUserDept (no dependency on the order of OnVisible, Reset and OnChange);
varUserDG (tooltip, OnVisible) uses the same expression."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV91', 'newV92'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))


def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)


RS = 'RequesDetailScreen'
DEP = 'Trim(Coalesce(varUserDept, ""))'
DG_EXPR = (f'With(\n'
           f'        {{dep: {DEP}, dgList: Sort(Choices(\'AV-CD-Requests\'.DG), Value, SortOrder.Ascending)}},\n'
           f'        With(\n'
           f'            {{k: Left(dep, Find(".", dep & ".") - 1)}},\n'
           f'            Coalesce(\n'
           f'                If(Len(k) >= 2, LookUp(dgList, StartsWith(Value, k)).Value),\n'
           f'                If(Len(dep) >= 3, LookUp(dgList, StartsWith(Value, Left(dep, 3))).Value),\n'
           f'                ""\n'
           f'            )\n'
           f'        )\n'
           f'    )')
ov = app.rule(RS, None, 'OnVisible')
i = ov.index('// the DG / Agency of a NEW request comes from the Microsoft 365 Department')
j = ov.index('If(Coalesce(varCurrentRequest.ID, 0) <= 0 And Coalesce(varRequestDG, "") = "" And varUserDG <> "", Set(varRequestDG, varUserDG));', i)
new_block = ('// the DG / Agency of a NEW request: the DG choice that starts with the department code (the department up to its first ".",\n'
             '// "COMM.A.4.007" -> COMM), else the one that starts with its first 3 characters, else nothing (to choose in the list)\n'
             f'Set(\n    varUserDG,\n    {DG_EXPR}\n);\n')
app.set(RS, None, 'OnVisible', ov[:i] + new_block + ov[j:], expect=ov)
setp(RS, 'HomeFilterDG', 'Default',
     '// a new request without a DG yet: the DG choice that starts with the department code (COMM.A.4.007 -> "COMM - Communication"),\n'
     '// else with its first 3 characters, else blank (FINAL230)\n'
     'If(\n'
     '    Coalesce(varCurrentRequest.ID, 0) <= 0 And Coalesce(varRequestDG, "") = "",\n'
     f'    {DG_EXPR},\n'
     '    varRequestDG\n'
     ')')
setp(RS, 'HomeFilterDG', 'Tooltip',
     'If(\n    varRequestorLocked,\n    "",\n'
     '    Coalesce(varUserDG, "") <> "" And HomeFilterDG.Selected.Value = varUserDG,\n'
     '    "Filled in from your department in Microsoft 365 (" & varUserDept & "). You can change it.",\n'
     '    Coalesce(varCurrentRequest.ID, 0) <= 0,\n'
     '    "Your department in Microsoft 365: " & If(IsBlank(varUserDept) Or varUserDept = "", "(empty)", varUserDept) & ". No DG / Agency starts with it: choose it in the list.",\n'
     '    ""\n)')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL230 built')
