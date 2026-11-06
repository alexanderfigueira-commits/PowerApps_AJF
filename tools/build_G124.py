#!/usr/bin/env python3
"""FINAL134 on TEST_9: PrintPhotoDetailScreen / PrintVideoDetailScreen / PrintPodcastDetailScreen print ALL the media files on A4 landscape sheets.
Print() prints the screen as it is on one page and cannot paginate, so each screen shows one page of media rows at a time (3 per page for Photo, 2 for Video and Podcast, as many as fit
between the header card and the footer): "Page x of y" navigation (hidden while printing), the page number in the footer, and the "+ n more" notice replaced by "Continued on page ...".
The gallery height now follows the row height (Photo had 200 x rows on 172-high rows, which pushed the last row over the footer)."""
import datetime, os, re, shutil
from payaml import App, find
from hp_common import Builder
SRC, NEW = 'newT9b', 'newU1'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
eol = lambda t: '\r\n' if '\r\n' in t else '\n'
def put(screen, ctl, prop, new, old_expect=None):
    t = app.rule(screen, ctl, prop)
    app.set(screen, ctl, prop, new.replace('\n', eol(t)), expect=old_expect if old_expect is not None else t)
CFG = (('PrintPhotoDetailScreen', 'PPD'), ('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD'))
meta = {}
for screen, P in CFG:
    G = f'{P}_Gallery'
    R = int(app.rule(screen, G, 'TemplateSize')); Y0 = int(app.rule(screen, G, 'Y'))
    RPP = (740 - Y0) // R                      # whole rows between the header card and the footer (footer at 744)
    assert RPP >= 2, (screen, RPP)
    meta[screen] = (P, R, RPP)
    PAGES = f'Max(1, RoundUp(CountRows(colPrintReqMedia) / {RPP}, 0))'
    PAGE = 'Coalesce(locPage, 1)'
    LEFT = f'Max(0, CountRows(colPrintReqMedia) - ({PAGE} - 1) * {RPP})'
    put(screen, G, 'Items', f'FirstN(LastN(colPrintReqMedia, {LEFT}), {RPP})', 'colPrintReqMedia')
    put(screen, G, 'Height', f'// the rows of this page only: a row is never cut by the page edge\n{R} * Min({RPP}, {LEFT})')
    put(screen, f'{P}_More', 'Text', f'"Continued on page " & ({PAGE} + 1) & " of " & {PAGES}')
    put(screen, f'{P}_More', 'Visible', f'{PAGE} < {PAGES}')
    t = app.rule(screen, f'{P}_Footer', 'Text')
    assert t.endswith('Text(Today(), "dd-mm-yyyy")')
    put(screen, f'{P}_Footer', 'Text', t + f' & If({PAGES} > 1, "  ·  Page " & {PAGE} & " of " & {PAGES}, "")', t)
    t = app.rule(screen, None, 'OnVisible')
    put(screen, None, 'OnVisible', t.rstrip() + ';\nUpdateContext({locPage: 1})', t)
app.save()

class NB(Builder):
    def grouped(self, tp): return set()
for screen, P in CFG:
    _, R, RPP = meta[screen]
    PAGES = f'Max(1, RoundUp(CountRows(colPrintReqMedia) / {RPP}, 0))'
    PAGE = 'Coalesce(locPage, 1)'
    b = NB(app, screen)
    b.clone(f'{P}_BtnPrevPage', screen, f'{P}_BtnBack', {
        'Text': '"◀"', 'X': '790', 'Y': '68', 'Width': '48', 'Height': '40',
        'OnSelect': f'UpdateContext({{locPage: Max(1, {PAGE} - 1)}})',
        'Visible': f'Not(locPrinting) And {PAGES} > 1',
        'DisplayMode': f'If({PAGE} <= 1, DisplayMode.Disabled, DisplayMode.Edit)',
        'Tooltip': '"Previous page"'})
    b.clone(f'{P}_PageLbl', screen, f'{P}_Footer', {
        'Text': f'"Page " & {PAGE} & " of " & {PAGES}', 'X': '842', 'Y': '76', 'Width': '112', 'Height': '24',
        'Align': 'Align.Center', 'Size': '12', 'FontWeight': 'FontWeight.Semibold',
        'Visible': f'Not(locPrinting) And {PAGES} > 1'})
    b.clone(f'{P}_BtnNextPage', screen, f'{P}_BtnBack', {
        'Text': '"▶"', 'X': '958', 'Y': '68', 'Width': '48', 'Height': '40',
        'OnSelect': f'UpdateContext({{locPage: Min({PAGES}, {PAGE} + 1)}})',
        'Visible': f'Not(locPrinting) And {PAGES} > 1',
        'DisplayMode': f'If({PAGE} >= {PAGES}, DisplayMode.Disabled, DisplayMode.Edit)',
        'Tooltip': '"Next page"'})
    b.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print(meta)
print('FINAL134 built')
