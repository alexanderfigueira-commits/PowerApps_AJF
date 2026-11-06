#!/usr/bin/env python3
"""FINAL59 on the user's TEST_last: the podcast visual (CI_BtnOpenAttach) follows the same rule as the episode visual:
mandatory only when Season nr. (CM_SeasonNumber) = 1, optional otherwise. Label, yellow border, tooltip and the
'Podcast visual attached (Podcast only)' validation row (both copies) all use it."""
import datetime, json, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG49', 'newG49out'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
CI, CV = 'ChildInfoScreen', 'ChildValidScreen'
SEASON1 = 'Coalesce(varChildSeasonNumber, 0) = 1'
FILES = 'Filter(CI_PodcastVisual.Attachments, EndsWith(Lower(Name), ".jpg") Or EndsWith(Lower(Name), ".jpeg") Or EndsWith(Lower(Name), ".png"))'
# label
o = app.rule(CI, 'CI_LblPodcastVisual', 'Text'); assert o == '"Podcast visual *"'
app.set(CI, 'CI_LblPodcastVisual', 'Text', f'"Podcast visual" & If({SEASON1}, " *", " (optional)")', expect=o)
# button: yellow only while mandatory (Season nr. = 1) and empty
for p, y, n in (('BorderColor', 'RGBA(255, 204, 0, 1)', 'RGBA(56, 96, 178, 1)'), ('BorderThickness', '3', '1')):
    o = app.rule(CI, 'CI_BtnOpenAttach', p)
    cond = f'CI_LblPodcastVisual.Visible And CountRows({FILES}) = 0'
    assert cond in o, p
    app.set(CI, 'CI_BtnOpenAttach', p, o.replace(cond, f'CI_LblPodcastVisual.Visible And {SEASON1} And CountRows({FILES}) = 0')
            .replace('// yellow while this mandatory field is empty', '// yellow while the podcast visual is mandatory (Season nr. = 1) and empty'), expect=o)
o = app.rule(CI, 'CI_BtnOpenAttach', 'Tooltip')
app.set(CI, 'CI_BtnOpenAttach', 'Tooltip', f'If({SEASON1}, "Mandatory: a podcast visual is required when Season nr. is 1.", "Optional: a podcast visual is only required when Season nr. is 1.")', expect=o)
# validation row: both copies of the checklist
old = 'varChildMediaType <> "Podcast" Or CountRows(Filter(CI_PodcastVisual.Attachments, EndsWith(Lower(Name), ".jpg") Or EndsWith(Lower(Name), ".jpeg") Or EndsWith(Lower(Name), ".png"))) > 0'
new = f'varChildMediaType <> "Podcast" Or Coalesce(varChildSeasonNumber, 0) <> 1 Or CountRows({FILES}) > 0'
note_old = 'Note: "Attach the podcast visual (square JPEG/PNG) on the Info tab (📎 Podcast visual)."'
note_new = 'Note: "Attach the podcast visual (square JPEG/PNG) on the Info tab (📎 Podcast visual). Mandatory when Season nr. is 1, optional otherwise."'
hits = 0
doc = app.doc(CV)
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
for c in list(walk(doc['TopParent'])):
    for r in c['Rules']:
        s = r['InvariantScript']
        if old in s:
            assert note_old in s
            app.set(CV, c['Name'] if c['Name'] != CV else None, r['Property'], s.replace(old, new).replace(note_old, note_new), expect=s)
            hits += 1
print('validation copies updated:', hits)
assert hits >= 1
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL59 built')
