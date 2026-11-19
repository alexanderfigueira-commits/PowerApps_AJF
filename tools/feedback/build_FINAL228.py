#!/usr/bin/env python3
"""FINAL228 on FINAL227. PDF of the three print sheets, both ways (2 media per page and 1 per page / full descriptions):
- the full-width rows (Photo: Description, Photo caption / Short Description; Video: Description; Podcast: Description of the
  podcast, Summary of the episode) print their whole text, no more "…" cut;
- their font size is the biggest that lets all of it fit above the page footer: 2 per page from 10 down to 7, 1 per page from
  12 down to 8 (a hidden label per row, <p>_FwFit, works it out from the room left under the field grid);
- each row is as tall as its text or its name needs, so the field names ("Photo caption / Short Description", ...) are never cut."""
import datetime, math, os, re, shutil
from payaml import App
from hp_common import Builder
SRC, NEW = 'newV89', 'newV90'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))


def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)


def lh(s): return math.ceil(s * 1.3333 * 1.40)
def cpl(s, w): return max(4, int((w - 12) / (s * 1.3333 * 0.57) * 0.92))


def lines_wrapped(text, per):
    """lines a label needs with word wrap (a word longer than a line is split)."""
    n, cur = 1, 0
    for w in text.split(' '):
        L = len(w)
        if cur == 0: cur = L
        elif cur + 1 + L <= per: cur += 1 + L
        else: n += 1; cur = L
        while cur > per: n += 1; cur -= per
    return n


SIZES = [12, 11, 10, 9, 8, 7]
FULL = 'Coalesce(locPdfFull, false)'
LH = 'Switch(s, ' + ', '.join(f'{s}, {lh(s)}' for s in SIZES[:-1]) + f', {lh(SIZES[-1])})'
CPL = 'Switch(s, ' + ', '.join(f'{s}, {cpl(s, 1096)}' for s in SIZES[:-1]) + f', {cpl(SIZES[-1], 1096)})'


def ll_expr(label):
    """lines of a field name at its size: the value's size on 1 per page, one point smaller on 2 per page (width 180)."""
    full = 'Switch(s, ' + ', '.join(f'{s}, {lines_wrapped(label, cpl(s, 180))}' for s in SIZES[:-1]) + f', {lines_wrapped(label, cpl(SIZES[-1], 180))})'
    half = 'Switch(s, ' + ', '.join(f'{s}, {lines_wrapped(label, cpl(s - 1, 180))}' for s in SIZES[:-1]) + f', {lines_wrapped(label, cpl(SIZES[-1] - 1, 180))})'
    return f'If({FULL}, {full}, {half})'


SHEETS = [('PrintPhotoDetailScreen', 'PPD', ['FwDesc', 'FwCaption']),
          ('PrintVideoDetailScreen', 'PVD', ['FwDesc']),
          ('PrintPodcastDetailScreen', 'PPoD', ['FwDesc', 'FwSummary'])]
OLD_TXT = re.compile(r'^With\(\n    \{t: (.*), n: If\(Coalesce\(locPdfFull, false\), 500, 262\)\},\n    If\(Len\(t\) > n, Left\(t, n - 1\) & "…", t\)\n\)$', re.S)
added = 0
for scr, p, rows in SHEETS:
    info = []
    for r in rows:
        t = app.rule(scr, f'{p}_{r}', 'Text'); m = OLD_TXT.match(t.strip()); assert m, (scr, r, t)
        expr = m.group(1)
        label = app.rule(scr, f'{p}_{r}Lbl', 'Text').strip().strip('"')
        info.append((r, expr, label))
    # the hidden helper: the font size of this row's full-width texts (a line break counts as one more line)
    terms = ' + '.join(
        f'If(L{i} > 0, Max(RoundUp(L{i} / {CPL}, 0) + N{i}, {ll_expr(label)}) * {LH} + 2, 0)' for i, (_, _, label) in enumerate(info))
    lens = ', '.join(f'L{i}: Len({expr}), N{i}: Len({expr}) - Len(Substitute({expr}, Char(10), ""))' for i, (_, expr, _) in enumerate(info))
    fit = (f'// FINAL228: font size of the full-width rows below the grid: the biggest that lets ALL their text and names fit above the\n'
           f'// page footer (1 per page: 12 to 8; 2 per page: 10 to 7)\n'
           f'With(\n'
           f'    {{a: If({FULL}, 868, If(Mod(Coalesce(ThisItem.PdfRowNo, 0), 2) = 0, 420, 444)) - {p}_FwDesc.Y, {lens}}},\n'
           f'    Text(Coalesce(\n'
           f'        First(Filter(\n'
           f'            ForAll([{", ".join(map(str, SIZES))}] As z, {{s: z.Value}}),\n'
           f'            s <= If({FULL}, 12, 10) And s >= If({FULL}, 8, 7) And ({terms}) <= a\n'
           f'        )).s,\n'
           f'        If({FULL}, 8, 7)\n'
           f'    ))\n'
           f')')
    gal = f'{p}_Gallery'
    b = Builder(app, scr)
    b.clone(f'{p}_FwFit', scr, f'{p}_FwDescLbl', {'Text': fit, 'X': '0', 'Y': '0', 'Width': '10', 'Height': '10', 'Visible': 'false'}, parent=gal)
    b.save()
    added += 1
    for r, expr, label in info:
        S = f'Value({p}_FwFit.Text)'
        setp(scr, f'{p}_{r}', 'Text', f'// the whole text (FINAL228): its size comes from {p}_FwFit so that it fits the page\n{expr}')
        setp(scr, f'{p}_{r}', 'Size', S)
        setp(scr, f'{p}_{r}', 'Height',
             f'// as tall as the text or its name needs, at the size {p}_FwFit chose\n'
             f'With({{s: {S}}}, {LH} * Max({ll_expr(label)}, RoundUp(Len(Self.Text) / {CPL}, 0) + Len(Self.Text) - Len(Substitute(Self.Text, Char(10), ""))))')
        setp(scr, f'{p}_{r}Lbl', 'Size', f'With({{s: {S}}}, If({FULL}, s, s - 1))')
p_ = f'{NEW}/Properties.json'
raw = open(p_, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
t = re.sub(r'("label"\s*:\s*)(\d+)', lambda mm: mm.group(1) + str(int(mm.group(2)) + added), t, count=1)
open(p_, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL228 built')
