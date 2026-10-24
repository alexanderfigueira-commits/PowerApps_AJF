#!/usr/bin/env python3
"""FINAL51 on FINAL50: RS_Owner and RS_Contractor search by user ID / e-mail / last and first name (Office365Users.SearchUserV2)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG40', 'newG41'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
FIELDS = '["DisplayName", "GivenName", "Surname", "MailNickname", "Mail"]'
def sub(s, ctl, prop, old, new):
    cur = app.rule(s, ctl, prop)
    assert old in cur, (ctl, prop)
    app.set(s, ctl, prop, cur.replace(old, new), expect=cur)
for ctl in ('RS_Owner', 'RS_Contractor'):
    app.set(S, ctl, 'InputTextPlaceholder', '"Search by user ID or email or last and first name"', expect=app.rule(S, ctl, 'InputTextPlaceholder'))
    app.set(S, ctl, 'DisplayFields', '["DisplayName","Mail"]', expect='["DisplayName"]')
    app.set(S, ctl, 'SearchFields', '["DisplayName","GivenName","Surname","MailNickname","Mail"]', expect='["DisplayName"]')
    # every row carries the searched columns
    sub(S, ctl, 'Items', '{DisplayName: o.DisplayName, Mail: o.Mail}',
        '{DisplayName: o.DisplayName, Mail: o.Mail, GivenName: o.GivenName, Surname: o.Surname, MailNickname: o.MailNickname}')
    sub(S, ctl, 'Items', 'Table({DisplayName: locManual, Mail: locManual})',
        'Table({DisplayName: locManual, Mail: locManual, GivenName: "", Surname: "", MailNickname: ""})')
    sub(S, ctl, 'DefaultSelectedItems', '{DisplayName: p.DisplayName, Mail: p.Email}',
        '{DisplayName: p.DisplayName, Mail: p.Email, GivenName: "", Surname: "", MailNickname: ""}')
    sub(S, ctl, 'DefaultSelectedItems', 'Table({DisplayName: locManual, Mail: locManual})',
        'Table({DisplayName: locManual, Mail: locManual, GivenName: "", Surname: "", MailNickname: ""})')
    # SearchItems: the connector already matches name, surname, alias and mail; do not narrow it back to DisplayName
    flt = 'Not(IsBlank(DisplayName)) And ' if ctl == 'RS_Owner' else ''
    app.set(S, ctl, 'SearchItems', f'Filter(Office365Users.SearchUserV2({{searchTerm: Self.SearchText, top: 20}}).value, {flt}Not(StartsWith(DisplayName, "\'")))',
            expect=app.rule(S, ctl, 'SearchItems'))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL51 built')
