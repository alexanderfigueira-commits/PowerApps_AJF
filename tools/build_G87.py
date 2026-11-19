#!/usr/bin/env python3
"""FINAL97 on FINAL96: DOA_List1RowBadge_5 copies the request link to the clipboard with Copy() and opens the request (Navigate), no pop-up.
The Share pop-up controls (RM_Share*) of FINAL95 are removed. Link = varAppLink & RequestID=<ID>."""
import datetime, json, os, re, shutil
from payaml import App
SRC, NEW = 'newG86', 'newG87'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RM = 'RequestManagementScreen'
LINK = 'varAppLink & If("?" in varAppLink, "&", "?") & "RequestID=" & ThisItem.ID'
ON = f'''// copy the shareable link of this request, then open it (the row opens it the same way)
If(
    StartsWith(varAppLink, "https://apps.powerapps.com/play/e/ENVIRONMENT-ID"),
    Notify("Set the app address in App.OnStart (varAppLink) to build real links.", NotificationType.Warning),
    Copy({LINK});
    Notify("Link of request " & ThisItem.RequestNumber & " copied.", NotificationType.Success)
);
With(
    {{req: Coalesce(LookUp('AV-CD-Requests', ID = ThisItem.ID), ThisItem)}},
    Set(varCurrentRequest, req);
    Set(varRequestTitle1, Coalesce(req.RequestTitle, ""));
    Set(varRequestTitle, Coalesce(req.RequestTitle, ""));
    Set(varRequestDG, Coalesce(req.DG.Value, ""));
    Set(varRequestDescription1, Coalesce(req.Description, ""));
    Set(varRequestDescription, Coalesce(req.Description, ""));
    Set(varRequestOwnerContact, Coalesce(First(req.DG_Agency_Contact).DisplayName, ""));
    Set(varRequestMediaType, "");
    Navigate(RequesDetailScreen, ScreenTransition.Cover, {{locShowTypePicker: false, locResetContacts: true, locFromReview: false}})
)'''
app.set(RM, 'DOA_List1RowBadge_5', 'OnSelect', ON)
app.set(RM, 'DOA_List1RowBadge_5', 'Tooltip', '"Open request ' + '" & ThisItem.RequestNumber & " and copy its link"')
app.save()
GONE = ['RM_ShareBackdrop', 'RM_SharePanel', 'RM_ShareTitle', 'RM_ShareHint', 'RM_ShareLink', 'RM_ShareOpen', 'RM_ShareMail', 'RM_ShareClose']
jp = [os.path.join(NEW, 'Controls', f) for f in os.listdir(f'{NEW}/Controls') if '"RequestManagementScreen"' in open(os.path.join(NEW, 'Controls', f), encoding='utf-8-sig').read()[:400]][0]
raw = open(jp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); crlf = b'\r\n' in raw
d = json.loads(raw.decode('utf-8-sig')); top = d['TopParent']; n0 = len(top['Children'])
top['Children'] = [c for c in top['Children'] if c['Name'] not in GONE]; assert n0 - len(top['Children']) == 8
out = json.dumps(d, ensure_ascii=False, indent=2)
open(jp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out.replace('\n', '\r\n') if crlf else out)
yp = f'{NEW}/Src/RequestManagementScreen.pa.yaml'
L = open(yp, 'rb').read().decode('utf-8').split('\n')
for g in GONE:
    i = [k for k, l in enumerate(L) if l.rstrip('\r') == f'      - {g}:'][0]; j = i + 1
    while j < len(L) and (L[j].strip() == '' or len(L[j]) - len(L[j].lstrip()) > 6): j += 1
    del L[i:j]
open(yp, 'wb').write('\n'.join(L).encode('utf-8'))
for f in os.listdir(f'{NEW}/Src'):
    assert 'RM_Share' not in open(os.path.join(NEW, 'Src', f), encoding='utf-8').read(), f
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL97 built')
