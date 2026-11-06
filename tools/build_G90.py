#!/usr/bin/env python3
"""FINAL100 on TEST_3: (1) Help menu button icon becomes the information icon on every screen; (2) HomePrintScreen table: TITLE is the 2nd column;
(3) HP_RowRequest shows RequestNumber; (4) HelpScreen: the 'Rate this application' card is deleted (controls, group, variables) and replaced by a Support section (mailbox + video link)."""
import copy, datetime, json, os, re, shutil, sys
from payaml import App, find
from hp_common import Builder
from jio import jwrite
SRC, NEW = 'newH1', 'newH3'
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
    ('HP_ThRequest', 'HP_RowRequest', 48, 120, 16, 120),
    ('HP_ThDescription', 'HP_RowDescription', 172, 266, 140, 256),
    ('HP_ThDG', 'HP_RowDG', 446, 170, 414, 170),
    ('HP_ThArchives', 'HP_RowArchives', 624, 78, 592, 65),
    ('HP_ThStatus', 'HP_RowStatus', 712, 120, 683, 120),
    ('HP_ThSubmitted', 'HP_RowDate', 840, 110, 810, 110),
    ('HP_ThDescription_1', 'HP_RowDate_1', 958, 280, 933, 280)]
for th, row, hx, hw, rx, rw in cols:
    for ctl, prop, v in ((th, 'X', hx), (th, 'Width', hw), (row, 'X', rx), (row, 'Width', rw)):
        old = app.rule(S, ctl, prop); app.set(S, ctl, prop, str(v), expect=old)

old = app.rule(S, 'HP_RowRequest', 'Text')
assert old == 'If(IsBlank(ThisItem.ID), "Untitled request", ThisItem.ID)'
app.set(S, 'HP_RowRequest', 'Text', 'If(IsBlank(ThisItem.RequestNumber), "Untitled request", ThisItem.RequestNumber)', expect=old)

# ---- 4. HelpScreen: the rating card becomes the Support section (controls reused in place, no donor is deleted)
H = 'HelpScreen'
def rules(c): return {r['Property']: r for r in c['Rules']}
doc = app.doc(H); tp = doc['TopParent']
yp = f'{NEW}/Src/{H}.pa.yaml'
def yaml_rename(old, new):
    L = open(yp, encoding='utf-8').read().split('\n')
    i = [k for k, l in enumerate(L) if l.rstrip('\r') == f'      - {old}:']; assert len(i) == 1, old
    i = i[0]; L[i] = f'      - {new}:'
    j = i + 1
    while j < len(L) and (L[j].strip() == '' or len(L[j]) - len(L[j].lstrip()) > 6):
        if L[j].strip() == 'Group: Rate Screen': del L[j]; continue
        j += 1
    open(yp, 'w', encoding='utf-8').write('\n'.join(L))
REN = {'HL_RateCard': 'HL_SupportCard', 'HL_RateTitle': 'HL_SupportTitle', 'HL_RateSub': 'HL_SupportSub',
       'HL_FeedbackLbl': 'HL_SupportMailLbl', 'HL_RatingHint': 'HL_SupportVideoLbl'}
for old, new in REN.items():
    c = find(tp, old); assert c is not None and c['Parent'] == H
    c['Name'] = new; yaml_rename(old, new)
T = lambda c, p, v: app.set(H, c, p, v, expect=app.rule(H, c, p))
T('HL_SupportCard', 'Height', '330')
T('HL_SupportTitle', 'Text', '"Support"')
T('HL_SupportSub', 'Text', '"Need help using the application? Write to the Central Deposit team or watch the video tutorial."')
T('HL_SupportMailLbl', 'Text', '"Central Deposit support mailbox"'); T('HL_SupportMailLbl', 'Y', '196')
T('HL_SupportVideoLbl', 'Text', '"How to use the application"'); T('HL_SupportVideoLbl', 'Y', '294')
T('HL_SupportVideoLbl', 'Color', 'RGBA(60, 66, 80, 1)'); T('HL_SupportVideoLbl', 'Height', '24')
app.set(H, 'HL_SupportVideoLbl', 'FontWeight', 'FontWeight.Semibold', expect=app.rule(H, 'HL_SupportVideoLbl', 'FontWeight'))
# delete the rest of the rating controls and the group (JSON + YAML)
DEL = ['HL_Star1', 'HL_Star2', 'HL_Star3', 'HL_Star4', 'HL_Star5', 'HL_Feedback', 'HL_BtnSubmitRating', 'HL_ThanksMsg']
names = set(DEL) | {'Rate Screen'}
n0 = len(tp['Children']); tp['Children'] = [c for c in tp['Children'] if c['Name'] not in names]
assert n0 - len(tp['Children']) == len(names)
L = open(yp, encoding='utf-8').read().split('\n')
for nm in DEL:
    i = [k for k, l in enumerate(L) if l.rstrip('\r') == f'      - {nm}:']; assert len(i) == 1, nm
    i = i[0]; j = i + 1
    while j < len(L) and (L[j].strip() == '' or len(L[j]) - len(L[j].lstrip()) > 6): j += 1
    del L[i:j]
open(yp, 'w', encoding='utf-8').write('\n'.join(L))
# new controls: links, cloned from the Help screen's own (kept) link and divider
class NB(Builder):
    def grouped(self, tp): return set()
b = NB(app, H)
X0 = 970
b.clone('HL_SupportMail', H, 'HL_Link3', {'Text': '"✉  " & varSupportMailbox', 'Tooltip': '"Write to the Central Deposit support mailbox"', 'OnSelect': 'Launch("mailto:" & varSupportMailbox)', 'Width': '360', 'X': str(X0), 'Y': '222', 'Size': '13'})
b.clone('HL_SupportDivider', H, 'HL_Divider1', {'Width': '360', 'X': str(X0), 'Y': '280'})
b.clone('HL_SupportVideo', H, 'HL_Link3', {'Text': '"▶  Watch the video tutorial"', 'Tooltip': '"Open the video that explains how to use the application"', 'OnSelect': 'Launch(varSupportVideoUrl)', 'Width': '360', 'X': str(X0), 'Y': '320', 'Size': '13'})
b.save()
def setj(c, p, v):
    rules(c)[p]['InvariantScript'] = v
    for e in c.get('ControlPropertyState', []):
        if isinstance(e, dict) and e.get('InvariantPropertyName') == p and e.get('AutoRuleBindingString') is not None: e['AutoRuleBindingString'] = v
top = max(int(rules(c)['ZIndex']['InvariantScript']) for c in tp['Children'] if 'ZIndex' in rules(c) and c['Name'] not in ('HL_SupportMail', 'HL_SupportDivider', 'HL_SupportVideo'))
for k, nm in enumerate(('HL_SupportMail', 'HL_SupportDivider', 'HL_SupportVideo'), 1): setj(find(tp, nm), 'ZIndex', str(top + k))
jwrite(doc, app.map[H])
# the support settings live in the screen's OnVisible (it only reset the rating flag before)
app.set(H, None, 'OnVisible', '// support mailbox and video tutorial of the Help screen (edit here)\nSet(varSupportMailbox, "audiovisual-service@ec.europa.eu");\nSet(varSupportVideoUrl, "https://example.com/central-deposit-video-tutorial")', expect='Set(varFeedbackSent, false)')
# App.OnStart: the rating variables go
t = app.rule('App', None, 'OnStart'); eol = '\r\n' if '\r\n' in t else '\n'; nt = t.replace('\r\n', '\n')
rm = '      Set(varRating, 0);\n      Set(varFeedbackText, "");\n      Set(varFeedbackSent, false);\n'
if rm not in nt: rm = rm.replace('      ', '')
assert nt.count(rm) == 1
app.set('App', None, 'OnStart', nt.replace(rm, '').replace('\n', eol), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL100 built')
