#!/usr/bin/env python3
"""FINAL109 on FINAL108: the STATUS badge of the media table (RS_CRowBadge) takes the look of the blue REF badge (DOA_List1RowBadge_8): pill radius 14, height 29, size 12, 1 px border,
blue fill / dark text where the old rules gave the light grey. The state colours stay as they were (approved link = green, archive only = dark grey) and the disabled look now follows them."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newJ9', 'newJ10'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, C = 'RequesDetailScreen', 'RS_CRowBadge'
def sub(prop, old, new):
    t = app.rule(S, C, prop); eol = '\r\n' if '\r\n' in t else '\n'; n = t.replace('\r\n', '\n')
    assert n.count(old) == 1, prop
    app.set(S, C, prop, n.replace(old, new).replace('\n', eol), expect=t)
sub('Fill', 'RGBA(22, 128, 80, 1), RGBA(236, 238, 242, 1))', 'RGBA(22, 128, 80, 1), RGBA(215, 223, 240, 1))')          # pending / none: REF blue
sub('Color', 'RGBA(255, 255, 255, 1), RGBA(110, 118, 132, 1))', 'RGBA(255, 255, 255, 1), RGBA(0, 13, 75, 1))')            # ... with the REF text colour
# the states shown read-only (archive, pending, none) were drawn with the generic grey disabled look: they follow their own colours now
for p, old, new in (('DisabledFill', 'RGBA(244, 244, 244, 1)', 'Self.Fill'), ('DisabledColor', 'RGBA(166, 166, 166, 1)', 'Self.Color')):
    app.set(S, C, p, new, expect=old)
for p, old, new in (('BorderThickness', '0', '1'), ('Height', '34', '29'), ('Y', '8', '14'), ('Size', '10', '12'), ('X', '756', '751'), ('Width', '140', '150'),
                    ('RadiusTopLeft', '10', '14'), ('RadiusTopRight', '10', '14'), ('RadiusBottomLeft', '10', '14'), ('RadiusBottomRight', '10', '14')):
    app.set(S, C, p, new, expect=old)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL109 built')
