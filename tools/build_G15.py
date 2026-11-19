#!/usr/bin/env python3
"""FINAL25 on FINAL24: yellow border for CM_SeasonNumber, CM_EpisodeNumber and CM_Producer (ChildMetaScreen).

* Season / Episode number: a new item holds 0 and the box showed "0", so it was never blank. The box now shows empty
  (hint "1") while the number is not above 0, the yellow test is "not a number above 0" (the Validations rule), and a
  non-numeric entry no longer raises an error (it counts as 0, so it stays yellow).
* Producer: yellow when nothing real is selected or when the producer text the Validations tab checks (varChildProducer)
  is empty.
* The border no longer turns navy under the mouse on the two number boxes.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG14', 'newG15'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, Y, NAVY = 'ChildMetaScreen', 'RGBA(255, 204, 0, 1)', 'RGBA(0, 18, 107, 1)'

for ctl, lbl, var in (('CM_SeasonNumber', 'CM_LblSeasonNumber', 'varChildSeasonNumber'), ('CM_EpisodeNumber', 'CM_LblEpisodeNumber', 'varChildEpisodeNumber')):
    d, oc, bc, bt = (app.rule(S, ctl, p) for p in ('Default', 'OnChange', 'BorderColor', 'BorderThickness'))
    old_t = f'IsBlank(Trim({ctl}.Text))'
    if d != f'Text({var})' or oc != f'Set({var}, Value(Self.Text))' or old_t not in bc or old_t not in bt:
        sys.exit(f'! {ctl}: rules changed')
    not_pos = f'Coalesce(IfError(Value(Trim({ctl}.Text)), 0), 0) <= 0'
    app.set(S, ctl, 'Default', f'// empty (showing the hint) until a number above 0 is stored\nIf({var} > 0, Text({var}), "")', expect=d)
    app.set(S, ctl, 'OnChange', f'Set({var}, Coalesce(IfError(Value(Self.Text), 0), 0))', expect=oc)
    app.set(S, ctl, 'BorderColor', bc.replace(old_t, not_pos), expect=bc)
    app.set(S, ctl, 'BorderThickness', bt.replace(old_t, not_pos), expect=bt)
    app.set(S, ctl, 'HoverBorderColor', 'Self.BorderColor', expect=NAVY)

bc, bt = app.rule(S, 'CM_Producer', 'BorderColor'), app.rule(S, 'CM_Producer', 'BorderThickness')
old_t = 'IsEmpty(CM_Producer.SelectedItems)'
if old_t not in bc or old_t not in bt:
    sys.exit('! CM_Producer rules changed')
none = 'IsBlank(varChildProducer) Or IsEmpty(Filter(CM_Producer.SelectedItems, Not(IsBlank(Trim(Coalesce(DisplayName, "")))) Or Not(IsBlank(Trim(Coalesce(Mail, ""))))))'
app.set(S, 'CM_Producer', 'BorderColor', bc.replace(old_t, f'({none})'), expect=bc)
app.set(S, 'CM_Producer', 'BorderThickness', bt.replace(old_t, f'({none})'), expect=bt)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL25 built')
