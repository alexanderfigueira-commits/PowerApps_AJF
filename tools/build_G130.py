#!/usr/bin/env python3
"""FINAL141 on FINAL140: the print screens no longer need "Background graphics" in the print dialog.
While printing (locPrinting): the top bar is white with a navy outline (it was a navy fill with white text, which vanished without background graphics), the header texts are navy / dark grey, the header card is white with a
light outline, the row rules are drawn with their border, and the EC logo is the coloured one ('logo--en', already in the app) instead of the white-on-blue one. On screen nothing changes."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newU6', 'newV1'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
NAVY, WHITE = 'RGBA(0, 18, 107, 1)', 'RGBA(255, 255, 255, 1)'
def pr(screen, ctl, prop, print_val):
    t = app.rule(screen, ctl, prop)
    app.set(screen, ctl, prop, f'If(locPrinting, {print_val}, {t.strip()})', expect=t)
for screen, P in (('PrintPhotoDetailScreen', 'PPD'), ('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD')):
    pr(screen, f'{P}_TopBar', 'Fill', WHITE)
    pr(screen, f'{P}_TopBar', 'BorderThickness', '2')
    pr(screen, f'{P}_Header_Title', 'Color', NAVY)
    pr(screen, f'{P}_RoleTag', 'Color', NAVY)
    pr(screen, f'{P}_Header_UserName', 'Color', 'RGBA(60, 66, 80, 1)')
    pr(screen, f'{P}_Header_Subtitle', 'Color', 'RGBA(60, 66, 80, 1)')
    pr(screen, f'{P}_Header_LogoEC', 'Image', "'logo--en'")
    pr(screen, f'{P}_HeaderCard', 'Fill', WHITE)
    pr(screen, f'{P}_HeaderCard', 'BorderThickness', '1')
    pr(screen, f'{P}_HeaderCard', 'BorderColor', 'RGBA(200, 205, 215, 1)')
    pr(screen, f'{P}_RowRule', 'BorderThickness', '1')
    pr(screen, f'{P}_RowRule', 'BorderColor', 'RGBA(200, 205, 215, 1)')
    t = app.rule(screen, f'{P}_PrintHint', 'Text')
    app.set(screen, f'{P}_PrintHint', 'Text', '"Printed in landscape, no background graphics needed. Dialog: A4 · Margins: None"', expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL141 built')
