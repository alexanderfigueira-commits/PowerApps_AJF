#!/usr/bin/env python3
"""FINAL111 on FINAL110: RequesDetailScreen shows who submitted the request and who the assignees are (bottom of the card's right column),
only from Processing onwards: 'Submitted by:' + author + submission date; 'Assignees:' + assignee + co-assignee (if any)."""
import datetime, os, re, shutil
from payaml import App, find
from hp_common import Builder
from jio import jwrite
SRC, NEW = 'newL2', 'newL3'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
class NB(Builder):
    def grouped(self, tp): return set()
b = NB(app, S)
SHOW = ('Not(locDetailsCollapsed) And Coalesce(varCurrentRequest.ID, 0) > 0 And '
        'Coalesce(varCurrentRequest.Status.Value, "Draft") in ["Processing", "Pending", "Approved", "Rejected"]')
def short(n): return f'With({{n: Coalesce({n}, "")}}, Trim(If("(" in n, Left(n, Find("(", n) - 1), n)))'
SUB = short("varCurrentRequest.'Created By'.DisplayName")
ASG = short('varCurrentRequest.Assignee.DisplayName')
CO = short('varCurrentRequest.CoAssignee.DisplayName')
NOASG = 'IsBlank(varCurrentRequest.Assignee.DisplayName)'
LBL = lambda name, text, y: b.clone(name, S, 'RS_LblDG', {'Text': f'"{text}"', 'X': '914', 'Y': str(y), 'Width': '96', 'Height': '24', 'Size': '12', 'Visible': SHOW})
PILL = lambda name, text, x, y, w, tip, fill, vis=SHOW: b.clone(name, S, 'DOA_List1RowBadge_2',
        {'Text': text, 'X': str(x), 'Y': str(y), 'Width': str(w), 'Height': '26', 'Size': '12', 'Visible': vis, 'DisplayMode': 'DisplayMode.View', 'OnSelect': 'false',
         'Tooltip': tip, 'Fill': fill, 'DisabledFill': fill})
b.clone('RS_PeopleDivider', S, 'RS_DetailsDivider', {'X': '914', 'Y': '326', 'Width': '380', 'Height': '1', 'Fill': 'RGBA(220, 224, 230, 1)', 'Visible': SHOW})
LBL('RS_LblSubmittedBy', 'Submitted by:', 333)
PILL('RS_PplSubmitter', '"👤  " & ' + SUB, 1012, 332, 150, 'Coalesce(varCurrentRequest.\'Created By\'.DisplayName, "") & Char(10) & Coalesce(varCurrentRequest.\'Created By\'.Email, "")', 'RGBA(215, 223, 240, 1)')
c = b.clone('RS_PplSubmittedOn', S, 'RS_LblDG', {'Text': 'If(IsBlank(varCurrentRequest.StartRequestDate), "", Text(varCurrentRequest.StartRequestDate, "dd mmm yyyy"))', 'X': '1170', 'Y': '333', 'Width': '124', 'Height': '24', 'Size': '12', 'Visible': SHOW,
        'FontWeight': 'FontWeight.Normal'})
LBL('RS_LblAssignees', 'Assignees:', 363)
PILL('RS_PplAssignee', 'If(' + NOASG + ', If(varUserRole = "ADMINISTRATOR", "Not assigned yet", "Waiting for assignment"), "👤  " & ' + ASG + ')', 1012, 362, 138,
     'If(' + NOASG + ', "Nobody is assigned to this request yet", varCurrentRequest.Assignee.DisplayName & Char(10) & Coalesce(varCurrentRequest.Assignee.Email, ""))',
     'If(' + NOASG + ', RGBA(244, 245, 248, 1), RGBA(215, 223, 240, 1))')
PILL('RS_PplCoAssignee', '"👤  " & ' + CO, 1156, 362, 138,
     'varCurrentRequest.CoAssignee.DisplayName & Char(10) & Coalesce(varCurrentRequest.CoAssignee.Email, "")', 'RGBA(238, 241, 248, 1)',
     vis=SHOW + ' And Not(IsBlank(varCurrentRequest.CoAssignee.DisplayName))')
b.save()
doc = app.doc(S); tp = doc['TopParent']
for nm in ('RS_PeopleDivider', 'RS_LblSubmittedBy', 'RS_PplSubmitter', 'RS_PplSubmittedOn', 'RS_LblAssignees', 'RS_PplAssignee', 'RS_PplCoAssignee'):
    c = find(tp, nm)
    for r in c['Rules']:
        if r['Property'] == 'ZIndex': r['InvariantScript'] = '60'
    for e in c.get('ControlPropertyState', []):
        if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString') is not None: e['AutoRuleBindingString'] = '60'
jwrite(doc, app.map[S])
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL111 built')
