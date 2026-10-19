#!/usr/bin/env python3
"""FINAL143 on FINAL142: the printed header is blue again, as on screen: top bar navy with white / light texts and the white EC logo, header card with its light grey fill (FINAL141 had made them white).
The row rules keep the border drawn as a line. The on-screen print hint says what the blue header needs: Background graphics on, Margins: None."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV2', 'newV3'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
def back(screen, ctl, prop, orig):
    t = app.rule(screen, ctl, prop)
    assert t.startswith('If(locPrinting, ') and t.endswith(', ' + orig + ')'), (screen, ctl, prop, t)
    app.set(screen, ctl, prop, orig, expect=t)
for screen, P in (('PrintPhotoDetailScreen', 'PPD'), ('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD')):
    back(screen, f'{P}_TopBar', 'Fill', 'RGBA(0, 18, 107, 1)')
    back(screen, f'{P}_TopBar', 'BorderThickness', '0')
    back(screen, f'{P}_Header_Title', 'Color', 'RGBA(255, 255, 255, 1)')
    back(screen, f'{P}_RoleTag', 'Color', 'RGBA(255, 255, 255, 1)')
    back(screen, f'{P}_Header_UserName', 'Color', 'RGBA(186, 202, 226, 1)')
    back(screen, f'{P}_Header_Subtitle', 'Color', 'RGBA(186, 202, 226, 1)')
    back(screen, f'{P}_Header_LogoEC', 'Image', "'LOGO CE_EN_RGB_HORIZONTAL_NEG1'")
    back(screen, f'{P}_HeaderCard', 'Fill', 'RGBA(247, 248, 250, 1)')
    back(screen, f'{P}_HeaderCard', 'BorderThickness', '0')
    back(screen, f'{P}_HeaderCard', 'BorderColor', 'RGBA(0, 18, 107, 1)')
    t = app.rule(screen, f'{P}_PrintHint', 'Text')
    app.set(screen, f'{P}_PrintHint', 'Text', '"Printed in landscape. Print dialog: A4 · Margins: None · Background graphics: on"', expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL143 built')
