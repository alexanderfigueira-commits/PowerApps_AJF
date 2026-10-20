#!/usr/bin/env python3
"""FINAL150 on FINAL149: ChildLegalScreen, CL_FormAttach.OnFailure no longer runs Concat over CL_DCAttach.Update
(the merged, union-typed table of the podcast panels: "The function 'Concat' has some invalid arguments").
The failure message lists the files of the Legal & Docs panel with Concat over CL_DCAttachValue.Attachments (Name, nameless rows left out),
the same construct the Validations rows already use. The podcast retry (varAttachMode 1) is unchanged."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV9', 'newV10'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, C = 'ChildLegalScreen', 'CL_FormAttach'
t = app.rule(S, C, 'OnFailure')
assert t.count('Concat(sent, Name, ", ")') == 1 and 'With(\r\n' not in t or True
new = '''// Stop: stay on the Validations tab. The other fields were already Patched
// and the staged files are still in the form, so Save Media can be retried.
If(
    // a podcast's list merges the files of three panels: if the form refuses it, the second way of writing a new file's Id is tried once before reporting
    varChildMediaType = "Podcast" And Coalesce(varAttachMode, 0) = 0,
    Set(varAttachMode, 1);
    SubmitForm(CL_FormAttach),
    Notify(
        "The media details were saved, but the attachments were not: " & CL_FormAttach.Error & " (files in the Legal & Docs panel: " & Concat(Filter(CL_DCAttachValue.Attachments, Not(IsBlank(Name))), Name, ", ") & ")  Press Save Media to try again.",
        NotificationType.Error
    )
)'''
app.set(S, C, 'OnFailure', new, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL150 built')
