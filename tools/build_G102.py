#!/usr/bin/env python3
"""FINAL112 on FINAL111: the request status badge (same one as on RequesDetailScreen) also shows on ChildInfoScreen, ChildMetaScreen, ChildLegalScreen and ChildValidScreen,
at the right end of the tabs row."""
import datetime, os, re, shutil
from payaml import App, find
from hp_common import Builder
from jio import jwrite
SRC, NEW = 'newL3', 'newL4'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
class NB(Builder):
    def grouped(self, tp): return set()
SCREENS = [('ChildInfoScreen', 'CI_StatusBadge', 'CI_Tab4'), ('ChildMetaScreen', 'CM_StatusBadge', 'CI_Tab4_1'),
           ('ChildLegalScreen', 'CL_StatusBadge', 'CI_Tab4_2'), ('ChildValidScreen', 'CV_StatusBadge', 'CI_Tab4_3')]
for scr, name, tab in SCREENS:
    b = NB(app, scr)
    b.clone(name, 'RequesDetailScreen', 'DOA_List1RowBadge_3', {'X': '1193', 'Y': '63', 'Tooltip': '"Request status"'})
    b.save()
    doc = app.doc(scr); tp = doc['TopParent']
    z = [r for r in find(tp, tab)['Rules'] if r['Property'] == 'ZIndex'][0]['InvariantScript']
    c = find(tp, name)
    for r in c['Rules']:
        if r['Property'] == 'ZIndex': r['InvariantScript'] = z
    for e in c.get('ControlPropertyState', []):
        if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString') is not None: e['AutoRuleBindingString'] = z
    jwrite(doc, app.map[scr])
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL112 built')
