#!/usr/bin/env python3
"""FINAL12 on FINAL11: co-assignee on ReviewScreen; yellow borders on RequesDetailScreen.

ReviewScreen
* RV_Assignee: two people can be picked (assignee + co-assignee). It shows only what is saved on the
  request (no DG-contact default any more), saves by itself when changed (the deleted RV_BtnAssign's
  job), and is read-only for non-administrators. A third person is refused.
  Stored as Assignee (the person who stays assignee while still picked, else the first one) and the new
  person column CoAssignee. Approve no longer writes the Assignee (it used to copy the combobox,
  i.e. the DG-contact default).
* The queue row shows the co-assignee after the assignee.
* RV_CRowNotes: already view-only in the file (nothing saves it) - left as is.
RequesDetailScreen
* RS_Owner / RS_Contractor: yellow only when nothing is picked AND no manual contact exists (typed in the
  Contact Extra pop-up or saved on the request).
* RS_TypeIconBtn (production type, needed before adding media): yellow while no type is chosen.
"""
import copy, datetime, json, os, re, shutil, sys
from payaml import App, find
from jio import jwrite

SRC, NEW = 'newG1', 'newG2'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RV, RS = 'ReviewScreen', 'RequesDetailScreen'
YELLOW = 'RGBA(255, 204, 0, 1)'


def put(s, n, p, v, cat='Design'):
    c = find(app.doc(s)['TopParent'], n)
    if not [r for r in c['Rules'] if r['Property'] == p]:
        c['Rules'].append({'Property': p, 'Category': cat, 'InvariantScript': v, 'RuleProviderType': 'Unknown'})
        c.setdefault('ControlPropertyState', []).append(p)
    app.set(s, n, p, v)


# ---------------------------------------------------------------- schema: person column CoAssignee
dsp = f'{NEW}/References/DataSources.json'
ds = json.load(open(dsp, encoding='utf-8'))
req = [x for x in ds['DataSources'] if x['Name'] == 'AV-CD-Requests'][0]
rk = list(req['DataEntityMetadataJson'])[0]
meta = json.loads(req['DataEntityMetadataJson'][rk])
items = meta['schema']['items']
if 'CoAssignee' in items['properties']:
    sys.exit('! CoAssignee already in the schema')
rn = lambda o: json.loads(json.dumps(o).replace('Assignee', 'CoAssignee'))
items['properties']['CoAssignee'] = rn(items['properties']['Assignee'])
items['properties']['CoAssignee#Claims'] = rn(items['properties']['Assignee#Claims'])
items['x-ms-relationships']['CoAssignee'] = rn(items['x-ms-relationships']['Assignee'])
meta['referencedEntities']['CoAssignee'] = rn(meta['referencedEntities']['Assignee'])
for k in ('propertiesDisplayOrder', 'propertiesCompactDisplayOrder', 'propertiesTabularDisplayOrder'):
    lst = items['x-ms-displayFormat'][k]
    lst.insert(lst.index('Assignee') + 1, 'CoAssignee')
req['DataEntityMetadataJson'][rk] = json.dumps(meta, separators=(',', ':'), ensure_ascii=False)
req['ConnectedDataSourceInfoNameMapping'].update({'CoAssignee': 'CoAssignee', 'CoAssignee#Claims': 'CoAssignee Claims'})
jwrite(ds, dsp)

# ---------------------------------------------------------------- ReviewScreen: RV_Assignee
PERSON = lambda v: ('{Claims: "i:0#.f|membership|" & Lower(%s.Mail), DisplayName: %s.DisplayName, Email: %s.Mail, '
                    'Department: "", JobTitle: "", Picture: ""}' % (v, v, v))
app.set(RV, 'RV_Assignee', 'SelectMultiple', 'true', expect='false')
old = app.rule(RV, 'RV_Assignee', 'DefaultSelectedItems')
if 'First(varReviewProject.DG_Agency_Contact)' not in old:
    sys.exit('! RV_Assignee default changed')
app.set(RV, 'RV_Assignee', 'DefaultSelectedItems', '''// only what is saved on the request: the assignee, then the co-assignee (no default from the DG contact)
Filter(
    Table(
        {DisplayName: Coalesce(varReviewProject.Assignee.DisplayName, ""), Mail: Coalesce(varReviewProject.Assignee.Email, "")},
        {DisplayName: Coalesce(varReviewProject.CoAssignee.DisplayName, ""), Mail: Coalesce(varReviewProject.CoAssignee.Email, "")}
    ),
    Not(IsBlank(DisplayName))
)''', expect=old)
app.set(RV, 'RV_Assignee', 'InputTextPlaceholder', '"Search people: assignee, and co-assignee when needed (max 2)…"')
put(RV, 'RV_Assignee', 'DisplayMode', 'If(varUserRole = "ADMINISTRATOR", DisplayMode.Edit, DisplayMode.View)')
put(RV, 'RV_Assignee', 'OnChange', '''// saves as soon as the selection changes (this replaces the Assign button)
With(
    {
        sel: Self.SelectedItems,
        id: varReviewProject.ID,
        oldA: Lower(Coalesce(varReviewProject.Assignee.Email, "")),
        oldC: Lower(Coalesce(varReviewProject.CoAssignee.Email, ""))
    },
    If(
        CountRows(sel) > 2,
        Notify("Only two people can be assigned: an assignee and a co-assignee.", NotificationType.Warning);
        Reset(Self),
        With(
            // the saved assignee stays the assignee while still picked; otherwise the first person picked
            {a: If(oldA <> "" And Not(IsBlank(LookUp(sel, Lower(Mail) = oldA))), LookUp(sel, Lower(Mail) = oldA), First(sel))},
            With(
                {c: First(Filter(sel, Lower(Mail) <> Lower(Coalesce(a.Mail, ""))))},
                If(
                    Lower(Coalesce(a.Mail, "")) <> oldA Or Lower(Coalesce(c.Mail, "")) <> oldC,
                    IfError(
                        Patch(
                            'AV-CD-Requests',
                            LookUp('AV-CD-Requests', ID = id),
                            {
                                Assignee: If(IsBlank(a.Mail), Blank(), %s),
                                CoAssignee: If(IsBlank(c.Mail), Blank(), %s)
                            }
                        );
                        Notify(
                            "Assignment saved: " & Coalesce(a.DisplayName, "no assignee") & If(IsBlank(c.DisplayName), "", " + " & c.DisplayName & " (co-assignee)") & ". A new assignee receives an email.",
                            NotificationType.Success
                        );
                        Refresh('AV-CD-Requests');
                        ClearCollect(colRevReqs, 'AV-CD-Requests');
                        // keep the same request open, now with the new assignment
                        Set(varReviewProject, LookUp(colRevReqs, ID = id));
                        Set(varReqDataLoaded, false),
                        Notify("Assign failed: " & FirstError.Message, NotificationType.Error)
                    )
                )
            )
        )
    )
)''' % (PERSON('a'), PERSON('c')), 'Behavior')

# Approve no longer writes the Assignee
t = app.rule(RV, 'RV_BtnApprove', 'OnSelect')
m = re.search(r'\n( *)Assignee: If\(\s*IsBlank\(RV_Assignee\.Selected\.Mail\),', t)
if not m:
    sys.exit('! Approve: Assignee block not found')
i = t.index('If(', m.start()) + 2
depth = 0
for j in range(i, len(t)):
    depth += t[j] == '('
    depth -= t[j] == ')'
    if depth == 0:
        break
end = j + 1
if t[end] != ',':
    sys.exit('! Approve: unexpected end of the Assignee block')
n = t[:m.start()] + t[end + 1:]
if 'RV_Assignee' in n:
    sys.exit('! Approve: RV_Assignee still referenced')
app.set(RV, 'RV_BtnApprove', 'OnSelect', n, expect=t)

# queue row: show the co-assignee
def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


lbls = [c for c in walk(app.doc(RV)['TopParent']) if any(r['Property'] == 'Text' and 'Not Assigned' in r['InvariantScript'] for r in c['Rules'])]
if len(lbls) != 1:
    sys.exit(f'! {len(lbls)} queue labels with "Not Assigned"')
lt = [r['InvariantScript'] for r in lbls[0]['Rules'] if r['Property'] == 'Text'][0]
old_t = 'Coalesce(ThisItem.Assignee.DisplayName, "— Not Assigned —")'
if lt.count(old_t) != 1:
    sys.exit('! queue label text changed')
app.set(RV, lbls[0]['Name'], 'Text', lt.replace(old_t, old_t + ' & If(IsBlank(ThisItem.CoAssignee.DisplayName), "", " + " & ThisItem.CoAssignee.DisplayName)'), expect=lt)
app.save()

# ---------------------------------------------------------------- RequesDetailScreen: yellow borders
for ctl, lbl, typ, store in (('RS_Owner', 'RS_LblOwner', 'DG/Agency', 'Manual_DG_Agency_Contact'),
                             ('RS_Contractor', 'RS_LblContractor', 'Contractor', 'Manual_Contractor_Contact')):
    bc, bt = app.rule(RS, ctl, 'BorderColor'), app.rule(RS, ctl, 'BorderThickness')
    cond = f'{lbl}.Visible And IsEmpty({ctl}.SelectedItems)'
    if f'If({cond}, {YELLOW}, RGBA(0, 18, 107, 1))' not in bc or f'If({cond}, 3, 2)' != bt:
        sys.exit(f'! {ctl}: border rules changed')
    manual = (f'Coalesce(Last(Filter(colManualContacts, ContactType = "{typ}" And ParentRequest = varCurrentRequest.RequestNumber)).EmailContact, '
              f'varCurrentRequest.{store})')
    empty = f'With({{manual: {manual}}}, {cond} And IsBlank(manual))'
    app.set(RS, ctl, 'BorderColor', f'// yellow only while nothing is picked and there is no manual contact either\nIf({empty}, {YELLOW}, RGBA(0, 18, 107, 1))', expect=bc)
    app.set(RS, ctl, 'BorderThickness', f'If({empty}, 3, 2)', expect=bt)
tc, tt = app.rule(RS, 'RS_TypeIconBtn', 'BorderColor'), app.rule(RS, 'RS_TypeIconBtn', 'BorderThickness')
NOTYPE = 'IsBlank(varRequestMediaType) Or varRequestMediaType = ""'
if tc != f'If({NOTYPE}, RGBA(210, 216, 224, 1), RGBA(56, 96, 178, 1))' or tt != f'If({NOTYPE}, 1, 2)':
    sys.exit('! RS_TypeIconBtn border rules changed')
app.set(RS, 'RS_TypeIconBtn', 'BorderColor', f'// yellow while the production type is not chosen (it is needed before media can be added)\nIf({NOTYPE}, {YELLOW}, RGBA(56, 96, 178, 1))', expect=tc)
app.set(RS, 'RS_TypeIconBtn', 'BorderThickness', f'If({NOTYPE}, 3, 2)', expect=tt)
app.save()

# ---------------------------------------------------------------- save time (no controls added)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL12 built')
