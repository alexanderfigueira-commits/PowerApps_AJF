#!/usr/bin/env python3
"""FINAL184 on FINAL183. ChildMetaScreen: the controls that sat ABOVE the blue shades of the pop-ups in the stacking order (the four tabs, the Draft badge, the media-number badge, the
'Media File' title and the active-tab underline) move BELOW them, so that when the audio-files window, the episode-visual window or the episode-visual preview opens, every
component of the screen is dimmed under the shade and only the pop-up stays in front.
Stacking order is the ZIndex rule in Controls/*.json and, equally, the order of the controls in Src/ChildMetaScreen.pa.yaml (back to front): both are rewritten."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV45', 'newV46'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'ChildMetaScreen'
top = app.doc(S)['TopParent']
kids = {c['Name']: c for c in top['Children']}
z = lambda n: int([r['InvariantScript'] for r in kids[n]['Rules'] if r['Property'] == 'ZIndex'][0])
def setz(n, v):
    [r for r in kids[n]['Rules'] if r['Property'] == 'ZIndex'][0]['InvariantScript'] = str(v)

# YAML order = stacking order, back to front
yf = f'{NEW}/Src/{S}.pa.yaml'
lines = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
starts = [(i, m.group(1)) for i, l in enumerate(lines) for m in [re.match(r'^      - ([A-Za-z0-9_]+):\s*$', l)] if m]
yaml_order = [n for _, n in starts]
groups = {n for n, c in kids.items() if c.get('IsGroupControl')}
plain = [n for n in yaml_order]                          # all top-level controls in the YAML are non-group
assert [z(n) for n in plain] == sorted(z(n) for n in plain), 'YAML order is not the ZIndex order'

MOVED = ['CI_Tab1_1', 'CI_Tab2_1', 'CI_Tab3_1', 'CM_StatusBadge', 'CI_Tab4_1', 'DOA_List1RowBadge_10', 'RS_CardTitle_2', 'CM_Tab2Line']
first = 'CM_AttachShade'
assert plain.index(first) < min(plain.index(m) for m in MOVED)
new_order = [n for n in plain if n not in MOVED]
at = new_order.index(first)
new_order[at:at] = MOVED
# ZIndex: consecutive again from the first moved position
base = z(first)
for k, n in enumerate(new_order[at:]):
    setz(n, base + k)
nz = [z(n) for n in new_order]
assert nz == sorted(nz) and len(set(nz)) == len(nz)
# groups keep their place in front of what they hold (the preview group was one above its last member)
assert z('EpisodeVisualGroupPopUp') == 53
setz('EpisodeVisualGroupPopUp', max(z(n) for n in ('CM_EpVisualImage', 'CM_EpVisualPanel', 'CM_LblEpVisualPanel', 'CM_EpVisualFile', 'CM_EpVisualClose')) + 1)

# YAML: same order
ends = [i for i, _ in starts[1:]] + [len(lines)]
block = {n: lines[s:e] for (s, n), e in zip(starts, ends)}
head = lines[:starts[0][0]]
out = head[:]
for n in new_order:
    out += block[n]
assert len(out) == len(lines) and sorted(out) == sorted(lines)
open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(out))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('moved below the shades:', MOVED)
print('first shade ZIndex', z('CM_AttachShade'), '| tab 1', z('CI_Tab1_1'), '| title', z('RS_CardTitle_2'), '| EV shade', z('CM_EVAttachShade'), '| preview shade', z('CM_EpVisualShade'), '| preview panel', z('CM_EpVisualPanel'), '| group', z('EpisodeVisualGroupPopUp'))
print('FINAL184 built')
