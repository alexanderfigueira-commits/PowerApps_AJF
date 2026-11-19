#!/usr/bin/env python3
"""FINAL18 on FINAL17: yellow border on every starred (mandatory) field of the Metadata / Info tabs.

* CM_ShootDate (new), CM_PlacePhoto (new), CM_Credits (new, only while its label carries the star), CI_Description (new, same):
  yellow while empty. The star test follows the label text, which changes with the media type.
* CM_ProdEnd, CM_PubStartV, CM_PubEndV: the test now uses the value the Validations tab checks (the variable) as well as the
  control's own date, so the border can never disagree with the validation.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG7', 'newG8'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
Y, NAVY = 'RGBA(255, 204, 0, 1)', 'RGBA(0, 18, 107, 1)'
META, INFO = 'ChildMetaScreen', 'ChildInfoScreen'

# (screen, control, label, "empty" test, is the star conditional?)
NEWFIELDS = [
    (META, 'CM_ShootDate', 'CM_LblShootDate', 'IsBlank(varChildCaptureDate) Or IsBlank(CM_ShootDate.SelectedDate)', True),
    (META, 'CM_PlacePhoto', 'CM_LblPlacePhoto', 'IsBlank(Trim(CM_PlacePhoto.Text))', True),
    (META, 'CM_Credits', 'CM_LblCredits', 'IsBlank(Trim(CM_Credits.Text))', True),
    (INFO, 'CI_Description', 'CI_LblDescription', 'IsBlank(Trim(CI_Description.Text))', True),
]
for s, ctl, lbl, empty, star in NEWFIELDS:
    bc, bt = app.rule(s, ctl, 'BorderColor'), app.rule(s, ctl, 'BorderThickness')
    if bc != NAVY or bt != '2':
        sys.exit(f'! {ctl}: border rules are not the plain ones ({bc!r}, {bt!r})')
    cond = f'{lbl}.Visible And Right(Trim({lbl}.Text), 1) = "*" And ({empty})'
    app.set(s, ctl, 'BorderColor', f'// yellow while this mandatory (starred) field is empty\nIf({cond}, {Y}, {NAVY})', expect=bc)
    app.set(s, ctl, 'BorderThickness', f'If({cond}, 3, 2)', expect=bt)

# the three date fields that had the rule: test the validation's own value too
for ctl, lbl, var in (('CM_ProdEnd', 'CM_LblProdEnd', 'varChildProductionEndDate'),
                      ('CM_PubStartV', 'CM_LblPubStartV', 'varChildPublicationStartDate'),
                      ('CM_PubEndV', 'CM_LblPubEndV', 'varChildPublicationEndDate')):
    bc, bt = app.rule(META, ctl, 'BorderColor'), app.rule(META, ctl, 'BorderThickness')
    old = f'{lbl}.Visible And IsBlank({ctl}.SelectedDate)'
    if old not in bc or old not in bt:
        sys.exit(f'! {ctl}: rule changed')
    new = f'{lbl}.Visible And (IsBlank({var}) Or IsBlank({ctl}.SelectedDate))'
    app.set(META, ctl, 'BorderColor', bc.replace(old, new), expect=bc)
    app.set(META, ctl, 'BorderThickness', bt.replace(old, new), expect=bt)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL18 built')
