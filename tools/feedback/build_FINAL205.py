#!/usr/bin/env python3
"""FINAL205 on FINAL204. Download() only takes a web address, so "Download PDF" now sends the PDF to the flow in print mode:
the flow saves a copy in AVCDPrints with a view-only link and the app opens it in a new browser tab (print / save there).
Needs the flow AVCD_SavePrintPDF 1.0.0.1 (optional input Mode) and a refresh of the flow in Studio."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV66', 'newV67'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)
GO = ('// the flow keeps a copy in AVCDPrints and returns a view-only link: the browser tab offers Print and Save\n'
      'Notify("Preparing the PDF for download...", NotificationType.Information);\n'
      'IfError(\n'
      '    With(\n'
      '        {r: AVCD_SavePrintPDF.Run(varPrintPdfName, {name: varPrintPdfName, contentBytes: varPrintPdf}, {mode: "print"})},\n'
      '        If(\n'
      '            r.status = "saved" And Not(IsBlank(r.fileurl)),\n'
      '            Launch(r.fileurl),\n'
      '            Notify(Coalesce(r.message, "The PDF could not be prepared for download."), NotificationType.Error)\n'
      '        )\n'
      '    ),\n'
      '    Notify("The PDF could not be prepared for download: " & FirstError.Message, NotificationType.Error)\n'
      ')')
for scr, p in (('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD'), ('PrintPhotoDetailScreen', 'PPD')):
    setp(scr, f'{p}_PdfDownload', 'OnSelect', GO)
    setp(scr, f'{p}_PdfDownload', 'Tooltip', '"Opens the PDF in a new browser tab, where you can print it or save it on your computer"')
    setp(scr, f'{p}_PdfText', 'Text', app.rule(scr, f'{p}_PdfText', 'Text').replace('  -  Download PDF saves it on your computer', '  -  Download PDF opens it in a new tab to print or save'))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL205 built')
