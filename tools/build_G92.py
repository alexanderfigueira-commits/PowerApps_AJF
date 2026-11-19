#!/usr/bin/env python3
"""FINAL102 on FINAL101: the shareable link is no longer copied by DOA_List1RowBadge_5 (the list row only opens the request); RequesDetailScreen gets its own
link badge (RS_BtnCopyLink, cloned from the envelope badge) that builds and copies the link of the open request."""
import datetime, os, re, shutil
from payaml import App, find
from hp_common import Builder
from jio import jwrite
SRC, NEW = 'newJ2', 'newJ3'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
# 1. the list row only opens the request
M = 'RequestManagementScreen'
t = app.rule(M, 'DOA_List1RowBadge_5', 'OnSelect'); eol = '\r\n' if '\r\n' in t else '\n'; n = t.replace('\r\n', '\n')
assert n.startswith('// copy the shareable link of this request, then open it')
i = n.index(');\nWith(\n    {req: Coalesce(LookUp(\'AV-CD-Requests\', ID = ThisItem.ID), ThisItem)}') + 3; assert n.count('Copy(') == 1
app.set(M, 'DOA_List1RowBadge_5', 'OnSelect', ('// open this request\n' + n[i:]).replace('\n', eol), expect=t)
# 2. a link badge on the request detail screen
R = 'RequesDetailScreen'
LINK = ('If(\n'
        '    StartsWith(varAppLink, "https://apps.powerapps.com/play/e/ENVIRONMENT-ID"),\n'
        '    Notify("Set the app address in App.OnStart (varAppLink) to build real links.", NotificationType.Warning),\n'
        '    // <app address>&RequestID=<ID>: whoever opens it lands on this request, if the roles list allows it\n'
        '    Copy(varAppLink & If("?" in varAppLink, "&", "?") & "RequestID=" & varCurrentRequest.ID);\n'
        '    Notify("Link of request " & varCurrentRequest.RequestNumber & " copied.", NotificationType.Success)\n'
        ')')
b = Builder(app, R)
b.clone('RS_BtnCopyLink', R, 'DOA_List1RowBadge_7',
        {'Text': '"🔗"', 'Tooltip': '"Copy the link of this request"', 'OnSelect': LINK, 'Width': '40', 'X': '510', 'Y': '72', 'Size': '16'})
b.save()
c = find(app.doc(R)['TopParent'], 'RS_BtnCopyLink')
for r in c['Rules']:
    if r['Property'] == 'ZIndex': r['InvariantScript'] = '81'
for e in c.get('ControlPropertyState', []):
    if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString') is not None: e['AutoRuleBindingString'] = '81'
jwrite(app.doc(R), app.map[R])
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL102 built')
