#!/usr/bin/env python3
"""FINAL76 on FINAL75: the Validations checklist read files from attachment controls on other screens (CL_DCAttachValue on Legal & Docs,
CI_PodcastVisual on Info). Those controls only hold the item's files once their screen has been opened and has re-read the record,
so a request opened straight on Validations (e.g. a Podcast in Processing) showed 'Legal annexes ... empty' and 'Podcast visual ... not
attached' although the files are in SharePoint. The three file checks (legal annexes, podcast visual, VTT) now also pass when the
SharePoint record (varAttachRecord, loaded at the top of the same OnVisible / refresh) holds a matching file."""
import datetime, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG65', 'newG66'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
CV = 'ChildValidScreen'
IMG = 'EndsWith(Lower(DisplayName), ".jpg") Or EndsWith(Lower(DisplayName), ".jpeg") Or EndsWith(Lower(DisplayName), ".png")'
AUD = 'EndsWith(Lower(DisplayName), ".mp3") Or EndsWith(Lower(DisplayName), ".wav") Or EndsWith(Lower(DisplayName), ".m4a") Or EndsWith(Lower(DisplayName), ".aac")'
LEGAL = f'varChildMediaType <> "Podcast" Or (Not(StartsWith(DisplayName, "EpisodeVisual_")) And Not({IMG}) And Not({AUD}))'
REPL = [
    ('Pass: CountRows(CL_DCAttachValue.Attachments) > 0,',
     f'Pass: CountRows(CL_DCAttachValue.Attachments) > 0 Or CountRows(Filter(varAttachRecord.Attachments, {LEGAL})) > 0,'),
    ('CountRows(Filter(CI_PodcastVisual.Attachments, EndsWith(Lower(Name), ".jpg") Or EndsWith(Lower(Name), ".jpeg") Or EndsWith(Lower(Name), ".png"))) > 0',
     'CountRows(Filter(CI_PodcastVisual.Attachments, EndsWith(Lower(Name), ".jpg") Or EndsWith(Lower(Name), ".jpeg") Or EndsWith(Lower(Name), ".png"))) > 0 '
     f'Or CountRows(Filter(varAttachRecord.Attachments, Not(StartsWith(DisplayName, "EpisodeVisual_")) And ({IMG}))) > 0'),
    ('CountRows(Filter(CL_DCAttachValue.Attachments, EndsWith(Lower(Name), ".vtt"))) > 0',
     'CountRows(Filter(CL_DCAttachValue.Attachments, EndsWith(Lower(Name), ".vtt"))) > 0 Or CountRows(Filter(varAttachRecord.Attachments, EndsWith(Lower(DisplayName), ".vtt"))) > 0'),
]
for ctl, prop in ((None, 'OnVisible'), ('CV_BtnRefresh', 'OnSelect')):
    t = app.rule(CV, ctl, prop); eol = '\r\n' if '\r\n' in t else '\n'; n = t
    for old, new in REPL:
        assert n.count(old) == 1, (ctl, old[:50], n.count(old))
        n = n.replace(old, new)
    app.set(CV, ctl, prop, n, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL76 built')
