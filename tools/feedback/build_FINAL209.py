#!/usr/bin/env python3
"""FINAL209 on FINAL208. Once the PDF of a request has been exported (Print in the preview), the button of the print sheet reads
"Download PDF" and opens the pop-up with the download link; the pop-up also offers "New preview" to build a fresh PDF.
Applies to the three print sheets (Video, Podcast, Photo); kept for the session (global variables)."""
import datetime, os, re, shutil
from payaml import App, find
from hp_common import Builder
SRC, NEW = 'newV70', 'newV71'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)
DONE = '(Not(IsBlank(varPrintPdfUrl)) And varPrintPdfFor = varPrintRequest.RequestNumber)'
SAVED = 'Coalesce(locPdfReady, false) And locPdfMode = "saved"'
for scr, p in (('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD'), ('PrintPhotoDetailScreen', 'PPD')):
    preview = app.rule(scr, f'{p}_BtnPrint', 'OnSelect')
    assert 'locPdfMode: "view"' in preview
    # the button: Preview Print until a PDF of this request has been exported, then Download PDF
    setp(scr, f'{p}_BtnPrint', 'Text', f'If({DONE}, "⬇  Download PDF", "🔍  Preview Print")')
    setp(scr, f'{p}_BtnPrint', 'OnSelect', f'If(\n    {DONE},\n    // already exported: the pop-up with the download link\n    UpdateContext({{locPdfMode: "saved", locPdfReady: true}}),\n    {preview.strip()}\n)')
    setp(scr, f'{p}_BtnPrint', 'Tooltip', f'If({DONE}, "Shows the link of the PDF you exported", "Shows one PDF with all the media files of this request; print it from the preview")')
    # export remembers which request it belongs to
    sv = app.rule(scr, f'{p}_PdfDownload', 'OnSelect')
    setp(scr, f'{p}_PdfDownload', 'OnSelect', sv.replace('Set(varPrintPdfUrl, r.fileurl);',
         'Set(varPrintPdfUrl, r.fileurl);\n            Set(varPrintPdfFor, varPrintRequest.RequestNumber);\n            Set(varPrintPdfSavedName, varPrintPdfName);'))
    assert 'varPrintPdfFor' in app.rule(scr, f'{p}_PdfDownload', 'OnSelect')
    setp(scr, f'{p}_PdfText', 'Text', app.rule(scr, f'{p}_PdfText', 'Text').replace('"The PDF is ready: " & varPrintPdfName', '"The PDF is ready: " & Coalesce(varPrintPdfSavedName, varPrintPdfName)'))
    # pop-up buttons: New preview | Close | Open / download
    setp(scr, f'{p}_PdfClose', 'X', 'If(locPdfMode = "view", 1166, 607)')
    setp(scr, f'{p}_PdfClose', 'Width', 'If(locPdfMode = "view", 160, 120)')
    setp(scr, f'{p}_PdfOpen', 'X', '737'); setp(scr, f'{p}_PdfOpen', 'Width', '196')
    b = Builder(app, scr)
    b.clone(f'{p}_PdfNewPreview', scr, f'{p}_PdfClose', {'Text': '"New preview"', 'X': '447', 'Y': '400', 'Width': '150', 'Height': '50',
            'Visible': SAVED, 'OnSelect': preview.strip(), 'Tooltip': '"Build a new PDF of this request (for example after changes)"'})
    b.save()
    tp = app.doc(scr)['TopParent']
    z = lambda n: int(([x['InvariantScript'] for x in n['Rules'] if x['Property'] == 'ZIndex'] or ['0'])[0])
    [x for x in find(tp, f'{p}_PdfNewPreview')['Rules'] if x['Property'] == 'ZIndex'][0]['InvariantScript'] = str(max(z(n) for n in tp['Children']) + 1)
    app.save()
p_ = f'{NEW}/Properties.json'
raw = open(p_, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
t = re.sub(r'("button"\s*:\s*)(\d+)', lambda mm: mm.group(1) + str(int(mm.group(2)) + 3), t, count=1)
open(p_, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL209 built')
