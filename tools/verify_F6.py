#!/usr/bin/env python3
"""Checks for FINAL_6 against FINAL_5: "Archiving only" checkbox + notes block redesign (RequesDetailScreen)."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL_6-archiving-notes-design.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL_5-notes-read-fixes.msapp'
fails, cnt = [], 0
RS = 'RequesDetailScreen'


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, ds = {}, None
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f == 'References/DataSources.json':
            ds = json.loads(z.read(i).decode('utf-8-sig'))
    return js, ds


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
new, nds = load(PKG); old, ods = load(BASE)
N = {s: {c['Name']: c for c in walk(t)} for s, t in new.items()}
O = {s: {c['Name']: c for c in walk(t)} for s, t in old.items()}

# ---- only RequesDetailScreen changed; the controls changed are the intended ones
check(all(json.dumps(new[s], sort_keys=True) == json.dumps(old[s], sort_keys=True) for s in new if s != RS), 'another screen changed')
NOTES = ['RS_LblAdminNotes', 'RS_LblAdminNotes_1', 'RS_AdminNotesOpen', 'RS_RequestorNotesOpen', 'RS_AdminNotesUpdated', 'RS_RequestorNotesUpdated']
changed = {}
for n, c in N[RS].items():
    if n in O[RS]:
        a, b = rd(c), rd(O[RS][n]); d = sorted(p for p in set(a) | set(b) if a.get(p) != b.get(p))
        if d: changed[n] = d
want = {'RS_DetailsDivider': ['Height'], 'Add_media_icon': ['OnSelect'], 'RS_BtnDraftSave': ['OnSelect'],
        'RS_BtnSubmitRequest': ['OnSelect'], 'RS_BtnResubmitRequest': ['OnSelect'], new[RS]['Name']: ['OnVisible']}
for n in NOTES[:2]: want[n] = ['Height', 'X', 'Y']
for n in NOTES[2:4]: want[n] = ['Height', 'PaddingBottom', 'PaddingTop', 'RadiusBottomLeft', 'RadiusBottomRight', 'RadiusTopLeft', 'RadiusTopRight', 'X', 'Y']
for n in NOTES[4:]: want[n] = ['Height', 'Width', 'X', 'Y']
check(changed == want, f'changed controls/rules: {[(k, v) for k, v in changed.items() if want.get(k) != v]} / missing {[k for k in want if k not in changed]}')
check(sorted(set(N[RS]) - set(O[RS])) == ['RS_ArchiveOnlyCheck', 'RS_NotesBand'] and set(O[RS]) <= set(N[RS]), 'controls added/removed')

# ---- schema
def req(ds):
    x = [x for x in ds['DataSources'] if x['Name'] == 'AV-CD-Requests'][0]
    return x, json.loads(list(x['DataEntityMetadataJson'].values())[0])
nx, nm = req(nds); ox, om = req(ods)
a = nm['schema']['items']['properties']; b = om['schema']['items']['properties']
check(set(a) - set(b) == {'ArchivingOnly'} and set(b) <= set(a) and all(a[k] == b[k] for k in b), 'schema: only ArchivingOnly added')
check(a['ArchivingOnly']['type'] == 'boolean' and a['ArchivingOnly']['x-ms-permission'] == 'read-write', 'ArchivingOnly is a Yes/No column')
check(nx['ConnectedDataSourceInfoNameMapping'].get('ArchivingOnly') == 'ArchivingOnly', 'name mapping')
check([x for x in nds['DataSources'] if x['Name'] != 'AV-CD-Requests'] == [x for x in ods['DataSources'] if x['Name'] != 'AV-CD-Requests'], 'other data sources changed')

# ---- saving
for ctl in ('Add_media_icon', 'RS_BtnDraftSave', 'RS_BtnSubmitRequest', 'RS_BtnResubmitRequest'):
    t = rd(N[RS][ctl])['OnSelect']; o = rd(O[RS][ctl])['OnSelect']
    p = len(re.findall(r"Patch\(\s*'AV-CD-Requests'\s*,\s*(?:Defaults|LookUp)", t))
    check(t.count('ArchivingOnly: varRequestArchivingOnly,') == p and p > 0, f'{ctl}: flag in every request save ({p})')
    check(re.sub(r'\n *ArchivingOnly: varRequestArchivingOnly,', '', t) == o, f'{ctl}: anything else changed')
    v = re.sub(r'//[^\n]*', '', t); check(v.count('(') == v.count(')') and v.count('{') == v.count('}'), f'{ctl}: brackets')
ov = rd(new[RS])['OnVisible']; oo = rd(old[RS])['OnVisible']
check(ov.startswith(oo) and 'Set(varRequestArchivingOnly, Coalesce(varCurrentRequest.ArchivingOnly, false))' in ov, 'OnVisible reads the flag')
ck = rd(N[RS]['RS_ArchiveOnlyCheck'])
check(ck['Text'] == '"Archiving only, not publication"' and ck['Default'] == 'varRequestArchivingOnly', 'checkbox text/default')
check(ck['DisplayMode'] == 'If(varRequestorLocked, DisplayMode.View, DisplayMode.Edit)', 'checkbox locked like the AI one')
for k, v in (('OnCheck', 'true'), ('OnUncheck', 'false')):
    t = ck[k]
    check(t.startswith(f'Set(varRequestArchivingOnly, {v});') and f'ArchivingOnly: {v}' in t and f'<> {v}' in t and t.count('(') == t.count(')'), f'checkbox {k}')
check(rd(N[RS]['RS_AICheck']) == rd(O[RS]['RS_AICheck']), 'AI checkbox untouched')

# ---- layout: everything inside the card, nothing overlapping, band under the notes
def box(n):
    r = rd(N[RS][n]); return float(r['X']), float(r['Y']), float(r['X']) + float(r['Width']), float(r['Y']) + float(r['Height'])
card = box('RS_RequestCard')
inside = lambda b: b[0] >= card[0] and b[2] <= card[2] and b[1] >= card[1] and b[3] <= card[3]
for n in ['RS_ArchiveOnlyCheck', 'RS_NotesBand'] + NOTES:
    check(inside(box(n)), f'{n} outside the card {box(n)}')
ov_ = lambda a, b: not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])
check(not ov_(box('RS_ArchiveOnlyCheck'), box('RS_AICheck')), 'checkboxes overlap')
check(not ov_(box('RS_ArchiveOnlyCheck'), box('RS_NotesBand')), 'checkbox overlaps the band')
bd = box('RS_NotesBand')
for n in NOTES:
    b_ = box(n); check(bd[0] <= b_[0] and b_[2] <= bd[2] and bd[1] <= b_[1] and b_[3] <= bd[3], f'{n} not inside the band')
check(box('RS_RequestorNotesOpen')[0] < box('RS_AdminNotesOpen')[0] and box('RS_LblAdminNotes_1')[0] < box('RS_LblAdminNotes')[0]
      and box('RS_RequestorNotesUpdated')[0] < box('RS_AdminNotesUpdated')[0], 'requestor left, administrator right')
check(rd(N[RS]['RS_LblAdminNotes_1'])['Text'] == '"Requestor Notes:"' and rd(N[RS]['RS_LblAdminNotes'])['Text'] == '"Adminstrator Notes:"', 'labels still match their sides')
for side in ('Requestor', 'Admin'):
    check(abs(box(f'RS_{side}NotesOpen')[0] - box(f'RS_{side}NotesUpdated')[0]) <= 5, f'{side}: pill and "Last updated" line up')
for n in ('RS_AdminNotesOpen', 'RS_RequestorNotesOpen'):
    r = rd(N[RS][n]); check(all(r[p] == '14' for p in ('RadiusTopLeft', 'RadiusTopRight', 'RadiusBottomLeft', 'RadiusBottomRight')) and r['Height'] == '28', f'{n}: pill')
    check(rd(O[RS][n]).get('OnSelect') == r['OnSelect'] and rd(O[RS][n]).get('Text') == r['Text'], f'{n}: logic unchanged')
z = lambda n: int(rd(N[RS][n])['ZIndex'])
check(z('RS_RequestCard') < z('RS_NotesBand') < min(z(n) for n in NOTES), 'band stacks between the card and the notes controls')
check(z('RS_ArchiveOnlyCheck') > z('RS_RequestCard') and z('RS_ArchiveOnlyCheck') < min(z(n) for n in ('Rectangle1', 'NT_Backdrop', 'RS_TypePickerOverlay', 'RS_AdminNotesBackdrop')), 'checkbox stays under the overlays')
for n in ('RS_ArchiveOnlyCheck', 'RS_NotesBand'):
    check(rd(N[RS][n])['Visible'] == 'Not(locDetailsCollapsed)', f'{n} hides with the card')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
