#!/usr/bin/env python3
"""FINAL227 on FINAL226. The pre-selected contact of a NEW request did not show in Contact (Official DG/Agency).
- The person is now pushed into RS_Owner with the mechanism the app already uses for a manual contact (colOwnerForce +
  locOwnerForce + Reset), right after the contact pickers are reset when a request is opened; the name and mail come straight
  from User() (FullName / Email), so nothing depends on the Office 365 profile call having answered.
- The DG / Agency dropdown is reset there too (it shows the DG found from the department), and it starts empty instead of
  showing the first DG of the list (AGRI) when no DG was found; its tooltip tells the department read from Microsoft 365."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV88', 'newV89'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))


def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)


def rep(scr, ctl, prop, old, new, count=1):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    assert t.count(old) == count, (scr, ctl, prop, t.count(old), old[:80])
    app.set(scr, ctl, prop, t.replace(old, new), expect=t)


RS = 'RequesDetailScreen'
ME = '{DisplayName: User().FullName, Mail: User().Email, GivenName: "", Surname: "", MailNickname: ""}'
rep(RS, None, 'OnVisible',
    '    Reset(RS_Owner);\n\n    Reset(RS_Contractor);\n\n    UpdateContext({locResetContacts: false})\n',
    '    Reset(RS_Owner);\n\n    Reset(RS_Contractor);\n\n'
    '    // a NEW request: the person who opens it (User()) is pre-selected in Contact (Official DG/Agency), pushed the way a manual\n'
    '    // contact is (colOwnerForce + locOwnerForce + Reset); the DG / Agency dropdown shows the DG found from the department\n'
    '    If(\n'
    '        Coalesce(varCurrentRequest.ID, 0) <= 0 And Not(IsBlank(User().Email)),\n'
    f'        ClearCollect(colOwnerForce, {ME});\n'
    '        UpdateContext({locOwnerForce: true});\n'
    '        Reset(RS_Owner);\n'
    '        Set(varRequestOwnerContact, User().FullName);\n'
    '        Reset(HomeFilterDG)\n'
    '    );\n\n'
    '    UpdateContext({locResetContacts: false})\n')
rep(RS, None, 'OnVisible',
    'If(Coalesce(varCurrentRequest.ID, 0) <= 0 And Not(IsBlank(varMeContact.Mail)), Set(varRequestOwnerContact, varMeContact.DisplayName));',
    'If(Coalesce(varCurrentRequest.ID, 0) <= 0 And Not(IsBlank(User().Email)), Set(varRequestOwnerContact, User().FullName));')
rep(RS, 'RS_Owner', 'DefaultSelectedItems',
    'Table({DisplayName: varMeContact.DisplayName, Mail: varMeContact.Mail, GivenName: "", Surname: "", MailNickname: ""})',
    f'Table({ME})')
setp(RS, 'HomeFilterDG', 'AllowEmptySelection', 'true')
setp(RS, 'HomeFilterDG', 'Tooltip',
     'If(\n    varRequestorLocked,\n    "",\n'
     '    Coalesce(varUserDG, "") <> "" And HomeFilterDG.Selected.Value = varUserDG,\n'
     '    "Filled in from your department in Microsoft 365 (" & varUserDept & "). You can change it.",\n'
     '    Coalesce(varCurrentRequest.ID, 0) <= 0,\n'
     '    "Your department in Microsoft 365: " & If(IsBlank(varUserDept) Or varUserDept = "", "(empty)", varUserDept) & ". No DG / Agency was found for it: choose it in the list.",\n'
     '    ""\n)')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL227 built')
