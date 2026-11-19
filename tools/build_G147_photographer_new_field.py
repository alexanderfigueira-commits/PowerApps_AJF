#!/usr/bin/env python3
"""FINAL158 on FINAL157: the people picker CM_Photographer (ChildMetaScreen, inside CM_Gallery) is deleted and a NEW free-text box,
CM_PhotographerName, is created in exactly the same place (same parent, same position in the stack, X 678 / Y 104 / 295 x 40, Photo only,
label CM_LblPhotographer unchanged). Mandatory (yellow border while empty, validation row, spaces only do not count).
The text is saved in the SharePoint text column PhotographerName of AV-CD-Mediafiles (must exist, internal name PhotographerName);
the old person column Photographer is not written any more and old items still show the name they have there."""
import datetime, json, os, re, shutil
from payaml import App
from hp_common import Builder
from jio import jwrite
SRC, NEW = 'newV19', 'newV20'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

def edit(screen, control, prop, subs):
    t = app.rule(screen, control, prop); u = t
    for pat, new, cnt in subs:
        found = len(re.findall(pat, u, re.S))
        assert found == cnt, (screen, control, prop, pat, found)
        u = re.sub(pat, lambda m: new, u, flags=re.S)
    app.set(screen, control, prop, u, expect=t)

# ---- 2. photographer: free text ---------------------------------------------------------------------------------------
M = 'ChildMetaScreen'
BLANK = 'IsBlank(Trim(CM_PhotographerName.Text))'
b = Builder(app, M)
b.swap('CM_Photographer', M, 'CM_Authority', new_name='CM_PhotographerName', overrides={
    'Default': 'varChildPhotographer',
    'HintText': '"Type the photographer\'s name (free text: external photographers are welcome)"',
    'OnChange': 'Set(varChildPhotographer, Self.Text)',
    'X': '678',
    'BorderColor': f'If(varRequestorLocked, RGBA(0, 18, 107, 1),\n// yellow while this mandatory field is empty\nIf(CM_LblPhotographer.Visible And {BLANK}, RGBA(255, 204, 0, 1), RGBA(0, 18, 107, 1))\n)',
    'BorderThickness': f'If(varRequestorLocked, 2, If(CM_LblPhotographer.Visible And {BLANK}, 3, 2))'})
b.save()

C = 'ChildInfoScreen'
for ctl in ('CI_TplRowBg', 'CI_TplConfirmOK'):
    edit(C, ctl, 'OnSelect', [
        (r'Set\(varChildPhotographerSel, If\(IsEmpty\(varTplCandidate\.Photographer\), Blank\(\), ForAll\(varTplCandidate\.Photographer As p, \{DisplayName: p\.DisplayName, Mail: p\.Email\}\)\)\);\s*',
         'Set(varChildPhotographerSel, Blank());\n    ', 1),
        (r'Set\(varChildPhotographer, Concat\(varTplCandidate\.Photographer, DisplayName, ", "\)\);',
         'Set(varChildPhotographer, Coalesce(varTplCandidate.PhotographerName, Concat(varTplCandidate.Photographer, DisplayName, ", ")));', 1),
        (r'Reset\(CM_Photographer\);', 'Reset(CM_PhotographerName);', 1)])

D = 'RequesDetailScreen'
edit(D, None, 'OnVisible', [
    (r'Photographer: ForAll\(\s*Photographer As p,\s*\{\s*DisplayName: p\.DisplayName,\s*Mail: p\.Email\s*\}\s*\),',
     'Photographer: Coalesce(PhotographerName, Concat(Photographer, DisplayName, ", ")),', 1)])
edit(D, 'DOA_List1RowBadge_8', 'OnSelect', [
    (r'Set\(varChildPhotographerSel, ThisItem\.Photographer\);\s*Set\(varChildPhotographer, Concat\(ThisItem\.Photographer, DisplayName, ", "\)\);',
     'Set(varChildPhotographerSel, Blank());\n                    Set(varChildPhotographer, Coalesce(ThisItem.Photographer, ""));', 1)])

V = 'ChildValidScreen'
PASS_OLD = r'Pass: varChildMediaType <> "Photo" Or \(Not\(IsBlank\(varChildPhotographer\)\) And varChildPhotographer <> ""\)'
PASS_NEW = 'Pass: varChildMediaType <> "Photo" Or Not(IsBlank(Trim(Coalesce(varChildPhotographer, ""))))'
NOTE_OLD = r'Note: "Select the photographer on the Metadata tab\."'
NOTE_NEW = 'Note: "Type the name of the photographer on the Metadata tab."'
for ctl, prop in ((None, 'OnVisible'), ('CV_BtnRefresh', 'OnSelect')):
    edit(V, ctl, prop, [(PASS_OLD, PASS_NEW, 1), (NOTE_OLD, NOTE_NEW, 1)])
edit(V, 'CV_BtnSaveArchive', 'OnSelect', [
    (r'Producer: varChildProducerSel, Photographer: varChildPhotographerSel,', 'Producer: varChildProducerSel, Photographer: varChildPhotographer,', 1),
    (r'Photographer: If\(IsBlank\(varChildPhotographerSel\), Blank\(\), ForAll\(varChildPhotographerSel As u, \{[^{}]*\}\)\),',
     'PhotographerName: Trim(Coalesce(varChildPhotographer, "")),', 1)])

P = 'PrintPhotoDetailScreen'
PH = 'Trim(Coalesce(ThisItem.PhotographerName, Concat(ThisItem.Photographer, DisplayName, ", ")))'
t = app.rule(P, 'PPD_Val13', 'Text'); assert t == 'If(IsEmpty(ThisItem.Photographer), "Not provided", Concat(ThisItem.Photographer, DisplayName, ", "))'
app.set(P, 'PPD_Val13', 'Text', f'With({{p: {PH}}}, If(IsBlank(p), "Not provided", p))', expect=t)
t = app.rule(P, 'PPD_Val13', 'Color'); assert t == 'If(IsEmpty(ThisItem.Photographer), RGBA(150, 155, 165, 1), RGBA(30, 34, 44, 1))'
app.set(P, 'PPD_Val13', 'Color', f'With({{p: {PH}}}, If(IsBlank(p), RGBA(150, 155, 165, 1), RGBA(30, 34, 44, 1)))', expect=t)
app.save()

# ---- 3. data source: the new text column ----------------------------------------------------------------------------
path = f'{NEW}/References/DataSources.json'
ds = json.load(open(path, encoding='utf-8'))
hit = [x for x in ds['DataSources'] if x['Name'] == 'AV-CD-Mediafiles']; assert len(hit) == 1
x = hit[0]
assert 'PhotographerName' not in x['ConnectedDataSourceInfoNameMapping']
x['ConnectedDataSourceInfoNameMapping']['PhotographerName'] = 'PhotographerName'
(k, v), = x['DataEntityMetadataJson'].items()
j = json.loads(v)
j['schema']['items']['properties']['PhotographerName'] = {
    'title': 'PhotographerName', 'type': 'string', 'x-ms-permission': 'read-write', 'x-ms-sort': 'asc,desc',
    'x-ms-capabilities': {'filterFunctions': ['eq', 'startswith']}, 'maxLength': 255}
x['DataEntityMetadataJson'][k] = json.dumps(j, separators=(',', ':'), ensure_ascii=False)
jwrite(ds, path)

h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL158 built')
