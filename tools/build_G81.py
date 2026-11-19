#!/usr/bin/env python3
"""FINAL91 on FINAL90: the Podcast block of the Metadata tab (Credits as a tall box on the left, Links over Pertinent tags on the right) becomes
the layout of all three production types. Links and tags were fixed at the Podcast height (Y 472 / 498 / ...), so Video and Photo showed them outside the
card. Now the block's top follows the production type:  Photo 398 | Video 372 | Podcast 462  (label Y; fields 26 below).
 Credits  X 56  W 606  H 114   Links X 678 W 606 (label Y, field Y+26)   Pertinent tags X 678 W 606 (label Y+74, field Y+100)
The AI voice-over warning and the card height make room under the block."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG80', 'newG81'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'ChildMetaScreen'; T = 'varChildMediaType'
def sw(p, v, po): return f'Switch({T}, "Photo", {p}, "Video", {v}, "Podcast", {po}, {p})'
def put(c, p, v): app.set(S, c, p, v)
Y0 = (398, 372, 462)
for c, dy in (('CM_LblCredits', 0), ('CM_Credits', 26), ('CM_LblLinksPhoto', 0), ('CM_LinksPhoto', 26), ('CM_LblTagsPhoto', 74), ('CM_TagsPhoto', 100)):
    put(c, 'Y', sw(*[y + dy for y in Y0]))
for c in ('CM_LblCredits', 'CM_Credits'): put(c, 'X', '56'); put(c, 'Width', '606')
for c in ('CM_LblLinksPhoto', 'CM_LinksPhoto', 'CM_LblTagsPhoto', 'CM_TagsPhoto'): put(c, 'X', '678'); put(c, 'Width', '606')
put('CM_Credits', 'Height', '114')
for c in ('CM_AIWarning', 'CM_AIWarningText'): put(c, 'Y', sw(548, 520, 790))
put('CM_Card', 'Height', f'Switch({T}, "Photo", 600, "Video", 553, "Podcast", 830, 553)')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL91 built')
