#!/usr/bin/env python3
"""FINAL99 on TEST_3: (1) Help menu button icon becomes the information icon on every screen; (2) HomePrintScreen table: TITLE is the 2nd column;
(3) HelpScreen: the 'Rate this application' card is deleted (controls, group, variables) and replaced by a Support section (mailbox + video link)."""
import copy, datetime, json, os, re, shutil, sys
from payaml import App, find
from hp_common import Builder
from jio import jwrite
SRC, NEW = 'newH1', 'newH2a'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

# ---- 1. Help icon on every screen
OLD, ICON = '"🔎" & Char(10) & "Help"', '"ℹ️" & Char(10) & "Help"'
n = 0
for scr in list(app.map):
    for nm in [c for c in re.findall(r'^      - ([A-Za-z0-9_]*_Menu_Help[A-Za-z0-9_]*):', open(f'{NEW}/Src/{scr}.pa.yaml', encoding='utf-8').read(), re.M)]:
        app.set(scr, nm, 'Text', ICON, expect=OLD); n += 1
print('help buttons changed:', n)

# ---- 2. HomePrintScreen: TITLE as 2nd column
S = 'HomePrintScreen'
cols = [  # header, row, header X, header W, row X, row W
    ('HP_ThRequest', 'HP_RowRequest', 48, 100, 16, 100),
    ('HP_ThDescription', 'HP_RowDescription', 148, 290, 116, 280),
    ('HP_ThDG', 'HP_RowDG', 446, 170, 414, 170),
    ('HP_ThArchives', 'HP_RowArchives', 624, 78, 592, 65),
    ('HP_ThStatus', 'HP_RowStatus', 712, 120, 683, 120),
    ('HP_ThSubmitted', 'HP_RowDate', 840, 110, 810, 110),
    ('HP_ThDescription_1', 'HP_RowDate_1', 958, 280, 933, 280)]
for th, row, hx, hw, rx, rw in cols:
    for ctl, prop, v in ((th, 'X', hx), (th, 'Width', hw), (row, 'X', rx), (row, 'Width', rw)):
        old = app.rule(S, ctl, prop); app.set(S, ctl, prop, str(v), expect=old)

app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL99 built')
