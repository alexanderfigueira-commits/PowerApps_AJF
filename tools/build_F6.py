#!/usr/bin/env python3
"""FINAL_6 on FINAL_5: "Archiving only" checkbox + notes redesign on RequesDetailScreen.

1. New Yes/No column ArchivingOnly on AV-CD-Requests (added to the app's cached schema; it must be
   created in the SharePoint list too). New checkbox RS_ArchiveOnlyCheck "Archiving only, not
   publication" under the AI checkbox (a clone of it: same look, locked like it for a requestor
   whose request is in Processing).
   * saved with every full save of the request (first save when adding media, Save draft, Submit,
     Resubmit); ticking it on an already saved request stores it straight away, so it survives
     opening a media item and coming back;
   * RequesDetailScreen.OnVisible reads it back from the request (a new request starts at No).
2. Notes block as in the user's picture: a light band (RS_NotesBand) at the bottom of the request
   card, Requestor notes on the left and Administrator notes on the right, each a compact rounded
   "Add a note" pill with "Last updated on" under it. Same controls, same logic (counts, unread
   red border): only position, size, radius and which side they are on.
"""
import datetime, json, os, re, shutil, sys
from collections import Counter
from payaml import App, find
from hp_common import Builder
from jio import jwrite

SRC, NEW = 'newF5', 'newF6'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RS, RM = 'RequesDetailScreen', 'RequestManagementScreen'


def put(s, n, p, v, cat='Design'):
    c = find(app.doc(s)['TopParent'], n)
    if not [r for r in c['Rules'] if r['Property'] == p]:
        c['Rules'].append({'Property': p, 'Category': cat, 'InvariantScript': v, 'RuleProviderType': 'Unknown'})
        c.setdefault('ControlPropertyState', []).append(p)
    app.set(s, n, p, v)


# ---------------------------------------------------------------- 1a. schema
dsp = f'{NEW}/References/DataSources.json'
ds = json.load(open(dsp, encoding='utf-8'))
srcs = {x['Name']: x for x in ds['DataSources']}
req, med = srcs['AV-CD-Requests'], srcs['AV-CD-Mediafiles']
rk = list(req['DataEntityMetadataJson'])[0]
rmeta = json.loads(req['DataEntityMetadataJson'][rk])
mmeta = json.loads(list(med['DataEntityMetadataJson'].values())[0])
rprops = rmeta['schema']['items']['properties']
if 'ArchivingOnly' in rprops:
    sys.exit('! AV-CD-Requests already has ArchivingOnly')
yesno = [v for k, v in mmeta['schema']['items']['properties'].items() if v.get('type') == 'boolean' and not k.startswith('{') and v.get('x-ms-permission') == 'read-write'][0]
rprops['ArchivingOnly'] = dict(yesno, title='ArchivingOnly')
fmt = rmeta['schema']['items']['x-ms-displayFormat']
fmt['propertiesDisplayOrder'].insert(fmt['propertiesDisplayOrder'].index('{Attachments}'), 'ArchivingOnly')
for k in ('propertiesCompactDisplayOrder', 'propertiesTabularDisplayOrder'):
    fmt[k].append('ArchivingOnly')
req['DataEntityMetadataJson'][rk] = json.dumps(rmeta, separators=(',', ':'), ensure_ascii=False)
req['ConnectedDataSourceInfoNameMapping']['ArchivingOnly'] = 'ArchivingOnly'
jwrite(ds, dsp)

# ---------------------------------------------------------------- 1b. saved with the request
FLAG = 'varRequestArchivingOnly'
DESC = 'Description: varRequestDescription'
for ctl, n_exp in (('Add_media_icon', 3), ('RS_BtnDraftSave', None), ('RS_BtnSubmitRequest', 1), ('RS_BtnResubmitRequest', 1)):
    t = app.rule(RS, ctl, 'OnSelect')
    patches = len(re.findall(r"Patch\(\s*'AV-CD-Requests'\s*,\s*(?:Defaults|LookUp)", t))
    hits = list(re.finditer(r'\n( *)' + re.escape(DESC), t))
    if len(hits) != patches or (n_exp is not None and len(hits) != n_exp) or not hits:
        sys.exit(f'! {ctl}: {len(hits)} "{DESC}" for {patches} request patches')
    n = t
    for m in reversed(hits):
        n = n[:m.start()] + f'\n{m.group(1)}ArchivingOnly: {FLAG},' + n[m.start():]
    app.set(RS, ctl, 'OnSelect', n, expect=t)
t = app.rule(RS, None, 'OnVisible')
app.set(RS, None, 'OnVisible', t + ''';
// "Archiving only, not publication": an opened request shows what is saved, a new request starts at No
Set(varRequestArchivingOnly, Coalesce(varCurrentRequest.ArchivingOnly, false))''', expect=t)
app.save()

# ---------------------------------------------------------------- 1c. the checkbox + 2. band
def z_used(tp):
    out = {}

    def w(c):
        for r in c['Rules']:
            if r['Property'] == 'ZIndex':
                out.setdefault(int(r['InvariantScript']), []).append(c)
        for k in c.get('Children', []):
            w(k)
    w(tp)
    return out


def rect(c):
    r = {x['Property']: x['InvariantScript'] for x in c['Rules']}
    try:
        return float(r['X']), float(r['Y']), float(r['X']) + float(r['Width']), float(r['Y']) + float(r['Height'])
    except (KeyError, ValueError):
        return None


def free_z(tp, area, lo=8, hi=26):
    """a stacking value between the card (7) and the notes controls (27+) that no control overlapping `area` shares."""
    used = z_used(tp)
    for z in range(lo, hi + 1):
        if all((rect(c) is None) or rect(c)[2] <= area[0] or rect(c)[0] >= area[2] or rect(c)[3] <= area[1] or rect(c)[1] >= area[3] for c in used.get(z, [])):
            return z
    sys.exit('! no free ZIndex')


def set_z(c, z):
    r = [x for x in c['Rules'] if x['Property'] == 'ZIndex'][0]
    r['InvariantScript'] = str(z)
    for e in c.get('ControlPropertyState', []):
        if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString'):
            e['AutoRuleBindingString'] = str(z)


b = Builder(app, RS)
tp = b.tp
card = rect(find(tp, 'RS_RequestCard'))
CK = (916, 276, 916 + 374, 276 + 44)
BAND = (885, 322, 1334, 399)
if card[3] != 399 or card[2] != 1334:
    sys.exit(f'! request card moved: {card}')
LOCK = 'If(varRequestorLocked, DisplayMode.View, DisplayMode.Edit)'
ON = lambda v: (f'Set({FLAG}, {v});\n'
                '// a saved request stores the answer straight away, so it survives opening a media item and coming back\n'
                'If(\n'
                f'    Coalesce(varCurrentRequest.ID, 0) > 0 And Coalesce(varCurrentRequest.ArchivingOnly, false) <> {v},\n'
                '    IfError(\n'
                f'        Set(varCurrentRequest, Patch(\'AV-CD-Requests\', LookUp(\'AV-CD-Requests\', ID = varCurrentRequest.ID), {{ArchivingOnly: {v}}})),\n'
                '        Notify("Could not save the answer: " & FirstError.Message, NotificationType.Error)\n'
                '    )\n'
                ')')
ck = b.clone('RS_ArchiveOnlyCheck', RS, 'RS_AICheck', {
    'Default': FLAG,
    'DisplayMode': LOCK,
    'OnCheck': ON('true'),
    'OnUncheck': ON('false'),
    'Text': '"Archiving only, not publication"',
    'Color': 'RGBA(0, 0, 0, 1)',
    'Y': '276',
    'Height': '44',
}, parent=None)
band = b.clone('RS_NotesBand', RS, 'RS_DetailsDivider', {
    'X': '885', 'Y': '322', 'Width': '449', 'Height': '77',
}, parent=None)
set_z(band, free_z(tp, BAND))
set_z(ck, free_z(tp, CK))
b.save()

# the divider line next to the right column runs down to the card's bottom edge
app.set(RS, 'RS_DetailsDivider', 'Height', '260', expect='220')

# ---------------------------------------------------------------- 2. notes: requestor left, administrator right
LEFT_LBL, RIGHT_LBL, LEFT_BTN, RIGHT_BTN = 916, 1136, 915, 1134
for ctl, x in (('RS_LblAdminNotes_1', LEFT_LBL), ('RS_LblAdminNotes', RIGHT_LBL)):
    app.set(RS, ctl, 'X', str(x)); app.set(RS, ctl, 'Y', '327'); app.set(RS, ctl, 'Height', '22')
for ctl, x in (('RS_RequestorNotesOpen', LEFT_BTN), ('RS_AdminNotesOpen', RIGHT_BTN)):
    app.set(RS, ctl, 'X', str(x)); app.set(RS, ctl, 'Y', '351'); app.set(RS, ctl, 'Height', '28')
    for p in ('RadiusTopLeft', 'RadiusTopRight', 'RadiusBottomLeft', 'RadiusBottomRight'):
        put(RS, ctl, p, '14')
    put(RS, ctl, 'PaddingTop', '0'); put(RS, ctl, 'PaddingBottom', '0')
for ctl, x in (('RS_RequestorNotesUpdated', 919), ('RS_AdminNotesUpdated', 1138)):
    app.set(RS, ctl, 'X', str(x)); app.set(RS, ctl, 'Y', '380'); app.set(RS, ctl, 'Width', '190'); app.set(RS, ctl, 'Height', '16')
app.save()

# ---------------------------------------------------------------- control count + save time
def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


cnt = Counter(c['Template']['Name'] for s in app.map if s != 'App' for c in walk(app.doc(s)['TopParent']))
p = open(f'{NEW}/Properties.json', encoding='utf-8').read()
for k, v in cnt.items():
    p = re.sub(rf'("{k}": )\d+', rf'\g<1>{v}', p, count=1)
open(f'{NEW}/Properties.json', 'w', encoding='utf-8', newline='').write(p)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL_6 built')
