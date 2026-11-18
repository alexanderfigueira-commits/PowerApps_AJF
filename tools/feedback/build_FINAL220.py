#!/usr/bin/env python3
"""FINAL220 on FINAL219. Long text boxes of the media file (Info / Metadata) show, when their own limit is reached, a red line at
the bottom of the box: "Maximum N characters. For longer texts, upload a text file in Legal & Docs or share it via FTP".
The box gives up 20 px for that line only while the limit is reached; the label counters stay (from about 80 % of the limit)."""
import datetime, os, re, shutil
from payaml import App
from hp_common import Builder
SRC, NEW = 'newV81', 'newV82'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)
BOXES = [('ChildInfoScreen', 'CI_Gallery', 'CI_Description', 'CI_LblDescription', 10),
         ('ChildInfoScreen', 'CI_Gallery', 'CI_PodcastDesc', 'CI_LblPodcastDesc', 10),
         ('ChildMetaScreen', 'CM_Gallery', 'CM_Caption', 'CM_LblCaptions', 10),
         ('ChildMetaScreen', 'CM_Gallery', 'CM_EpisodeSummary', 'CM_LblEpisodeSummary', 10),
         ('ChildMetaScreen', 'CM_Gallery', 'CM_Script', 'CM_LblScript', 10),
         ('ChildMetaScreen', 'CM_Gallery', 'CM_Credits', 'CM_LblCredits', 9)]
for scr, gal, box, lbl, size in BOXES:
    n = int(app.rule(scr, box, 'MaxLength').strip())
    h = app.rule(scr, box, 'Height').strip(); assert re.fullmatch(r'\d+', h), (box, h); h = int(h)
    full = f'Len({box}.Text) >= {n}'
    setp(scr, box, 'Height', f'// 20 px for the limit message while the limit is reached\nIf(Len(Self.Text) >= {n}, {h - 20}, {h})')
    b = Builder(app, scr)
    b.clone(f'{box}_Max', scr, lbl, {
        'Text': f'"Maximum {n} characters. For longer texts, upload a text file in Legal & Docs or share it via FTP"',
        'X': app.rule(scr, box, 'X'), 'Y': f'{box}.Y + {h} - 18', 'Width': app.rule(scr, box, 'Width'), 'Height': '18',
        'Size': str(size), 'Color': 'RGBA(193, 40, 40, 1)', 'FontWeight': 'FontWeight.Semibold',
        'Visible': f'{box}.Visible And {full}'}, parent=gal)
    b.save()
p_ = f'{NEW}/Properties.json'
raw = open(p_, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
t = re.sub(r'("label"\s*:\s*)(\d+)', lambda mm: mm.group(1) + str(int(mm.group(2)) + len(BOXES)), t, count=1)
open(p_, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL220 built')
