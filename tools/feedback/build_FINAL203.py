#!/usr/bin/env python3
"""FINAL203 on FINAL202. locPrinting was created only by the old Print() button (UpdateContext({locPrinting: true})); FINAL202 replaced
that formula, so the context variable no longer existed and every rule that reads it failed (877 errors). It is now created by the
screen's OnVisible (false: the print geometry is the screen geometry since printing goes through the PDF)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV64', 'newV65'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
for scr in ('PrintVideoDetailScreen', 'PrintPodcastDetailScreen', 'PrintPhotoDetailScreen'):
    t = app.rule(scr, None, 'OnVisible')
    assert t.rstrip().endswith('UpdateContext({locPage: 1})'), t[-80:]
    n = t.rstrip()[:-len('UpdateContext({locPage: 1})')] + 'UpdateContext({locPage: 1, locPrinting: false, locPdfReady: false, locPdfPending: false, locAllPages: false, locPdfMode: ""})'
    app.set(scr, None, 'OnVisible', n, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL203 built')
