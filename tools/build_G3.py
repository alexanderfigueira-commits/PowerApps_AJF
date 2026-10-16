#!/usr/bin/env python3
"""FINAL13 on FINAL12.

A. ChildInfoScreen: a Video's Language (EN) and Type of product (Clip) dropdowns show their first item
   while nothing is stored; OnVisible now stores what is shown (as in FINAL_5, which FINAL10+ lost).
B. Export detail pages (Photo / Video / Podcast): one media file per page, laid out so nothing is cut:
   * every value label grows with its text (AutoHeight) and the next one follows it; long texts
     (description, notes, script, caption, summary) and the attached file names go in a full-width block
     under the three columns;
   * Legal & Documents (contract case, case 1 documents, third-party rights, model release, music,
     pre-existing rights) on all three pages (it was Video only), plus the names of the attached files;
   * a pager (File i of N); the PDF button saves the file shown, a second one saves every file (one PDF
     per file); the old "3 / 4 per page" cut-off is gone;
   * header values wrap instead of being cut.
C. Export list (HomePrintScreen): 8 requests per page with a pager; the PDF button saves the page shown,
   a second one saves every page. Filters go back to page 1.
"""
import datetime, json, os, re, shutil, sys
from payaml import App, find
from hp_common import Builder

SRC, NEW = 'newG2', 'newG3'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
DARK = 'RGBA(30, 34, 44, 1)'


def put(s, n, p, v, cat='Design'):
    c = find(app.doc(s)['TopParent'], n)
    if c is None:
        sys.exit(f'! {s}.{n} not found')
    if not [r for r in c['Rules'] if r['Property'] == p]:
        c['Rules'].append({'Property': p, 'Category': cat, 'InvariantScript': v, 'RuleProviderType': 'Unknown'})
        c.setdefault('ControlPropertyState', []).append(p)
    app.set(s, n, p, v)


# ================================================================ A. Video defaults stored
CI = 'ChildInfoScreen'
t = app.rule(CI, None, 'OnVisible')
tail = 'UpdateContext({locShowVisualPreview: false})'
if not t.endswith(tail):
    sys.exit('! ChildInfoScreen.OnVisible does not end as expected')
app.set(CI, None, 'OnVisible', t + ''';
// A Video's Language and Type of product dropdowns show their first item (EN / Clip) while nothing is
// stored yet. Store what is shown, or the Validations tab sees them empty until they are re-selected.
If(
    varChildMediaType = "Video" And Not(varRequestorLocked),
    If(Coalesce(varChildLanguageVersions, "") = "", Set(varChildLanguageVersions, "EN"));
    If(Coalesce(varChildProductType, varChildProductType1, "") = "", Set(varChildProductType, "Clip"))
)''', expect=t)
app.save()

# ================================================================ B. print detail pages
LEGAL = [  # (label, value formula)
    ('Contract case', 'If(IsEmpty(ThisItem.ContractCase), "Not provided", Concat(ThisItem.ContractCase, Value, ", "))'),
    ('Case 1 — required documents', 'If(IsEmpty(ThisItem.ContractCase1Sub), "Not provided", Concat(ThisItem.ContractCase1Sub, Value, ", "))'),
    ('No third-party rights', 'If(ThisItem.NoThirdPartyRights, "✅  Yes", "⛔  No")'),
    ('Model release provided', 'If(ThisItem.ModelReleaseProvided, "✅  Yes", "⛔  No")'),
    ('Music used', 'If(ThisItem.MusicUsed, "✅  Yes", "⛔  No")'),
    ('Music licence provided', 'If(ThisItem.MusicLicenseProvided, "✅  Yes", "⛔  No")'),
    ('Pre-existing rights provided', 'If(ThisItem.PreexistingRightsProvided, "✅  Yes", "⛔  No")'),
]
FILES_LBL = '"Attached files (" & CountRows(ThisItem.Attachments) & ")"'
FILES_VAL = 'If(IsEmpty(ThisItem.Attachments), "No files attached", Concat(ThisItem.Attachments, DisplayName, Char(10)))'
COLX = {'A': (12, 194), 'B': (442, 624), 'C': (872, 1054)}   # (label / section X, value X)

# existing numbers are the screens' own; new ones start at 30
SPECS = {
    'PrintVideoDetailScreen': dict(P='PVD', avail=520, cols={
        'A': [('S', 0), ('V', 1), ('V', 3), ('V', 4), ('S', 6), ('V', 7), ('V', 8), ('V', 9), ('V', 10)],
        'B': [('S', 42, 'Dates & place'), ('V', 11), ('V', 12), ('V', 13), ('V', 14), ('V', 15), ('S', 43, 'Links & tags'), ('V', 17), ('V', 18)],
        'C': [('S', 19), ('V', 20), ('V', 21), ('V', 22), ('V', 23), ('V', 24), ('V', 25), ('V', 26)]},
        texts=[2, 5, 16], legal=None, hdr_shift=12),
    'PrintPhotoDetailScreen': dict(P='PPD', avail=520, cols={
        'A': [('S', 0), ('V', 1), ('V', 3), ('S', 5), ('V', 9), ('V', 10), ('V', 13)],
        'B': [('S', 42, 'Contracting'), ('V', 6), ('V', 7), ('S', 43, 'Links & tags'), ('V', 11), ('V', 12)],
        'C': [('S', 30, 'Legal & Documents')] + [('V', 31 + i) for i in range(7)]},
        texts=[2, 8, 4], legal=31, hdr_shift=12),
    'PrintPodcastDetailScreen': dict(P='PPoD', avail=472, cols={
        'A': [('S', 0), ('V', 1), ('V', 2), ('V', 3), ('V', 5), ('S', 44, 'People'), ('V', 6), ('V', 7), ('V', 8)],
        'B': [('S', 42, 'Dates & place'), ('V', 9), ('V', 10), ('V', 11), ('V', 12), ('V', 13), ('S', 43, 'Links & tags'), ('V', 14), ('V', 15)],
        'C': [('S', 30, 'Legal & Documents')] + [('V', 31 + i) for i in range(7)]},
        texts=[4, 16], legal=31, hdr_shift=12),
}
FILES_N, TXSEC_N = 40, 41

for S, sp in SPECS.items():
    P, G = sp['P'], sp['P'] + '_Gallery'
    nm = lambda kind, n: f'{P}_{kind}{n}'
    tp = app.doc(S)['TopParent']
    gal = find(tp, G)
    avail, shift = sp['avail'], sp['hdr_shift']

    # ---- new controls (cloned from this screen's own labels, so look and font are the same)
    b = Builder(app, S)
    new_secs = [(it[1], it[2]) for col in sp['cols'].values() for it in col if it[0] == 'S' and len(it) == 3]
    for n, text in new_secs:
        b.clone(nm('Sec', n), S, nm('Sec', 0), {'Text': f'"{text}"'}, parent=G)
    if sp['legal']:
        for i, (lab, val) in enumerate(LEGAL):
            n = sp['legal'] + i
            b.clone(nm('Lbl', n), S, nm('Lbl', 1), {'Text': f'"{lab}"'}, parent=G)
            b.clone(nm('Val', n), S, nm('Val', 1), {'Text': val, 'Color': DARK}, parent=G)
    b.clone(nm('Sec', TXSEC_N), S, nm('Sec', 0), {'Text': '"Descriptions, notes & files"'}, parent=G)
    b.clone(nm('Lbl', FILES_N), S, nm('Lbl', 1), {'Text': FILES_LBL}, parent=G)
    b.clone(nm('Val', FILES_N), S, nm('Val', 1), {'Text': FILES_VAL, 'Color': DARK}, parent=G)
    # pager + PDF buttons (clones of the Back / Print buttons)
    b.clone(nm('PagePrev', ''), S, f'{P}_BtnBack', {'Text': '"◀"', 'X': '700', 'Y': '68', 'Width': '44',
            'OnSelect': 'UpdateContext({locPrintPage: Max(1, Coalesce(locPrintPage, 1) - 1)})',
            'Visible': 'Not(locPrinting) And CountRows(colPrintReqMedia) > 1'})
    b.clone(nm('PageNext', ''), S, f'{P}_BtnBack', {'Text': '"▶"', 'X': '902', 'Y': '68', 'Width': '44',
            'OnSelect': 'UpdateContext({locPrintPage: Min(CountRows(colPrintReqMedia), Coalesce(locPrintPage, 1) + 1)})',
            'Visible': 'Not(locPrinting) And CountRows(colPrintReqMedia) > 1'})
    b.clone(nm('BtnPdfAll', ''), S, f'{P}_BtnPrint', {'Text': '"⬇  PDF (all " & CountRows(colPrintReqMedia) & ")"', 'X': '1182', 'Y': '68', 'Width': '152',
            'OnSelect': ('UpdateContext({locPrinting: true});\n'
                         '// one PDF per media file: show file 1, 2, ... and save each\n'
                         'ForAll(\n    Sequence(CountRows(colPrintReqMedia)) As pg,\n    UpdateContext({locPrintPage: pg.Value});\n    Download(PDF(' + S + '))\n);\n'
                         'UpdateContext({locPrintPage: 1, locPrinting: false})'),
            'Visible': 'Not(locPrinting) And CountRows(colPrintReqMedia) > 1'})
    b.save()

    # ---- column geometry and chains
    for col, items in sp['cols'].items():
        lx, vx = COLX[col]
        prev = None
        for it in items:
            kind, n = it[0], it[1]
            if kind == 'S':
                c = nm('Sec', n)
                y = '20' if prev is None else f'{prev}.Y + If({prev}.Visible, {prev}.Height + 8, 0)'
                app.set(S, c, 'X', str(lx)); app.set(S, c, 'Y', y); app.set(S, c, 'Width', '420')
                prev = c
            else:
                c = nm('Val', n)
                y = f'{prev}.Y + If({prev}.Visible, {prev}.Height' + (' + 3' if prev.split('_')[1].startswith('Val') else '') + ', 0)'
                app.set(S, c, 'X', str(vx)); app.set(S, c, 'Y', y); app.set(S, c, 'Width', '240')
                app.set(S, c, 'AutoHeight', 'true'); app.set(S, c, 'VerticalAlign', 'VerticalAlign.Top')
                lb = nm('Lbl', n)
                app.set(S, lb, 'X', str(lx)); app.set(S, lb, 'Y', f'{c}.Y'); app.set(S, lb, 'Width', '180')
                app.set(S, lb, 'VerticalAlign', 'VerticalAlign.Top')
                put(S, lb, 'Visible', f'{c}.Visible')
                if n >= 30:
                    put(S, c, 'Visible', 'true')
                prev = c
    # section membership
    for col, items in sp['cols'].items():
        cur, mem = None, {}
        for it in items:
            if it[0] == 'S':
                cur = nm('Sec', it[1]); mem[cur] = []
            else:
                mem[cur].append(nm('Val', it[1]))
        for sec, vals in mem.items():
            put(S, sec, 'Visible', ' Or '.join(f'{v}.Visible' for v in vals))
    # full-width block under the three columns
    allv = [nm('Val', it[1]) for items in sp['cols'].values() for it in items if it[0] == 'V']
    bottom = 'Max(' + ', '.join(f'{v}.Y + If({v}.Visible, {v}.Height + 3, 0)' for v in allv) + ')'
    tx = nm('Sec', TXSEC_N)
    app.set(S, tx, 'X', '12'); app.set(S, tx, 'Width', '1270'); app.set(S, tx, 'Y', bottom + ' + 6'); put(S, tx, 'Visible', 'true')
    prev = tx
    for n in sp['texts'] + [FILES_N]:
        c, lb = nm('Val', n), nm('Lbl', n)
        app.set(S, c, 'X', '194'); app.set(S, c, 'Width', '1090')
        app.set(S, c, 'Y', f'{prev}.Y + If({prev}.Visible, {prev}.Height' + (' + 3' if prev != tx else '') + ', 0)')
        app.set(S, c, 'AutoHeight', 'true'); app.set(S, c, 'VerticalAlign', 'VerticalAlign.Top')
        app.set(S, lb, 'X', '12'); app.set(S, lb, 'Y', f'{c}.Y'); app.set(S, lb, 'Width', '180'); app.set(S, lb, 'VerticalAlign', 'VerticalAlign.Top')
        put(S, lb, 'Visible', f'{c}.Visible')
        prev = c
    put(S, nm('Val', FILES_N), 'Visible', 'true')
    # the row rule follows the page height; the 3/4-per-page note becomes the page label
    app.set(S, f'{P}_RowRule', 'Y', str(avail - 1))

    # ---- gallery: one media file per page
    page = 'Min(Max(Coalesce(locPrintPage, 1), 1), CountRows(colPrintReqMedia))'
    app.set(S, G, 'Items', f'// one media file per page (pager above); the page is always a whole file\nLastN(FirstN(colPrintReqMedia, {page}), 1)')
    app.set(S, G, 'TemplateSize', str(avail)); app.set(S, G, 'Height', str(avail)); app.set(S, G, 'Y', str(208 + shift) if P != 'PPoD' else str(256 + shift))
    app.set(S, f'{P}_More', 'Text', f'"File " & {page} & " of " & CountRows(colPrintReqMedia)')
    app.set(S, f'{P}_More', 'X', '748'); app.set(S, f'{P}_More', 'Y', '74'); app.set(S, f'{P}_More', 'Width', '150'); app.set(S, f'{P}_More', 'Height', '28')
    put(S, f'{P}_More', 'Align', 'Align.Center')
    app.set(S, f'{P}_More', 'Visible', 'CountRows(colPrintReqMedia) > 1')
    # header card: values wrap instead of being cut
    app.set(S, f'{P}_HeaderCard', 'Height', str(88 + shift))
    for i in range(7):
        app.set(S, f'{P}_HdrVal{i}', 'Height', '34'); app.set(S, f'{P}_HdrVal{i}', 'VerticalAlign', 'VerticalAlign.Top')
    app.set(S, f'{P}_Empty', 'Y', str(int(app.rule(S, f'{P}_Empty', 'Y')) + shift))
    if P == 'PPoD':
        app.set(S, 'PPoD_PodVal0', 'Y', str(int(app.rule(S, 'PPoD_PodVal0', 'Y')) + shift))
    # buttons: Print becomes "PDF (this file)"
    app.set(S, f'{P}_BtnPrint', 'Text', '"⬇  PDF (this file)"')
    app.set(S, f'{P}_BtnPrint', 'X', '1002'); app.set(S, f'{P}_BtnPrint', 'Width', '170')
    app.set(S, f'{P}_BtnPrint', 'OnSelect', f'UpdateContext({{locPrinting: true}});\nDownload(PDF({S}));\nUpdateContext({{locPrinting: false}})')
    # screen OnVisible: start on file 1
    t = app.rule(S, None, 'OnVisible')
    app.set(S, None, 'OnVisible', t + ';\nUpdateContext({locPrintPage: 1})', expect=t)
    app.save()

# ================================================================ C. Export list
HP = 'HomePrintScreen'
PER = 8
t = app.rule(HP, None, 'OnVisible')
app.set(HP, None, 'OnVisible', t + ';\nUpdateContext({locHPPage: 1})', expect=t)
rows = app.rule(HP, 'HP_Gallery', 'Items').strip()
if not rows.startswith('Filter(') or app.rule(HP, 'HP_Gallery', 'TemplateSize') != '52':
    sys.exit('! HP_Gallery changed')
PG = (f'With({{n: CountRows({rows})}}, Min(Max(Coalesce(locHPPage, 1), 1), Max(1, RoundUp(n / {PER}, 0))))')
app.set(HP, 'HP_Gallery', 'Items',
        f'// {PER} requests per page (pager above): the page shown is exactly what is printed\n'
        f'With({{rows: {rows}}},\n    With({{pg: Min(Max(Coalesce(locHPPage, 1), 1), Max(1, RoundUp(CountRows(rows) / {PER}, 0)))}},\n'
        f'        LastN(FirstN(rows, pg * {PER}), Max(0, Min({PER}, CountRows(rows) - (pg - 1) * {PER})))\n    )\n)')
app.set(HP, 'HP_Gallery', 'Height',
        f'With({{rows: {rows}}},\n    With({{pg: Min(Max(Coalesce(locHPPage, 1), 1), Max(1, RoundUp(CountRows(rows) / {PER}, 0)))}},\n'
        f'        Max(52, 52 * Max(0, Min({PER}, CountRows(rows) - (pg - 1) * {PER})))\n    )\n)')
b = Builder(app, HP)
b.clone('HP_PagePrev', HP, 'HP_BtnBack', {'Text': '"◀"', 'X': '640', 'Y': '68', 'Width': '44',
        'OnSelect': 'UpdateContext({locHPPage: Max(1, Coalesce(locHPPage, 1) - 1)})', 'Visible': 'Not(locHPPrinting)'})
b.clone('HP_PageNext', HP, 'HP_BtnBack', {'Text': '"▶"', 'X': '852', 'Y': '68', 'Width': '44',
        'OnSelect': ('With({rows: ' + rows + '},\n    UpdateContext({locHPPage: Min(Max(1, RoundUp(CountRows(rows) / ' + str(PER) + ', 0)), Coalesce(locHPPage, 1) + 1)})\n)'),
        'Visible': 'Not(locHPPrinting)'})
b.clone('HP_BtnDownloadAll', HP, 'HP_BtnDownload', {
    'Text': '"⬇  PDF (all pages)"', 'X': '1150', 'Width': '184',
    'OnSelect': ('UpdateContext({locHPPrinting: true});\n'
                 '// one PDF per page of ' + str(PER) + ' requests: show page 1, 2, ... and save each\n'
                 'With({pages: Max(1, RoundUp(CountRows(' + rows + ') / ' + str(PER) + ', 0))},\n'
                 '    ForAll(\n        Sequence(pages) As pg,\n        UpdateContext({locHPPage: pg.Value});\n        Download(PDF(HomePrintScreen))\n    )\n);\n'
                 'UpdateContext({locHPPage: 1, locHPPrinting: false})'),
    'Visible': 'Not(locHPPrinting)'})
b.clone('HP_PageLbl', HP, 'HP_SubTitle', {
    'Text': '"Page " & ' + PG + ' & " of " & Max(1, RoundUp(CountRows(' + rows + ') / ' + str(PER) + ', 0))',
    'X': '688', 'Y': '68', 'Width': '160'})
b.save()
put(HP, 'HP_PageLbl', 'Align', 'Align.Center')
app.set(HP, 'HP_SubTitle', 'Width', '480')
app.set(HP, 'HP_BtnDownload', 'Text', '"⬇  PDF (this page)"')
app.set(HP, 'HP_BtnDownload', 'X', '950'); app.set(HP, 'HP_BtnDownload', 'Width', '190')
app.set(HP, 'HP_BtnDownload', 'OnSelect', 'UpdateContext({locHPPrinting: true});\nDownload(PDF(HomePrintScreen));\nUpdateContext({locHPPrinting: false})')
put(HP, 'HP_BtnDownload', 'Visible', 'Not(locHPPrinting)')
# filters go back to page 1
for n in ('HP_BtnAllMedia', 'HP_BtnPhoto', 'HP_BtnVideo', 'HP_BtnPodcast', 'HP_BtnStatusAll', 'HP_BtnStatusDraft',
          'HP_BtnStatusProcessing', 'HP_BtnStatusPending', 'HP_BtnStatusApproved', 'HP_BtnStatusRejected', 'HP_BtnClear'):
    o = app.rule(HP, n, 'OnSelect')
    app.set(HP, n, 'OnSelect', 'UpdateContext({locHPPage: 1});\n' + o, expect=o)
app.save()

# ================================================================ save time (control count)
from collections import Counter


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


cnt = Counter(c['Template']['Name'] for s in app.map if s != 'App' for c in walk(app.doc(s)['TopParent']))
p = open(f'{NEW}/Properties.json', encoding='utf-8').read()
for k, v in cnt.items():
    p = re.sub(rf'("{k}": )\d+', rf'\g<1>{v}', p, count=1)
open(f'{NEW}/Properties.json', 'w', encoding='utf-8', newline='').write(p)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL13 built')
