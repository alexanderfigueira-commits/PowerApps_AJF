#!/usr/bin/env python3
"""FINAL168 on FINAL167. Save Media's audit named "producer" as not kept on a Photo/Reportage.
The Producer box (CM_Producer) is only shown for Video and Podcast, but its OnChange stores Self.SelectedItems in varChildProducerSel whatever the type,
and a combo box with nothing selected can hold ONE record with every field blank (the box's own yellow-border rule already filters such records out).
Save Media then sent that blank record as a person ("i:0#.f|membership|" with no e-mail), which SharePoint drops. Fixed at the source and in Save Media:
 1. CM_Producer.OnChange keeps only selected entries that have a name or an e-mail;
 2. the Save Media Patch sends only entries that have an e-mail (a person column cannot be written without one) and nothing otherwise;
 3. the audit looks only at real entries and, when SharePoint did not keep them, names who was sent."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV29', 'newV30'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))

REAL = 'Not(IsBlank(Trim(Coalesce(DisplayName, "")))) Or Not(IsBlank(Trim(Coalesce(Mail, ""))))'
WITHMAIL = 'Not(IsBlank(Trim(Coalesce(Mail, ""))))'

# 1. the Producer box
M = 'ChildMetaScreen'
t = app.rule(M, 'CM_Producer', 'OnChange')
assert t == 'Set(varChildProducerSel, Self.SelectedItems); Set(varChildProducer, Concat(Self.SelectedItems, DisplayName, ", "))', t
app.set(M, 'CM_Producer', 'OnChange',
        f'// only real entries: a box with nothing selected can hold one record with every field blank\nSet(varChildProducerSel, Filter(Self.SelectedItems, {REAL})); Set(varChildProducer, Concat(Self.SelectedItems, DisplayName, ", "))', expect=t)

# 2 + 3. Save Media
V = 'ChildValidScreen'
t = app.rule(V, 'CV_BtnSaveArchive', 'OnSelect')
old = 'Producer: If(IsBlank(varChildProducerSel), Blank(), ForAll(varChildProducerSel As u, {Claims: "i:0#.f|membership|" & Lower(u.Mail), DisplayName: u.DisplayName, Email: u.Mail, Department: "", JobTitle: "", Picture: ""})),'
assert t.count(old) == 1
new = (f'Producer: If(IsEmpty(Filter(varChildProducerSel, {WITHMAIL})), Blank(), '
       f'ForAll(Filter(varChildProducerSel, {WITHMAIL}) As u, {{Claims: "i:0#.f|membership|" & Lower(u.Mail), DisplayName: u.DisplayName, Email: u.Mail, Department: "", JobTitle: "", Picture: ""}})),')
t = t.replace(old, new)
old = '{n: "producer", bad: Not(IsEmpty(varChildProducerSel)) And IsEmpty(chk.Producer)}'
assert t.count(old) == 1
sel = f'Filter(varChildProducerSel, {REAL})'
new = (f'{{n: "producer (sent: " & Concat({sel}, Coalesce(DisplayName, "?") & " <" & Coalesce(Mail, "no e-mail") & ">", "; ") & ")", '
       f'bad: Not(IsEmpty({sel})) And IsEmpty(chk.Producer)}}')
t = t.replace(old, new)
app.set(V, 'CV_BtnSaveArchive', 'OnSelect', t, expect=app.rule(V, 'CV_BtnSaveArchive', 'OnSelect'))

app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL168 built')
