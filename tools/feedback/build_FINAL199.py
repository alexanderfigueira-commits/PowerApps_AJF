#!/usr/bin/env python3
"""FINAL199 on FINAL198. One PDF with all the media files of a request (first step).
Each print sheet (Video / Podcast / Photo) gets "PDF (all pages)": the gallery switches to all media files (one A4 landscape page each),
a timer lets it render, then PDF() turns it into one file kept in varPrintPdf / varPrintPdfName. A confirmation panel says it is ready.
The on-screen viewer (everyone) and "Save to AV-CD-Exports" (administrators, flow AVCD_SavePrintPDF) are added once the PDF viewer
control and the flow are in the app (they cannot be created from the file)."""
import copy, datetime, os, re, shutil
from payaml import App, find, _fmt
from hp_common import Builder
SRC, NEW = os.environ.get('SRC', 'newV60'), os.environ.get('NEW', 'newV61')
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)
# A4 landscape, 10 mm margins, 120 DPI: printable 10.9 x 7.48 in = 1309 x 898 px -> the 1302 px gallery fits the width, one row per page
PAGE_ROW = 896
CI = 'ChildInfoScreen'
for scr, p, typ in (('PrintVideoDetailScreen', 'PVD', 'Video'), ('PrintPodcastDetailScreen', 'PPoD', 'Podcast'), ('PrintPhotoDetailScreen', 'PPD', 'Photo')):
    ALL = 'Coalesce(locAllPages, false)'
    items = app.rule(scr, f'{p}_Gallery', 'Items'); ts = app.rule(scr, f'{p}_Gallery', 'TemplateSize')
    setp(scr, f'{p}_Gallery', 'Items', f'// "PDF (all pages)" shows every media file; otherwise the rows of this page\nIf({ALL}, colPrintReqMedia, {items.strip()})')
    setp(scr, f'{p}_Gallery', 'TemplateSize', f'// one A4 landscape page per media file in the PDF\nIf({ALL}, {PAGE_ROW}, {ts.strip()})')
    b = Builder(app, scr)
    b.clone(f'{p}_BtnPdfAll', scr, f'{p}_BtnPrint', {
        'Text': '"📄  PDF (all pages)"', 'X': '1018', 'Width': '178',
        'Visible': 'Not(locPrinting) And Not(Coalesce(locPdfPending, false))',
        'Tooltip': '"One PDF with all the media files of this request (one page each)"',
        'OnSelect': ('If(\n    IsEmpty(colPrintReqMedia),\n    Notify("This request has no media file to put in the PDF.", NotificationType.Warning),\n'
                     '    UpdateContext({locPdfReady: false, locAllPages: true, locPdfPending: true});\n'
                     '    Notify("Preparing one PDF with all the media files of this request...", NotificationType.Information)\n)')})
    GEN = (f'// the gallery now shows every media file (one page each): turn it into one PDF\n'
           f'IfError(\n'
           f'    Set(varPrintPdf, PDF({p}_Gallery, {{Size: PaperSize.A4, Orientation: PageOrientation.Landscape, Margin: "10mm", DPI: 120, ExpandContainers: true}}));\n'
           f'    Set(varPrintPdfName, Coalesce(varPrintRequest.RequestNumber, "request") & "_{typ}_" & Text(Now(), "yyyymmdd-hhmm") & ".pdf");\n'
           f'    UpdateContext({{locPdfReady: true}}),\n'
           f'    Notify("The PDF could not be generated: " & FirstError.Message, NotificationType.Error)\n'
           f');\n'
           f'UpdateContext({{locPdfPending: false, locAllPages: false}})')
    b.clone(f'{p}_PdfTimer', 'RequesDetailScreen', 'Timer1', {'AutoStart': 'false', 'Repeat': 'false', 'Duration': '1500', 'Visible': 'false',
            'OnTimerEnd': GEN, 'X': '0', 'Y': '0', 'Width': '10', 'Height': '10'})
    V = {'Visible': 'Coalesce(locPdfReady, false)'}
    b.clone(f'{p}_PdfShade', CI, 'CI_TplConfirmShade', dict(V))
    b.clone(f'{p}_PdfPanel', CI, 'CI_TplConfirmPanel', dict(V, Height='190'))
    b.clone(f'{p}_PdfText', CI, 'CI_TplConfirmText', dict(V, Height='96', Text=(
        '"The PDF is ready: " & varPrintPdfName & Char(10) & CountRows(colPrintReqMedia) & If(CountRows(colPrintReqMedia) = 1, " media file", " media files") & '
        '", one page each." & Char(10) & "On-screen view and saving are added in the next version."')))
    b.clone(f'{p}_PdfClose', CI, 'CI_TplConfirmCancel', dict(V, Text='"Close"', X='603', Y='400', Width='160', Height='50', Size='12',
            OnSelect='UpdateContext({locPdfReady: false})'))
    b.save()
    # Start rule on the timer (the donor has none)
    tp = app.doc(scr)['TopParent']; tm = find(tp, f'{p}_PdfTimer')
    r0 = [r for r in tm['Rules'] if r['Property'] == 'Repeat'][0]
    r1 = copy.deepcopy(r0); r1['Property'] = 'Start'; r1['InvariantScript'] = 'Coalesce(locPdfPending, false)'; tm['Rules'].append(r1)
    yf = f'{NEW}/Src/{scr}.pa.yaml'; L = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
    i0 = next(i for i, l in enumerate(L) if l == f'      - {p}_PdfTimer:')
    j = next(i for i in range(i0, len(L)) if L[i].startswith('            Repeat:'))
    L.insert(j + 1, '            Start: =Coalesce(locPdfPending, false)')
    open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(L))
    # the panel sits above everything
    def z(n):
        v = [x for x in n['Rules'] if x['Property'] == 'ZIndex']; return int(v[0]['InvariantScript']) if v else 0
    def deep(n):
        yield n
        for c in n.get('Children', []): yield from deep(c)
    NEWC = [f'{p}_PdfShade', f'{p}_PdfPanel', f'{p}_PdfText', f'{p}_PdfClose']
    mx = max(z(n) for n in deep(tp) if n['Name'] not in NEWC)
    for k, nm in enumerate(NEWC): [x for x in find(tp, nm)['Rules'] if x['Property'] == 'ZIndex'][0]['InvariantScript'] = str(mx + 1 + k)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL199 built')
