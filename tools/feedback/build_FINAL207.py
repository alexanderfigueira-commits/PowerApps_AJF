#!/usr/bin/env python3
"""FINAL207 on FINAL206. One button on the print sheet: "Preview Print" (the single PDF with all pages, on screen).
Inside the preview, "Print" saves the PDF in the background through the flow (administrators and requestors alike) and a
pop-up shows the download link ("Open / download" + the link itself). Background-print is removed."""
import datetime, os, re, shutil
from payaml import App, find, block_span
from hp_common import Builder
SRC, NEW = 'newV68', 'newV69'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)
def delete(scr, name):
    tp = app.doc(scr)['TopParent']
    n0 = len(tp['Children']); tp['Children'] = [c for c in tp['Children'] if c['Name'] != name]; assert len(tp['Children']) == n0 - 1, name
    app.save()
    yf = f'{NEW}/Src/{scr}.pa.yaml'; L = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
    s, e = block_span(L, name); del L[s:e]; open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(L))
SAVE = ('// saved in the background by the flow (every user); the pop-up gives the download link\n'
        'Notify("Saving the PDF...", NotificationType.Information);\n'
        'IfError(\n'
        '    With(\n'
        '        {r: AVCD_SavePrintPDF.Run(varPrintPdfName, {name: varPrintPdfName, contentBytes: varPrintPdf})},\n'
        '        If(\n'
        '            r.status = "saved" And Not(IsBlank(r.fileurl)),\n'
        '            Set(varPrintPdfUrl, r.fileurl);\n'
        '            UpdateContext({locPdfMode: "saved"}),\n'
        '            Notify(Coalesce(r.message, "The PDF could not be saved."), NotificationType.Error)\n'
        '        )\n'
        '    ),\n'
        '    Notify("The PDF could not be saved: " & FirstError.Message, NotificationType.Error)\n'
        ')')
SAVED = 'Coalesce(locPdfReady, false) And locPdfMode = "saved"'
for scr, p in (('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD'), ('PrintPhotoDetailScreen', 'PPD')):
    # print sheet: one button
    setp(scr, f'{p}_BtnPrint', 'Text', '"🔍  Preview Print"')
    setp(scr, f'{p}_BtnPrint', 'X', '1166'); setp(scr, f'{p}_BtnPrint', 'Width', '168')
    setp(scr, f'{p}_BtnPrint', 'Tooltip', '"Shows one PDF with all the media files of this request; print it from the preview"')
    delete(scr, f'{p}_BtnBgPrint')
    # preview bar: Print = background save + link
    setp(scr, f'{p}_PdfDownload', 'Text', '"🖨  Print"')
    setp(scr, f'{p}_PdfDownload', 'OnSelect', SAVE)
    setp(scr, f'{p}_PdfDownload', 'Tooltip', '"Saves the PDF and gives you the link to download or print it"')
    setp(scr, f'{p}_PdfText', 'Text', ('If(\n    locPdfMode = "view",\n'
          '    varPrintPdfName & "  ·  " & RoundUp(CountRows(colPrintReqMedia) / 2, 0) & If(RoundUp(CountRows(colPrintReqMedia) / 2, 0) = 1, " page", " pages") & "  -  Print saves it and gives you the download link",\n'
          '    "The PDF is ready: " & varPrintPdfName\n)'))
    setp(scr, f'{p}_PdfText', 'Height', 'If(locPdfMode = "view", 44, 44)')
    setp(scr, f'{p}_PdfOpen', 'Text', '"Open / download"')
    setp(scr, f'{p}_PdfOpen', 'Width', '170'); setp(scr, f'{p}_PdfOpen', 'X', '763')
    setp(scr, f'{p}_PdfClose', 'X', 'If(locPdfMode = "view", 1166, 583)')
    b = Builder(app, scr)
    b.clone(f'{p}_PdfLink', scr, f'{p}_PdfClose', {'Visible': SAVED, 'X': '447', 'Y': '346', 'Width': '472', 'Height': '46', 'Size': '10',
            'Text': 'varPrintPdfUrl', 'Color': 'RGBA(56, 96, 178, 1)', 'Underline': 'true', 'OnSelect': 'Launch(varPrintPdfUrl)',
            'Fill': 'RGBA(0, 0, 0, 0)', 'HoverFill': 'RGBA(240, 244, 250, 1)', 'BorderThickness': '0', 'Align': 'Align.Left',
            'Tooltip': '"Open the PDF in a new tab to download or print it"'})
    b.save()
    tp = app.doc(scr)['TopParent']
    z = lambda n: int(([x['InvariantScript'] for x in n['Rules'] if x['Property'] == 'ZIndex'] or ['0'])[0])
    [x for x in find(tp, f'{p}_PdfLink')['Rules'] if x['Property'] == 'ZIndex'][0]['InvariantScript'] = str(max(z(n) for n in tp['Children']) + 1)
    app.save()
p_ = f'{NEW}/Properties.json'
raw = open(p_, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
for k, d in (('button', 0),):
    t = re.sub(r'("%s"\s*:\s*)(\d+)' % k, lambda mm: mm.group(1) + str(int(mm.group(2)) + d), t, count=1)
open(p_, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL207 built')
