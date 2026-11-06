#!/usr/bin/env python3
"""FINAL66 on FINAL65: the three print pages show everything the media tabs show.
Photo   + Beluga reference; Photographer moved next to the metadata; Legal & Documents (contract case, case 1 documents, no third-party
          rights, model release provided, attached documents)
Video   + Beluga reference, AI voice-over, attached documents
Podcast + Beluga reference, AI voice-over, Files (podcast visual, episode visual, audio files, attached documents), Legal & Documents
          (contract case, case 1 documents, no third-party rights, model release, music used / licence, pre-existing rights)
Rows grow with the content (172 / 202 / 232), so a printed page holds 3 / 2 / 2 media files; the gallery height and the '+ n more' note follow."""
import datetime, os, re, shutil, sys
from payaml import App
from hp_common import Builder
SRC, NEW = 'newG55', 'newG56'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
DARK, GREY = 'RGBA(30, 34, 44, 1)', 'RGBA(150, 155, 165, 1)'
YF = lambda p: f'{p}.Y + If({p}.Visible, {p}.Height, 0)'
IMG = 'EndsWith(Lower(DisplayName), ".jpg") Or EndsWith(Lower(DisplayName), ".jpeg") Or EndsWith(Lower(DisplayName), ".png")'
AUDIO = 'EndsWith(Lower(DisplayName), ".mp3") Or EndsWith(Lower(DisplayName), ".wav") Or EndsWith(Lower(DisplayName), ".m4a") Or EndsWith(Lower(DisplayName), ".aac")'
YESNO = lambda col: f'If(ThisItem.{col}, "✅  Yes", "⛔  No")'
BELUGA = 'If(IsBlank(ThisItem.BelugaReference), "Not provided", ThisItem.BelugaReference)'
CASE = 'If(IsEmpty(ThisItem.ContractCase), "Not provided", Concat(ThisItem.ContractCase, Value, ", "))'
CASE1 = 'If(IsEmpty(ThisItem.ContractCase1Sub), "Not provided", Concat(ThisItem.ContractCase1Sub, Value, ", "))'
AIV = 'If(ThisItem.AIVoiceover = "Yes", "⚠  Yes", "No")'
COLS = {1: (12, 194), 2: (442, 624), 3: (872, 1054)}

def run(scr, pre, donors, rows, cap_rows, R, edits, specs):
    for ctl, prop, val in edits:
        app.set(scr, ctl, prop, val, expect=app.rule(scr, ctl, prop))
    b = Builder(app, scr); G = pre + '_Gallery'
    dl, dv, ds = donors
    for s in specs:
        kind, n, col = s[0], s[1], s[2]
        lx, vx = COLS[col]
        if kind == 'sec':
            _, n, col, text, yexpr, vis = s
            b.clone(f'{pre}_Sec{n}', scr, ds, {'Text': f'"{text}"', 'X': str(lx), 'Y': yexpr, 'Visible': vis}, parent=G)
        else:
            _, n, col, label, text, vis, h, yexpr, color = s
            b.clone(f'{pre}_Lbl{n}', scr, dl, {'Text': f'"{label}"', 'X': str(lx), 'Y': f'{pre}_Val{n}.Y', 'Visible': f'{pre}_Val{n}.Visible'}, parent=G)
            b.clone(f'{pre}_Val{n}', scr, dv, {'Text': text, 'X': str(vx), 'Y': yexpr, 'Visible': vis, 'Height': str(h), 'Color': color or DARK}, parent=G)
    b.save()
    # row height, gallery height, row rule, "more" note
    gal = app.rule(scr, G, 'Height'); ts = app.rule(scr, G, 'TemplateSize')
    app.set(scr, G, 'TemplateSize', str(R), expect=ts)
    app.set(scr, G, 'Height', f'// whole media rows only: a row is never cut by the page edge\n{R} * Min(CountRows(colPrintReqMedia), RoundDown((740 - Self.Y) / {R}, 0))', expect=gal)
    app.set(scr, pre + '_RowRule', 'Y', str(R - 1), expect=app.rule(scr, pre + '_RowRule', 'Y'))
    m = app.rule(scr, pre + '_More', 'Text'); v = app.rule(scr, pre + '_More', 'Visible')
    old = re.search(r'CountRows\(colPrintReqMedia\) - (\d+)', m).group(1)
    new = re.sub(r'(CountRows\(colPrintReqMedia\) - )\d+', lambda x: x.group(1) + str(cap_rows), m).replace(f'holds {old}.', f'holds {cap_rows}.')
    assert new != m
    app.set(scr, pre + '_More', 'Text', new, expect=m)
    app.set(scr, pre + '_More', 'Visible', v.replace(f'> {old}', f'> {cap_rows}'), expect=v)

# ---------------- Photo ----------------
P = 'PPD'
run('PrintPhotoDetailScreen', P, ('PPD_Lbl6', 'PPD_Val7', 'PPD_Sec5'), None, 3, 172,
    [('PPD_Lbl13', 'X', '442'), ('PPD_Val13', 'X', '624'), ('PPD_Val13', 'Y', YF('PPD_Val9'))],
    [('f', 14, 1, 'Beluga reference', BELUGA, 'Not(IsBlank(ThisItem.BelugaReference))', 15, YF('PPD_Val4'), None),
     ('sec', 15, 3, 'Legal & Documents', YF('PPD_Val12'), 'true'),
     ('f', 16, 3, 'Contract case', CASE, 'Not(IsEmpty(ThisItem.ContractCase))', 15, YF('PPD_Sec15'), None),
     ('f', 17, 3, 'Case 1 — required documents', CASE1, 'Not(IsEmpty(ThisItem.ContractCase1Sub))', 15, YF('PPD_Val16'), None),
     ('f', 18, 3, 'No third-party rights', YESNO('NoThirdPartyRights'), 'true', 15, YF('PPD_Val17'), None),
     ('f', 19, 3, 'Model release provided', YESNO('ModelReleaseProvided'), 'true', 15, YF('PPD_Val18'), None),
     ('f', 20, 3, 'Attached documents', 'Concat(ThisItem.Attachments, DisplayName, ", ")', 'Not(IsEmpty(ThisItem.Attachments))', 28, YF('PPD_Val19'), None)])
# ---------------- Video ----------------
V = 'PVD'
run('PrintVideoDetailScreen', V, ('PVD_Lbl2', 'PVD_Val3', 'PVD_Sec19'), None, 2, 202,
    [('PVD_Sec6', 'Y', YF('PVD_Val27'))],
    [('f', 27, 1, 'Beluga reference', BELUGA, 'Not(IsBlank(ThisItem.BelugaReference))', 15, YF('PVD_Val5'), None),
     ('f', 28, 2, 'AI voice-over', AIV, 'true', 15, YF('PVD_Val16'), None),
     ('f', 29, 3, 'Attached documents', 'Concat(ThisItem.Attachments, DisplayName, ", ")', 'Not(IsEmpty(ThisItem.Attachments))', 28, YF('PVD_Val26'), None)])
# ---------------- Podcast ----------------
Q = 'PPoD'
PV = f'Filter(ThisItem.Attachments, Not(StartsWith(DisplayName, "EpisodeVisual_")) And ({IMG}))'
EV = f'Filter(ThisItem.Attachments, StartsWith(DisplayName, "EpisodeVisual_") And ({IMG}))'
AU = f'Filter(ThisItem.Attachments, {AUDIO})'
DOCS = f'Filter(ThisItem.Attachments, Not({IMG}) And Not({AUDIO}))'
def files(f): return (f'If(IsEmpty({f}), "Not provided", Concat({f}, DisplayName, ", "))', f'If(IsEmpty({f}), {GREY}, {DARK})')
run('PrintPodcastDetailScreen', Q, ('PPoD_Lbl1', 'PPoD_Val1', 'PPoD_Sec0'), None, 2, 232,
    [],
    [('f', 17, 1, 'Beluga reference', BELUGA, 'Not(IsBlank(ThisItem.BelugaReference))', 15, YF('PPoD_Val5'), None),
     ('f', 18, 1, 'AI voice-over', AIV, 'true', 15, YF('PPoD_Val17'), None),
     ('sec', 19, 2, 'Files', YF('PPoD_Val11'), 'true'),
     ('f', 20, 2, 'Podcast visual', files(PV)[0], 'true', 15, YF('PPoD_Sec19'), files(PV)[1]),
     ('f', 21, 2, 'Episode visual', files(EV)[0], 'true', 15, YF('PPoD_Val20'), files(EV)[1]),
     ('f', 22, 2, 'Audio files', files(AU)[0], 'true', 28, YF('PPoD_Val21'), files(AU)[1]),
     ('f', 23, 2, 'Attached documents', f'Concat({DOCS}, DisplayName, ", ")', f'Not(IsEmpty({DOCS}))', 28, YF('PPoD_Val22'), None),
     ('sec', 24, 3, 'Legal & Documents', YF('PPoD_Val16'), 'true'),
     ('f', 25, 3, 'Contract case', CASE, 'Not(IsEmpty(ThisItem.ContractCase))', 15, YF('PPoD_Sec24'), None),
     ('f', 26, 3, 'Case 1 — required documents', CASE1, 'Not(IsEmpty(ThisItem.ContractCase1Sub))', 15, YF('PPoD_Val25'), None),
     ('f', 27, 3, 'No third-party rights', YESNO('NoThirdPartyRights'), 'true', 15, YF('PPoD_Val26'), None),
     ('f', 28, 3, 'Model release provided', YESNO('ModelReleaseProvided'), 'true', 15, YF('PPoD_Val27'), None),
     ('f', 29, 3, 'Music used', YESNO('MusicUsed'), 'true', 15, YF('PPoD_Val28'), None),
     ('f', 30, 3, 'Music licence provided', YESNO('MusicLicenseProvided'), 'true', 15, YF('PPoD_Val29'), None),
     ('f', 31, 3, 'Pre-existing rights provided', YESNO('PreexistingRightsProvided'), 'true', 15, YF('PPoD_Val30'), None)])
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL66 built')
