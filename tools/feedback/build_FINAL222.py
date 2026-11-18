#!/usr/bin/env python3
"""FINAL222 on FINAL221. The DG / Agency of a NEW request is filled in from the user's Microsoft 365 Department
(Office365Users.MyProfile().Department, already read into varUserDept): the DG code is the first word of the department
("COMM.B.3" -> COMM, "DG COMM.B.3" -> COMM) and the DG choice that carries that code as a word is picked ("DG COMM", "COMM",
"COMM - Communication", "Communication (COMM)"). When the department gives no DG, the code in brackets of the display name is
tried ("SURNAME Name (COMM-EXT)" -> COMM). Nothing is picked when neither matches. The field stays editable; existing requests
keep their DG."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV83', 'newV84'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))


def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)


RS = 'RequesDetailScreen'
NORM = 'Trim(Upper(Substitute(Substitute(Substitute(Substitute(Substitute(Substitute(%s, ".", " "), "-", " "), "(", " "), ")", " "), "/", " "), ",", " ")))'
anchor = 'If(Coalesce(varCurrentRequest.ID, 0) <= 0 And Not(varMeIsExt) And Not(IsBlank(varMeContact.Mail)), Set(varRequestOwnerContact, varMeContact.DisplayName));\n'
ins = '''// the DG / Agency of a NEW request comes from the Microsoft 365 Department ("COMM.B.3" -> the DG choice carrying the word COMM,
// e.g. "DG COMM"); when the department gives no DG, the code in brackets of the display name is tried ("SURNAME Name (COMM-EXT)").
// Nothing is picked when neither matches; the field stays editable and an existing request keeps its DG.
Set(
    varUserDG,
    With(
        {
            dgs: ForAll(Choices('AV-CD-Requests'.DG) As c, {Value: c.Value, Key: " " & %(normc)s & " "}),
            codes: ForAll(
                Table(
                    {s: Coalesce(varUserDept, "")},
                    {s: With({n: Coalesce(varMeContact.DisplayName, "")}, If(Find("(", n) > 0, Mid(n, Find("(", n) + 1), ""))}
                ) As t,
                {Code: With({w: Split(%(norms)s, " ")}, If(First(w).Value = "DG" And CountRows(w) > 1, Index(w, 2).Value, First(w).Value))}
            )
        },
        Coalesce(
            First(Filter(dgs, Not(IsBlank(First(codes).Code)) And (" " & First(codes).Code & " ") in Key)).Value,
            First(Filter(dgs, Not(IsBlank(Last(codes).Code)) And (" " & Last(codes).Code & " ") in Key)).Value,
            ""
        )
    )
);
If(Coalesce(varCurrentRequest.ID, 0) <= 0 And Coalesce(varRequestDG, "") = "" And varUserDG <> "", Set(varRequestDG, varUserDG));
''' % {'normc': NORM % 'c.Value', 'norms': NORM % 'Coalesce(t.s, "")'}
ov = app.rule(RS, None, 'OnVisible'); assert ov.count(anchor) == 1
app.set(RS, None, 'OnVisible', ov.replace(anchor, anchor + ins), expect=ov)
setp(RS, 'HomeFilterDG', 'Tooltip',
     'If(\n    Not(varRequestorLocked) And Coalesce(varUserDG, "") <> "" And HomeFilterDG.Selected.Value = varUserDG,\n'
     '    "Filled in from your department in Microsoft 365 (" & varUserDept & "). You can change it.",\n    ""\n)')

app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL222 built')
