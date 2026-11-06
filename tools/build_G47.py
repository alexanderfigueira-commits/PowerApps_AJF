#!/usr/bin/env python3
"""FINAL57 on the user's FINAL56 + Timer1 upload (Timer1 gets Repeat = true; its OnTimerEnd is the user's): Save in the Contact Extra pop-up puts the e-mail into the matching field (RS_Owner for DG/Agency,
RS_Contractor for Contractor). The combobox is reset so its DefaultSelectedItems (saved contacts + the manual e-mail) are
re-read; only the saved type is replaced, the other type's manual e-mail is kept (Clear used to drop both)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG47b', 'newG47'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
old = app.rule(S, 'RS_btnSaveContact', 'OnSelect')
new = '''With(
    {
        locType: RS_drpContactType.Selected.Value,
        locEmail: Trim(RS_txtEmailContact.Text)
    },
    If(
        IsBlank(locEmail),
        Notify("Enter the contact email before saving.", NotificationType.Warning),
        // one e-mail per type and request; the other type is left alone
        RemoveIf(
            colManualContacts,
            ContactType = locType And Coalesce(ParentRequest, "") = Coalesce(varCurrentRequest.RequestNumber, "")
        );
        Collect(
            colManualContacts,
            {
                ContactType: locType,
                EmailContact: locEmail,
                ParentRequest: varCurrentRequest.RequestNumber
            }
        );
        // the e-mail now shows in the matching field (DefaultSelectedItems reads the manual contact)
        If(locType = "DG/Agency", Reset(RS_Owner), Reset(RS_Contractor));
        Notify(
            "Contact saved: " & locEmail,
            NotificationType.Success
        );
        Reset(RS_txtEmailContact);
        Set(
            locShowContactPopup,
            false
        )
    )
)'''
app.set(S, 'RS_btnSaveContact', 'OnSelect', new, expect=old)
app.save()
# Timer1 only fired once without Repeat: make it a 400 ms loop (JSON rule + YAML line)
import json
jp = f'{NEW}/Controls/463.json'
raw = open(jp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); crlf = b'\r\n' in raw
d = json.loads(raw.decode('utf-8-sig'))
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
t = [c for c in walk(d['TopParent']) if c['Name'] == 'Timer1'][0]
assert not any(r['Property'] == 'Repeat' for r in t['Rules'])
t['Rules'].append({'Property': 'Repeat', 'Category': 'Data', 'InvariantScript': 'true', 'RuleProviderType': 'Unknown'})
ps = [e for e in t.get('ControlPropertyState', [])]
if all(isinstance(e, str) for e in ps): ps.append('Repeat')
t['ControlPropertyState'] = ps
out = json.dumps(d, ensure_ascii=False, indent=2)
open(jp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out.replace('\n', '\r\n') if crlf else out)
yp = f'{NEW}/Src/RequesDetailScreen.pa.yaml'
y = open(yp, 'rb').read().decode('utf-8'); eol = '\r\n' if '\r\n' in y else '\n'
i = y.index('- Timer1:'); k = y.index('PressedFill: =Self.Color', i); k = y.index(eol, k) + len(eol)
y = y[:k] + '            Repeat: =true' + eol + y[k:]
open(yp, 'wb').write(y.encode('utf-8'))
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL57 built')
