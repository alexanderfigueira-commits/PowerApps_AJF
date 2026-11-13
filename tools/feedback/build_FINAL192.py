#!/usr/bin/env python3
"""FINAL192 on TEST_20 (the user's base, which already carries FINAL185-191).
A. Photo reportage: typed 'Number of photos' on the Metadata tab (Photo only), new SharePoint Number column NumberOfPhotos
   on AV-CD-Mediafiles, shown in the media list of the request (second line under the title).
B. Validations tab: a failed row is clickable and opens the tab that holds the field (Info / Metadata / Legal & Docs / Request)."""
import copy, datetime, json, os, re, shutil
from payaml import App, find, _fmt
from hp_common import Builder
SRC, NEW = 'newT20', 'newV54'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
COL, VAR = 'NumberOfPhotos', 'varChildNumberOfPhotos'
# ---------- schema: clone the numeric column SeasonNumber (field_7)
dp = f'{NEW}/References/DataSources.json'
raw = open(dp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); txt = raw.decode('utf-8-sig')
d = json.loads(txt)
ds = [x for x in d['DataSources'] if x.get('Name') == 'AV-CD-Mediafiles'][0]
key, meta = next(iter(ds['DataEntityMetadataJson'].items()))
m = json.loads(meta); props = m['schema']['items']['properties']
assert COL not in props
p = json.loads(json.dumps(props['field_7'])); p['title'] = COL; props[COL] = p
fmt = m['schema']['items']['x-ms-displayFormat']
for lst in ('propertiesDisplayOrder', 'propertiesCompactDisplayOrder', 'propertiesTabularDisplayOrder'):
    L = fmt[lst]; at = L.index('{Attachments}') if '{Attachments}' in L else len(L); L[at:at] = [COL]
ds['DataEntityMetadataJson'][key] = json.dumps(m, separators=(',', ':'), ensure_ascii=False)
ds['ConnectedDataSourceInfoNameMapping'][COL] = COL
indent = 2 if '\n  "' in txt else None
out = json.dumps(d, ensure_ascii=False, indent=indent, separators=(',', ': ') if indent else (',', ':'))
if '\r\n' in txt: out = out.replace('\n', '\r\n')
open(dp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out)

app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def sub(t, old, new, n=1):
    assert t.count(old) == n, (old[:60], t.count(old)); return t.replace(old, new)
def rsub(t, pat, rep, n=1):
    new, k = re.subn(pat, rep, t); assert k == n, (pat, k); return new
def edit(screen, ctl, prop, fn):
    t = app.rule(screen, ctl, prop); n = fn(t); assert n != t, (screen, ctl, prop)
    app.set(screen, ctl, prop, n, expect=t)
CI, CM, CL, CV, RS = 'ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen', 'RequesDetailScreen'
# ---------- A1. variable: reset / load / open / template / save
A, B = 'Set(varChildSeasonNumber, 0);', f'Set(varChildSeasonNumber, 0); Set({VAR}, 0);'
doc = app.doc('App'); rl = [r for r in doc['TopParent']['Rules'] if r['Property'] == 'OnStart'][0]
rl['InvariantScript'] = sub(rl['InvariantScript'], A, B)
yf = f'{NEW}/Src/App.pa.yaml'; y = open(yf, encoding='utf-8', newline='').read()
open(yf, 'w', encoding='utf-8', newline='').write(sub(y, A, B))
edit(RS, 'addMediaItem', 'OnSelect', lambda t: rsub(t, r'Set\(varChildSeasonNumber, 0\);', B))
edit(RS, 'DOA_List1RowBadge_8', 'OnSelect', lambda t: sub(t, 'Set(varChildSeasonNumber, Coalesce(ThisItem.SeasonNumber, 0));',
     f'Set(varChildSeasonNumber, Coalesce(ThisItem.SeasonNumber, 0));\nSet({VAR}, Coalesce(ThisItem.{COL}, 0));'))
edit(RS, None, 'OnVisible', lambda t: rsub(t, r'(SeasonNumber: Coalesce\(\s*SeasonNumber,\s*0\s*\),)', r'\1\n                ' + f'{COL}: Coalesce({COL}, 0),'))
for c in ('CI_TplRowUse', 'CI_TplConfirmOK'):
    edit(CI, c, 'OnSelect', lambda t: rsub(t, r'([ \t]*)Set\(varChildSeasonNumber, Coalesce\(varTplCandidate\.SeasonNumber, 0\)\);',
         lambda mm: mm.group(0) + '\n' + mm.group(1) + f'Set({VAR}, Coalesce(varTplCandidate.{COL}, 0));'))
def save(t):
    t = sub(t, 'SeasonNumber: varChildSeasonNumber,', f'SeasonNumber: varChildSeasonNumber,\n                          {COL}: {VAR},', 2)
    a = '{n: "season number", bad: Coalesce(varChildSeasonNumber, 0) > 0 And Coalesce(chk.SeasonNumber, 0) = 0},'
    return sub(t, a, a + f'\n                                {{n: "number of photos", bad: Coalesce({VAR}, 0) > 0 And Coalesce(chk.{COL}, 0) = 0}},')
edit(CV, 'CV_BtnSaveArchive', 'OnSelect', save)
# ---------- A2. Metadata tab (Photo): label + numeric box, in the free slot right of "Place"
b = Builder(app, CM)
b.clone('CM_LblNumPhotos', CM, 'CM_LblPlacePhoto', {'Text': '"Number of photos"', 'X': '367', 'Y': '308', 'Width': '295',
        'Visible': 'varChildMediaType = "Photo"'}, parent='CM_Gallery')
b.clone('CM_NumPhotos', CM, 'CM_PlacePhoto', {
    'X': '367', 'Y': '334', 'Width': '295', 'Visible': 'varChildMediaType = "Photo"',
    'Default': f'// empty (showing the hint) until a number above 0 is stored\nIf(Coalesce({VAR}, 0) > 0, Text({VAR}), "")',
    'OnChange': f'Set({VAR}, Coalesce(IfError(Value(Self.Text), 0), 0))',
    'HintText': '"How many photos are in this reportage (e.g. 25)"', 'Format': 'TextFormat.Number', 'MaxLength': '5',
    'AccessibleLabel': 'CM_LblNumPhotos.Text', 'Tooltip': '"Optional: the number of photos delivered with this reportage"',
    'BorderColor': 'RGBA(0, 18, 107, 1)', 'BorderThickness': '2'}, parent='CM_Gallery')
b.save()
# ---------- A3. media list of the request: second line under the title
b = Builder(app, RS)
SHOW = f'ThisItem.MediaType = "Photo" And Coalesce(ThisItem.{COL}, 0) > 0'
b.clone('RS_CRowPhotos', RS, 'RS_CRowTitle', {
    'X': '151', 'Y': '30', 'Width': '391', 'Height': '22', 'Size': '10', 'PaddingTop': '0', 'Color': 'RGBA(96, 104, 120, 1)',
    'Text': f'"📷 " & Text(ThisItem.{COL}) & If(ThisItem.{COL} = 1, " photo", " photos")', 'Visible': SHOW, 'Tooltip': '"Number of photos in this reportage"'},
    parent='RS_ChildrenGallery')
b.save()
edit(RS, 'RS_CRowTitle', 'Y', lambda t: sub(t, '9', f'If({SHOW}, 4, 9)'))
edit(RS, 'RS_CRowTitle', 'Height', lambda t: sub(t, '47', f'If({SHOW}, 28, 47)'))
# ---------- B. Validations: a failed row opens the tab that holds the field
docs = {s: app.doc(s)['TopParent'] for s in (CI, CM)}
def walk(n):
    yield n
    for c in n.get('Children', []): yield from walk(c)
ai_screen = CI
for s, tp in docs.items():
    for n in walk(tp):
        for r in n['Rules']:
            if r['Property'] in ('OnCheck', 'OnChange', 'OnSelect', 'OnUncheck') and 'varChildAIVoiceover' in r['InvariantScript'] and 'Tpl' not in n['Name']:
                ai_screen = s
print('AI voice-over input is on', ai_screen)
GO = f'''// a failed check opens the tab that holds the field (passed rows do nothing)
If(
    Not(ThisItem.Pass),
    With(
        {{c: ThisItem.Check, n: ThisItem.Note}},
        If(
            "Request screen" in n, Navigate(RequesDetailScreen, ScreenTransition.None, {{locShowTypePicker: false, locResetContacts: false}}),
            "Legal & Docs" in n Or "SRT" in c Or "VTT" in c Or StartsWith(c, "Contract case") Or StartsWith(c, "Case 1"), Navigate(ChildLegalScreen),
            // the shooting / filming / recording date sits on the Metadata tab for Photo, Video and Podcast
            StartsWith(c, "Capture"), If(varChildMediaType in ["Photo", "Video", "Podcast"], Navigate(ChildMetaScreen), Navigate(ChildInfoScreen)),
            StartsWith(c, "Language"), If(varChildMediaType = "Podcast", Navigate(ChildMetaScreen), Navigate(ChildInfoScreen)),
            StartsWith(c, "No AI"), Navigate({ai_screen}),
            "not earlier than" in c Or "Metadata tab" in n, Navigate(ChildMetaScreen),
            Navigate(ChildInfoScreen)
        )
    )
)'''
tp = app.doc(CV)['TopParent']; g = find(tp, 'CV_ChecklistGallery')
assert not [r for r in g['Rules'] if r['Property'] == 'OnSelect']
proto = [r for r in find(tp, 'CV_BtnRefresh')['Rules'] if r['Property'] == 'OnSelect'][0]
nr = copy.deepcopy(proto); nr['InvariantScript'] = GO; g['Rules'].append(nr)
yf = f'{NEW}/Src/{CV}.pa.yaml'; L = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
i0 = next(i for i, l in enumerate(L) if l == '      - CV_ChecklistGallery:')
j = next(i for i in range(i0, len(L)) if L[i].startswith('            LoadingSpinner:'))
L[j + 1:j + 1] = _fmt('OnSelect', GO, 12)
open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(L))
edit(CV, 'CV_RowBg', 'HoverFill', lambda t: 'If(ThisItem.Pass, Self.Fill, RGBA(254, 226, 226, 1))')
edit(CV, 'CV_RowNote', 'Width', lambda t: sub(t, '640', '540'))
bg = find(tp, 'CV_RowBg')
if [r for r in bg['Rules'] if r['Property'] == 'OnSelect']: edit(CV, 'CV_RowBg', 'OnSelect', lambda t: 'Select(Parent)')
b = Builder(app, CV)
b.clone('CV_RowFix', CV, 'CV_RowNote', {'X': '1196', 'Width': '96', 'Text': '"Fix  →"', 'Visible': 'Not(ThisItem.Pass)', 'Align': 'Align.Right',
        'Color': 'RGBA(56, 96, 178, 1)', 'FontWeight': 'FontWeight.Semibold', 'PaddingRight': '12',
        'Tooltip': '"Open the tab where this field is"'}, parent='CV_ChecklistGallery')
b.save()
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL192 built')
