#!/usr/bin/env python3
"""FINAL24 on FINAL23: RS_Owner / RS_Contractor turn yellow when nothing real is picked.

Likely cause of "no yellow": for a new request varCurrentRequest is Defaults('AV-CD-Requests'), whose person lists can hold one
empty placeholder row. The combobox then looks empty but SelectedItems has one blank row, so IsEmpty(SelectedItems) is never
true. (The save already ignores such rows: Filter(..., Not(IsBlank(Mail))).)
* DefaultSelectedItems: the saved contacts are filtered on a non-blank Email, so no blank token / blank row is selected;
* BorderColor / BorderThickness: "nothing picked" = no selected item with a name or an e-mail, and still no manual contact;
* HoverBorderColor follows BorderColor, so the yellow does not turn navy under the mouse.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG13', 'newG14'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
for ctl, lbl, src in (('RS_Owner', 'RS_LblOwner', 'DG_Agency_Contact'), ('RS_Contractor', 'RS_LblContractor', 'Contractor_Contact')):
    d = app.rule(S, ctl, 'DefaultSelectedItems')
    old = f'ForAll(varCurrentRequest.{src} As p,'
    if d.count(old) != 1:
        sys.exit(f'! {ctl}: default changed')
    app.set(S, ctl, 'DefaultSelectedItems', d.replace(old, f'ForAll(Filter(varCurrentRequest.{src}, Not(IsBlank(Email))) As p,'), expect=d)
    bc, bt = app.rule(S, ctl, 'BorderColor'), app.rule(S, ctl, 'BorderThickness')
    old_t = f'IsEmpty({ctl}.SelectedItems)'
    if bc.count(old_t) != 1 or bt.count(old_t) != 1:
        sys.exit(f'! {ctl}: border rule changed')
    new_t = f'IsEmpty(Filter({ctl}.SelectedItems, Not(IsBlank(Trim(Coalesce(DisplayName, "")))) Or Not(IsBlank(Trim(Coalesce(Mail, ""))))))'
    app.set(S, ctl, 'BorderColor', bc.replace(old_t, new_t), expect=bc)
    app.set(S, ctl, 'BorderThickness', bt.replace(old_t, new_t), expect=bt)
    app.set(S, ctl, 'HoverBorderColor', 'Self.BorderColor', expect='RGBA(0, 18, 107, 1)')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL24 built')
