#!/usr/bin/env python3
"""FINAL58 on FINAL57: saving a manual e-mail keeps the contacts already picked and shows the new e-mail in the field.
Reset(RS_Owner) re-read DefaultSelectedItems, which does not include unsaved picks (they vanished) and did not show the new
e-mail. Now the save builds the full selection (current picks + the new e-mail) in colOwnerForce / colContractorForce, flags it
(locOwnerForce / locContractorForce) and DefaultSelectedItems returns that list while the flag is set. The flags are cleared
where the screen already drops the pickers (locResetContacts: opening a request)."""
import datetime, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG47', 'newG48'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
PICK = '{DisplayName: locEmail, Mail: locEmail, GivenName: "", Surname: "", MailNickname: ""}'
for ctl, coll, flag in (('RS_Owner', 'colOwnerForce', 'locOwnerForce'), ('RS_Contractor', 'colContractorForce', 'locContractorForce')):
    o = app.rule(S, ctl, 'DefaultSelectedItems')
    app.set(S, ctl, 'DefaultSelectedItems', f'If(\n    {flag},\n    {coll},\n    {o}\n)', expect=o)
o = app.rule(S, 'RS_btnSaveContact', 'OnSelect')
old = '        If(locType = "DG/Agency", Reset(RS_Owner), Reset(RS_Contractor));\n'
n = o.replace('\r\n', '\n')
if n.count(old) != 1: sys.exit('! save block')
new = f'''        // the new e-mail joins what is already picked in the matching field (nothing picked is dropped)
        If(
            locType = "DG/Agency",
            ClearCollect(colOwnerForce, RS_Owner.SelectedItems);
            If(IsEmpty(Filter(colOwnerForce, Lower(Mail) = Lower(locEmail))), Collect(colOwnerForce, {PICK}));
            UpdateContext({{locOwnerForce: true}});
            Reset(RS_Owner),
            ClearCollect(colContractorForce, RS_Contractor.SelectedItems);
            If(IsEmpty(Filter(colContractorForce, Lower(Mail) = Lower(locEmail))), Collect(colContractorForce, {PICK}));
            UpdateContext({{locContractorForce: true}});
            Reset(RS_Contractor)
        );
'''
n = n.replace(old, new)
app.set(S, 'RS_btnSaveContact', 'OnSelect', n.replace('\n', '\r\n') if '\r\n' in o else n, expect=o)
# opening a request drops the pickers: drop the forced lists with them
t = app.rule(S, None, 'OnVisible'); m = t.replace('\r\n', '\n')
a = '    Reset(RS_Owner);\n'
if m.count(a) != 1: sys.exit('! OnVisible block')
m = m.replace(a, '    UpdateContext({locOwnerForce: false, locContractorForce: false});\n' + a)
app.set(S, None, 'OnVisible', m.replace('\n', '\r\n') if '\r\n' in t else m, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL58 built')
