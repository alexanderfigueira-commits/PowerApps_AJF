#!/usr/bin/env python3
"""FINAL104 on FINAL103: the tooltip of SaveButton also tells when (and by whom) the request was last saved."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newJ4', 'newJ5'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
TIP = ('"Save draft" & If(\n'
       '    Coalesce(varCurrentRequest.ID, 0) > 0 And Not(IsBlank(varCurrentRequest.Modified)),\n'
       '    With(\n'
       '        {who: Coalesce(varCurrentRequest.\'Modified By\'.DisplayName, "")},\n'
       '        Char(10) & "Last saved: " & Text(varCurrentRequest.Modified, "dd mmm yyyy, hh:mm")\n'
       '            & If(IsBlank(who), "", " by " & Trim(If("(" in who, Left(who, Find("(", who) - 1), who)))\n'
       '    ),\n'
       '    Char(10) & "Not saved yet"\n'
       ')')
app.set('RequesDetailScreen', 'SaveButton', 'Tooltip', TIP, expect='"Save draft"')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL104 built')
