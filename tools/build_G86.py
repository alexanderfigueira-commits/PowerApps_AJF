#!/usr/bin/env python3
"""FINAL96 on FINAL95: 'Navigate cannot be used here' in the OnVisible of both dashboards. The shared-link opening moves out of OnVisible into a hidden
one-shot Timer on each dashboard (DOA_DeepLinkTimer, cloned from Timer1): it fires 300 ms after the screen shows and does the same permission check and Navigate
(Navigate is allowed in OnTimerEnd)."""
import datetime, os, re, shutil, sys
from payaml import App
from hp_common import Builder
SRC, NEW = 'newG85', 'newG86'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
OPEN = '''Set(varCurrentRequest, req);
            Set(varRequestTitle1, Coalesce(req.RequestTitle, ""));
            Set(varRequestTitle, Coalesce(req.RequestTitle, ""));
            Set(varRequestDG, Coalesce(req.DG.Value, ""));
            Set(varRequestDescription1, Coalesce(req.Description, ""));
            Set(varRequestDescription, Coalesce(req.Description, ""));
            Set(varRequestOwnerContact, Coalesce(First(req.DG_Agency_Contact).DisplayName, ""));
            Set(varRequestMediaType, "");
            Navigate(RequesDetailScreen, ScreenTransition.Cover, {locShowTypePicker: false, locResetContacts: true, locFromReview: false})'''
DEEP = ('If(\n    Coalesce(varDeepLinkId, 0) > 0,\n'
        '    With(\n        {\n            req: LookUp(\'AV-CD-Requests\', ID = varDeepLinkId),\n'
        '            mine: Lower(LookUp(\'AV-CD-Requests\', ID = varDeepLinkId).\'Created By\'.Email) = Lower(User().Email)\n        },\n'
        '        Set(varDeepLinkId, 0);\n'
        '        If(\n            IsBlank(req),\n            Notify("The shared request was not found.", NotificationType.Warning),\n'
        '            mine Or (varUserRole = "ADMINISTRATOR" And Coalesce(req.Status.Value, "Draft") <> "Draft"),\n'
        '            Set(varViewOnly, false);\n            ' + OPEN + ',\n'
        '            Notify("You do not have access to this request.", NotificationType.Warning)\n        )\n    )\n)')
MARK = '\n// shared link (&RequestID=): open that request if the roles list allows it'
for s in ('Dashboard-Ope-Administrator', 'Dashboard-Ope-Requestor'):
    t = app.rule(s, None, 'OnVisible'); eol = '\r\n' if '\r\n' in t else '\n'; n = t.replace('\r\n', '\n')
    i = n.index(MARK); cleaned = n[:i].rstrip()
    if cleaned.endswith(';'): cleaned = cleaned[:-1]
    app.set(s, None, 'OnVisible', cleaned.replace('\n', eol), expect=t)
    b = Builder(app, s)
    b.clone('DOA_DeepLinkTimer', 'RequesDetailScreen', 'Timer1', {'OnTimerEnd': DEEP, 'Duration': '300', 'AutoStart': 'true', 'Repeat': 'false', 'Visible': 'false'}, parent=None)
    b.save()
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL96 built')
