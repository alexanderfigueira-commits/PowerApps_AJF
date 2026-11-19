#!/usr/bin/env python3
"""FINAL210 on TEST_22 (= FINAL209 + the AV-CD-Exports library added as a data source in Studio).
When the print sheet opens, the app looks in AV-CD-Exports for the newest PDF of this request (file names start with the request
number). If there is one, the button reads "Download PDF" and opens the pop-up with its link, in any session and for every user;
"New preview" in the pop-up still builds a fresh PDF."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newT22', 'newV72'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
SITE = 'https://eceuropaeu.sharepoint.com/teams/GRP-EBSProductionForm'
FIND = ('// a PDF of this request already in AV-CD-Exports (newest first; file names start with the request number)\n'
        'With(\n'
        "    {f: First(Filter(Sort('AV-CD-Exports', Created, SortOrder.Descending), StartsWith('File name with extension', Coalesce(varPrintRequest.RequestNumber, \"§\") & \"_\")))},\n"
        '    If(\n'
        '        Not(IsBlank(f)),\n'
        f"        Set(varPrintPdfUrl, \"{SITE}/\" & f.'Full Path');\n"
        '        Set(varPrintPdfFor, varPrintRequest.RequestNumber);\n'
        "        Set(varPrintPdfSavedName, f.'File name with extension')\n"
        '    )\n'
        ');\n')
for scr in ('PrintVideoDetailScreen', 'PrintPodcastDetailScreen', 'PrintPhotoDetailScreen'):
    t = app.rule(scr, None, 'OnVisible')
    i = t.rindex('UpdateContext({locPage: 1')
    app.set(scr, None, 'OnVisible', t[:i] + FIND + t[i:], expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL210 built')
