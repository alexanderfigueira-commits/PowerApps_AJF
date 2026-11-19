#!/usr/bin/env python3
"""FINAL190 on FINAL189. Leave-guard pop-up + media-level Save Draft.
Clicking any top-menu item inside a request or a media file (Info, Metadata, Legal & Docs, Validations, Request screen) asks:
Leave without saving / Go back / Save and leave. Read-only users skip the pop-up.
Media: 'Save and leave' runs the existing CV_BtnSaveArchive save in draft mode (varDraftSave): no validation list, only title + type + request id
are needed, then it navigates to the menu target. Request: it presses the existing SaveButton and leaves only if it reported success."""
import datetime, os, re, shutil
from payaml import App
from hp_common import Builder
SRC, NEW = 'newV51', 'newV52'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def sub(t, old, new, n=1):
    assert t.count(old) == n, (old, t.count(old)); return t.replace(old, new)
def edit(screen, ctl, prop, fn):
    t = app.rule(screen, ctl, prop); n = fn(t); assert n != t, (screen, ctl, prop)
    app.set(screen, ctl, prop, n, expect=t)
CI, CM, CL, CV, RS = 'ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen', 'RequesDetailScreen'
RSN = 'Navigate(RequesDetailScreen, ScreenTransition.None, {locShowTypePicker: false, locResetContacts: false})'
NAV = ('Switch(varLeaveTo, "Requests", Navigate(RequestManagementScreen), "Dashboard", If(varUserRole = "ADMINISTRATOR", Navigate(\'Dashboard-Ope-Administrator\'), '
       'Navigate(\'Dashboard-Ope-Requestor\')), "Review", Navigate(ReviewScreen), "Export", Navigate(HomePrintScreen), "Help", Navigate(HelpScreen), ' + RSN + ')')
LEAVE = 'Set(varDraftSave, false); Set(varLeaveAsk, false); ' + NAV + '; Set(varLeaveTo, "")'
BACKFAIL = 'If(varDraftSave, Set(varDraftSave, false); Navigate(varLeaveFrom))'
# ---------- 1. save block in draft mode
def save(t):
    t = sub(t, 'Notify("Save the request first (Draft Save): it has no id yet, so the media file cannot be saved.", NotificationType.Warning),',
            'Notify("Save the request first (Draft Save): it has no id yet, so the media file cannot be saved.", NotificationType.Warning);\n    ' + BACKFAIL + ',')
    t = sub(t, '    CountIf(colValidations, Not(Pass)) > 0,\n', '    Not(varDraftSave) And CountIf(colValidations, Not(Pass)) > 0,\n')
    t = sub(t, 'Or IsBlank(varChildMediaType) Or varChildMediaType = "" Or IsBlank(varChildContractCase) Or varChildContractCase = "",',
            'Or IsBlank(varChildMediaType) Or varChildMediaType = "" Or (Not(varDraftSave) And (IsBlank(varChildContractCase) Or varChildContractCase = "")),')
    t = sub(t, '"no contract case is selected (Legal & Docs tab).")), NotificationType.Warning),',
            '"no contract case is selected (Legal & Docs tab).")), NotificationType.Warning);\n    ' + BACKFAIL + ',')
    t = sub(t, 'ContractCase: Table({Value: varChildContractCase}),', 'ContractCase: Filter(Table({Value: varChildContractCase}), Len(Coalesce(Value, "")) > 0),')
    t = sub(t, '{n: "contract case", bad: IsEmpty(chk.ContractCase)},', '{n: "contract case", bad: Not(IsBlank(varChildContractCase)) And varChildContractCase <> "" And IsEmpty(chk.ContractCase)},')
    t = sub(t, 'Notify("Media saved to SharePoint.", NotificationType.Success)', 'Notify(If(varDraftSave, "Draft saved.", "Media saved to SharePoint."), NotificationType.Success)')
    t = sub(t, 'Notify("Save failed: " & FirstError.Message, NotificationType.Error)', 'Notify("Save failed: " & FirstError.Message, NotificationType.Error);\n            ' + BACKFAIL)
    n = t.count(RSN); assert n == 2, n
    return t.replace(RSN, 'If(varDraftSave, ' + LEAVE + ', ' + RSN + ')')
edit(CV, 'CV_BtnSaveArchive', 'OnSelect', save)
edit(CV, 'CV_BtnSaveArchive', 'DisplayMode', lambda t: sub(t, 'If(CountIf(colValidations, Not(Pass)) = 0,', 'If(Coalesce(varDraftSave, false) Or CountIf(colValidations, Not(Pass)) = 0,'))
def onok(t):
    t = sub(t, 'Notify("Media and attachments saved to SharePoint.", NotificationType.Success);', 'Notify(If(varDraftSave, "Draft saved.", "Media and attachments saved to SharePoint."), NotificationType.Success);')
    return sub(t, RSN, 'If(varDraftSave, ' + LEAVE + ', ' + RSN + ')')
edit(CL, 'CL_FormAttach', 'OnSuccess', onok)
edit(CL, 'CL_FormAttach', 'OnFailure', lambda t: 'Set(varDraftSave, false);\n' + t)
# request-level draft save reports success
edit(RS, 'SaveButton', 'OnSelect', lambda t: sub(t, 'Notify("Draft saved.", NotificationType.Success)', 'Set(varDraftOK, true); Notify("Draft saved.", NotificationType.Success)'))
# ---------- 2. menu buttons
KEY = {'Requests': 'Requests', 'Dashboard': 'Dashboard', 'Review': 'Review', 'Export': 'Export', 'Help': 'Help'}
SCR = {CI: 'CI', CM: 'CM', CL: 'CL', CV: 'CV', RS: 'RS'}
for scr, p in SCR.items():
    for k in KEY:
        name = f'{p}_Menu_{k}'
        def wrap(t, k=k, scr=scr):
            ask = f'Set(varLeaveTo, "{k}"); Set(varLeaveFrom, App.ActiveScreen); Set(varLeaveAsk, true)'
            cond = 'varViewOnly Or varRequestorLocked' + (' Or locShowTypePicker' if scr == RS else '')
            return f'If({cond}, {t.strip()}, {ask})'
        edit(scr, name, 'OnSelect', wrap)
# ---------- 3. timer on Validations (starts the draft save once the tab is on screen)
b = Builder(app, CV)
b.clone('CV_DraftTimer', RS, 'Timer1', {'AutoStart': 'false', 'Repeat': 'false', 'Duration': '600', 'Visible': 'false',
        'OnTimerEnd': 'Set(varDraftPending, false);\nSelect(CV_BtnSaveArchive)', 'X': '0', 'Y': '0', 'Width': '10', 'Height': '10'})
b.save()
from payaml import find
import copy
tp = app.doc(CV)['TopParent']; tm = find(tp, 'CV_DraftTimer')
r0 = [r for r in tm['Rules'] if r['Property'] == 'Repeat'][0]
r1 = copy.deepcopy(r0); r1['Property'] = 'Start'; r1['InvariantScript'] = 'Coalesce(varDraftPending, false)'
tm['Rules'].append(r1)
yf = f'{NEW}/Src/{CV}.pa.yaml'; L = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
i0 = next(i for i, l in enumerate(L) if l == '      - CV_DraftTimer:')
j = next(i for i in range(i0, len(L)) if L[i].startswith('            Repeat:'))
L.insert(j + 1, '            Start: =Coalesce(varDraftPending, false)')
open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(L))
# ---------- 4. pop-ups
def popup(scr, p, text, saveact, savedm='DisplayMode.Edit'):
    b = Builder(app, scr)
    V = {'Visible': 'Coalesce(varLeaveAsk, false)'}
    b.clone(f'{p}_LeaveShade', CI, 'CI_TplConfirmShade', dict(V))
    b.clone(f'{p}_LeavePanel', CI, 'CI_TplConfirmPanel', dict(V, Height='190'))
    b.clone(f'{p}_LeaveText', CI, 'CI_TplConfirmText', dict(V, Text=text, Height='80'))
    b.clone(f'{p}_LeaveDiscard', CI, 'CI_TplConfirmCancel', dict(V, Text='"Leave without saving"', Width='170', X='447', Y='400', Height='50', Size='12',
            OnSelect='Set(varDraftSave, false); Set(varLeaveAsk, false); ' + NAV + '; Set(varLeaveTo, "")'))
    b.clone(f'{p}_LeaveBack', CI, 'CI_TplConfirmCancel', dict(V, Text='"Go back"', Width='110', X='627', Y='400', Height='50', Size='12',
            OnSelect='Set(varLeaveAsk, false); Set(varLeaveTo, "")'))
    b.clone(f'{p}_LeaveSave', CI, 'CI_TplConfirmOK', dict(V, Text='"Save and leave"', Width='196', X='747', Y='400', Height='50', Size='12',
            OnSelect=saveact, DisplayMode=savedm))
    b.save()
MEDIA = '"This media file has changes that may not be saved. Leave without saving, save it as a draft and leave, or go back?"'
GOTO_VALID = 'Set(varLeaveAsk, false); Set(varDraftSave, true); Set(varDraftPending, true); Navigate(ChildValidScreen, ScreenTransition.None)'
for scr, p in ((CI, 'CI'), (CM, 'CM'), (CL, 'CL')):
    popup(scr, p, MEDIA, GOTO_VALID)
popup(CV, 'CV', MEDIA, 'Set(varLeaveAsk, false); Set(varDraftSave, true); Set(varDraftPending, true)')
popup(RS, 'RS', '"This request has changes that may not be saved. Leave without saving, save it as a draft and leave, or go back?"',
      'Set(varDraftOK, false);\nSelect(SaveButton);\nIf(varDraftOK, Set(varLeaveAsk, false); ' + NAV + '; Set(varLeaveTo, ""))',
      'If(SaveButton.DisplayMode = DisplayMode.Edit, DisplayMode.Edit, DisplayMode.Disabled)')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL190 built')
