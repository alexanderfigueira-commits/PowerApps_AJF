#!/usr/bin/env python3
"""FINAL211 on FINAL210. No delegation warnings on the print sheets: the newest files of AV-CD-Exports are first loaded into a
collection with a delegable Sort (Created, newest first, up to the app's data row limit), then the request's PDF is looked up in
that collection (StartsWith on the file name is not delegable to SharePoint, so it now runs on the collection)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV72', 'newV73'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
OLD_C = "// a PDF of this request already in AV-CD-Exports (newest first; file names start with the request number)\nWith(\n    {f: First(Filter(Sort('AV-CD-Exports', Created, SortOrder.Descending), StartsWith("
NEW_C = ("// a PDF of this request already in AV-CD-Exports: the newest files are loaded with a delegable Sort, then looked up locally\n"
         "// (the file name cannot be filtered by SharePoint itself); file names start with the request number\n"
         "ClearCollect(colPrintExports, Sort('AV-CD-Exports', Created, SortOrder.Descending));\n"
         "With(\n    {f: First(Filter(colPrintExports, StartsWith(")
for scr in ('PrintVideoDetailScreen', 'PrintPodcastDetailScreen', 'PrintPhotoDetailScreen'):
    t = app.rule(scr, None, 'OnVisible')
    assert t.count(OLD_C) == 1, scr
    app.set(scr, None, 'OnVisible', t.replace(OLD_C, NEW_C), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL211 built')
