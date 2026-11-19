#!/usr/bin/env python3
"""FINAL163 on FINAL162.
 A. Beluga reference (ChildInfoScreen, CI_LblBeluga / CI_BelugaRef):
    * an administrator can edit it whenever the request is not Draft / Pending (Processing, Rejected, Approved, Partially approved,
      Published), whoever created the request and from any entry (also the dashboards' view-only mode); in Draft / Pending it is read-only;
    * new button CI_BtnBelugaSave next to the field saves only this reference on the media item (no Save Media needed, no lock);
      the media list of the request screen is updated too;
    * a requestor never sees the field unless it is filled in, and then only to read it;
    * read-only = grey like the other read-only boxes.
 B. Assignee colours: AV-CD-RolesPermissionsList gets a choice column Colour (Red, Blue, Yellow, Purple, Green, Orange, Pink, Brown, Gray,
    Light Blue, Navy Blue, Gold, Bege). colAdminColours (e-mail -> colour) is loaded in App.OnStart, RequestManagementScreen and HomePrintScreen
    and the labels that show an assignee's name take that colour: HomeRowAssignee, HP_RowDate_1 and the Assignee value of the three print headers.
    The column is added to the app's data source description (References/DataSources.json) until Studio refreshes it."""
import datetime, json, os, re, shutil
from payaml import App, find
from hp_common import Builder
from jio import jwrite
SRC, NEW = 'newV24', 'newV25'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

# ===================================== A. Beluga =====================================================================
C = 'ChildInfoScreen'
STATUS = 'Coalesce(varCurrentRequest.Status.Value, "Draft")'
CAN = f'varUserRole = "ADMINISTRATOR" And Not({STATUS} in ["Draft", "Pending"])'
SEE = 'varUserRole = "ADMINISTRATOR" Or Not(IsBlank(Trim(Coalesce(varChildBelugaRef, ""))))'
def setp(ctl, prop, new, old=None):
    t = app.rule(C, ctl, prop)
    if old is not None: assert t == old, (ctl, prop, t)
    app.set(C, ctl, prop, new, expect=t)
setp('CI_LblBeluga', 'Visible', SEE, 'true')
setp('CI_BelugaRef', 'Visible', SEE, 'true')
setp('CI_BelugaRef', 'DisplayMode', f'If({CAN}, DisplayMode.Edit, DisplayMode.View)',
     'If(varViewOnly Or varRequestorLocked Or varUserRole <> "ADMINISTRATOR", DisplayMode.View, DisplayMode.Edit)')
setp('CI_BelugaRef', 'Fill', 'If(Self.DisplayMode = DisplayMode.View, RGBA(244, 245, 248, 1), RGBA(255, 255, 255, 1))', 'RGBA(255, 255, 255, 1)')
app.save()

SAVE = '''// saves only the Beluga reference of this media item: it does not depend on the request being open for editing
IfError(
    With(
        {id: Coalesce(varCurrentChildSPId, 0), ref: Trim(Coalesce(varChildBelugaRef, ""))},
        Patch('AV-CD-Mediafiles', LookUp('AV-CD-Mediafiles', ID = id), {BelugaReference: ref});
        // the media list of the request screen shows the new reference at once
        UpdateIf(colArchives, SPId = id, {BelugaReference: ref});
        Set(varChildBelugaRef, ref);
        Notify("Beluga reference saved: " & If(ref = "", "(empty)", ref), NotificationType.Success)
    ),
    Notify("The Beluga reference could not be saved: " & FirstError.Message, NotificationType.Error)
)'''
b = Builder(app, C)
b.clone('CI_BtnBelugaSave', 'ChildValidScreen', 'CV_BtnSaveArchive', {
    'Text': '"💾  Save reference"',
    'Tooltip': '"Saves only the Beluga reference of this media file"',
    'X': '464', 'Y': '480 + If(varChildMediaType = "Photo", 0, 90)', 'Width': '170', 'Height': '40', 'Size': '12',
    'Visible': CAN + ' And Coalesce(varCurrentChildSPId, 0) > 0',
    'DisplayMode': 'DisplayMode.Edit',
    'OnSelect': SAVE}, parent='CI_Gallery')
b.save()

# ===================================== B. colours ====================================================================
COLOURS = [('Red', '200, 30, 30'), ('Blue', '30, 100, 210'), ('Yellow', '204, 160, 0'), ('Purple', '122, 48, 160'), ('Green', '22, 140, 70'),
           ('Orange', '230, 120, 0'), ('Pink', '214, 51, 132'), ('Brown', '133, 77, 14'), ('Gray', '110, 118, 130'),
           ('Light Blue', '0, 160, 220'), ('Navy Blue', '0, 18, 107'), ('Gold', '184, 134, 11'), ('Bege', '176, 148, 104'), ('Beige', '176, 148, 104')]
SW = ',\n                '.join(f'"{n}", RGBA({c}, 1)' for n, c in COLOURS)
LOAD = f'''// one colour per administrator (roles list, column Colour): the assignee names are shown in it
ClearCollect(
    colAdminColours,
    ForAll(
        Filter('AV-CD-RolesPermissionsList', Role.Value = "ADMINISTRATOR"),
        {{
            Mail: Lower(UserEmail.Email),
            Color: Switch(
                Colour.Value,
                {SW},
                RGBA(96, 104, 120, 1)
            )
        }}
    )
)'''
def with_load(screen, ctl):
    t = app.rule(screen, ctl, 'OnVisible'); assert 'colAdminColours' not in t
    app.set(screen, ctl, 'OnVisible', t.rstrip().rstrip(';') + ';\n' + LOAD, expect=t)
with_load('RequestManagementScreen', None)
with_load('HomePrintScreen', None)
# App.OnStart: its YAML is shaped differently, JSON and YAML are written here
tp = app.doc('App')['TopParent']
r = [x for x in tp['Rules'] if x['Property'] == 'OnStart'][0]
assert r['InvariantScript'].rstrip().endswith('Set(currentIndex, 1);') and 'colAdminColours' not in r['InvariantScript']
r['InvariantScript'] = r['InvariantScript'].rstrip() + '\n' + LOAD
app.save()
yp = f'{NEW}/Src/App.pa.yaml'
Y = open(yp, encoding='utf-8', newline='').read().replace('\r\n', '\n').replace('\r', '\n').split('\n')
i = [k for k, l in enumerate(Y) if l == '      Set(currentIndex, 1);']; assert len(i) == 1
Y[i[0] + 1:i[0] + 1] = ['      ' + l if l else l for l in LOAD.split('\n')]
open(yp, 'w', encoding='utf-8', newline='').write('\n'.join(Y))

def colour_of(email, fallback):
    return f'Coalesce(LookUp(colAdminColours, Mail = Lower({email})).Color, {fallback})'
def setc(screen, ctl, email, old_colour):
    t = app.rule(screen, ctl, 'Color'); assert t == old_colour, (ctl, t)
    app.set(screen, ctl, 'Color', colour_of(email, old_colour), expect=t)
setc('RequestManagementScreen', 'HomeRowAssignee', 'ThisItem.Assignee.Email', 'RGBA(96, 104, 120, 1)')
setc('HomePrintScreen', 'HP_RowDate_1', 'ThisItem.Assignee.Email', 'RGBA(96, 104, 120, 1)')
for screen, P in (('PrintVideoDetailScreen', 'PVD'), ('PrintPhotoDetailScreen', 'PPD'), ('PrintPodcastDetailScreen', 'PPoD')):
    setc(screen, f'{P}_HdrVal6', 'varPrintRequest.Assignee.Email', 'RGBA(30, 34, 44, 1)')
app.save()

# data source description: the Colour choice column of the roles list
path = f'{NEW}/References/DataSources.json'
ds = json.load(open(path, encoding='utf-8'))
x = [d for d in ds['DataSources'] if d['Name'] == 'AV-CD-RolesPermissionsList'][0]
m = x['ConnectedDataSourceInfoNameMapping']
assert 'Colour' not in m
m['Colour'] = 'Colour'; m['Colour#Id'] = 'Colour Id'
(k, v), = x['DataEntityMetadataJson'].items()
j = json.loads(v); props = j['schema']['items']['properties']
role = props['Role']
props['Colour#Id'] = json.loads(json.dumps(props['Role#Id']))
col = json.loads(json.dumps(role)); col['title'] = 'Colour'
del col['properties']['Value']['default']; col['properties']['Value'].pop('x-ms-dynamic-values', None)
props['Colour'] = col
for key in ('propertiesDisplayOrder', 'propertiesCompactDisplayOrder', 'propertiesTabularDisplayOrder'):
    lst = j['schema']['items']['x-ms-displayFormat'][key]
    lst.insert(lst.index('UserEmail') + 1, 'Colour')
x['DataEntityMetadataJson'][k] = json.dumps(j, separators=(',', ':'), ensure_ascii=False)
jwrite(ds, path)

h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL163 built')
