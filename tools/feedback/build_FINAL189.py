#!/usr/bin/env python3
"""FINAL189 on FINAL188.
1. 'Signed framework contract' checkbox shown for every case (mandatory only for Case 1; same column FrameworkContractSigned).
2. FTP option not ticked -> non-blocking reminder on the Validations tab (screen open and Refresh).
3. FTP delivery path: mandatory and must be a valid link (ftp, ftps, sftp, http, https)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV50', 'newV51'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def sub(t, old, new, n=1):
    assert t.count(old) == n, (old, t.count(old)); return t.replace(old, new)
def edit(screen, ctl, prop, fn):
    t = app.rule(screen, ctl, prop); n = fn(t); assert n != t, (screen, ctl, prop)
    app.set(screen, ctl, prop, n, expect=t)
CL, CV, CI = 'ChildLegalScreen', 'ChildValidScreen', 'ChildInfoScreen'
C1 = 'Left(varChildContractCase, 6) = "Case 1"'
# 1. framework contract for all cases
edit(CL, 'CL_ChkFramework', 'Visible', lambda t: 'true')
edit(CL, 'CL_ChkFramework', 'Y', lambda t: f'If({C1}, 152, 130)')
edit(CL, 'CL_ChkFramework', 'Text', lambda t: f'If({C1}, "Signed framework contract *", "Signed framework contract (optional)")')
edit(CL, 'CL_Divider1', 'Y', lambda t: sub(t, '274, 134)', '274, 170)'))
edit(CL, 'CL_Gallery', 'TemplateSize', lambda t: sub(t, 'If(Left(varChildContractCase, 6) = "Case 1", 140, 0)', 'If(Left(varChildContractCase, 6) = "Case 1", 140, 36)'))
# 3. FTP format
PAT = 'IsMatch(Trim(Coalesce(varChildFTPPath1, "")), "^(ftp|ftps|sftp|https?)://\\S+$", MatchOptions.IgnoreCase)'
OLDP = 'Pass: Not(IsBlank(Trim(Coalesce(varChildFTPPath1, "")))), Note: "Paste the FTP link of the media file in the FTP delivery path on the Info tab."'
NEWP = 'Pass: ' + PAT + ', Note: "Paste a valid link in the FTP delivery path on the Info tab (it must start with ftp://, ftps://, sftp://, http:// or https://)."'
NOTE = ('\n;\nIf(\n    Not(varDocsViaFTP),\n    Notify("Reminder: check that you are sending all supported media files. If the legal and supporting documents travel in the same FTP, tick the FTP option on the Legal & Docs tab.", NotificationType.Warning)\n)')
def val(t):
    t = sub(t, OLDP, NEWP)
    return t.rstrip('\n') + NOTE
edit(CV, None, 'OnVisible', val)
edit(CV, 'CV_BtnRefresh', 'OnSelect', val)
BAD = 'IsBlank(Trim(CI_FTPPath.Text))'
GOOD = 'Not(IsMatch(Trim(CI_FTPPath.Text), "^(ftp|ftps|sftp|https?)://\\S+$", MatchOptions.IgnoreCase))'
edit(CI, 'CI_FTPPath', 'BorderColor', lambda t: sub(t, BAD, GOOD).replace('while this mandatory field is empty', 'while this mandatory field is empty or not a valid link'))
edit(CI, 'CI_FTPPath', 'BorderThickness', lambda t: sub(t, BAD, GOOD))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL189 built')
