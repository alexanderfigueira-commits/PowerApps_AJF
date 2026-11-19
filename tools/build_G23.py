#!/usr/bin/env python3
"""FINAL33 on FINAL32, from the audit answers:
* FTP delivery path (Photo): Validations already require it, so the label gets the * and the box the yellow border while it is empty;
* Export (HomePrintScreen) loads the requests itself when it opens: all requests the user may see (own requests; an ADMINISTRATOR sees all
  except drafts), so it no longer depends on the Request Management screen having been opened first, nor on that screen's filters
  (which hid every status except the one selected there).
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG22', 'newG23'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
CI = 'ChildInfoScreen'
app.set(CI, 'CI_LblFTPPath', 'Text', '"FTP delivery path *"', expect='"FTP delivery path"')
bc, bt = app.rule(CI, 'CI_FTPPath', 'BorderColor'), app.rule(CI, 'CI_FTPPath', 'BorderThickness')
if bc != 'RGBA(0, 18, 107, 1)' or bt != '2':
    sys.exit('! CI_FTPPath border rules changed')
EMPTY = 'CI_LblFTPPath.Visible And IsBlank(Trim(CI_FTPPath.Text))'
app.set(CI, 'CI_FTPPath', 'BorderColor', f'// yellow while this mandatory field is empty\nIf({EMPTY}, RGBA(255, 204, 0, 1), RGBA(0, 18, 107, 1))', expect=bc)
app.set(CI, 'CI_FTPPath', 'BorderThickness', f'If({EMPTY}, 3, 2)', expect=bt)

HP = 'HomePrintScreen'
t = app.rule(HP, None, 'OnVisible')
old = 'UpdateContext({locHPProductionType: "All", locHPStatus: "All"});\nClearCollect(colPrintMedia, \'AV-CD-Mediafiles\')'
if t.replace('\r\n', '\n') != old:
    sys.exit(f'! HomePrintScreen.OnVisible changed: {t!r}')
app.set(HP, None, 'OnVisible', '''UpdateContext({locHPProductionType: "All", locHPStatus: "All"});
// Export loads its own data: it no longer depends on the Request Management gallery having been opened (or on its filters).
// The same visibility rule as that gallery: own requests; an ADMINISTRATOR sees every request except drafts.
Refresh('AV-CD-Requests');
ClearCollect(colPrintData, 'AV-CD-Requests');
RemoveIf(colPrintData, Not('Created By'.Email = User().Email Or (varUserRole = "ADMINISTRATOR" And Status.Value <> "Draft")));
ClearCollect(colPrintMedia, 'AV-CD-Mediafiles')''', expect=old)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL33 built')
