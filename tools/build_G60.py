#!/usr/bin/env python3
"""FINAL70 on FINAL69: ChildMetaScreen gets one grid for Photo, Video and Podcast (4 columns at X 56 / 367 / 678 / 989, 295 wide, 16 gap;
labels 26 px above their fields, rows 90 px apart), replacing the Photo-only layout the Video and Podcast fields had been bolted onto
(Links sat on top of Producer, Credits and Summary overlapped, Tags/Exec producer collided).
  Photo   : dates/authority/photographer | caption | place + contractor | tags + links
  Video   : 4 dates | script | place, producer, executive producer | credits | tags + links
  Podcast : 4 dates | season, episode nr, episode title | summary | place, language, producer, executive producer | credits | tags + links | files
The screen stays one screen: the tabs, variables, validations and Save Media all read these controls by name."""
import datetime, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG59', 'newG60'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, G = 'ChildMetaScreen', 'CM_Gallery'
C = [56, 367, 678, 989]
T = 'varChildMediaType'
def sw(p, v, po):
    vals = [p, v, po]
    if vals[0] == vals[1] == vals[2]: return str(p)
    return f'Switch({T}, "Photo", {p}, "Video", {v}, "Podcast", {po}, {p})'
def put(ctl, prop, script):
    cur = app.rule(S, ctl, prop)
    if cur is None: sys.exit(f'! {ctl}.{prop} missing')
    app.set(S, ctl, prop, script)
def field(lbl, fld, p, v, po, h=None, lh=None):
    """p / v / po = (x, label_y, width) or None when the type does not show it"""
    d = {k: x for k, x in (('P', p), ('V', v), ('Po', po)) if x}
    base = next(iter(d.values()))
    g = lambda k, i: d.get(k, base)[i]
    for c, dy in ((lbl, 0), (fld, 26)):
        put(c, 'X', sw(g('P', 0), g('V', 0), g('Po', 0)))
        put(c, 'Y', sw(g('P', 1) + dy, g('V', 1) + dy, g('Po', 1) + dy))
        put(c, 'Width', sw(g('P', 2), g('V', 2), g('Po', 2)))
    if h: put(fld, 'Height', str(h))
    if lh: put(lbl, 'Height', str(lh))
W1, W2, W4 = 295, 606, 1228
field('CM_LblShootDate', 'CM_ShootDate', (C[0], 78, W1), (C[0], 78, W1), (C[0], 78, W1))
field('CM_LblAuthority', 'CM_Authority', (C[1], 78, W1), None, None)
field('CM_LblPhotographer', 'CM_Photographer', (C[2], 78, W1), None, None)
field('CM_LblProdEnd', 'CM_ProdEnd', None, (C[1], 78, W1), (C[1], 78, W1))
field('CM_LblPubStartV', 'CM_PubStartV', None, (C[2], 78, W1), (C[2], 78, W1))
field('CM_LblPubEndV', 'CM_PubEndV', None, (C[3], 78, W1), (C[3], 78, W1))
field('CM_LblCaptions', 'CM_Caption', (C[0], 168, W4), None, None, h=90)
field('CM_LblScript', 'CM_Script', None, (C[0], 168, W4), None, h=64)
field('CM_LblSeasonNumber', 'CM_SeasonNumber', None, None, (C[0], 168, 139))
field('CM_LblEpisodeNumber', 'CM_EpisodeNumber', None, None, (212, 168, 139))
field('CM_LblEpisodeTitleP', 'CM_EpisodeTitleP', None, None, (C[1], 168, 917), lh=22)
field('CM_LblEpisodeSummary', 'CM_EpisodeSummary', None, None, (C[0], 258, W4), h=64)
field('CM_LblPlacePhoto', 'CM_PlacePhoto', (C[0], 308, W1), (C[0], 282, W1), (C[0], 372, W1))
field('CM_LblCredits', 'CM_Credits', (C[1], 308, 917), (C[0], 372, W4), (C[0], 462, W4), h=40)
field('CM_LblLanguage', 'CM_Language', None, None, (C[1], 372, W1))
field('CM_LblProducer', 'CM_Producer', None, (C[1], 282, W1), (C[2], 372, W1))
field('CM_LblExecProducer', 'CM_ExecProducer', None, (C[2], 282, W1), (C[3], 372, W1))
field('CM_LblTagsPhoto', 'CM_TagsPhoto', (C[0], 398, W2), (C[0], 462, W2), (C[0], 552, W2))
field('CM_LblLinksPhoto', 'CM_LinksPhoto', (C[2], 398, W2), (C[2], 462, W2), (C[2], 552, W2))
# Podcast: episode files below the new last row; AI voice-over warning clear of every row
for c, y in (('CM_PodcastDivider', 640), ('CM_LblPodcastSection', 645), ('CM_HintEpisodeVisual', 676), ('CM_LblEpisodeVisual', 700),
             ('CM_BtnOpenEpisodeVisual', 726), ('CM_BtnViewEpisodeVisual', 726)):
    put(c, 'Y', str(y))
for c in ('CM_AIWarning', 'CM_AIWarningText'):
    put(c, 'Y', f'Switch({T}, "Photo", 480, "Video", 545, "Podcast", 790, 480)')
put('CM_Card', 'Height', f'If({T} = "Podcast", 830, 553)')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL70 built')
