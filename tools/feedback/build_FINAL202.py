#!/usr/bin/env python3
"""FINAL202 on TEST_21 (= FINAL199 + PdfViewer1 + flow AVCD_SavePrintPDF added by the user in Studio).
A. Re-applies FINAL200 (PaperOrientation) and FINAL201 (12 pt fields, darker labels, header card) as a property patch
   (every property changed from FINAL199 to FINAL201 is set on TEST_21 when TEST_21 still holds the FINAL199 value).
B. Print sheets:
   - "Print" (everyone): builds ONE PDF with all the media files of the request and shows it on screen (PDF viewer).
   - "Background-print" (administrators): builds the same PDF and saves it in AV-CD-Exports through the flow, without
     opening it; a panel confirms with the file name and an "Open file" button.
   - The "PDF (all pages)" button and the loose PdfViewer1 are removed; the page-by-page Print() is gone."""
import datetime, json, glob, os, re, shutil, sys
from payaml import App, find, block_span
from hp_common import Builder
SRC, NEW = 'newT21', 'newV64'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)
# ---------- A. patch FINAL199 -> FINAL201
def rules(tree):
    out = {}
    for f in glob.glob(f'{tree}/Controls/*.json'):
        j = json.load(open(f, encoding='utf-8-sig')); s = j['TopParent']['Name']
        def walk(n):
            out[(s, n['Name'])] = {x['Property']: x['InvariantScript'].replace('\r\n', '\n') for x in n['Rules']}
            for c in n.get('Children', []): walk(c)
        walk(j['TopParent'])
    return out
F199, F201 = rules('newV61'), rules('newV63')
applied = skipped = 0
for key, r201 in F201.items():
    r199 = F199.get(key)
    assert r199 is not None, key
    for prop, v in r201.items():
        if prop == 'ZIndex' or r199.get(prop) == v: continue
        scr, ctl = key
        cur = app.rule(scr, None if ctl == scr else ctl, prop)
        if cur is not None and cur.strip() == (r199.get(prop) or '').strip():
            app.set(scr, None if ctl == scr else ctl, prop, v, expect=cur); applied += 1
        else:
            skipped += 1; print('  skipped', key, prop)
print('FINAL200/201 patch: applied', applied, 'skipped', skipped)
app.save()
# ---------- B. Print / Background-print / viewer
def delete(scr, name):
    tp = app.doc(scr)['TopParent']
    def rm(n):
        before = len(n.get('Children', []))
        n['Children'] = [c for c in n.get('Children', []) if c['Name'] != name]
        if len(n['Children']) != before: return True
        return any(rm(c) for c in n['Children'])
    assert rm(tp), (scr, name)
    app.save()
    yf = f'{NEW}/Src/{scr}.pa.yaml'
    L = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
    s, e = block_span(L, name); del L[s:e]
    open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(L))
VIEW = 'Coalesce(locPdfReady, false) And locPdfMode = "view"'
SAVED = 'Coalesce(locPdfReady, false) And locPdfMode = "saved"'
START = ('If(\n    IsEmpty(colPrintReqMedia),\n    Notify("This request has no media file to put in the PDF.", NotificationType.Warning),\n'
         '    UpdateContext({{locPdfMode: "{mode}", locPdfReady: false, locAllPages: true, locPdfPending: true}});\n'
         '    Notify("{msg}", NotificationType.Information)\n)')
for scr, p, typ in (('PrintVideoDetailScreen', 'PVD', 'Video'), ('PrintPodcastDetailScreen', 'PPoD', 'Podcast'), ('PrintPhotoDetailScreen', 'PPD', 'Photo')):
    b = Builder(app, scr)
    b.clone(f'{p}_BtnBgPrint', scr, f'{p}_BtnPdfAll', {
        'Text': '"🗄  Background-print"',
        'Visible': 'varUserRole = "ADMINISTRATOR" And Not(locPrinting) And Not(Coalesce(locPdfPending, false))',
        'Tooltip': '"Save one PDF with all the media files of this request in AV-CD-Exports (administrators)"',
        'OnSelect': START.format(mode='save', msg='Saving one PDF with all the media files in AV-CD-Exports...')})
    b.clone(f'{p}_PdfView', 'PrintPodcastDetailScreen', 'PdfViewer1', {
        'Document': 'varPrintPdf', 'Zoom': 'Zoom.FitWidth', 'X': '40', 'Y': '64', 'Width': '1286', 'Height': '636',
        'Fill': 'RGBA(255, 255, 255, 1)', 'BorderColor': 'RGBA(186, 202, 226, 1)'})
    b.clone(f'{p}_PdfOpen', 'ChildInfoScreen', 'CI_TplConfirmOK', {
        'Text': '"Open file"', 'X': '773', 'Y': '400', 'Width': '160', 'Height': '50', 'Size': '12', 'Visible': SAVED,
        'DisplayMode': 'If(IsBlank(varPrintPdfUrl), DisplayMode.Disabled, DisplayMode.Edit)', 'OnSelect': 'Launch(varPrintPdfUrl)'})
    b.save()
    # the viewer is visible only in "view" mode (no Visible rule on the donor: added here)
    tp = app.doc(scr)['TopParent']; pv = find(tp, f'{p}_PdfView')
    import copy as _c
    vr = _c.deepcopy([r for r in pv['Rules'] if r['Property'] == 'DisplayMode'][0]); vr['Property'] = 'Visible'; vr['InvariantScript'] = VIEW
    pv['Rules'].append(vr); app.save()
    yf = f'{NEW}/Src/{scr}.pa.yaml'; L = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
    s, e = block_span(L, f'{p}_PdfView')
    j = next(i for i in range(s, e) if L[i].strip().startswith('Width:'))
    L.insert(j, ' ' * 12 + f'Visible: ={VIEW}')
    open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(L))
    # Print = the single PDF on screen
    setp(scr, f'{p}_BtnPrint', 'OnSelect', START.format(mode='view', msg='Preparing one PDF with all the media files of this request...'))
    setp(scr, f'{p}_BtnPrint', 'Visible', 'Not(locPrinting) And Not(Coalesce(locPdfPending, false))')
    setp(scr, f'{p}_BtnPrint', 'Tooltip', '"One PDF with all the media files of this request, shown on screen to print or save"') if app.rule(scr, f'{p}_BtnPrint', 'Tooltip') is not None else None
    # generation: view -> viewer; save -> flow, then confirmation
    GEN = (f'// the gallery now shows every media file (one A4 landscape page each): turn it into one PDF\n'
           f'IfError(\n'
           f'    Set(varPrintPdf, PDF({p}_Gallery, {{Size: PaperSize.A4, Orientation: PaperOrientation.Landscape, Margin: "10mm", DPI: 120, ExpandContainers: true}}));\n'
           f'    Set(varPrintPdfName, Coalesce(varPrintRequest.RequestNumber, "request") & "_{typ}_" & Text(Now(), "yyyymmdd-hhmm") & ".pdf");\n'
           f'    If(\n'
           f'        locPdfMode = "save",\n'
           f'        // administrators: saved in AV-CD-Exports by the flow (the flow checks the role again)\n'
           f'        With(\n'
           f'            {{r: AVCD_SavePrintPDF.Run(varPrintPdfName, {{name: varPrintPdfName, contentBytes: varPrintPdf}})}},\n'
           f'            If(\n'
           f'                r.status = "saved",\n'
           f'                Set(varPrintPdfUrl, r.fileurl);\n'
           f'                UpdateContext({{locPdfMode: "saved", locPdfReady: true}}),\n'
           f'                Notify(Coalesce(r.message, "The PDF was not saved in AV-CD-Exports."), NotificationType.Error)\n'
           f'            )\n'
           f'        ),\n'
           f'        // everyone: shown on screen\n'
           f'        UpdateContext({{locPdfReady: true}})\n'
           f'    ),\n'
           f'    Notify("The PDF could not be generated or saved: " & FirstError.Message, NotificationType.Error)\n'
           f');\n'
           f'UpdateContext({{locPdfPending: false, locAllPages: false}})')
    setp(scr, f'{p}_PdfTimer', 'OnTimerEnd', GEN)
    # overlay: shade for both modes; bottom bar (view) or centred panel (saved)
    ANY = 'Coalesce(locPdfReady, false)'
    setp(scr, f'{p}_PdfShade', 'Visible', ANY)
    for prop, v in (('Visible', ANY), ('X', 'If(locPdfMode = "view", 40, 423)'), ('Y', 'If(locPdfMode = "view", 706, 290)'),
                    ('Width', 'If(locPdfMode = "view", 1286, 520)'), ('Height', 'If(locPdfMode = "view", 56, 190)')):
        setp(scr, f'{p}_PdfPanel', prop, v)
    for prop, v in (('Visible', ANY), ('X', 'If(locPdfMode = "view", 56, 447)'), ('Y', 'If(locPdfMode = "view", 712, 306)'),
                    ('Width', 'If(locPdfMode = "view", 900, 472)'), ('Height', 'If(locPdfMode = "view", 44, 80)'),
                    ('Text', 'If(\n    locPdfMode = "view",\n    varPrintPdfName & "  ·  " & CountRows(colPrintReqMedia) & If(CountRows(colPrintReqMedia) = 1, " page", " pages") & "  -  print or save it from the viewer",\n'
                             '    "Saved in AV-CD-Exports:" & Char(10) & varPrintPdfName\n)')):
        setp(scr, f'{p}_PdfText', prop, v)
    for prop, v in (('Visible', ANY), ('X', 'If(locPdfMode = "view", 1166, 603)'), ('Y', 'If(locPdfMode = "view", 709, 400)'),
                    ('Height', 'If(locPdfMode = "view", 50, 50)'), ('OnSelect', 'UpdateContext({locPdfReady: false})')):
        setp(scr, f'{p}_PdfClose', prop, v)
    delete(scr, f'{p}_BtnPdfAll')
    # z-order: overlay above everything (shade, viewer, panel, text, buttons)
    tp = app.doc(scr)['TopParent']
    def z(n):
        v = [x for x in n['Rules'] if x['Property'] == 'ZIndex']; return int(v[0]['InvariantScript']) if v else 0
    def deep(n):
        yield n
        for c in n.get('Children', []): yield from deep(c)
    TOP = [f'{p}_PdfShade', f'{p}_PdfView', f'{p}_PdfPanel', f'{p}_PdfText', f'{p}_PdfClose', f'{p}_PdfOpen']
    mx = max(z(n) for n in deep(tp) if n['Name'] not in TOP and n['Name'] != 'PdfViewer1')
    for k, nm in enumerate(TOP): [x for x in find(tp, nm)['Rules'] if x['Property'] == 'ZIndex'][0]['InvariantScript'] = str(mx + 1 + k)
    app.save()
delete('PrintPodcastDetailScreen', 'PdfViewer1')
app.save()
p = f'{NEW}/Properties.json'
raw = open(p, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
for k, v in (('button', 261), ('pdfViewer', 3)):
    t, n = re.subn(r'("%s"\s*:\s*)\d+' % k, r'\g<1>%d' % v, t, count=1); assert n == 1, k
open(p, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL202 built')
