#!/usr/bin/env python3
"""FINAL79 on FINAL78: audit of ChildMetaScreen against the three print pages. Every metadata column the Metadata tab saves already had a
printed counterpart for its production type; what made data look missing was (a) empty mandatory (*) fields being hidden instead of printed
as 'Not provided' and (b) labels that differ from the tab. Now:
 - every mandatory metadata field of the type is always printed ('Not provided' in grey when empty)
     Photo   : Contracting authority, Contractor / Agency, Photo caption, Shooting date, Place, Name of the photographer
     Video   : Filming date, Production end date, Publication start / end date, Production place, Producer
     Podcast : Title / Season / Episode nr. / Summary / Language, Producer, Filming date, Production end date, Publication start / end date, Production place
 - the labels use the wording of the Metadata tab"""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG68', 'newG69'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
ALWAYS = {('PrintPhotoDetailScreen', 'PPD'): (6, 7, 8, 9, 10, 13),
          ('PrintVideoDetailScreen', 'PVD'): (9, 11, 12, 13, 14, 15),
          ('PrintPodcastDetailScreen', 'PPoD'): (1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13)}
for (scr, pre), ids in ALWAYS.items():
    for i in ids:
        app.set(scr, f'{pre}_Val{i}', 'Visible', 'true')
LABELS = [('PrintPhotoDetailScreen', 'PPD_Lbl7', 'Contractor / credits', 'Contractor / Agency'),
          ('PrintPhotoDetailScreen', 'PPD_Lbl8', 'Photo caption', 'Photo caption / Short Description'),
          ('PrintPhotoDetailScreen', 'PPD_Lbl9', 'Capture / shoot date', 'Shooting date'),
          ('PrintPhotoDetailScreen', 'PPD_Lbl10', 'Production place', 'Place'),
          ('PrintPhotoDetailScreen', 'PPD_Lbl13', 'Photographer', 'Name of the photographer'),
          ('PrintVideoDetailScreen', 'PVD_Lbl11', 'Shoot date', 'Filming date'),
          ('PrintPodcastDetailScreen', 'PPoD_Lbl9', 'Recording date', 'Filming date')]
for scr, c, old, new in LABELS:
    app.set(scr, c, 'Text', f'"{new}"', expect=f'"{old}"')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL79 built')
