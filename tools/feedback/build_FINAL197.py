#!/usr/bin/env python3
"""FINAL197 on FINAL196. Export and print: larger text.
Print sheets (Video / Podcast / Photo): every control of the media row is scaled by 1.5 (font sizes, heights, vertical positions),
so values go from 9 to 14 pt and labels from 8 to 12 pt, in both the full and the compact print layout. A page now holds
1 Video / Podcast media file (was 2) and 2 Photo media files (was 3); paging, 'Page x of y', 'Continued on page' and the
footer follow. The Podcast FTP path is cut at 29 characters instead of 44 (wider letters).
Export list: row text 11 -> 13 pt, column headers 11 -> 12 pt."""
import datetime, os, re, shutil
from payaml import App, find
SRC, NEW = 'newV58', 'newV59'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
F = 1.5
def r5(x): return int(x * F + 0.5)
def setp(scr, ctl, prop, fn):
    t = app.rule(scr, ctl, prop); n = fn(t)
    if n != t: app.set(scr, ctl, prop, n, expect=t); return True
    return False
def walk(n):
    yield n
    for c in n.get('Children', []): yield from walk(c)
SIZE_RE = re.compile(r'^If\(locPrinting And Coalesce\(varCompactPrint, false\), (\d+), (\d+)\)$')
for scr, p, old_k, new_k, ts, gh in (('PrintVideoDetailScreen', 'PVD', 2, 1, 217, 217), ('PrintPodcastDetailScreen', 'PPoD', 2, 1, 224, 232),
                                     ('PrintPhotoDetailScreen', 'PPD', 3, 2, 172, 172)):
    tp = app.doc(scr)['TopParent']; g = find(tp, f'{p}_Gallery')
    kids = [n['Name'] for n in list(walk(g))[1:]]
    nsz = ngeo = 0
    for k in kids:
        def fsize(t):
            m = SIZE_RE.match(t.strip())
            if m: return f'If(locPrinting And Coalesce(varCompactPrint, false), {r5(int(m.group(1)))}, {r5(int(m.group(2)))})'
            if re.fullmatch(r'\d+', t.strip()): return str(r5(int(t)))
            raise SystemExit(f'! unexpected Size on {k}: {t}')
        c = find(tp, k); props = {x['Property'] for x in c['Rules']}
        if 'Size' in props: nsz += setp(scr, k, 'Size', fsize)
        for prop in ('Y', 'Height'):
            if prop in props:
                ngeo += setp(scr, k, prop, lambda t: str(r5(int(t))) if re.fullmatch(r'\d+', t.strip()) else t)
    TS = r5(ts); GH = r5(gh)
    setp(scr, f'{p}_RowRule', 'Y', lambda t: str(TS - 1))
    setp(scr, f'{p}_Gallery', 'TemplateSize', lambda t: str(TS))
    def heightf(t):
        t = t.replace(f'{gh} * Min({old_k},', f'{GH} * Min({new_k},'); return t.replace(f'- 1) * {old_k}))', f'- 1) * {new_k}))')
    assert setp(scr, f'{p}_Gallery', 'Height', heightf)
    assert setp(scr, f'{p}_Gallery', 'Items', lambda t: t.replace(f'- 1) * {old_k})), {old_k})', f'- 1) * {new_k})), {new_k})'))
    n = 0
    for c in walk(tp):
        for x in list(c['Rules']):
            if f'CountRows(colPrintReqMedia) / {old_k}' in x['InvariantScript'] and x['Property'] != 'OnVisible':
                n += setp(scr, c['Name'], x['Property'], lambda t: t.replace(f'CountRows(colPrintReqMedia) / {old_k}', f'CountRows(colPrintReqMedia) / {new_k}'))
    print(scr, 'sizes', nsz, 'geometry', ngeo, 'paging rules', n, 'TemplateSize', TS)
assert setp('PrintPodcastDetailScreen', 'PPoD_Val32', 'Text', lambda t: t.replace('Len(ThisItem.FTPPath) > 44, Left(ThisItem.FTPPath, 43)', 'Len(ThisItem.FTPPath) > 29, Left(ThisItem.FTPPath, 28)'))
# Export list
HP = 'HomePrintScreen'
for k in ('HP_RowRequest', 'HP_RowDescription', 'HP_RowDG', 'HP_RowArchives', 'HP_RowStatus', 'HP_RowDate', 'HP_RowDate_1'):
    assert setp(HP, k, 'Size', lambda t: '13' if t.strip() == '11' else t)
for k in ('HP_ThRequest', 'HP_ThDescription', 'HP_ThDG', 'HP_ThArchives', 'HP_ThStatus', 'HP_ThSubmitted', 'HP_ThDescription_1'):
    assert setp(HP, k, 'Size', lambda t: '12' if t.strip() == '11' else t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL197 built')
