#!/usr/bin/env python3
"""Checks for FINAL12 against FINAL11: co-assignee (ReviewScreen) and yellow borders (RequesDetailScreen)."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL12-coassignee-yellow.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL11-archiving-only.msapp'
fails, cnt = [], 0
RV, RS = 'ReviewScreen', 'RequesDetailScreen'


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, ds, other = {}, None, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f == 'References/DataSources.json':
            ds = json.loads(z.read(i).decode('utf-8-sig'))
        elif f.startswith('Src/'):
            other[f] = z.read(i).decode('utf-8')
    return js, ds, other


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
new, nds, nsrc = load(PKG); old, ods, _ = load(BASE)
N = {s: {c['Name']: c for c in walk(t)} for s, t in new.items()}
O = {s: {c['Name']: c for c in walk(t)} for s, t in old.items()}
bal = lambda t: (lambda v: v.count('(') == v.count(')') and v.count('{') == v.count('}') and v.count('[') == v.count(']'))(re.sub(r'//[^\n]*', '', t))

# ---- scope
check(all(json.dumps(new[s], sort_keys=True) == json.dumps(old[s], sort_keys=True) for s in new if s not in (RV, RS)), 'another screen changed')
check({s: set(N[s]) for s in N} == {s: set(O[s]) for s in O}, 'controls added or removed')
lbl = [n for n, c in N[RV].items() if 'Not Assigned' in rd(c).get('Text', '')]
changed = {}
for s in (RV, RS):
    for n, c in N[s].items():
        a, b = rd(c), rd(O[s][n]); d = sorted(p for p in set(a) | set(b) if a.get(p) != b.get(p))
        if d: changed[(s, n)] = d
want = {(RV, 'RV_Assignee'): ['DefaultSelectedItems', 'DisplayMode', 'InputTextPlaceholder', 'OnChange', 'SelectMultiple'],
        (RV, 'RV_BtnApprove'): ['OnSelect'], (RV, lbl[0]): ['Text'],
        (RS, 'RS_Owner'): ['BorderColor', 'BorderThickness'], (RS, 'RS_Contractor'): ['BorderColor', 'BorderThickness'],
        (RS, 'RS_TypeIconBtn'): ['BorderColor', 'BorderThickness']}
check(len(lbl) == 1, 'queue label')
check(changed == want, f'changed: {[(k, v) for k, v in changed.items() if want.get(k) != v]} / missing {[k for k in want if k not in changed]}')

# ---- schema
def req(ds):
    x = [x for x in ds['DataSources'] if x['Name'] == 'AV-CD-Requests'][0]
    return x, json.loads(list(x['DataEntityMetadataJson'].values())[0])
nx, nm = req(nds); ox, om = req(ods)
a, b = nm['schema']['items']['properties'], om['schema']['items']['properties']
check(set(a) - set(b) == {'CoAssignee', 'CoAssignee#Claims'} and set(b) <= set(a) and all(a[k] == b[k] for k in b), 'schema: only the two CoAssignee entries added')
check(a['CoAssignee']['type'] == 'object' and a['CoAssignee']['title'] == 'CoAssignee' and 'Assignee"' not in json.dumps(a['CoAssignee']).replace('CoAssignee', ''), 'CoAssignee is a person column like Assignee')
check('CoAssignee' in nm['schema']['items']['x-ms-relationships'] and 'CoAssignee' in nm['referencedEntities'], 'relationships / lookup')
check(all('CoAssignee' in nm['schema']['items']['x-ms-displayFormat'][k] for k in ('propertiesDisplayOrder', 'propertiesCompactDisplayOrder', 'propertiesTabularDisplayOrder')), 'display orders')
check(nx['ConnectedDataSourceInfoNameMapping'].get('CoAssignee') == 'CoAssignee', 'name mapping')
check(nm['schema']['items']['properties']['Assignee'] == om['schema']['items']['properties']['Assignee'], 'Assignee column untouched')
check([x for x in nds['DataSources'] if x['Name'] != 'AV-CD-Requests'] == [x for x in ods['DataSources'] if x['Name'] != 'AV-CD-Requests'], 'other data sources changed')

# ---- RV_Assignee
r = rd(N[RV]['RV_Assignee'])
check(r['SelectMultiple'] == 'true', 'two people can be picked')
check('DG_Agency_Contact' not in r['DefaultSelectedItems'] and 'CoAssignee' in r['DefaultSelectedItems'], 'no default fill; shows saved assignee + co-assignee')
oc = r['OnChange']
check(bal(oc) and 'CountRows(sel) > 2' in oc and 'Reset(Self)' in oc, 'OnChange: max 2')
check("Patch(\n'AV-CD-Requests'".replace('\n', '') in oc.replace('\n', '').replace(' ', '').replace("Patch(", "Patch(\n'", 1).replace('\n', '') or 'Patch(' in oc, 'OnChange patches the request')
check('Assignee: If(IsBlank(a.Mail)' in oc and 'CoAssignee: If(IsBlank(c.Mail)' in oc, 'OnChange writes Assignee and CoAssignee')
check('<> oldA Or' in oc and '<> oldC' in oc, 'OnChange only saves a real change (no loops, no needless flow runs)')
check(oc.index('Patch(') < oc.index("ClearCollect(colRevReqs") < oc.index('Set(varReviewProject'), 'OnChange: save, reload, keep request open')
check(r['DisplayMode'] == 'If(varUserRole = "ADMINISTRATOR", DisplayMode.Edit, DisplayMode.View)', 'administrators only')
# Approve
t, o = rd(N[RV]['RV_BtnApprove'])['OnSelect'], rd(O[RV]['RV_BtnApprove'])['OnSelect']
check('RV_Assignee' not in t and 'Assignee' not in t and bal(t), 'Approve no longer writes the assignee')
m = re.search(r'\n *Assignee: If\(', o); i = o.index('If(', m.start()) + 2; d = 0
for j in range(i, len(o)):
    d += o[j] == '('; d -= o[j] == ')'
    if d == 0: break
check((o[:m.start()] + o[j + 2:]).split() == t.split(), 'Approve: only the Assignee block removed')
# deleted controls stay deleted, notes box stays view-only
alltxt = json.dumps(new) + '\n'.join(nsrc.values())
check('RV_BtnAssign' not in alltxt and 'RV_OwnerEmail' not in alltxt, 'RV_BtnAssign / RV_OwnerEmail gone, nothing refers to them')
nr = rd(N[RV]['RV_CRowNotes'])
check(nr['DisplayMode'] == 'DisplayMode.View' and 'OnChange' not in nr and 'RV_CRowNotesSave' not in alltxt, 'internal notes view-only, nothing saves them')
check('CoAssignee' in rd(N[RV][lbl[0]])['Text'] and bal(rd(N[RV][lbl[0]])['Text']), 'queue row shows the co-assignee')

# ---- yellow borders
Y = 'RGBA(255, 204, 0, 1)'
for ctl, typ, store in (('RS_Owner', 'DG/Agency', 'Manual_DG_Agency_Contact'), ('RS_Contractor', 'Contractor', 'Manual_Contractor_Contact')):
    r = rd(N[RS][ctl])
    for p in ('BorderColor', 'BorderThickness'):
        check(f'ContactType = "{typ}"' in r[p] and f'varCurrentRequest.{store}' in r[p] and 'IsBlank(manual)' in r[p] and f'IsEmpty({ctl}.SelectedItems)' in r[p] and bal(r[p]), f'{ctl}.{p}: yellow only when empty and no manual contact')
    check(Y in r['BorderColor'] and 'RGBA(0, 18, 107, 1)' in r['BorderColor'] and r['BorderThickness'].endswith(', 3, 2)'), f'{ctl}: colours / thickness')
r = rd(N[RS]['RS_TypeIconBtn'])
check(Y in r['BorderColor'] and r['BorderThickness'] == 'If(IsBlank(varRequestMediaType) Or varRequestMediaType = "", 3, 2)' and 'RGBA(56, 96, 178, 1)' in r['BorderColor'], 'production type: yellow until chosen')
# earlier work intact
check(rd(N[RS]['RS_Archive']) == rd(O[RS]['RS_Archive']), 'Archiving-only checkbox untouched')
z = lambda n: int(rd(N[RS][n])['ZIndex'])
g4 = [c for c in new[RS]['Children'] if c['Name'] == 'Group4'][0]['GroupedControlsKey']
check(z('DOA_List1Counter_1') < z('Group4') and max(z('DOA_List1CounterCircle_1'), z('DOA_List1CounterText_1')) < min(z(n) for n in g4), 'counter is behind Group4')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
