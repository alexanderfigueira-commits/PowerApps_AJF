#!/usr/bin/env python3
"""FINAL214 on FINAL213. One PDF per request in AV-CD-Exports, replaced by every new export:
- the file name no longer carries the time ("<request>_<type>.pdf"), so Print after "New preview" overwrites the same file
  (SharePoint keeps the previous one as an older version);
- the lookup takes the most recently modified file of the request;
- the link is opened with a cache-busting parameter, so the browser never shows a stale copy."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV75', 'newV76'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def edit(scr, ctl, prop, fn):
    t = app.rule(scr, ctl, prop); n = fn(t); assert n != t, (scr, ctl, prop)
    app.set(scr, ctl, prop, n, expect=t)
OPEN = 'Launch(varPrintPdfUrl & "?v=" & Text(Now(), "yyyymmddhhmmss"))'
for scr, p, typ in (('PrintVideoDetailScreen', 'PVD', 'Video'), ('PrintPodcastDetailScreen', 'PPoD', 'Podcast'), ('PrintPhotoDetailScreen', 'PPD', 'Photo')):
    old_name = f'Set(varPrintPdfName, Coalesce(varPrintRequest.RequestNumber, "request") & "_{typ}_" & Text(Now(), "yyyymmdd-hhmm") & ".pdf");'
    new_name = f'// one file per request: a new export replaces it\n    Set(varPrintPdfName, Coalesce(varPrintRequest.RequestNumber, "request") & "_{typ}.pdf");'
    edit(scr, f'{p}_PdfTimer', 'OnTimerEnd', lambda t: t.replace(old_name, new_name))
    edit(scr, None, 'OnVisible', lambda t: t.replace("Sort('AV-CD-Exports', Created, SortOrder.Descending)", "Sort('AV-CD-Exports', Modified, SortOrder.Descending)")
                                         .replace('(newest first;', '(most recently replaced first;'))
    for c in (f'{p}_PdfOpen', f'{p}_PdfLink'):
        edit(scr, c, 'OnSelect', lambda t: t.replace('Launch(varPrintPdfUrl)', OPEN))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL214 built')
