#!/usr/bin/env python3
"""FINAL206 on FINAL203 (FINAL204 rebuilt with a 12 pt page header and footer; FINAL205 applied after).
FINAL204 on FINAL203. The PDF (Print / Background-print) gets two media files per A4 landscape page, a header on every page
and a footer with the page number; the on-screen sheet is unchanged.
- PDF mode (locAllPages): rows of 448 px = half a page at 120 DPI; rows are numbered (PdfRowNo) and padded with a blank row so the
  last page also ends with its footer. Odd rows start with the page header (request title, status, number, type, creator, DG,
  submitted, assignee); even rows end with the footer.
- Field sizes / line budgets in PDF mode are fitted to half a page (smaller text, long texts shortened with '…');
  screen mode keeps the FINAL201 values.
- Viewer bar: "Download PDF" button (hands the generated PDF to the browser; to be confirmed in the player)."""
import copy, datetime, os, re, shutil, sys
sys.path.insert(0, '.')
from payaml import App, find, block_span, _fmt
from hp_common import Builder
from fit_lib import line_h, cpl
from fit_plan import plan, fit, lab_of
SRC, NEW = os.environ.get('SRC', 'newV65'), os.environ.get('NEW', 'newV66')
BIG = os.environ.get('BIG_HEADER') == '1'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)
ALL = 'Coalesce(locAllPages, false)'
ROW, H_H, F_H = (448, 56, 24) if BIG else (448, 42, 20)
BLANK = 'Coalesce(ThisItem.PdfBlank, false)'
ODD = f'{ALL} And Mod(ThisItem.PdfRowNo, 2) = 1'
report = []
HEIGHT_RE = re.compile(r'Max\(\s*If\(c, \d+, (\d+)\) \* Max\(1, Min\((\d+), RoundUp\(Len\(Self\.Text\) / If\(c, \d+, (\d+)\), 0\)\)\),\s*If\(c, \d+, (\d+)\)\s*\)', re.S)
TEXT_RE = re.compile(r'^With\(\n    \{t: (.*)\n    \},\n    If\(Len\(t\) > (\d+), Left\(t, \d+\) & "…", t\)\n\)$', re.S)
for scr, p, typ in (('PrintVideoDetailScreen', 'PVD', 'Video'), ('PrintPodcastDetailScreen', 'PPoD', 'Podcast'), ('PrintPhotoDetailScreen', 'PPD', 'Photo')):
    P = plan('newV59', scr, p)
    chosen = None
    for lbl, val, sec, cap in ((11, 11, 13, 15), (10, 11, 12, 14), (10, 10, 12, 14), (9, 10, 11, 13)):
        top = line_h(cap) + 2
        ok, caps, h, m, sech = fit(P, lbl, val, ROW - H_H - 2, top, sec)
        if ok: chosen = (lbl, val, sec, cap, caps, h, m, sech); break
    assert chosen, scr
    lbl, val, sec, cap, caps, h, m, sech = chosen
    report.append((scr, lbl, val, sec, cap, h, {lab_of(i): caps[i['name']] for i in P['vals'] if caps[i['name']] < {'short': 1, 'normal': 2, 'long': 4}[i['cls']]}))
    tp = app.doc(scr)['TopParent']
    capn = f'{p}_RowCaption'
    setp(scr, capn, 'Size', f'If({ALL}, {cap}, 17)')
    setp(scr, capn, 'Height', f'If({ALL}, {line_h(cap)}, {line_h(17)})')
    setp(scr, capn, 'Y', f'// PDF: the first media file of a page sits under the page header\nIf({ODD}, {H_H}, 0)')
    for c, col in P['cols'].items():
        first = col[0]['name']
        assert app.rule(scr, first, 'Y').strip() == '34', (first, app.rule(scr, first, 'Y'))
        setp(scr, first, 'Y', f'{capn}.Y + {capn}.Height + 2')
    for i in P['items']:
        nm = i['name']
        if i['kind'] == 'sec':
            setp(scr, nm, 'Size', f'If({ALL}, {sec}, 14)'); setp(scr, nm, 'Height', f'If({ALL}, {sech}, {line_h(14)})')
        elif i['kind'] == 'lbl':
            setp(scr, nm, 'Size', f'If({ALL}, {lbl}, 12)')
        elif i['kind'] == 'val':
            setp(scr, nm, 'Size', f'If({ALL}, {val}, 12)')
            hm = HEIGHT_RE.search(app.rule(scr, nm, 'Height')); assert hm, nm
            lvF, kF, cpF, llF = map(int, hm.groups())
            mm = m[nm]; kP = caps[nm]; cpP = mm['cp']; lvP = mm['lv']; llP = mm['ll'] * mm['LL']
            setp(scr, nm, 'Height', (f'// lines the text needs (screen up to {kF}, PDF up to {kP}), never less than its label\n'
                                    f'With(\n    {{c: {ALL}}},\n    Max(\n        If(c, {lvP}, {lvF}) * Max(1, Min(If(c, {kP}, {kF}), RoundUp(Len(Self.Text) / If(c, {cpP}, {cpF}), 0))),\n'
                                    f'        If(c, {llP}, {llF})\n    )\n)'))
            t = app.rule(scr, nm, 'Text'); tm = TEXT_RE.match(t.strip())
            if tm:
                orig, nF = tm.group(1), int(tm.group(2)); nP = kP * cpP
                setp(scr, nm, 'Text', f'With(\n    {{t: {orig}\n    , n: If({ALL}, {nP}, {nF})}},\n    If(Len(t) > n, Left(t, n - 1) & "…", t)\n)')
    # every control of the row is hidden on the blank padding row
    g = find(tp, f'{p}_Gallery')
    def kids(n):
        for c in n.get('Children', []):
            yield c; yield from kids(c)
    for k in [c['Name'] for c in kids(g)]:
        v = app.rule(scr, k, 'Visible')
        if v is not None and BLANK not in v:
            setp(scr, k, 'Visible', f'Not({BLANK}) And ({v.strip()})' if v.strip() != 'true' else f'Not({BLANK})')
    # rows numbered, one blank row at the end of an odd PDF
    items = app.rule(scr, f'{p}_Gallery', 'Items')
    paged = re.search(r'If\(Coalesce\(locAllPages, false\), colPrintReqMedia, (.*)\)\s*$', items, re.S).group(1)
    setp(scr, f'{p}_Gallery', 'Items', (
        f'// rows numbered for the PDF (two per page: header on odd rows, footer on even rows); an odd PDF gets a blank last row\n'
        f'With(\n    {{T: If({ALL}, colPrintReqMedia, {paged}), all: {ALL}}},\n'
        f'    ForAll(\n        Sequence(If(all, RoundUp(CountRows(T) / 2, 0) * 2, CountRows(T))),\n'
        f'        If(\n            Value <= CountRows(T),\n            Patch(Index(T, Value), {{PdfRowNo: Value, PdfBlank: false}}),\n'
        f'            Patch(Index(T, 1), {{PdfRowNo: Value, PdfBlank: true}})\n        )\n    )\n)'))
    setp(scr, f'{p}_Gallery', 'TemplateSize', re.sub(r'If\(Coalesce\(locAllPages, false\), \d+,', f'If({ALL}, {ROW},', app.rule(scr, f'{p}_Gallery', 'TemplateSize')))
    rr = app.rule(scr, f'{p}_RowRule', 'Y')
    setp(scr, f'{p}_RowRule', 'Y', f'If({ALL}, {ROW - 1}, {rr.strip()})')
    setp(scr, f'{p}_RowRule', 'Visible', f'Not({BLANK}) And (Not({ALL}) Or Mod(ThisItem.PdfRowNo, 2) = 1)')
    # page header and footer (PDF only)
    b = Builder(app, scr)
    if BIG:
        # page header: line 1 = title (14 pt) + request / type / status at the right (12 pt); line 2 = people, DG and date (12 pt)
        b.clone(f'{p}_PgHdrBg', scr, f'{p}_RowRule', {'X': '0', 'Y': '0', 'Width': '1302', 'Height': str(H_H - 4), 'Fill': 'RGBA(247, 248, 250, 1)',
                'BorderThickness': '0', 'Visible': ODD}, parent=f'{p}_Gallery')
        b.clone(f'{p}_PgHdrTitle', scr, f'{p}_Sec0', {'X': '12', 'Y': '2', 'Width': '760', 'Height': '27', 'Size': '14', 'Visible': ODD,
                'Color': 'RGBA(0, 18, 107, 1)', 'FontWeight': 'FontWeight.Semibold', 'VerticalAlign': 'VerticalAlign.Top',
                'Text': 'With(\n    {t: Coalesce(varPrintRequest.RequestTitle, "Untitled request")},\n    If(Len(t) > 70, Left(t, 69) & "…", t)\n)'}, parent=f'{p}_Gallery')
        b.clone(f'{p}_PgHdrRef', scr, f'{p}_Sec0', {'X': '780', 'Y': '5', 'Width': '510', 'Height': '23', 'Size': '12', 'Visible': ODD,
                'Color': 'RGBA(0, 18, 107, 1)', 'FontWeight': 'FontWeight.Semibold', 'VerticalAlign': 'VerticalAlign.Top', 'Align': 'Align.Right',
                'Text': ('"Request " & Coalesce(varPrintRequest.RequestNumber, "—") & "  ·  ID " & Text(varPrintRequest.ID) & "  ·  ' + typ + '  ·  "'
                         ' & Coalesce(varPrintRequest.Status.Value, "Draft")')}, parent=f'{p}_Gallery')
        INFO = ('"Created by " & Coalesce(varPrintRequest.\'Created By\'.DisplayName, "—")'
                ' & "  ·  " & Coalesce(varPrintRequest.DG.Value, "—")'
                ' & "  ·  Submitted " & If(Not(IsBlank(varPrintRequest.SubmittedOn)), Text(varPrintRequest.SubmittedOn, "dd-mm-yyyy"), If(Not(IsBlank(varPrintRequest.StartRequestDate)), Text(varPrintRequest.StartRequestDate, "dd-mm-yyyy"), "—"))'
                ' & "  ·  Assignee " & Coalesce(varPrintRequest.Assignee.DisplayName, "Not assigned")')
        b.clone(f'{p}_PgHdrInfo', scr, f'{p}_Sec0', {'X': '12', 'Y': '29', 'Width': '1278', 'Height': '23', 'Size': '12', 'Visible': ODD,
                'Color': 'RGBA(70, 76, 90, 1)', 'FontWeight': 'FontWeight.Normal', 'VerticalAlign': 'VerticalAlign.Top',
                'Text': f'With(\n    {{t: {INFO}}},\n    If(Len(t) > 150, Left(t, 149) & "…", t)\n)'}, parent=f'{p}_Gallery')
        b.clone(f'{p}_PgFooter', scr, f'{p}_Sec0', {'X': '12', 'Y': str(ROW - F_H), 'Width': '1278', 'Height': '23', 'Size': '12',
                'Visible': f'{ALL} And Mod(ThisItem.PdfRowNo, 2) = 0', 'Color': 'RGBA(70, 76, 90, 1)', 'FontWeight': 'FontWeight.Normal',
                'VerticalAlign': 'VerticalAlign.Top',
                'Text': ('"AV Central Deposit Ticket System  ·  Audiovisual Service, DG COMM  ·  " & Text(Today(), "dd-mm-yyyy") & '
                         '"  ·  Page " & RoundUp(ThisItem.PdfRowNo / 2, 0) & " of " & RoundUp(CountRows(colPrintReqMedia) / 2, 0)')}, parent=f'{p}_Gallery')
    else:
        b.clone(f'{p}_PgHdrBg', scr, f'{p}_RowRule', {'X': '0', 'Y': '0', 'Width': '1302', 'Height': str(H_H - 4), 'Fill': 'RGBA(247, 248, 250, 1)',
                'BorderThickness': '0', 'Visible': ODD}, parent=f'{p}_Gallery')
        b.clone(f'{p}_PgHdrTitle', scr, f'{p}_Sec0', {'X': '12', 'Y': '2', 'Width': '1278', 'Height': '20', 'Size': '11', 'Visible': ODD,
                'Color': 'RGBA(0, 18, 107, 1)', 'FontWeight': 'FontWeight.Semibold', 'VerticalAlign': 'VerticalAlign.Top',
                'Text': ('With(\n    {t: Coalesce(varPrintRequest.RequestTitle, "Untitled request") & "     ·     " & Coalesce(varPrintRequest.Status.Value, "Draft")},\n'
                         '    If(Len(t) > 150, Left(t, 149) & "…", t)\n)')}, parent=f'{p}_Gallery')
        INFO = ('"Request " & Coalesce(varPrintRequest.RequestNumber, "—") & "   ·   ID " & Text(varPrintRequest.ID) & "   ·   ' + typ + '"'
                ' & "   ·   Created by " & Coalesce(varPrintRequest.\'Created By\'.DisplayName, "—")'
                ' & "   ·   " & Coalesce(varPrintRequest.DG.Value, "—")'
                ' & "   ·   Submitted " & If(Not(IsBlank(varPrintRequest.SubmittedOn)), Text(varPrintRequest.SubmittedOn, "dd-mm-yyyy"), If(Not(IsBlank(varPrintRequest.StartRequestDate)), Text(varPrintRequest.StartRequestDate, "dd-mm-yyyy"), "—"))'
                ' & "   ·   Assignee " & Coalesce(varPrintRequest.Assignee.DisplayName, "Not assigned")')
        b.clone(f'{p}_PgHdrInfo', scr, f'{p}_Sec0', {'X': '12', 'Y': '21', 'Width': '1278', 'Height': '16', 'Size': '8', 'Visible': ODD,
                'Color': 'RGBA(70, 76, 90, 1)', 'FontWeight': 'FontWeight.Normal', 'VerticalAlign': 'VerticalAlign.Top',
                'Text': f'With(\n    {{t: {INFO}}},\n    If(Len(t) > 230, Left(t, 229) & "…", t)\n)'}, parent=f'{p}_Gallery')
        b.clone(f'{p}_PgFooter', scr, f'{p}_Sec0', {'X': '12', 'Y': str(ROW - F_H), 'Width': '1278', 'Height': '18', 'Size': '8',
                'Visible': f'{ALL} And Mod(ThisItem.PdfRowNo, 2) = 0', 'Color': 'RGBA(110, 116, 128, 1)', 'FontWeight': 'FontWeight.Normal',
                'VerticalAlign': 'VerticalAlign.Top',
                'Text': ('"AV Central Deposit Ticket System  ·  Audiovisual Service, DG COMM  ·  " & Text(Today(), "dd-mm-yyyy") & '
                         '"  ·  Page " & RoundUp(ThisItem.PdfRowNo / 2, 0) & " of " & RoundUp(CountRows(colPrintReqMedia) / 2, 0)')}, parent=f'{p}_Gallery')
    # viewer bar: Download PDF
    VIEW = 'Coalesce(locPdfReady, false) And locPdfMode = "view"'
    b.clone(f'{p}_PdfDownload', scr, f'{p}_PdfClose', {'Text': '"⬇  Download PDF"', 'X': '990', 'Y': '709', 'Width': '168', 'Height': '50',
            'Visible': VIEW, 'OnSelect': 'Download(varPrintPdf)'})
    b.save()
    setp(scr, f'{p}_PdfText', 'Text', app.rule(scr, f'{p}_PdfText', 'Text').replace('  -  print or save it from the viewer', '  -  Download PDF saves it on your computer'))
    setp(scr, f'{p}_PdfText', 'Text', app.rule(scr, f'{p}_PdfText', 'Text').replace(
        'CountRows(colPrintReqMedia) & If(CountRows(colPrintReqMedia) = 1, " page", " pages")',
        'RoundUp(CountRows(colPrintReqMedia) / 2, 0) & If(RoundUp(CountRows(colPrintReqMedia) / 2, 0) = 1, " page", " pages")'))
    # z-order of the new viewer button: with the overlay
    tp = app.doc(scr)['TopParent']
    z = lambda n: int(([x['InvariantScript'] for x in n['Rules'] if x['Property'] == 'ZIndex'] or ['0'])[0])
    zc = z(find(tp, f'{p}_PdfClose'))
    [x for x in find(tp, f'{p}_PdfDownload')['Rules'] if x['Property'] == 'ZIndex'][0]['InvariantScript'] = str(zc + 1)
    app.save()
p_ = f'{NEW}/Properties.json'
raw = open(p_, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
def bump(k, d):
    global t
    t = re.sub(r'("%s"\s*:\s*)(\d+)' % k, lambda mm: mm.group(1) + str(int(mm.group(2)) + d), t, count=1)
bump('button', 3); bump('label', 12 if BIG else 9); bump('rectangle', 3)
open(p_, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
for r in report: print('REPORT', r)
print('FINAL206 base built' if BIG else 'FINAL204 built')
