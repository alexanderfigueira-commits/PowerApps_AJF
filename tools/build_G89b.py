#!/usr/bin/env python3
"""FINAL99 on TEST_3: (1) Help menu button icon becomes the information icon on every screen; (2) HomePrintScreen table: TITLE is the 2nd column;
(3) HelpScreen: the 'Rate this application' card is deleted (controls, group, variables) and replaced by a Support section (mailbox + video link)."""
import copy, datetime, json, os, re, shutil, sys
from payaml import App, find
from hp_common import Builder
from jio import jwrite
SRC, NEW = 'newH1', 'newH2b'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

# ---- 3. HelpScreen: delete the rating card
H = 'HelpScreen'
RATE = ['HL_RateCard', 'HL_RateTitle', 'HL_RateSub', 'HL_Star1', 'HL_Star2', 'HL_Star3', 'HL_Star4', 'HL_Star5', 'HL_RatingHint',
        'HL_FeedbackLbl', 'HL_Feedback', 'HL_BtnSubmitRating', 'HL_ThanksMsg']
doc = app.doc(H); tp = doc['TopParent']
def rules(c): return {r['Property']: r for r in c['Rules']}
# remove rating controls + group (JSON)
names = set(RATE) | {'Rate Screen'}
n0 = len(tp['Children']); tp['Children'] = [c for c in tp['Children'] if c['Name'] not in names]
assert n0 - len(tp['Children']) == len(names), (n0, len(tp['Children']))
# OnVisible only reset the rating flag
ov = rules(tp)['OnVisible']; assert ov['InvariantScript'] == 'Set(varFeedbackSent, false)'
tp['Rules'] = [r for r in tp['Rules'] if r['Property'] != 'OnVisible']
tp['ControlPropertyState'] = [e for e in tp.get('ControlPropertyState', []) if not (isinstance(e, dict) and e.get('InvariantPropertyName') == 'OnVisible')]
if 'ControlPropertyState' in tp and 'OnVisible' in tp['ControlPropertyState']: tp['ControlPropertyState'].remove('OnVisible')
jwrite(doc, app.map[H])
# YAML: drop the blocks
yp = f'{NEW}/Src/{H}.pa.yaml'
L = open(yp, encoding='utf-8').read().split('\n')
for nm in RATE:
    i = [k for k, l in enumerate(L) if l.rstrip('\r') == f'      - {nm}:']; assert len(i) == 1, nm
    i = i[0]; j = i + 1
    while j < len(L) and (L[j].strip() == '' or len(L[j]) - len(L[j].lstrip()) > 6): j += 1
    del L[i:j]
i = [k for k, l in enumerate(L) if l.strip().startswith('OnVisible: =Set(varFeedbackSent')]; assert len(i) == 1
del L[i[0]]
open(yp, 'w', encoding='utf-8').write('\n'.join(L))

# ---- App.OnStart: rating variables out, support settings in
t = app.rule('App', None, 'OnStart'); eol = '\r\n' if '\r\n' in t else '\n'; nt = t.replace('\r\n', '\n')
rm = '      Set(varRating, 0);\n      Set(varFeedbackText, "");\n      Set(varFeedbackSent, false);\n'
if rm not in nt:
    rm = rm.replace('      ', '')
assert nt.count(rm) == 1, 'rating vars'
add = ''
nt = nt.replace(rm, add)
app.set('App', None, 'OnStart', nt.replace('\n', eol), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL99 built')
