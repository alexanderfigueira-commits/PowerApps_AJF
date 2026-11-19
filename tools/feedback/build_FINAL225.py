#!/usr/bin/env python3
"""FINAL225 on FINAL224. A NEW request pre-selects the person who opens it (User(), with the Microsoft 365 profile's name and
mail) in Contact (Official DG/Agency) (RS_Owner), whatever the account type; Contact (Contractor) is no longer pre-filled,
so the same person is not proposed twice. Both stay editable; existing requests keep their saved contacts."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV86', 'newV87'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))


def rep(scr, ctl, prop, old, new, count=1):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    assert t.count(old) == count, (scr, ctl, prop, t.count(old), old[:80])
    app.set(scr, ctl, prop, t.replace(old, new), expect=t)


RS = 'RequesDetailScreen'
rep(RS, None, 'OnVisible',
    '''// a NEW request proposes the person who opens it as its first contact (it stays editable): an external account
// ("-EXT)" in the display name, or an @ext. mail) as Contact (Contractor), EC staff as Contact (Official DG/Agency)
''',
    '''// a NEW request pre-selects the person who opens it (User()) in Contact (Official DG/Agency); it stays editable.
// varMeIsExt (an "-EXT)" display name or an @ext. mail) is kept for information only
''')
rep(RS, None, 'OnVisible',
    'If(Coalesce(varCurrentRequest.ID, 0) <= 0 And Not(varMeIsExt) And Not(IsBlank(varMeContact.Mail)), Set(varRequestOwnerContact, varMeContact.DisplayName));',
    'If(Coalesce(varCurrentRequest.ID, 0) <= 0 And Not(IsBlank(varMeContact.Mail)), Set(varRequestOwnerContact, varMeContact.DisplayName));')
rep(RS, 'RS_Owner', 'DefaultSelectedItems',
    'Coalesce(varCurrentRequest.ID, 0) <= 0 And Not(varMeIsExt) And Not(IsBlank(Mail))',
    'Coalesce(varCurrentRequest.ID, 0) <= 0 And Not(IsBlank(Mail))')
rep(RS, 'RS_Contractor', 'DefaultSelectedItems',
    ''')},
            // a NEW request: the person who opens it (see OnVisible)
            {rows: Filter(
                Table({DisplayName: varMeContact.DisplayName, Mail: varMeContact.Mail, GivenName: "", Surname: "", MailNickname: ""}),
                Coalesce(varCurrentRequest.ID, 0) <= 0 And varMeIsExt And Not(IsBlank(Mail))
            )}
        ),''',
    ''')}
        ),''')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL225 built')
