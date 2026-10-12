#!/usr/bin/env python3
"""FINAL83 on FINAL82: CL_DCAttach (Legal & Docs, Podcast) - hardening against "Field 'Id' is required" when files from several panels are merged.
 1. a new episode visual is saved as 'EpisodeVisual_<name>' but its Id was looked up by the bare <name>: with a podcast visual of the same name it
    took that file's Id (two records, one Id). The lookup now uses the name the file is saved under (f.pre & f.Name).
 2. which files are already in SharePoint (saved) and their Ids are read fresh from the media item, not from varAttachRecord, which can be a
    stale copy; a file already saved but missing from the stale copy used to go out as new with its name as Id.
 3. records without a file name are dropped, so no record can leave without an Id."""
import datetime, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG72', 'newG73'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'ChildLegalScreen'
t = app.rule(S, 'CL_DCAttach', 'Update'); eol = '\r\n' if '\r\n' in t else '\n'; n = t.replace('\r\n', '\n')
a = '    With(\n        {\n            podcast: varChildMediaType = "Podcast",\n            saved: varAttachRecord.Attachments.DisplayName,\n            here: CL_DCAttachValue.Attachments.Name\n        },\n'
assert n.count(a) == 1
b = ('    With(\n        // the media item as it is in SharePoint now (the form\'s copy, varAttachRecord, may be stale)\n'
     '        {rec: Coalesce(LookUp(\'AV-CD-Mediafiles\', ID = Coalesce(varCurrentChildSPId, 0)), varAttachRecord)},\n'
     '    With(\n        {\n            podcast: varChildMediaType = "Podcast",\n            saved: rec.Attachments.DisplayName,\n            here: CL_DCAttachValue.Attachments.Name\n        },\n')
n = n.replace(a, b)
old_rec = ('            {\n                DisplayName: f.pre & f.Name,\n                Id: Coalesce(LookUp(varAttachRecord.Attachments, DisplayName = f.Name).Id, f.pre & f.Name),\n                Value: f.Value\n            }\n')
assert n.count(old_rec) == 1
new_rec = ('            {\n                DisplayName: f.pre & f.Name,\n                Id: Coalesce(LookUp(rec.Attachments, DisplayName = f.pre & f.Name).Id, f.pre & f.Name),\n                Value: f.Value\n            }\n')
n = n.replace(old_rec, new_rec)
# drop nameless files before they are shaped
old_ug = '            ) As f,\n'
assert n.count(old_ug) == 1
# the Ungroup(...) result is filtered inside ForAll through the With below: wrap by Filter
assert n.rstrip().endswith('    )\n)')
n = n.rstrip()[:-len('\n)')] + '\n    )\n)'     # one more closing paren for the extra With
n = n.replace('        ForAll(\n            Ungroup(', '        ForAll(\n            Filter(Ungroup(', 1)
n = n.replace('                files\n            ) As f,\n', '                files\n            ), Not(IsBlank(Name))) As f,\n', 1)
assert n.count('Filter(Ungroup(') == 1 and n.count('), Not(IsBlank(Name))) As f,') == 1
# paren balance
def bal(s):
    s = re.sub(r'//[^\n]*', '', s); s = re.sub(r'"[^"]*"', '""', s)
    return s.count('(') - s.count(')')
assert bal(n) == 0 and bal(t.replace('\r\n', '\n')) == 0, (bal(n), bal(t))
app.set(S, 'CL_DCAttach', 'Update', n.replace('\n', eol), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL83 built')
