#!/usr/bin/env python3
"""FINAL53 on FINAL52: the contact '+' buttons (RS_DetailsToggle_contrator_1 / RS_DetailsToggle_contrator) are enabled only
after a typed search in RS_Owner / RS_Contractor found nobody. The 'found nobody' state is latched in locOwnerNoMatch /
locContractorNoMatch because a combobox clears SearchText when it loses focus (the click on the button blurs it)."""
import datetime, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG42', 'newG43'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
def nomatch(ctl, extra):
    return f'Not(IsBlank({ctl}.SearchText)) And IsEmpty(Filter(Office365Users.SearchUserV2({{searchTerm: {ctl}.SearchText, top: 20}}).value, {extra}Not(StartsWith(DisplayName, "\'"))))'
for ctl, btn, flag, typ in (('RS_Owner', 'RS_DetailsToggle_contrator_1', 'locOwnerNoMatch', 'DG/Agency'),
                            ('RS_Contractor', 'RS_DetailsToggle_contrator', 'locContractorNoMatch', 'Contractor')):
    old = app.rule(S, btn, 'DisplayMode')
    new = (f'// enabled only after a typed search found nobody (latched in {flag}, since the combobox clears its\n'
           f'// SearchText when the click on this button takes the focus away); never in view mode\n'
           f'If(\n    IsEmpty({ctl}.SelectedItems) And Not(varRequestorLocked) And ({flag} Or ({nomatch(ctl, "")})),\n'
           f'    DisplayMode.Edit,\n    DisplayMode.Disabled\n)')
    app.set(S, btn, 'DisplayMode', new, expect=old)
    o = app.rule(S, btn, 'OnSelect')
    app.set(S, btn, 'OnSelect', f'UpdateContext({{{flag}: false}});\n' + o, expect=o)
    o = app.rule(S, ctl, 'OnChange')
    app.set(S, ctl, 'OnChange', f'UpdateContext({{{flag}: false}});\n' + o, expect=o)
    o = app.rule(S, btn, 'Tooltip')
    app.set(S, btn, 'Tooltip', o[:-1] + ' (type a name first; enabled when the search finds nobody)"', expect=o)
t = app.rule(S, None, 'OnVisible')
a = 'locShowAdminNotes: false,'
n = t.replace('\r\n', '\n')
if n.count(a) != 1: sys.exit('! OnVisible block')
n = n.replace(a, a + '\n        locOwnerNoMatch: false,\n        locContractorNoMatch: false,')
app.set(S, None, 'OnVisible', n.replace('\n', '\r\n') if '\r\n' in t else n, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL53 built')
