#!/usr/bin/env python3
"""FINAL151 on FINAL150: a refresh icon on every gallery of the two operational dashboards
(Dashboard-Ope-Administrator: DOA_List1/2/3Refresh, Dashboard-Ope-Requestor: DOR_List1/2/3Refresh).
Each icon sits in its card header, left of the row counter, and reloads the data the three galleries share
(the same loads as the screen's OnVisible; the administrator's also re-reads AV-CD-Notes for the row tooltips).
The icon is disabled while the reload runs (locRefreshing)."""
import datetime, os, re, shutil
from payaml import App
from hp_common import Builder
SRC, NEW = 'newV10', 'newV11'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

ADMIN = '''UpdateContext({locRefreshing: true});
IfError(
    Refresh('AV-CD-Requests');
    Refresh('AV-CD-Notes');
    // every request except drafts, as on entering the screen
    ClearCollect(colOpeAll, 'AV-CD-Requests');
    ClearCollect(colOpeReqs, Filter(colOpeAll, Status.Value <> "Draft"));
    ClearCollect(colOpeMedia, 'AV-CD-Mediafiles');
    If(
        CountRows(colOpeAll) >= 2000,
        Notify("Only the first 2000 requests are loaded, so older ones may be missing.", NotificationType.Warning),
        Notify("Lists refreshed.", NotificationType.Success)
    ),
    Notify("Could not refresh the lists: " & FirstError.Message, NotificationType.Error)
);
UpdateContext({locRefreshing: false})'''
REQUESTOR = '''UpdateContext({locRefreshing: true});
IfError(
    Refresh('AV-CD-Requests');
    // the requestor's own requests and media items, as on entering the screen
    ClearCollect(colOpeReqs, Filter('AV-CD-Requests', 'Created By'.Email = User().Email));
    ClearCollect(colOpeMedia, Filter('AV-CD-Mediafiles', 'Created By'.Email = User().Email));
    Notify("Lists refreshed.", NotificationType.Success),
    Notify("Could not refresh the lists: " & FirstError.Message, NotificationType.Error)
);
UpdateContext({locRefreshing: false})'''

def counter_box(screen, counter):
    tp = app.doc(screen)['TopParent']
    n = [c for c in tp['Children'] if c['Name'] == counter][0]
    g = {r['Property']: r['InvariantScript'] for r in n['Rules']}
    return float(g['X']), float(g['Y']), float(g['Height'])

for screen, P, script in (('Dashboard-Ope-Administrator', 'DOA', ADMIN), ('Dashboard-Ope-Requestor', 'DOR', REQUESTOR)):
    b = Builder(app, screen)
    for i in (1, 2, 3):
        cx, cy, ch = counter_box(screen, f'{P}_List{i}CounterCircle')
        x, y = int(cx - 28), int(round(cy + ch / 2 - 10))
        b.clone(f'{P}_List{i}Refresh', screen, f'{P}_List{i}Info', {
            'Icon': 'Icon.Reload',
            'AccessibleLabel': '"Refresh the lists"',
            'Tooltip': '"Refresh the lists"',
            'Color': 'RGBA(56, 96, 178, 1)',
            'DisplayMode': 'If(locRefreshing, DisplayMode.Disabled, DisplayMode.Edit)',
            'Width': '20', 'Height': '20', 'X': str(x), 'Y': str(y),
            'OnSelect': script})
        print(P, i, 'X', x, 'Y', y)
    b.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL151 built')
