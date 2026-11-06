#!/usr/bin/env python3
"""FINAL186 on FINAL185. The print screens of Video and Podcast show the FTP delivery path (Photo already did): one row at the END of the middle column, so no existing row moves.
Video: after 'AI voice-over' (two lines, ends before the 217 px row). Podcast: after 'Attached documents' (one line, long links cut with an ellipsis; ends before the row rule at 231)."""
import datetime, os, re, shutil
from payaml import App
from hp_common import Builder
SRC, NEW = 'newV47', 'newV48'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
FTP = 'ThisItem.FTPPath'
GREY, DARK = 'RGBA(150, 155, 165, 1)', 'RGBA(30, 34, 44, 1)'

b = Builder(app, 'PrintVideoDetailScreen')
b.clone('PVD_Val30', 'PrintVideoDetailScreen', 'PVD_Val28', {
    'Y': 'PVD_Val28.Y + If(PVD_Val28.Visible, PVD_Val28.Height, 0)', 'Height': '28',
    'Text': f'If(IsBlank({FTP}), "Not provided", {FTP})', 'Color': f'If(IsBlank({FTP}), {GREY}, {DARK})', 'Visible': 'true'}, parent='PVD_Gallery')
b.clone('PVD_Lbl30', 'PrintVideoDetailScreen', 'PVD_Lbl28', {'Y': 'PVD_Val30.Y', 'Text': '"FTP delivery path"', 'Visible': 'PVD_Val30.Visible'}, parent='PVD_Gallery')
b.save()

b = Builder(app, 'PrintPodcastDetailScreen')
b.clone('PPoD_Val32', 'PrintPodcastDetailScreen', 'PPoD_Val23', {
    'Y': 'PPoD_Val23.Y + If(PPoD_Val23.Visible, PPoD_Val23.Height, 0)', 'Height': '15',
    'Text': f'If(IsBlank({FTP}), "Not provided", If(Len({FTP}) > 44, Left({FTP}, 43) & "…", {FTP}))', 'Color': f'If(IsBlank({FTP}), {GREY}, {DARK})', 'Visible': 'true'}, parent='PPoD_Gallery')
b.clone('PPoD_Lbl32', 'PrintPodcastDetailScreen', 'PPoD_Lbl23', {'Y': 'PPoD_Val32.Y', 'Text': '"FTP delivery path"', 'Visible': 'PPoD_Val32.Visible'}, parent='PPoD_Gallery')
b.save()

app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL186 built')
