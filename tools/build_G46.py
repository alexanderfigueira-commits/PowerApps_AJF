#!/usr/bin/env python3
"""FINAL56 on FINAL54 (keeps the FINAL53 latch variables; FINAL55 is dropped): the contact '+' buttons no longer depend on SelectedItems being empty (a contact already picked, or a
saved one, kept them disabled even after a search with no result) and an error in the search can no longer disable them."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG44', 'newG46'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
for ctl, btn, flag in (('RS_Owner', 'RS_DetailsToggle_contrator_1', 'locOwnerNoMatch'), ('RS_Contractor', 'RS_DetailsToggle_contrator', 'locContractorNoMatch')):
    old = app.rule(S, btn, 'DisplayMode')
    new = (f'// disabled by default; enabled after a typed {ctl} search found nobody (latched in {flag} because the combobox\n'
           f'// clears SearchText when the click takes the focus away), whatever is already picked; never in view mode\n'
           f'If(\n    Not(varRequestorLocked)\n'
           f'        And ({flag} Or IfError(Not(IsBlank({ctl}.SearchText)) And IsEmpty(Filter(Office365Users.SearchUserV2({{searchTerm: {ctl}.SearchText, top: 20}}).value, Not(StartsWith(DisplayName, "\'")))), false)),\n'
           f'    DisplayMode.Edit,\n    DisplayMode.Disabled\n)')
    app.set(S, btn, 'DisplayMode', new, expect=old)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL56 built')
