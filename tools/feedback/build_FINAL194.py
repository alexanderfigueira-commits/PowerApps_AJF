#!/usr/bin/env python3
"""FINAL194 on FINAL193. The media list of the request gets a PHOTOS column between TITLE and VALIDATION
(photo reportages show their number of photos, or a dash while none is typed; other types stay blank).
The second line under the title (FINAL192) is replaced by this column."""
import datetime, os, re, shutil
from payaml import App
from hp_common import Builder
SRC, NEW = 'newV55', 'newV56'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def setp(ctl, prop, val):
    t = app.rule(RS, ctl, prop); assert t != val, (ctl, prop); app.set(RS, ctl, prop, val, expect=t)
RS = 'RequesDetailScreen'
# title column narrower (row + header)
setp('RS_CRowTitle', 'Y', '9'); setp('RS_CRowTitle', 'Height', '47'); setp('RS_CRowTitle', 'Width', '300')
setp('RS_ThTitle', 'X', '180'); setp('RS_ThTitle', 'Width', '300')
# the photos cell becomes a column
setp('RS_CRowPhotos', 'X', '455'); setp('RS_CRowPhotos', 'Y', '1'); setp('RS_CRowPhotos', 'Width', '70'); setp('RS_CRowPhotos', 'Height', '55')
setp('RS_CRowPhotos', 'Size', '11'); setp('RS_CRowPhotos', 'PaddingTop', '5'); setp('RS_CRowPhotos', 'Color', 'RGBA(32, 31, 30, 1)')
setp('RS_CRowPhotos', 'Visible', 'true')
setp('RS_CRowPhotos', 'Text', 'If(\n    ThisItem.MediaType = "Photo",\n    If(Coalesce(ThisItem.NumberOfPhotos, 0) > 0, "📷 " & Text(ThisItem.NumberOfPhotos), "—"),\n    ""\n)')
setp('RS_CRowPhotos', 'Tooltip', 'If(ThisItem.MediaType = "Photo", "Number of photos in this reportage (typed on the Metadata tab)", "")')
b = Builder(app, RS)
b.clone('RS_ThPhotos', RS, 'RS_ThApproved', {'Text': '"PHOTOS"', 'X': '481', 'Y': '460', 'Width': '70', 'Height': '31'})
b.save()
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL194 built')
