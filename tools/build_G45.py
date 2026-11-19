#!/usr/bin/env python3
"""FINAL55 on FINAL54: the contact '+' buttons stay clickable whenever the search result is empty.
A combobox clears SearchText on blur, i.e. while the click lands, so an empty search (typed-but-not-found, or blank after
the focus moved) counts as 'no result': the button is disabled only while the list actually shows matches, when a contact is
already picked, or in view mode. The FINAL53 latch variables are no longer needed and are removed."""
import datetime, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG44', 'newG45'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
for ctl, btn, flag, tip in (('RS_Owner', 'RS_DetailsToggle_contrator_1', 'locOwnerNoMatch', 'Add Official Contact'),
                            ('RS_Contractor', 'RS_DetailsToggle_contrator', 'locContractorNoMatch', 'Add Contractor Contact')):
    old = app.rule(S, btn, 'DisplayMode')
    new = (f'// enabled while nothing is picked in {ctl} and its search result is empty (typed but not found, or blank);\n'
           f'// disabled while the list shows matches; never in view mode, where the popup cannot save\n'
           f'If(\n    IsEmpty({ctl}.SelectedItems) And Not(varRequestorLocked)\n'
           f'        And (IsBlank({ctl}.SearchText) Or IsEmpty(Filter(Office365Users.SearchUserV2({{searchTerm: {ctl}.SearchText, top: 20}}).value, Not(StartsWith(DisplayName, "\'"))))),\n'
           f'    DisplayMode.Edit,\n    DisplayMode.Disabled\n)')
    app.set(S, btn, 'DisplayMode', new, expect=old)
    pre = f'UpdateContext({{{flag}: false}});\n'
    for c, p in ((btn, 'OnSelect'), (ctl, 'OnChange')):
        o = app.rule(S, c, p); assert o.startswith(pre), (c, p)
        app.set(S, c, p, o[len(pre):], expect=o)
    o = app.rule(S, btn, 'Tooltip')
    app.set(S, btn, 'Tooltip', f'"{tip}"', expect=o)
t = app.rule(S, None, 'OnVisible')
n = t.replace('\r\n', '\n')
rm = '\n        locOwnerNoMatch: false,\n        locContractorNoMatch: false,'
if n.count(rm) != 1: sys.exit('! OnVisible block')
n = n.replace(rm, '')
app.set(S, None, 'OnVisible', n.replace('\n', '\r\n') if '\r\n' in t else n, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL55 built')
