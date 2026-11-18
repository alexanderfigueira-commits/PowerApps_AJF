#!/usr/bin/env python3
"""FINAL229 on FINAL228. DG / Agency of a NEW request (COMM user -> "COMM - Communication") was still empty.
- The DG code is now read with plain text functions (first word of the department, a leading "DG " dropped: "COMM.B.3" -> COMM)
  and looked up in the DG choices with LookUp (the word COMM in "COMM - Communication"); the code in brackets of the display
  name stays the fallback.
- The dropdown's Default proposes that DG itself while a new request has no DG yet, so it no longer depends on the order in
  which OnVisible, Reset and the dropdown's OnChange run; the end of OnVisible also takes it instead of the dropdown's (empty) choice."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV90', 'newV91'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))


def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)


def rep(scr, ctl, prop, old, new, count=1):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    assert t.count(old) == count, (scr, ctl, prop, t.count(old), old[:80])
    app.set(scr, ctl, prop, t.replace(old, new), expect=t)


RS = 'RequesDetailScreen'
NORM = 'Trim(Upper(Substitute(Substitute(Substitute(Substitute(Substitute(Substitute(%s, ".", " "), "-", " "), "(", " "), ")", " "), "/", " "), ",", " ")))'
ov = app.rule(RS, None, 'OnVisible')
i = ov.index('// the DG / Agency of a NEW request')
j = ov.index('Set(varRequestDG, varUserDG));', i) + len('Set(varRequestDG, varUserDG));')
paren = 'With({n: Coalesce(User().FullName, "")}, If(Find("(", n) > 0, Mid(n, Find("(", n) + 1), ""))'
new_block = f'''// the DG / Agency of a NEW request comes from the Microsoft 365 Department: its first word, a leading "DG " dropped
// ("COMM.B.3" -> COMM), is looked up as a word of the DG choices ("COMM - Communication"); when the department gives no DG, the
// code in brackets of the display name is tried ("SURNAME Name (COMM-EXT)"). Nothing is picked when neither matches.
Set(
    varUserDG,
    With(
        {{
            d: With({{x: {NORM % 'Coalesce(varUserDept, "")'}}}, If(StartsWith(x, "DG "), Mid(x, 4), x)),
            p: With({{x: {NORM % paren}}}, If(StartsWith(x, "DG "), Mid(x, 4), x))
        }},
        With(
            {{dc: Left(d, Find(" ", d & " ") - 1), pc: Left(p, Find(" ", p & " ") - 1)}},
            Coalesce(
                If(dc <> "", LookUp(Choices('AV-CD-Requests'.DG), (" " & dc & " ") in (" " & {NORM % 'Value'} & " ")).Value),
                If(pc <> "", LookUp(Choices('AV-CD-Requests'.DG), (" " & pc & " ") in (" " & {NORM % 'Value'} & " ")).Value),
                ""
            )
        )
    )
);
If(Coalesce(varCurrentRequest.ID, 0) <= 0 And Coalesce(varRequestDG, "") = "" And varUserDG <> "", Set(varRequestDG, varUserDG));'''
nov = ov[:i] + new_block + ov[j:]
old_end = '''If(

    IsBlank(varRequestDG) Or varRequestDG = "",

    Set(varRequestDG, HomeFilterDG.Selected.Value)'''
assert nov.count(old_end) == 1, nov.count(old_end)
nov = nov.replace(old_end, '''If(

    IsBlank(varRequestDG) Or varRequestDG = "",

    // a new request: the DG found from the department (FINAL229), else what the dropdown shows
    Set(varRequestDG, Coalesce(If(Coalesce(varCurrentRequest.ID, 0) <= 0, varUserDG), HomeFilterDG.Selected.Value))''')
app.set(RS, None, 'OnVisible', nov, expect=ov)
setp(RS, 'HomeFilterDG', 'Default',
     '// a new request without a DG yet proposes the DG of the user\'s department (FINAL229)\n'
     'If(Coalesce(varCurrentRequest.ID, 0) <= 0 And Coalesce(varRequestDG, "") = "", varUserDG, varRequestDG)')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL229 built')
