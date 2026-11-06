#!/usr/bin/env python3
"""Checks for FINAL_4 (notes read / unread; reviewer comment as a note) against the user's FINAL_061086."""
import io, json, os, re, sys, zipfile
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paload import PaLoader
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL_4-notes-read.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/Central_Deposit_Ticket_System_FINAL_061086.msapp'
fails, cnt = [], 0
RS, RV = 'RequesDetailScreen', 'ReviewScreen'


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, ys, ds = {}, {}, None
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('Src/'):
            ys[f[4:-8]] = z.read(i).decode('utf-8')
        elif f == 'References/DataSources.json':
            ds = json.loads(z.read(i).decode('utf-8-sig'))
    return js, ys, ds


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


def yrules(text, screen):
    """control -> {property: script} from the .pa.yaml, '=' stripped."""
    doc = yaml.load(io.StringIO(text), PaLoader)
    root = doc['Screens'][screen]
    out = {None: {k: str(v)[1:] for k, v in (root.get('Properties') or {}).items()}}

    def rec(ch):
        for d in ch or []:
            k = list(d)[0]
            out[k] = {p: str(v)[1:] for p, v in ((d[k] or {}).get('Properties') or {}).items()}
            rec((d[k] or {}).get('Children'))
    rec(root.get('Children'))
    return out


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
new, ny, nds = load(PKG); old, _, ods = load(BASE)
N = {s: {c['Name']: c for c in walk(t)} for s, t in new.items()}
O = {s: {c['Name']: c for c in walk(t)} for s, t in old.items()}

# ---- exactly the intended rules changed, one control added
want = sorted([(RS, None, 'OnVisible'), (RS, 'NT_BtnAdd', 'OnSelect')]
              + [(RS, b, p) for b in ('RS_AdminNotesOpen', 'RS_RequestorNotesOpen')
                 for p in ('OnSelect', 'Text', 'BorderColor', 'BorderThickness', 'Tooltip')]
              + [(RV, b, 'OnSelect') for b in ('RV_BtnApprove', 'RV_BtnReject', 'RV_BtnNeedInfo')]
              + [(RV, 'RV_LblComment', 'Text'), (RV, 'RV_Comment', 'Tooltip')], key=str)
changed = []
for s in new:
    for n, c in N[s].items():
        if n in O[s]:
            a, b = rd(c), rd(O[s][n])
            key = None if c is new[s] else n
            changed += [(s, key, p) for p in set(a) | set(b) if a.get(p) != b.get(p)]
changed = sorted(changed, key=str)
check(changed == want, f'changed rules: extra {[c for c in changed if c not in want]} / missing {[w for w in want if w not in changed]}')
added = [(s, n) for s in new for n in N[s] if n not in O[s]]
check(added == [(RS, 'NT_ReadStatus')] and all(set(O[s]) <= set(N[s]) for s in old), f'controls added/removed: {added}')
check(N[RS]['NT_ReadStatus'].get('Parent') == 'Gallery1', 'NT_ReadStatus not inside Gallery1')

# ---- YAML mirrors JSON on the two screens
for s in (RS, RV):
    y = yrules(ny[s], s)
    for n, c in N[s].items():
        if c.get('IsGroupControl') or c['Template']['Name'] == 'galleryTemplate':
            continue
        key = None if c is new[s] else n
        for p, v in rd(c).items():
            if p in y.get(key, {}):
                check(y[key][p].split() == v.split(), f'{s}.{n}.{p}: YAML differs from JSON')

# ---- schema
def notes_schema(ds):
    x = [x for x in ds['DataSources'] if x['Name'] == 'AV-CD-Notes'][0]
    return x, json.loads(list(x['DataEntityMetadataJson'].values())[0])
nx, nm = notes_schema(nds); ox, om = notes_schema(ods)
pp = nm['schema']['items']['properties']
check(pp.get('ReadOn', {}).get('format') == 'date-time' and pp['ReadOn'].get('x-ms-permission') == 'read-write', 'ReadOn column')
check(pp.get('ReadBy', {}).get('type') == 'string' and pp['ReadBy'].get('x-ms-permission') == 'read-write', 'ReadBy column')
check(set(pp) - set(om['schema']['items']['properties']) == {'ReadOn', 'ReadBy'}, 'schema: other columns changed')
check(nx['ConnectedDataSourceInfoNameMapping'].get('ReadOn') == 'ReadOn' and nx['ConnectedDataSourceInfoNameMapping'].get('ReadBy') == 'ReadBy', 'name mapping')
others = lambda ds: [x for x in ds['DataSources'] if x['Name'] != 'AV-CD-Notes']
check(others(nds) == others(ods), 'other data sources changed')

# ---- loader: one version everywhere
loaders = [rd(new[RS])['OnVisible'], rd(N[RS]['NT_BtnAdd'])['OnSelect'],
           rd(N[RS]['RS_AdminNotesOpen'])['OnSelect'], rd(N[RS]['RS_RequestorNotesOpen'])['OnSelect']]
core = lambda t: ' '.join(re.sub(r'//[^\n]*', '', t[t.index('If(\n'):t.index('Clear(colReqNotes)')]).split()) if 'If(\n' in t else ''
for t in loaders:
    check(t.count('ClearCollect(') == 1 and t.count('colReqNotes,') >= 3, 'loader shape')
    check('NNew: noteSide <> "" And AuthorRole.Value <> noteSide And IsBlank(ReadOn)' in t, 'NNew rule')
    check('rc <> "" And Not(inThread)' in t, 'reviewer comment counted once')
    v = re.sub(r'//[^\n]*', '', t); check(v.count('(') == v.count(')') and v.count('{') == v.count('}'), 'loader brackets')
check(len({core(t) for t in loaders}) == 1 and core(loaders[0]), 'the four loaders differ')
for b in ('RS_AdminNotesOpen', 'RS_RequestorNotesOpen'):
    t = rd(N[RS][b])['OnSelect']
    i = [t.index(k) for k in ('ClearCollect(', 'UpdateContext({locNewNotes:', "{ReadOn: Now(), ReadBy: User().FullName}",
                               'UpdateIf(colReqNotes, NNew, {NNew: false})', 'UpdateContext({locShowNotes: true})')]
    check(i == sorted(i), f'{b}: load -> remember new -> mark read -> show, in that order')
    check(' new"' in rd(N[RS][b])['Text'] and 'NNew' in rd(N[RS][b])['BorderColor'], f'{b}: unread count / border')
st = rd(N[RS]['NT_ReadStatus'])
check('locNewNotes.Value' in st['Text'] and 'ThisItem.ReadOn' in st['Text'] and 'ThisItem.ReadBy' in st['Text'], 'status text')
check(st['Y'] == '134' and st['Align'] == rd(N[RS]['Body1'])['Align'], 'status position')
check('locNewNotes' in rd(N[RS]['RS_AdminNotesOpen'])['OnSelect'], 'locNewNotes set')

# ---- reviewer comment -> note
for b, lab in (('RV_BtnApprove', 'Approved'), ('RV_BtnReject', 'Rejected'), ('RV_BtnNeedInfo', 'More information needed')):
    t = rd(N[RV][b])['OnSelect']; o = rd(O[RV][b])['OnSelect']
    check(t.count("Defaults('AV-CD-Notes')") == 1 and f'"<b>{lab}</b> · "' in t, f'{b}: note patch')
    check(t.index("Patch('AV-CD-Requests'") < t.index("'AV-CD-Notes'") < t.index('Set(varReviewComment, "")'), f'{b}: order')
    check('ParentRequest: varReviewProject.RequestNumber' in t and 'Title: varReviewProject.RequestNumber' in t, f'{b}: links to the request')
    check('AdminNotesUpdatedOn' in t, f'{b}: notes date')
    v = re.sub(r'//[^\n]*', '', t); check(v.count('(') == v.count(')'), f'{b}: brackets')
    stripped = re.sub(r"\n *// the comment is also a note.*?\n *\);\n", '\n', t, flags=re.S)
    stripped = re.sub(r',\n *// the dashboards\' notes icon reads this date\n *AdminNotesUpdatedOn: If\(IsBlank\(Trim\(varReviewComment\)\), varReviewProject.AdminNotesUpdatedOn, Now\(\)\)', '', stripped)
    check(stripped == o, f'{b}: anything else changed')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
