#!/usr/bin/env python3
"""FINAL185 = R1 of the Requestor feedback of 2026-11-04, on TEST_19 (all the user's edits kept).
FB-01 Back button on the request screen; FB-04 taller Description (Info tab); FB-05 FTP path mandatory (all types); FB-06 language 'Multilingual / Other languages (INT)';
FB-07 Production end date optional; FB-08 'Producer (DG/Agency)' wording; FB-11 model-release wording by production type."""
import datetime, json, os, re, shutil
from payaml import App, find
from hp_common import Builder
SRC, NEW = 'newT19', 'newV47'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def sub(t, old, new, n=1):
    assert t.count(old) == n, (old[:70], t.count(old))
    return t.replace(old, new)

I, M, L, V, R = 'ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen', 'RequesDetailScreen'

# ---- FB-05 FTP mandatory: label, border
t = app.rule(I, 'CI_LblFTPPath', 'Text')
app.set(I, 'CI_LblFTPPath', 'Text', sub(t, '("FTP delivery path (optional)")', '("FTP delivery path *")'), expect=t)
t = app.rule(I, 'CI_FTPPath', 'BorderColor'); assert t == 'RGBA(0, 18, 107, 1)'
app.set(I, 'CI_FTPPath', 'BorderColor', 'If(varRequestorLocked, RGBA(0, 18, 107, 1),\n// yellow while this mandatory field is empty\nIf(IsBlank(Trim(CI_FTPPath.Text)), RGBA(255, 204, 0, 1), RGBA(0, 18, 107, 1))\n)', expect=t)
t = app.rule(I, 'CI_FTPPath', 'BorderThickness'); assert t == '2'
app.set(I, 'CI_FTPPath', 'BorderThickness', 'If(varRequestorLocked, 2, If(IsBlank(Trim(CI_FTPPath.Text)), 3, 2))', expect=t)

# ---- FB-04 taller description: Info tab
SHIFT = 'If(varChildMediaType = "Podcast", 44, 56)'
tp = app.doc(I)['TopParent']
gal = find(tp, 'CI_Gallery')
EXCL = {'CI_BtnOpenAttach', 'CI_BtnViewVisual', 'CI_HintPodcastVisual', 'CI_LblPodcastVisual', 'CI_Card', 'CI_SectionHeader'}
moved = []
for c in gal['Children']:
    nm = c['Name']; tn = c['Template']['Name'] if isinstance(c.get('Template'), dict) else c.get('Template')
    if nm in EXCL or tn not in ('label', 'text', 'datepicker', 'dropdown', 'button', 'combobox', 'rectangle'):
        continue
    rules = {r['Property']: r['InvariantScript'] for r in c['Rules']}
    y = rules.get('Y'); vis = rules.get('Visible', 'true').strip()
    if y is None or vis == 'false':
        continue
    ys = y.replace('\r\n', '\n').strip()
    m = re.match(r'^(\d+)', ys)
    if nm in ('CI_LblFTPPath', 'CI_FTPPath') or (m and int(m.group(1)) >= 255):
        app.set(I, nm, 'Y', f'({ys}) + {SHIFT}', expect=y)
        moved.append(nm)
print('shifted', len(moved), moved)
assert {'CI_LblNotes', 'CI_Notes', 'CI_LblFTPPath', 'CI_FTPPath', 'CI_LblLanguage', 'CI_Language', 'CI_BelugaRef', 'CI_BtnBelugaSave'} <= set(moved)
for ctl, old, new in (('CI_Description', '64', '120'), ('CI_PodcastDesc', '86', '130'), ('CI_Card', '780', '840')):
    t = app.rule(I, ctl, 'Height'); assert t.strip() == old, (ctl, t)
    app.set(I, ctl, 'Height', new, expect=t)
t = app.rule(I, 'CI_Gallery', 'TemplateSize')
app.set(I, 'CI_Gallery', 'TemplateSize', sub(t, 'If(varChildMediaType = "Photo", 540, If(varChildMediaType = "Video", 680, If(varChildMediaType = "Podcast", 750, 916)))',
        'If(varChildMediaType = "Photo", 596, If(varChildMediaType = "Video", 736, If(varChildMediaType = "Podcast", 794, 972)))'), expect=t)

# ---- FB-06 language INT
LANG_OLD = '"GA", "Other"]'
LANG_NEW = '"GA", "Multilingual / Other languages (INT)", "Other"]'
for sc, ctl in ((I, 'CI_Language'), (M, 'CM_Language')):
    t = app.rule(sc, ctl, 'Items'); app.set(sc, ctl, 'Items', sub(t, LANG_OLD, LANG_NEW), expect=t)

# ---- FB-07 production end date optional (Metadata tab)
t = app.rule(M, 'CM_LblProdEnd', 'Text'); assert t == '"Production end date *"'
app.set(M, 'CM_LblProdEnd', 'Text', '"Production end date"', expect=t)
t = app.rule(M, 'CM_ProdEnd', 'BorderColor')
app.set(M, 'CM_ProdEnd', 'BorderColor', 'RGBA(0, 18, 107, 1)', expect=t)
t = app.rule(M, 'CM_ProdEnd', 'BorderThickness')
app.set(M, 'CM_ProdEnd', 'BorderThickness', '2', expect=t)

# ---- FB-08 'Producer (DG/Agency)' wording
t = app.rule(M, 'CM_LblAuthority', 'Text'); app.set(M, 'CM_LblAuthority', 'Text', sub(t, '("Contracting authority *")', '("Producer (DG/Agency) *")'), expect=t)
t = app.rule(M, 'CM_Authority', 'HintText'); app.set(M, 'CM_Authority', 'HintText', sub(t, '"Contracting authority"', '"Producer (DG/Agency)"'), expect=t)
t = app.rule(M, 'CM_LblProducer', 'Text'); assert t == '"Producer *"'
app.set(M, 'CM_LblProducer', 'Text', '"Producer (DG/Agency) *"', expect=t)
t = app.rule('PrintPhotoDetailScreen', 'PPD_Lbl6', 'Text'); assert t == '"Contracting authority"'
app.set('PrintPhotoDetailScreen', 'PPD_Lbl6', 'Text', '"Producer (DG/Agency)"', expect=t)

# ---- FB-11 model release wording by production type (declaration unchanged, the 'provided' box names the forms)
t = app.rule(L, 'CL_ChkModelProvided', 'Text'); assert t == '"  ↳  Model release form(s) provided (attach on the right)"'
app.set(L, 'CL_ChkModelProvided', 'Text',
        '"  ↳  " & Switch(varChildMediaType, "Video", "Signed model release forms for filmed private persons (if recognisable)", "Podcast", "Signed model release forms for voice-recorded private persons", "Signed model release forms for photographed private persons (if recognisable)") & " (attach on the right)"', expect=t)

# ---- Validations (OnVisible of the screen and the Re-check button hold the same list)
def fix_checks(t):
    t = sub(t, '{Check: "Contracting authority provided (Photo only)"', '{Check: "Producer (DG/Agency) provided (Photo only)"')
    t = sub(t, 'Note: "Enter the contracting authority on the Metadata tab."', 'Note: "Enter the producer (DG/Agency) on the Metadata tab."')
    t = sub(t, 'Note: "Select the producer (contracting authority) on the Metadata tab."', 'Note: "Select the producer (DG/Agency) on the Metadata tab."')
    t = sub(t, '{Check: "Producer selected (Video / Podcast)"', '{Check: "Producer (DG/Agency) selected (Video / Podcast)"')
    t, n = re.subn(r'\s*\{Check: "Production end date set \(Video / Podcast\)",\s*Pass: [^\n]*?\s*Note: "Set the production end date on the Metadata tab\."\},', '', t, flags=re.S)
    assert n == 1, n
    old = '{Check: "FTP delivery path (optional)", Pass: true, Note: "Optional: enter the FTP path on the Info tab if the files are delivered by FTP."}'
    new = '{Check: "FTP delivery path provided", Pass: Not(IsBlank(Trim(Coalesce(varChildFTPPath1, "")))), Note: "Paste the FTP link of the media file in the FTP delivery path on the Info tab."}'
    return sub(t, old, new)
t = app.rule(V, None, 'OnVisible'); app.set(V, None, 'OnVisible', fix_checks(t), expect=t)
t = app.rule(V, 'CV_BtnRefresh', 'OnSelect'); app.set(V, 'CV_BtnRefresh', 'OnSelect', fix_checks(t), expect=t)
t = app.rule(V, 'CV_BtnSaveArchive', 'OnSelect')
app.set(V, 'CV_BtnSaveArchive', 'OnSelect', sub(t, '{n: "contracting authority",', '{n: "producer (DG/Agency)",'), expect=t)

# ---- FB-01 back button on the request screen
b = Builder(app, R)
b.clone('RS_BtnBackToList', M, 'CM_BtnPrev', {
    'Text': '"←  Back to Request Management"',
    'OnSelect': 'If(\n    locShowTypePicker,\n    Notify("Select a production type to continue.", NotificationType.Warning),\n    Navigate(RequestManagementScreen)\n)',
    'X': '32', 'Y': '719', 'Width': '300', 'Height': '43'})
b.save()

app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL185 built')
