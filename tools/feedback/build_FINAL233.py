#!/usr/bin/env python3
"""FINAL233 on FINAL232. PDF page header (Photo, Video and Podcast print sheets): the app's brand block - European Commission
logo, Central Deposit badge, "Central Deposit" / "Ticket System" on the dark blue of the app's top bar - is printed centred at
the top of every page header. The header's two lines (request title, created by / DG / dates) stay aligned on the left, just
under it; the media file under a page header starts 52 px lower (108 instead of 56). Only in the PDF (page header rows)."""
import datetime, os, re, shutil
from payaml import App
from hp_common import Builder
SRC, NEW = 'newV94', 'newV95'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))


def setp(scr, ctl, prop, val, old=None):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if old is not None: assert t.strip() == old, (scr, ctl, prop, t)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)


def rep(scr, ctl, prop, old, new, count=1):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    assert t.count(old) == count, (scr, ctl, prop, t.count(old), old[:80])
    app.set(scr, ctl, prop, t.replace(old, new), expect=t)


BW = 450          # brand block width
SHIFT = 52        # header lines and first media file move down
n_rect = n_img = n_lbl = 0
for scr, p in (('PrintPhotoDetailScreen', 'PPD'), ('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD')):
    gal = f'{p}_Gallery'
    vis = app.rule(scr, f'{p}_PgHdrBg', 'Visible')
    L = f'(Parent.TemplateWidth - {BW}) / 2'
    # the header lines move under the brand block
    setp(scr, f'{p}_PgHdrBg', 'Y', str(SHIFT), '0')
    setp(scr, f'{p}_PgHdrTitle', 'Y', str(2 + SHIFT), '2')
    setp(scr, f'{p}_PgHdrInfo', 'Y', str(29 + SHIFT), '29')
    rep(scr, f'{p}_RowCaption', 'Y', 'Mod(ThisItem.PdfRowNo, 2) = 1), 56, 0)', f'Mod(ThisItem.PdfRowNo, 2) = 1), {56 + SHIFT}, 0)')
    zmax = max(int(app.rule(scr, c['Name'], 'ZIndex') or 0) for c in hp_common.find(app.doc(scr)['TopParent'], gal)['Children']
               if app.rule(scr, c['Name'], 'ZIndex') is not None)
    b = Builder(app, scr)
    b.clone(f'{p}_PdfBrandBg', scr, f'{p}_PgHdrBg', {
        'X': L, 'Y': '0', 'Width': str(BW), 'Height': '50', 'Fill': 'RGBA(0, 18, 107, 1)', 'Visible': vis, 'ZIndex': str(zmax + 1)}, parent=gal)
    b.clone(f'{p}_PdfBrandLogoEC', 'ChildInfoScreen', 'CI_VisualImage', {'AccessibleLabel': '"European Commission"', 'BorderColor': 'RGBA(0, 18, 107, 1)', 'BorderThickness': '0', 'CalculateOriginalDimensions': 'false', 'Fill': 'RGBA(0, 0, 0, 0)', 'Tooltip': '""', 'PaddingLeft': '10',
        'Image': "'LOGO CE_EN_RGB_HORIZONTAL_NEG1'", 'ImagePosition': 'ImagePosition.Fit',
        'X': f'{L} + 4', 'Y': '1', 'Width': '186', 'Height': '48', 'Visible': vis, 'ZIndex': str(zmax + 2)}, parent=gal)
    b.clone(f'{p}_PdfBrandLogoCD', 'ChildInfoScreen', 'CI_VisualImage', {'AccessibleLabel': '"Central Deposit"', 'BorderColor': 'RGBA(0, 18, 107, 1)', 'BorderThickness': '0', 'CalculateOriginalDimensions': 'false', 'Fill': 'RGBA(0, 0, 0, 0)', 'Tooltip': '""', 'PaddingLeft': '0',
        'Image': 'cd_badge_play', 'ImagePosition': 'ImagePosition.Fit',
        'X': f'{L} + 208', 'Y': '10', 'Width': '30', 'Height': '30', 'Visible': vis, 'ZIndex': str(zmax + 3)}, parent=gal)
    b.clone(f'{p}_PdfBrandTitle', scr, f'{p}_PgHdrTitle', {
        'Text': '"Central Deposit"', 'X': f'{L} + 242', 'Y': '1', 'Width': '200', 'Height': '32', 'Size': '14',
        'Color': 'RGBA(255, 255, 255, 1)', 'FontWeight': 'FontWeight.Semibold', 'Visible': vis, 'ZIndex': str(zmax + 4)}, parent=gal)
    b.clone(f'{p}_PdfBrandSub', scr, f'{p}_PgHdrInfo', {
        'Text': '"Ticket System"', 'X': f'{L} + 264', 'Y': '24', 'Width': '170', 'Height': '22', 'Size': '10',
        'Color': 'RGBA(186, 202, 226, 1)', 'Visible': vis, 'ZIndex': str(zmax + 5)}, parent=gal)
    b.save()
    # the image donor (the Info screen's podcast visual, the only image outside a group) has no click; tooltip cleared above
    for nm in (f'{p}_PdfBrandLogoEC', f'{p}_PdfBrandLogoCD'):
        for prop in ('OnSelect', 'Tooltip'):
            t = app.rule(scr, nm, prop)
            if t is not None and t.strip() not in ('false', '""', ''):
                app.set(scr, nm, prop, 'false' if prop == 'OnSelect' else '""', expect=t)
    n_rect += 1; n_img += 2; n_lbl += 2
p_ = f'{NEW}/Properties.json'
raw = open(p_, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
for key, k in (('rectangle', n_rect), ('image', n_img), ('label', n_lbl)):
    t = re.sub(r'("%s"\s*:\s*)(\d+)' % key, lambda mm: mm.group(1) + str(int(mm.group(2)) + k), t, count=1)
open(p_, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL233 built')
