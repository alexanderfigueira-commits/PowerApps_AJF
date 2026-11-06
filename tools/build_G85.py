#!/usr/bin/env python3
"""FINAL95 on FINAL94: shareable request link.
 * DOA_List1RowBadge_5 (Requests list) opens a 'Share request' pop-up: link = <varAppLink> & RequestID=<ID>, a selectable box to copy it, a 'Send by e-mail'
   button (mailto) and an 'Open request' button (what the badge used to do; the row itself still opens the request).
 * Opening the app with &RequestID=<ID> goes straight to that request's detail screen, with the permissions of the roles list: a requestor only opens
   his own requests, an administrator opens any non-draft request (and his own drafts); otherwise a message says there is no access.
 * varAppLink (App.OnStart) is the address of the app, a placeholder to replace: https://apps.powerapps.com/play/e/<environment>/a/<app id>?tenantId=<tenant>"""
import datetime, json, os, re, shutil, sys
from payaml import App
from hp_common import Builder
SRC, NEW = 'newG84', 'newG85'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RM, RS = 'RequestManagementScreen', 'RequesDetailScreen'
LINK = 'varAppLink & If("?" in varAppLink, "&", "?") & "RequestID=" & locShareReq.ID'
OPEN = '''Set(varCurrentRequest, req);
    Set(varRequestTitle1, Coalesce(req.RequestTitle, ""));
    Set(varRequestTitle, Coalesce(req.RequestTitle, ""));
    Set(varRequestDG, Coalesce(req.DG.Value, ""));
    Set(varRequestDescription1, Coalesce(req.Description, ""));
    Set(varRequestDescription, Coalesce(req.Description, ""));
    Set(varRequestOwnerContact, Coalesce(First(req.DG_Agency_Contact).DisplayName, ""));
    Set(varRequestMediaType, "");
    Navigate(RequesDetailScreen, ScreenTransition.Cover, {locShowTypePicker: false, locResetContacts: true, locFromReview: false})'''
# ---- App.OnStart: link address + parameter ----
t = app.rule('App', None, 'OnStart'); eol = '\r\n' if '\r\n' in t else '\n'
add = ('// address of this app, used to build shareable request links (replace the placeholders)\n'
       'Set(varAppLink, "https://apps.powerapps.com/play/e/ENVIRONMENT-ID/a/APP-ID?tenantId=TENANT-ID");\n'
       '// a shared link carries &RequestID=<id>; the start screen opens that request\n'
       'Set(varDeepLinkId, IfError(Value(Param("RequestID")), 0));\n')
app.set('App', None, 'OnStart', add.replace('\n', eol) + t, expect=t)
# ---- start screens open the shared request ----
DEEP = ('\n// shared link (&RequestID=): open that request if the roles list allows it\n'
        'If(\n    Coalesce(varDeepLinkId, 0) > 0,\n'
        '    With(\n        {\n            req: LookUp(\'AV-CD-Requests\', ID = varDeepLinkId),\n'
        '            mine: Lower(LookUp(\'AV-CD-Requests\', ID = varDeepLinkId).\'Created By\'.Email) = Lower(User().Email)\n        },\n'
        '        Set(varDeepLinkId, 0);\n'
        '        If(\n            IsBlank(req),\n            Notify("The shared request was not found.", NotificationType.Warning),\n'
        '            mine Or (varUserRole = "ADMINISTRATOR" And Coalesce(req.Status.Value, "Draft") <> "Draft"),\n'
        '            Set(varViewOnly, false);\n    ' + OPEN.replace('\n    ', '\n            ').replace('Set(varCurrentRequest', 'Set(varCurrentRequest', 1) + ',\n'
        '            Notify("You do not have access to this request.", NotificationType.Warning)\n        )\n    )\n)')
for s in ('Dashboard-Ope-Administrator', 'Dashboard-Ope-Requestor'):
    t = app.rule(s, None, 'OnVisible'); eol = '\r\n' if '\r\n' in t else '\n'
    app.set(s, None, 'OnVisible', t.rstrip() + (';' if not t.rstrip().endswith(';') else '') + DEEP.replace('\n', eol), expect=t)
# ---- share pop-up on the Requests screen ----
b = Builder(app, RM)
G = lambda **k: k
vis = 'locShowShare'
b.clone('RM_ShareBackdrop', RS, 'RS_DelBackdrop', {'Visible': vis, 'OnSelect': 'UpdateContext({locShowShare: false})'}, parent=None)
b.clone('RM_SharePanel', RS, 'RS_DelPanel', {'Visible': vis, 'X': '333', 'Y': '230', 'Width': '700', 'Height': '270'}, parent=None)
b.clone('RM_ShareTitle', RS, 'RS_DelTitle', {'Visible': vis, 'X': '363', 'Y': '248', 'Width': '640', 'Text': '"Share request " & locShareReq.RequestNumber'}, parent=None)
b.clone('RM_ShareHint', RS, 'RS_DelText', {'Visible': vis, 'X': '363', 'Y': '290', 'Width': '640', 'Height': '50',
        'Text': 'If(StartsWith(varAppLink, "https://apps.powerapps.com/play/e/ENVIRONMENT-ID"), "⚠ Set the app address in App.OnStart (varAppLink) first.  ", "") & "Copy this link: whoever opens it goes straight to this request, with the permissions of their role."'}, parent=None)
link = b.clone('RM_ShareLink', RM, 'HomeFilterRequestName', {'Visible': vis, 'X': '363', 'Y': '350', 'Width': '640', 'Height': '40', 'Default': LINK, 'HintText': '""'}, parent=None)
b.clone('RM_ShareOpen', RS, 'RS_DelYes', {'Visible': vis, 'X': '363', 'Y': '430', 'Width': '200', 'Height': '44', 'Text': '"Open request"',
        'Fill': 'RGBA(56, 96, 178, 1)', 'HoverFill': 'RGBA(0, 18, 107, 1)',
        'OnSelect': 'With(\n    {req: locShareReq},\n    UpdateContext({locShowShare: false});\n    ' + OPEN + '\n)'}, parent=None)
b.clone('RM_ShareMail', RS, 'RS_DelYes', {'Visible': vis, 'X': '583', 'Y': '430', 'Width': '200', 'Height': '44', 'Text': '"Send by e-mail"',
        'Fill': 'RGBA(56, 96, 178, 1)', 'HoverFill': 'RGBA(0, 18, 107, 1)',
        'OnSelect': 'Launch("mailto:?subject=" & EncodeUrl("Central Deposit request " & locShareReq.RequestNumber) & "&body=" & EncodeUrl(' + LINK + '))'}, parent=None)
b.clone('RM_ShareClose', RS, 'RS_DelNo', {'Visible': vis, 'X': '803', 'Y': '430', 'Width': '200', 'Height': '44', 'Text': '"Close"',
        'OnSelect': 'UpdateContext({locShowShare: false})'}, parent=None)
b.save()
# stacking above everything on the screen
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
doc = app.doc(RM)['TopParent']
zs = [int([r for r in c['Rules'] if r['Property'] == 'ZIndex'][0]['InvariantScript']) for c in walk(doc) if c['Name'] != 'RequestManagementScreen' and any(r['Property'] == 'ZIndex' for r in c['Rules']) and not c['Name'].startswith('RM_Share')]
top = max(zs)
for i, n in enumerate(('RM_ShareBackdrop', 'RM_SharePanel', 'RM_ShareTitle', 'RM_ShareHint', 'RM_ShareLink', 'RM_ShareOpen', 'RM_ShareMail', 'RM_ShareClose')):
    c = [x for x in walk(doc) if x['Name'] == n][0]
    r = [x for x in c['Rules'] if x['Property'] == 'ZIndex'][0]; r['InvariantScript'] = str(top + 1 + i)
    for e in c.get('ControlPropertyState', []):
        if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString'): e['AutoRuleBindingString'] = str(top + 1 + i)
app.save()
# ---- DOA_List1RowBadge_5: share instead of open ----
app.set(RM, 'DOA_List1RowBadge_5', 'OnSelect', 'UpdateContext({locShareReq: ThisItem, locShowShare: true});\nReset(RM_ShareLink)')
app.set(RM, 'DOA_List1RowBadge_5', 'Tooltip', '"Share a link to request " & ThisItem.RequestNumber & " (the row opens it)"')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL95 built; top z', top)
