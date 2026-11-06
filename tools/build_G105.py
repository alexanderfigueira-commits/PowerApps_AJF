#!/usr/bin/env python3
"""FINAL115 on FINAL114: ImportFormScreen (no menu link; opened with <app address>&Page=import).
An administrator or an internal requestor uploads the filled Word metadata form (.docx); the flow 'CD - 09 Import form' reads it; the screen shows what was read;
after the confirmation the flow creates the Draft request and e-mails the requestor the link.
 * 8 import columns on AV-CD-Requests (embedded schema): the staging item of an import is the request itself (Draft, hidden from every list until ImportStatus = Done)
 * App.OnStart: varDeepPage = Param("Page"); both dashboards' deep-link Timer opens the screen when it is 'import'
"""
import copy, datetime, json, os, re, shutil, sys
from payaml import App, find
from hp_common import Builder, next_ids
from jio import jwrite
SRC, NEW = 'newN2', 'newO1'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
# ------------------------------------------------------------------ 1. columns on AV-CD-Requests
COLS = ['ImportRequestorEmail', 'ImportStatus', 'ImportDG', 'ImportedBy', 'ImportRequestID', 'ImportData', 'ImportPreview', 'ImportMessage']
dp = f'{NEW}/References/DataSources.json'
raw = open(dp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); txt = raw.decode('utf-8-sig')
d = json.loads(txt)
ds = [x for x in d['DataSources'] if x.get('Name') == 'AV-CD-Requests'][0]
key, meta = next(iter(ds['DataEntityMetadataJson'].items()))
m = json.loads(meta); props = m['schema']['items']['properties']; tmpl = props['Manual_DG_Agency_Contact']
for c in COLS:
    assert c not in props
    p = json.loads(json.dumps(tmpl)); p['title'] = c; props[c] = p
fmt = m['schema']['items']['x-ms-displayFormat']
for lst in ('propertiesDisplayOrder', 'propertiesCompactDisplayOrder', 'propertiesTabularDisplayOrder'):
    L = fmt[lst]; at = L.index('{Attachments}') if '{Attachments}' in L else len(L); L[at:at] = COLS
ds['DataEntityMetadataJson'][key] = json.dumps(m, separators=(',', ':'), ensure_ascii=False)
for c in COLS: ds['ConnectedDataSourceInfoNameMapping'][c] = c
indent = 2 if '\n  "' in txt else None
out = json.dumps(d, ensure_ascii=False, indent=indent, separators=(',', ': ') if indent else (',', ':'))
if '\r\n' in txt: out = out.replace('\n', '\r\n')
open(dp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out)
app = App(NEW)
# ------------------------------------------------------------------ 2. deep link: &Page=import
t = app.rule('App', None, 'OnStart'); eol = '\r\n' if '\r\n' in t else '\n'; n = t.replace('\r\n', '\n')
a = 'Set(varDeepLinkId, IfError(Value(Param("RequestID")), 0));'
assert n.count(a) == 1
app.set('App', None, 'OnStart', n.replace(a, a + '\n// &Page=import opens the import of the metadata form (not in any menu)\nSet(varDeepPage, Lower(Coalesce(Param("Page"), "")));').replace('\n', eol), expect=t)
for scr, tm in (('Dashboard-Ope-Administrator', 'DOA_DeepLinkTimer_1'), ('Dashboard-Ope-Requestor', 'DOA_DeepLinkTimer')):
    t = app.rule(scr, tm, 'OnTimerEnd'); eol = '\r\n' if '\r\n' in t else '\n'; n = t.replace('\r\n', '\n')
    ind = '\n'.join('    ' + l if l else l for l in n.split('\n'))
    new = 'If(\n    varDeepPage = "import",\n    Set(varDeepPage, "");\n    Navigate(ImportFormScreen, ScreenTransition.None),\n' + ind + '\n)'
    app.set(scr, tm, 'OnTimerEnd', new.replace('\n', eol), expect=t)
app.save()
# ------------------------------------------------------------------ 2b. staging requests (ImportStatus New / Uploaded / Parsed / Confirmed / Error) stay out of every list
HIDE = 'Coalesce(ImportStatus, "Done") <> "Done"'
n_hide = 0
for scr in list(app.map):
    def walk(c, ctl, scr=scr):
        global n_hide
        for r in c['Rules']:
            t = r['InvariantScript']
            for m in sorted(set(re.findall(r"ClearCollect\((col[A-Za-z]+), (?:Filter\()?'AV-CD-Requests'", t))):
                pat = re.compile(r"ClearCollect\(" + m + r", (?:Filter\('AV-CD-Requests', 'Created By'\.Email = User\(\)\.Email\)|'AV-CD-Requests')\)")
                new, k = pat.subn(lambda mm: mm.group(0) + f"; RemoveIf({m}, {HIDE})", t)
                if k:
                    app.set(scr, ctl, r['Property'], new, expect=t); t = new; n_hide += k
        for k_ in c.get('Children', []): walk(k_, k_['Name'])
    walk(app.doc(scr)['TopParent'], None)
assert n_hide == 11, n_hide
app.save()
print('staging requests hidden in', n_hide, 'collection loads')
# ------------------------------------------------------------------ 3. the screen shell
S = 'ImportFormScreen'
uid, poi = next_ids(NEW)
hp = [f for f in os.listdir(os.path.join(NEW, 'Controls')) if json.load(open(os.path.join(NEW, 'Controls', f), encoding='utf-8'))['TopParent']['Name'] == 'HelpScreen'][0]
src = json.load(open(os.path.join(NEW, 'Controls', hp), encoding='utf-8'))      # HelpScreen as skeleton
doc = copy.deepcopy(src); tp = doc['TopParent']
tp['Name'] = S; tp['ControlUniqueId'] = str(uid); tp['PublishOrderIndex'] = poi; tp['Index'] = 15; tp['Children'] = []
for r in tp['Rules']:
    if r['Property'] == 'Fill': r['InvariantScript'] = 'RGBA(247, 248, 250, 1)'
ONVIS = ('UpdateContext({locImpStep: 1, locImpPoll: false, locImpName: "", locImpErr: ""});\nSet(varImpItem, Blank());\nReset(ImpEmail);\nReset(ImpDG)')
for r in tp['Rules']:
    if r['Property'] == 'OnVisible': r['InvariantScript'] = ONVIS
jwrite(doc, os.path.join(NEW, 'Controls', f'{uid}.json'))
head = open(os.path.join(NEW, 'Src', 'HelpScreen.pa.yaml'), encoding='utf-8').read(); banner = head[:head.index('Screens:')]
vis_yaml = '      OnVisible: |-\n' + ''.join(f'        {"=" if i == 0 else ""}{l}\n' for i, l in enumerate(ONVIS.split('\n')))
open(os.path.join(NEW, 'Src', f'{S}.pa.yaml'), 'w', encoding='utf-8').write(
    banner + 'Screens:\n' + f'  {S}:\n    Properties:\n      Fill: =RGBA(247, 248, 250, 1)\n      LoadingSpinnerColor: =RGBA(0, 51, 102, 1)\n' + vis_yaml + '    Children:\n')
ef = os.path.join(NEW, 'Src', '_EditorState.pa.yaml'); L = open(ef, encoding='utf-8').read().split('\n')
at = max(i for i, l in enumerate(L) if l.startswith('    - ')) + 1; L[at:at] = [f'    - {S}']; open(ef, 'w', encoding='utf-8').write('\n'.join(L))
# ------------------------------------------------------------------ 4. the controls
app = App(NEW)
class NB(Builder):
    def grouped(self, tp): return set()
b = NB(app, S)
BLUE, GREY, RED, GREEN = 'RGBA(56, 96, 178, 1)', 'RGBA(96, 104, 120, 1)', 'RGBA(193, 40, 40, 1)', 'RGBA(22, 128, 80, 1)'
HP, RS, HL = 'HomePrintScreen', 'RequesDetailScreen', 'HelpScreen'
step = lambda *n: ' Or '.join(f'locImpStep = {i}' for i in n)
b.clone('ImpTopBar', HP, 'HP_TopBar', {'X': '0', 'Y': '0', 'Width': '1366', 'Height': '56'})
b.clone('ImpHeading', HP, 'HP_SubTitle', {'Text': '"📥  Import a metadata form"', 'X': '32', 'Y': '10', 'Width': '600', 'Height': '36', 'Color': 'RGBA(255, 255, 255, 1)', 'Size': '16', 'FontWeight': 'FontWeight.Semibold'})
b.clone('ImpBtnBack', HP, 'HP_BtnBack', {'Text': '"←  Back"', 'X': '32', 'Y': '68', 'Width': '100', 'Height': '40',
        'OnSelect': 'If(varUserRole = "ADMINISTRATOR", Navigate(\'Dashboard-Ope-Administrator\'), Navigate(\'Dashboard-Ope-Requestor\'))'})
b.clone('ImpCard', HL, 'HL_Card', {'X': '148', 'Y': '120', 'Width': '1070', 'Height': '570'})
b.clone('ImpStepTitle', RS, 'RS_LblTitle', {'Text': 'Switch(locImpStep, 1, "1   Who is the requestor?", 2, "2   Attach the filled Word form", 3, "3   Reading the form…", 4, "4   Check what was read", 5, "5   Creating the draft…", 6, "6   Draft created", "The import did not finish")',
        'X': '188', 'Y': '144', 'Width': '900', 'Height': '34', 'Size': '20', 'Color': 'RGBA(0, 18, 107, 1)', 'Visible': 'true'})
ITEM = ("{\n        RequestNumber: Right(Text(Year(Today())), 2) & \"-\" & Text(%s, \"0000\"),\n        RequestTitle: \"Import in progress\",\n        DG: {Value: ImpDG.Selected.Value},\n        MediaType_Request: {Value: \"Photo\"},\n"
        "        ArchivedOnly: false,\n        Status: {Value: \"Draft\"},\n        ImportStatus: \"New\",\n        ImportRequestorEmail: Lower(Trim(ImpEmail.Text)),\n        ImportDG: ImpDG.Selected.Value,\n        ImportedBy: Lower(User().Email)\n    }")
NEXT_SEL = ('// the request number is reserved now (same rule as the app), so the staging request is the draft itself\n'
            'With(\n    {\n        yr4: Text(Year(Today())),\n        yr2: Right(Text(Year(Today())), 2),\n        lastNum: Coalesce(First(Sort(\'AV-CD-Requests\', ID, SortOrder.Descending)).RequestNumber, "")\n    },\n'
            '    With(\n        {n0: If(Left(lastNum, 3) = yr2 & "-", Value(Mid(lastNum, 4, 10)), If(Left(lastNum, 5) = yr4 & "-", Value(Right(lastNum, 4)), 0)) + 1},\n'
            '        IfError(\n            Set(varImpItem, IfError(\n                Patch(\'AV-CD-Requests\', Defaults(\'AV-CD-Requests\'), ' + ITEM % 'n0' + '),\n'
            '                IfError(\n                    Patch(\'AV-CD-Requests\', Defaults(\'AV-CD-Requests\'), ' + ITEM % 'n0 + 1' + '),\n'
            '                    Patch(\'AV-CD-Requests\', Defaults(\'AV-CD-Requests\'), ' + ITEM % 'n0 + 2' + ')\n                )\n            ));\n'
            '            UpdateContext({locImpStep: 2}),\n            Notify("Could not start the import: " & FirstError.Message, NotificationType.Error)\n        )\n    )\n)')
# ---- step 1
b.clone('ImpLblEmail', RS, 'RS_LblTitle', {'Text': '"Requestor e-mail *"', 'X': '188', 'Y': '210', 'Width': '420', 'Visible': step(1)})
b.clone('ImpEmail', HP, 'HP_TxtTitle', {'Default': 'If(varUserRole = "ADMINISTRATOR", "", Lower(User().Email))', 'HintText': '"name.surname@ec.europa.eu"', 'X': '188', 'Y': '236', 'Width': '520', 'Height': '44', 'Size': '13',
        'DisplayMode': 'If(varUserRole = "ADMINISTRATOR", DisplayMode.Edit, DisplayMode.View)', 'Visible': step(1),
        'OnChange': 'UpdateContext({locImpName: Coalesce(LookUp(Office365Users.SearchUserV2({searchTerm: Trim(ImpEmail.Text), top: 5}).value, Lower(Mail) = Lower(Trim(ImpEmail.Text))).DisplayName, "")})'})
b.clone('ImpEmailHint', RS, 'RS_LblTitle', {'Text': 'If(varUserRole <> "ADMINISTRATOR", "✓ " & User().FullName, IsBlank(Trim(ImpEmail.Text)), "The requestor must be a person of the organisation: the draft is created for that person.", Not(IsBlank(locImpName)), "✓ " & locImpName, "⚠  This e-mail was not found in the directory. Check it.")',
        'Color': 'If(varUserRole <> "ADMINISTRATOR" Or Not(IsBlank(locImpName)), RGBA(22, 128, 80, 1), If(IsBlank(Trim(ImpEmail.Text)), RGBA(96, 104, 120, 1), RGBA(193, 40, 40, 1)))',
        'X': '188', 'Y': '284', 'Width': '640', 'Height': '24', 'FontWeight': 'FontWeight.Normal', 'Size': '12', 'Visible': step(1)})
b.clone('ImpLblDG', RS, 'RS_LblTitle', {'Text': '"DG / Agency *"', 'X': '760', 'Y': '210', 'Width': '380', 'Visible': step(1)})
dgi = app.rule(RS, 'HomeFilterDG', 'Items')
b.clone('ImpDG', RS, 'HomeFilterDG', {'Items': dgi, 'Default': 'Blank()', 'OnChange': 'false', 'AllowEmptySelection': 'true', 'X': '760', 'Y': '236', 'Width': '380', 'Height': '44', 'Visible': step(1), 'DisplayMode': 'DisplayMode.Edit',
        'BorderColor': 'If(IsBlank(ImpDG.Selected), RGBA(255, 204, 0, 1), RGBA(0, 18, 107, 1))', 'BorderThickness': 'If(IsBlank(ImpDG.Selected), 3, 2)', 'Fill': 'RGBA(255, 255, 255, 1)'})
b.clone('ImpBtnNext', RS, 'RS_RequestorNotesSave', {'Text': '"Next: attach the form  ➤"', 'Tooltip': '"Choose the requestor and the DG first"', 'X': '188', 'Y': '340', 'Width': '280', 'Height': '48', 'Visible': step(1),
        'DisplayMode': 'If(IsBlank(ImpDG.Selected) Or IsBlank(Trim(ImpEmail.Text)) Or (varUserRole = "ADMINISTRATOR" And IsBlank(locImpName)), DisplayMode.Disabled, DisplayMode.Edit)',
        'OnSelect': NEXT_SEL})
# ---- step 2: the form with its attachments card (same pattern as the Legal screen)
b.clone('ImpForm', 'ChildLegalScreen', 'CL_FormAttach', {'DataSource': "'AV-CD-Requests'", 'DefaultMode': 'FormMode.Edit', 'Item': 'varImpItem', 'X': '188', 'Y': '200', 'Width': '640', 'Height': '300',
        'OnSuccess': ('IfError(\n    Patch(\'AV-CD-Requests\', LookUp(\'AV-CD-Requests\', ID = varImpItem.ID), {ImportStatus: "Uploaded"});\n    Set(varImpItem, LookUp(\'AV-CD-Requests\', ID = varImpItem.ID));\n'
                      '    UpdateContext({locImpStep: 3, locImpPoll: true}),\n    Notify("The file was uploaded but could not be released for reading: " & FirstError.Message, NotificationType.Error)\n)'),
        'OnFailure': 'Notify("The file could not be uploaded: " & ImpForm.Error, NotificationType.Error)'})
b.clone('ImpDCAttach', 'ChildLegalScreen', 'CL_DCAttach', {'Update': 'ImpDCAttachValue.Attachments', 'DisplayName': "DataSourceInfo([@'AV-CD-Requests'],DataSourceInfo.DisplayName,Attachments)", 'DisplayMode': 'Parent.DisplayMode', 'Width': 'Parent.Width', 'Height': '280'}, parent='ImpForm')
b.clone('ImpDCAttachStar', 'ChildLegalScreen', 'CL_DCAttachStar', {'Y': 'ImpDCAttachKey.Y', 'Height': 'ImpDCAttachKey.Height'}, parent='ImpDCAttach')
b.clone('ImpDCAttachKey', 'ChildLegalScreen', 'CL_DCAttachKey', {'Text': '"Word form (.docx) *"'}, parent='ImpDCAttach')
b.clone('ImpDCAttachValue', 'ChildLegalScreen', 'CL_DCAttachValue',
        {'BorderColor': 'If(Not(IsBlank(Parent.Error)), Color.Red, CountRows(ImpDCAttachValue.Attachments) = 0, RGBA(255, 204, 0, 1), RGBA(0, 18, 107, 1))',
         'BorderThickness': 'If(CountRows(ImpDCAttachValue.Attachments) = 0, 3, 2)', 'Height': '200'}, parent='ImpDCAttach')
b.clone('ImpDCAttachError', 'ChildLegalScreen', 'CL_DCAttachError', {'Y': 'ImpDCAttachValue.Y + ImpDCAttachValue.Height'}, parent='ImpDCAttach')
b.clone('ImpLblFormHint', RS, 'RS_LblTitle', {'Text': '"Attach the Word form exactly as it was filled in (one file). Photo, video and podcast forms are recognised automatically. Other file types are not accepted."',
        'X': '860', 'Y': '210', 'Width': '300', 'Height': '110', 'FontWeight': 'FontWeight.Normal', 'Size': '12', 'Color': 'RGBA(96, 104, 120, 1)', 'Visible': step(2)})
b.clone('ImpBtnRead', RS, 'RS_RequestorNotesSave', {'Text': '"Read the form  ➤"', 'X': '188', 'Y': '520', 'Width': '280', 'Height': '48', 'Visible': step(2),
        'Tooltip': 'If(CountRows(ImpDCAttachValue.Attachments) <> 1, "Attach exactly one .docx file", "")',
        'DisplayMode': 'If(CountRows(ImpDCAttachValue.Attachments) = 1 And EndsWith(Lower(First(ImpDCAttachValue.Attachments).Name), ".docx"), DisplayMode.Edit, DisplayMode.Disabled)',
        'OnSelect': 'SubmitForm(ImpForm)'})
# ---- steps 3 and 5: waiting
b.clone('ImpWaitLbl', RS, 'RS_LblTitle', {'Text': 'If(locImpStep = 3, "⏳  Reading the form… this takes a few seconds. You can stay on this page.", "⏳  Creating the draft request and sending the link… this takes a few seconds.")',
        'X': '188', 'Y': '230', 'Width': '900', 'Height': '30', 'FontWeight': 'FontWeight.Normal', 'Size': '15', 'Color': 'RGBA(60, 66, 80, 1)', 'Visible': step(3, 5)})
b.clone('ImpTimer', RS, 'Timer1', {'Duration': '3000', 'Repeat': 'true', 'AutoStart': 'false', 'Visible': 'false', 'X': '60', 'Y': '60',
        'OnTimerEnd': ('Refresh(\'AV-CD-Requests\');\nSet(varImpItem, LookUp(\'AV-CD-Requests\', ID = varImpItem.ID));\nSwitch(\n    varImpItem.ImportStatus,\n'
                       '    "Parsed", UpdateContext({locImpStep: 4, locImpPoll: false}),\n    "Done", UpdateContext({locImpStep: 6, locImpPoll: false}),\n    "Error", UpdateContext({locImpStep: 7, locImpPoll: false})\n)')})
# ---- step 4: what was read
b.clone('ImpWho', RS, 'RS_LblTitle', {'Text': '"Requestor: " & varImpItem.ImportRequestorEmail & "     ·     DG / Agency: " & varImpItem.ImportDG', 'X': '188', 'Y': '186', 'Width': '960', 'Height': '24',
        'FontWeight': 'FontWeight.Semibold', 'Size': '13', 'Color': 'RGBA(0, 18, 107, 1)', 'Visible': step(4)})
PREV = ('Concat(\n    Split(varImpItem.ImportPreview, Char(10)),\n    IfError(\n        With(\n            {k: Left(Result, Find("|", Result) - 1), v: Trim(Mid(Result, Find("|", Result) + 1))},\n'
        '            // an empty answer is only worth a warning when the draft needs it; the other empty rows are not listed\n'
        '            If(\n                IsBlank(v) And Not(k in ["Request title", "Request description", "Media title", "Capture / shooting / filming date", "Production place", "Contract case"]),\n                "",\n'
        '                k & "   →   " & If(IsBlank(v), "⚠  (empty)", v) & Char(10)\n            )\n        ),\n        ""\n    )\n)')
b.clone('ImpPreviewBox', RS, 'RS_Description', {'Default': PREV, 'HintText': '""', 'X': '188', 'Y': '214', 'Width': '960', 'Height': '300', 'DisplayMode': 'DisplayMode.View', 'Visible': step(4), 'Size': '12', 'OnChange': 'false',
        'Fill': 'RGBA(244, 245, 248, 1)', 'BorderColor': 'RGBA(220, 224, 230, 1)'})
b.clone('ImpWarn', RS, 'RS_LblTitle', {'Text': '"⚠  " & varImpItem.ImportMessage', 'X': '188', 'Y': '518', 'Width': '960', 'Height': '40', 'FontWeight': 'FontWeight.Semibold', 'Size': '12', 'Color': 'RGBA(193, 40, 40, 1)',
        'Visible': '(' + step(4) + ') And Not(IsBlank(Trim(varImpItem.ImportMessage)))'})
b.clone('ImpInfo', RS, 'RS_LblTitle', {'Text': '"Check the data. If something is wrong, correct the Word form and start again. Language and type of product are chosen in the request. The draft is created for the requestor, who receives an e-mail with the link."',
        'X': '188', 'Y': '548', 'Width': '960', 'Height': '36', 'FontWeight': 'FontWeight.Normal', 'Size': '11', 'Color': 'RGBA(96, 104, 120, 1)', 'Visible': step(4)})
b.clone('ImpBtnConfirm', RS, 'RS_RequestorNotesSave', {'Text': '"✓  Confirm and create the draft"', 'X': '188', 'Y': '598', 'Width': '320', 'Height': '48', 'Visible': step(4), 'Tooltip': '"Creates the draft request and e-mails the requestor"',
        'DisplayMode': 'DisplayMode.Edit',
        'OnSelect': ('IfError(\n    Patch(\'AV-CD-Requests\', LookUp(\'AV-CD-Requests\', ID = varImpItem.ID), {ImportStatus: "Confirmed"});\n    UpdateContext({locImpStep: 5, locImpPoll: true}),\n'
                     '    Notify("Could not confirm: " & FirstError.Message, NotificationType.Error)\n)')})
# ---- steps 6 and 7
b.clone('ImpDoneLbl', RS, 'RS_LblTitle', {'Text': '"✓  Draft request " & Coalesce(varImpItem.RequestNumber, "") & " was created for " & varImpItem.ImportRequestorEmail & ", who received an e-mail with the link."',
        'X': '188', 'Y': '210', 'Width': '960', 'Height': '60', 'FontWeight': 'FontWeight.Normal', 'Size': '15', 'Color': 'RGBA(22, 128, 80, 1)', 'Visible': step(6)})
b.clone('ImpBtnOpen', RS, 'RS_RequestorNotesSave', {'Text': '"Open the draft  ➤"', 'X': '188', 'Y': '300', 'Width': '280', 'Height': '48', 'Visible': step(6), 'DisplayMode': 'DisplayMode.Edit',
        'OnSelect': ('With(\n    {req: LookUp(\'AV-CD-Requests\', ID = varImpItem.ID)},\n    Set(varViewOnly, varUserRole = "ADMINISTRATOR" And Lower(Coalesce(req.\'Created By\'.Email, "")) <> Lower(User().Email));\n'
                     '    Set(varCurrentRequest, req);\n    Set(varRequestTitle1, Coalesce(req.RequestTitle, ""));\n    Set(varRequestTitle, Coalesce(req.RequestTitle, ""));\n    Set(varRequestDG, Coalesce(req.DG.Value, ""));\n'
                     '    Set(varRequestDescription1, Coalesce(req.Description, ""));\n    Set(varRequestDescription, Coalesce(req.Description, ""));\n    Set(varRequestOwnerContact, Coalesce(First(req.DG_Agency_Contact).DisplayName, ""));\n'
                     '    Set(varRequestMediaType, "");\n    Navigate(RequesDetailScreen, ScreenTransition.Cover, {locShowTypePicker: false, locResetContacts: true, locFromReview: false})\n)')})
b.clone('ImpErrLbl', RS, 'RS_LblTitle', {'Text': '"⛔  " & Coalesce(varImpItem.ImportMessage, "Something went wrong.") & Char(10) & "The support mailbox was told. Nothing was created."', 'X': '188', 'Y': '210', 'Width': '960', 'Height': '110',
        'FontWeight': 'FontWeight.Normal', 'Size': '13', 'Color': 'RGBA(193, 40, 40, 1)', 'Visible': step(7)})
b.clone('ImpBtnAgain', HP, 'HP_BtnClear', {'Text': 'If(locImpStep = 6, "Import another form", "↺  Start again")', 'X': '540', 'Y': '598', 'Width': '220', 'Height': '48', 'Size': '13', 'Visible': step(4, 6, 7),
        'OnSelect': '// a staging request that was not finished is removed (the number it reserved is simply skipped)\nIf(\n    Coalesce(varImpItem.ID, 0) > 0 And varImpItem.ImportStatus <> "Done",\n    IfError(Remove(\'AV-CD-Requests\', LookUp(\'AV-CD-Requests\', ID = varImpItem.ID)), Blank())\n);\nUpdateContext({locImpStep: 1, locImpPoll: false, locImpName: "", locImpErr: ""});\nSet(varImpItem, Blank());\nReset(ImpEmail);\nReset(ImpDG)'})
b.save()
# the order of the children is the order of creation: ZIndex follows it (the card stays under the controls)
doc = app.doc(S); tp = doc['TopParent']
for i, c in enumerate(tp['Children'], 1):
    for r in c['Rules']:
        if r['Property'] == 'ZIndex': r['InvariantScript'] = str(i)
    for e in c.get('ControlPropertyState', []):
        if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString') is not None: e['AutoRuleBindingString'] = str(i)
jwrite(doc, app.map[S])
# the timer starts when the screen is waiting
app = App(NEW)
c = find(app.doc(S)['TopParent'], 'ImpTimer')
c['Rules'].append({'Property': 'Start', 'Category': 'Behavior', 'InvariantScript': 'locImpPoll', 'RuleProviderType': 'Unknown'}); c.setdefault('ControlPropertyState', []).append('Start')
app.set(S, 'ImpTimer', 'Start', 'locImpPoll')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL115 built')
