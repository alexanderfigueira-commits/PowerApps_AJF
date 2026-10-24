#!/usr/bin/env python3
"""FINAL99 on TEST_3: (1) Help menu button icon becomes the information icon on every screen; (2) HomePrintScreen table: TITLE is the 2nd column;
(3) HelpScreen: the 'Rate this application' card is deleted (controls, group, variables) and replaced by a Support section (mailbox + video link)."""
import copy, datetime, json, os, re, shutil, sys
from payaml import App, find
from hp_common import Builder
from jio import jwrite
SRC, NEW = 'newH1', 'newH2c'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

# ---- 3. HelpScreen: delete the rating card
H = 'HelpScreen'
RATE = ['HL_RateCard', 'HL_RateTitle', 'HL_RateSub', 'HL_Star1', 'HL_Star2', 'HL_Star3', 'HL_Star4', 'HL_Star5', 'HL_RatingHint',
        'HL_FeedbackLbl', 'HL_Feedback', 'HL_BtnSubmitRating', 'HL_ThanksMsg']
# donors (cloned before the originals go away)
b = Builder(app, H)
class NB(Builder):
    def grouped(self, tp): return set()
b = NB(app, H)
X0, W0 = 970, 360
b.clone('HL_SupportCard', H, 'HL_RateCard', {'Height': '330'})
b.clone('HL_SupportTitle', H, 'HL_RateTitle', {'Text': '"Support"'})
b.clone('HL_SupportSub', H, 'HL_RateSub', {'Text': '"Need help using the application? Write to the Central Deposit team or watch the video tutorial."', 'Y': '128'})
b.clone('HL_SupportMailLbl', H, 'HL_FeedbackLbl', {'Text': '"Central Deposit support mailbox"', 'Y': '196', 'Width': '360'})
b.clone('HL_SupportMail', H, 'HL_Link3', {'Text': '"✉  " & varSupportMailbox', 'Tooltip': '"Write to the Central Deposit support mailbox"', 'OnSelect': 'Launch("mailto:" & varSupportMailbox)', 'Width': '360', 'X': str(X0), 'Y': '222', 'Size': '13'})
b.clone('HL_SupportDivider', H, 'HL_Divider1', {'Width': '360', 'X': str(X0), 'Y': '280'})
b.clone('HL_SupportVideoLbl', H, 'HL_FeedbackLbl', {'Text': '"How to use the application"', 'Y': '294', 'Width': '360'})
b.clone('HL_SupportVideo', H, 'HL_Link3', {'Text': '"▶  Watch the video tutorial"', 'Tooltip': '"Open the video that explains how to use the application"', 'OnSelect': 'Launch(varSupportVideoUrl)', 'Width': '360', 'X': str(X0), 'Y': '320', 'Size': '13'})
b.save()
doc = app.doc(H); tp = doc['TopParent']
# position of the donors used for the card: same place as the old card
for nm, props in (('HL_SupportCard', {'X': '946', 'Y': '72', 'Width': '400'}),
                  ('HL_SupportTitle', {}), ('HL_SupportSub', {}), ('HL_SupportMailLbl', {'X': '970'}), ('HL_SupportVideoLbl', {'X': '970'})):
    pass

def rules(c): return {r['Property']: r for r in c['Rules']}
def setj(c, p, v):
    rules(c)[p]['InvariantScript'] = v
    for e in c.get('ControlPropertyState', []):
        if isinstance(e, dict) and e.get('InvariantPropertyName') == p and e.get('AutoRuleBindingString') is not None: e['AutoRuleBindingString'] = v
# (the clones inherit X/Y/Width of their donors; the ones I moved were overridden above)
top = max(int(rules(c)['ZIndex']['InvariantScript']) for c in tp['Children'] if 'ZIndex' in rules(c) and c['Name'] not in RATE and not c['Name'].startswith('HL_Support'))
k = 0
for c in tp['Children']:
    if c['Name'].startswith('HL_Support'):
        k += 1; setj(c, 'ZIndex', str(top + k))

jwrite(doc, app.map[H])
# ---- App.OnStart: rating variables out, support settings in
t = app.rule('App', None, 'OnStart'); eol = '\r\n' if '\r\n' in t else '\n'; nt = t.replace('\r\n', '\n')
anchor = '      Set(varRating, 0);\n'
if anchor not in nt: anchor = anchor.replace('      ', '')
assert nt.count(anchor) == 1
add = ('// Help screen: support mailbox and video tutorial (edit here)\nSet(varSupportMailbox, "audiovisual-service@ec.europa.eu");\n'
       'Set(varSupportVideoUrl, "https://example.com/central-deposit-video-tutorial");\n')
nt = nt.replace(anchor, add + anchor)
app.set('App', None, 'OnStart', nt.replace('\n', eol), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL99 built')
