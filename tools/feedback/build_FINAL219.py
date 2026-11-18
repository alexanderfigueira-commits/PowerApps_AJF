#!/usr/bin/env python3
"""FINAL219 on FINAL218. Print sheets: checkbox "Print full descriptions".
- Not ticked (default): the PDF as today, 2 media files per page, long texts up to 2 lines.
- Ticked: 1 media file per page, header and footer on every page, the screen sizes (12 pt) and the descriptions / caption /
  summary in full (up to 500 characters, 6 lines) in the full-width rows."""
import datetime, os, re, shutil, sys
sys.path.insert(0, '.')
from payaml import App, find
from hp_common import Builder
from fit_lib import cpl, line_h
SRC, NEW = 'newV80', 'newV81'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)
def edit(scr, ctl, prop, old, new, n=1):
    t = app.rule(scr, ctl, prop); assert t is not None and t.count(old) == n, (scr, ctl, prop, old, t and t.count(old))
    app.set(scr, ctl, prop, t.replace(old, new), expect=t)
ALL = 'Coalesce(locAllPages, false)'
FULL = 'Coalesce(locPdfFull, false)'
C2 = f'({ALL} And Not({FULL}))'      # the compact PDF (2 per page): its sizes; the full PDF uses the screen sizes
ODD = f'{ALL} And Mod(ThisItem.PdfRowNo, 2) = 1'
F_H, ROWC, ROWF = 24, 448, 896
CP12, CP10 = cpl(12, 1096), cpl(10, 1096)
for scr, p in (('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD'), ('PrintPhotoDetailScreen', 'PPD')):
    tp = app.doc(scr)['TopParent']; g = find(tp, f'{p}_Gallery')
    def kids(n):
        for c in n.get('Children', []):
            yield c; yield from kids(c)
    names = [c['Name'] for c in kids(g)]
    fw = [n for n in names if '_Fw' in n]
    hdr = [n for n in names if '_PgHdr' in n or n.endswith('_PgFooter')]
    # 1. sizes / heights / line budgets: compact PDF only
    for n in names:
        if n in fw or n in hdr: continue
        for prop in ('Size', 'Height', 'Text'):
            t = app.rule(scr, n, prop)
            if t and ALL in t and C2 not in t:
                app.set(scr, n, prop, t.replace(ALL, C2), expect=t)
    # 2. page header on every row of the full PDF; caption under it
    edit(scr, f'{p}_RowCaption', 'Y', ODD, f'{ALL} And ({FULL} Or Mod(ThisItem.PdfRowNo, 2) = 1)')
    for n in (f'{p}_PgHdrBg', f'{p}_PgHdrTitle', f'{p}_PgHdrInfo'):
        edit(scr, n, 'Visible', ODD, f'{ALL} And ({FULL} Or Mod(ThisItem.PdfRowNo, 2) = 1)')
    # 3. footer on every row of the full PDF, at the bottom of the page
    edit(scr, f'{p}_PgFooter', 'Visible', f'{ALL} And Mod(ThisItem.PdfRowNo, 2) = 0', f'{ALL} And ({FULL} Or Mod(ThisItem.PdfRowNo, 2) = 0)')
    setp(scr, f'{p}_PgFooter', 'Y', f'If({FULL}, {ROWF - F_H}, {ROWC - F_H})')
    edit(scr, f'{p}_PgFooter', 'Text', '"  ·  Page " & RoundUp(ThisItem.PdfRowNo / 2, 0) & " of " & RoundUp(CountRows(colPrintReqMedia) / 2, 0)',
         f'"  ·  Page " & If({FULL}, ThisItem.PdfRowNo, RoundUp(ThisItem.PdfRowNo / 2, 0)) & " of " & If({FULL}, CountRows(colPrintReqMedia), RoundUp(CountRows(colPrintReqMedia) / 2, 0))')
    # 4. rows and pages
    edit(scr, f'{p}_RowRule', 'Visible', f'Or Mod(ThisItem.PdfRowNo, 2) = 1)', f'Or (Not({FULL}) And Mod(ThisItem.PdfRowNo, 2) = 1))')
    edit(scr, f'{p}_RowRule', 'Y', f'If({ALL}, {ROWC - 1},', f'If({ALL}, If({FULL}, {ROWF - 1}, {ROWC - 1}),')
    edit(scr, f'{p}_Gallery', 'Items', 'Sequence(If(all, RoundUp(CountRows(T) / 2, 0) * 2, CountRows(T)))',
         f'Sequence(If(all And Not({FULL}), RoundUp(CountRows(T) / 2, 0) * 2, CountRows(T)))')
    edit(scr, f'{p}_Gallery', 'TemplateSize', f'If({ALL}, {ROWC},', f'If({ALL}, If({FULL}, {ROWF}, {ROWC}),')
    # 5. full-width rows: full texts in the full PDF
    for n in fw:
        if n.endswith('Lbl'):
            setp(scr, n, 'Size', f'If({FULL}, 12, 9)')
        else:
            setp(scr, n, 'Size', f'If({FULL}, 12, 10)')
            setp(scr, n, 'Height', f'// full-width row of the PDF: up to 2 lines (2 per page) or 6 lines (full descriptions)\n'
                                   f'If({FULL}, {line_h(12)}, {line_h(10)}) * Max(1, Min(If({FULL}, 6, 2), RoundUp(Len(Self.Text) / If({FULL}, {CP12}, {CP10}), 0)))')
            t = app.rule(scr, n, 'Text'); m = re.search(r', n: (\d+)\}', t); assert m, n
            app.set(scr, n, 'Text', t[:m.start()] + f', n: If({FULL}, 500, {m.group(1)})}}' + t[m.end():], expect=t)
    # 6. preview bar: number of pages
    edit(scr, f'{p}_PdfText', 'Text', 'RoundUp(CountRows(colPrintReqMedia) / 2, 0)',
         f'If({FULL}, CountRows(colPrintReqMedia), RoundUp(CountRows(colPrintReqMedia) / 2, 0))', n=2)
    # 7. the checkbox, next to the title of the sheet
    setp(scr, f'{p}_Heading', 'Width', 'If(locPrinting And Coalesce(varCompactPrint, false), 260, 370)')
    b = Builder(app, scr)
    b.clone(f'{p}_ChkFullDesc', 'ChildLegalScreen', 'CL_ChkDocsFTP', {
        'Text': '"Print full descriptions (1 media per page)"', 'X': '510', 'Y': '70', 'Width': '330', 'Height': '36', 'Size': '11',
        'Default': f'{FULL}', 'OnCheck': 'UpdateContext({locPdfFull: true})', 'OnUncheck': 'UpdateContext({locPdfFull: false})',
        'DisplayMode': 'DisplayMode.Edit', 'Fill': 'RGBA(0, 0, 0, 0)',
        'Visible': 'Not(locPrinting) And Not(Coalesce(locPdfPending, false)) And Not(Coalesce(locSavePending, false))'})
    b.save()
    # page buttons move right to make room
    for n, x in ((f'{p}_BtnPrevPage', 850), (f'{p}_PageLbl', 902), (f'{p}_BtnNextPage', 1018)):
        setp(scr, n, 'X', str(x))
    t = app.rule(scr, None, 'OnVisible')
    t2 = re.sub(r'locDot: 0(, locSavePending: false)?\}\)\s*$', 'locDot: 0, locSavePending: false, locPdfFull: false})', t.rstrip())
    app.set(scr, None, 'OnVisible', t2, expect=t)
    assert 'locPdfFull: false' in app.rule(scr, None, 'OnVisible')
app.save()   # the last screen's OnVisible is saved too
p_ = f'{NEW}/Properties.json'
raw = open(p_, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
t = re.sub(r'("checkbox"\s*:\s*)(\d+)', lambda mm: mm.group(1) + str(int(mm.group(2)) + 3), t, count=1)
open(p_, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL219 built')
