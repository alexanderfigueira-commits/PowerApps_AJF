#!/usr/bin/env python3
"""FINAL26 on FINAL25: the checklist on ChildValidScreen says "media file" instead of "archive".

Texts changed (CV_ChecklistGallery rows come from colValidations, defined in OnVisible and in CV_BtnRefresh):
  "Archive title is provided"                       -> "Media file title is provided"
  "...This archive cannot be submitted."            -> "...This media file cannot be submitted."
  "FTP delivery path set on this archive (Photo only)" -> "... on this media file (Photo only)"   (the "(Photo only)" marker the gallery filter reads is kept)
  CV_OverallStatus: "Press Save archive to add ..." -> "Press Save Media to add ..."  (the button is "Save Media")
The "New archive" placeholder is data (other screens compare against it) and is left alone.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG15', 'newG16'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'ChildValidScreen'
PAIRS = [('"Archive title is provided"', '"Media file title is provided"'),
         ('This archive cannot be submitted.', 'This media file cannot be submitted.'),
         ('"FTP delivery path set on this archive (Photo only)"', '"FTP delivery path set on this media file (Photo only)"')]


def edit(ctl, prop, pairs):
    t = app.rule(S, ctl, prop)
    n = t
    for old, new in pairs:
        if n.count(old) != 1:
            sys.exit(f'! {ctl}.{prop}: {n.count(old)} x {old!r}')
        n = n.replace(old, new)
    app.set(S, ctl, prop, n, expect=t)


edit(None, 'OnVisible', PAIRS)
edit('CV_BtnRefresh', 'OnSelect', PAIRS)
edit('CV_OverallStatus', 'Text', [('Press Save archive to add to your request.', 'Press Save Media to add to your request.')])
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL26 built')
