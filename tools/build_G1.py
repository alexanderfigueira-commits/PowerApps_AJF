#!/usr/bin/env python3
"""Checkbox "Archiving only, not publication" on RequesDetailScreen, on the user's FINAL10.

The user already placed a bare checkbox RS_Archive (no logic, hidden behind the request card) and
created the Yes/No column ArchivedOnly on AV-CD-Requests (it is in the app's schema). This wires it:

* RS_Archive: text "Archiving only, not publication", under RS_AICheck, shown with the card, above
  the card in stacking order, locked like RS_AICheck for a requestor whose request is in Processing;
  Default = varRequestArchivedOnly.
* saved with every full save of the request (first save when adding media, Save draft, Submit,
  Resubmit); ticking it on an already saved request stores it straight away (survives opening a
  media item and coming back);
* RequesDetailScreen.OnVisible reads it back from the request (a new request starts at No).
Nothing else is changed.
"""
import datetime, json, os, re, shutil, sys
from payaml import App, find

SRC, NEW = 'f10', 'newG1'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RS = 'RequesDetailScreen'
COL, VAR = 'ArchivedOnly', 'varRequestArchivedOnly'

# the column the user created must be in the app's schema, as Yes/No
ds = json.load(open(f'{NEW}/References/DataSources.json', encoding='utf-8'))
x = [x for x in ds['DataSources'] if x['Name'] == 'AV-CD-Requests'][0]
pr = json.loads(list(x['DataEntityMetadataJson'].values())[0])['schema']['items']['properties']
if pr.get(COL, {}).get('type') != 'boolean':
    sys.exit(f'! {COL} is not a Yes/No column of AV-CD-Requests in the app')


def put(s, n, p, v, cat='Design'):
    c = find(app.doc(s)['TopParent'], n)
    if not [r for r in c['Rules'] if r['Property'] == p]:
        c['Rules'].append({'Property': p, 'Category': cat, 'InvariantScript': v, 'RuleProviderType': 'Unknown'})
        c.setdefault('ControlPropertyState', []).append(p)
    app.set(s, n, p, v)


# ---------------------------------------------------------------- saved with the request
DESC = 'Description: varRequestDescription'
for ctl, n_exp in (('Add_media_icon', 3), ('RS_BtnDraftSave', 4), ('RS_BtnSubmitRequest', 1), ('RS_BtnResubmitRequest', 1)):
    t = app.rule(RS, ctl, 'OnSelect')
    patches = len(re.findall(r"Patch\(\s*'AV-CD-Requests'\s*,\s*(?:Defaults|LookUp)", t))
    hits = list(re.finditer(r'\n( *)' + re.escape(DESC), t))
    if len(hits) != patches or len(hits) != n_exp:
        sys.exit(f'! {ctl}: {len(hits)} "{DESC}" for {patches} request patches')
    n = t
    for m in reversed(hits):
        n = n[:m.start()] + f'\n{m.group(1)}{COL}: {VAR},' + n[m.start():]
    app.set(RS, ctl, 'OnSelect', n, expect=t)
t = app.rule(RS, None, 'OnVisible')
app.set(RS, None, 'OnVisible', t + f''';
// "Archiving only, not publication": an opened request shows what is saved, a new request starts at No
Set({VAR}, Coalesce(varCurrentRequest.{COL}, false))''', expect=t)
app.save()

# ---------------------------------------------------------------- the checkbox
ON = lambda v: (f'Set({VAR}, {v});\n'
                '// a saved request stores the answer straight away, so it survives opening a media item and coming back\n'
                'If(\n'
                f'    Coalesce(varCurrentRequest.ID, 0) > 0 And Coalesce(varCurrentRequest.{COL}, false) <> {v},\n'
                '    IfError(\n'
                f'        Set(varCurrentRequest, Patch(\'AV-CD-Requests\', LookUp(\'AV-CD-Requests\', ID = varCurrentRequest.ID), {{{COL}: {v}}})),\n'
                '        Notify("Could not save the answer: " & FirstError.Message, NotificationType.Error)\n'
                '    )\n'
                ')')


def rect(c):
    r = {x['Property']: x['InvariantScript'] for x in c['Rules']}
    try:
        return float(r['X']), float(r['Y']), float(r['X']) + float(r['Width']), float(r['Y']) + float(r['Height'])
    except (KeyError, ValueError):
        return None


tp = app.doc(RS)['TopParent']
card = find(tp, 'RS_RequestCard')
ai = find(tp, 'RS_AICheck')
AREA = (916, 266, 916 + 374, 266 + 44)
# a stacking value above the card and below every overlay, shared with nothing that overlaps the checkbox
zs = {}


def collect(c):
    for r in c['Rules']:
        if r['Property'] == 'ZIndex':
            zs.setdefault(int(r['InvariantScript']), []).append(c)
    for k in c.get('Children', []):
        collect(k)


collect(tp)
cz = int(app.rule(RS, 'RS_RequestCard', 'ZIndex'))
overlay = min(int(app.rule(RS, n, 'ZIndex')) for n in ('Rectangle1', 'NT_Backdrop', 'RS_TypePickerOverlay', 'RS_AdminNotesBackdrop'))
free = [z for z in range(cz + 1, overlay)
        if all(rect(c) is None or rect(c)[2] <= AREA[0] or rect(c)[0] >= AREA[2] or rect(c)[3] <= AREA[1] or rect(c)[1] >= AREA[3]
               for c in zs.get(z, []) if c['Name'] != 'RS_Archive')]
if not free:
    sys.exit('! no stacking value for the checkbox')
Z = free[0]
if rect(ai)[3] > 266:
    sys.exit('! RS_AICheck now reaches the checkbox row')

app.set(RS, 'RS_Archive', 'Text', '"Archiving only, not publication"', expect='"Archiving only (no publication)"')
app.set(RS, 'RS_Archive', 'X', '916')
app.set(RS, 'RS_Archive', 'Y', '266')
app.set(RS, 'RS_Archive', 'Width', '374')
app.set(RS, 'RS_Archive', 'Height', '44')
put(RS, 'RS_Archive', 'Default', VAR)
put(RS, 'RS_Archive', 'OnCheck', ON('true'), 'Behavior')
put(RS, 'RS_Archive', 'OnUncheck', ON('false'), 'Behavior')
app.set(RS, 'RS_Archive', 'DisplayMode', 'If(varRequestorLocked, DisplayMode.View, DisplayMode.Edit)')
put(RS, 'RS_Archive', 'Visible', 'Not(locDetailsCollapsed)')
r = [r for r in find(tp, 'RS_Archive')['Rules'] if r['Property'] == 'ZIndex'][0]
r['InvariantScript'] = str(Z)
for e in find(tp, 'RS_Archive').get('ControlPropertyState', []):
    if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString'):
        e['AutoRuleBindingString'] = str(Z)
app.save()

# ---------------------------------------------------------------- save time (no controls added)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('built; checkbox z =', Z)
