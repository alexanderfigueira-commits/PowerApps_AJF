#!/usr/bin/env python3
"""FINAL29: FINAL28 minus the changes the user did NOT choose, plus the user's own edit from the uploaded FINAL_2.

The uploaded FINAL_2 is FINAL10 + the user's edit on RequestManagementScreen (collapsing filter bar). The user chose which of
the later changes to keep. Taken out of FINAL28 again:
  * notes read / unread (NT_ReadStatus, red message badge, mark-as-read, notes loaders)  -> as in FINAL_2
  * the Legal answers saved (SubtitlesProvided, DocFramework, DocSpecific, DocOffer)      -> not saved, columns not in schema
  * Export / print changes (the three print pages and HomePrintScreen)                    -> screens as in FINAL_2
Kept: archiving-only + admin archive, co-assignee, add media after draft save, yellow borders (request + media file tabs),
save fixes (PublicationChannel gone, ScriptShotlist, producers kept), video defaults, "media file" wording, badge colours/links.
ModelRelease / Preexisting stay removed (user: not relevant).
"""
import datetime, json, os, re, shutil, sys
from collections import Counter
from payaml import App, find, CTL_RE, _indent, screens
from jio import jwrite

SRC, NEW, UP = 'newG18', 'newG19', 'up2'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
up = App(UP)
RS = 'RequesDetailScreen'


def nl(t):
    return t.replace('\r\n', '\n')


def like(orig, t):
    return t.replace('\n', '\r\n') if '\r\n' in orig else t


def up_rule(s, c, p):
    return up.rule(s, c, p)


# ---------------------------------------------------------------- 1. user's own edit: RequestManagementScreen
RM = 'RequestManagementScreen'
n_rm = 0
for c in ('HomeBtnNew', 'HomeFilterBar', 'HomeThAction', 'HomeThAction_1', 'HomeThAction_2', 'HomeThAction_3', 'HomeThArchives',
          'HomeThAssignee', 'HomeThDG', 'HomeThName', 'HomeThRequest', 'HomeThStatus'):
    ca = find(app.doc(RM)['TopParent'], c)
    cu = find(up.doc(RM)['TopParent'], c)
    ra = {r['Property']: r['InvariantScript'] for r in ca['Rules']}
    ru = {r['Property']: r['InvariantScript'] for r in cu['Rules']}
    for p in sorted(set(ra) | set(ru)):
        if p == 'ZIndex' or ra.get(p) == ru.get(p):
            continue
        if p not in ra or p not in ru:
            sys.exit(f'! {c}.{p} missing on one side')
        app.set(RM, c, p, ru[p], expect=ra[p])
        n_rm += 1
app.save()
print('user edit rules copied:', n_rm)

# ---------------------------------------------------------------- 2. notes read/unread out again
# controls
def drop_controls(scr, gone):
    tp = app.doc(scr)['TopParent']
    def strip(node):
        node['Children'] = [k for k in node.get('Children', []) if k['Name'] not in gone]
        for k in node['Children']:
            strip(k)
    strip(tp)
    for g in [c for c in tp['Children'] if c.get('IsGroupControl')]:
        if gone & set(g.get('GroupedControlsKey', [])):
            g['GroupedControlsKey'] = [x for x in g['GroupedControlsKey'] if x not in gone]
    app.save()
    yp = os.path.join(NEW, 'Src', f'{scr}.pa.yaml')
    lines = open(yp, encoding='utf-8').read().split('\n')
    for lab in sorted(gone):
        hit = [i for i, l in enumerate(lines) if CTL_RE.match(l) and CTL_RE.match(l).group(1) == lab]
        if len(hit) != 1:
            sys.exit(f'! {lab}: {len(hit)} YAML blocks')
        a = hit[0]; mi = _indent(lines[a]); b = len(lines)
        for i in range(a + 1, len(lines)):
            if lines[i].strip() and _indent(lines[i]) <= mi:
                b = i; break
        del lines[a:b]
    open(yp, 'w', encoding='utf-8').write('\n'.join(lines))
    app._json.pop(scr, None)


drop_controls(RS, {'NT_ReadStatus'})
for p in ('Color', 'Fill', 'OnSelect', 'Size', 'Text', 'Tooltip'):
    app.set(RS, 'DOA_List1RowBadge_7', p, up_rule(RS, 'DOA_List1RowBadge_7', p), expect=app.rule(RS, 'DOA_List1RowBadge_7', p))
t = app.rule(RS, 'NT_BtnAdd', 'OnSelect')
app.set(RS, 'NT_BtnAdd', 'OnSelect', up_rule(RS, 'NT_BtnAdd', 'OnSelect'), expect=t)
app.save()

# OnVisible: notes block as in FINAL_2, rest of FINAL28 kept; the four Legal loader fields out
t = app.rule(RS, None, 'OnVisible')
u = up_rule(RS, None, 'OnVisible')
t_, u_ = nl(t), nl(u)
s28 = t_.index('If(\n    Coalesce(varCurrentRequest.ID, 0) > 0,\n    With(')
e28 = t_.index('    Clear(colReqNotes)\n)', s28) + len('    Clear(colReqNotes)\n)')
su = u_.index('If(\n    Coalesce(varCurrentRequest.ID, 0) > 0,\n    ClearCollect(')
eu = u_.index('    Clear(colReqNotes)\n)', su) + len('    Clear(colReqNotes)\n)')
n_ = t_[:s28] + u_[su:eu] + t_[e28:]
pat = (r'\),\n *SubtitlesProvided: Coalesce\(SubtitlesProvided, false\),\n *DocFramework: Coalesce\(DocFramework, false\),'
       r'\n *DocSpecific: Coalesce\(DocSpecific, false\),\n *DocOffer: Coalesce\(DocOffer, false\)')
if len(re.findall(pat, n_)) != 1:
    sys.exit('! loader Legal fields not found')
n_ = re.sub(pat, ')', n_)
if re.search(r'NNew|locNewNotes|ReadOn', n_):
    sys.exit('! OnVisible still has note-read pieces')
app.set(RS, None, 'OnVisible', like(t, n_), expect=t)

# ---------------------------------------------------------------- 3. Legal answers not saved
t = app.rule(RS, 'RS_CRowSelect', 'OnSelect')
t_ = nl(t)
old = ('Set(varDocFramework, Coalesce(ThisItem.DocFramework, false)); Set(varDocSpecific, Coalesce(ThisItem.DocSpecific, false)); Set(varDocOffer, Coalesce(ThisItem.DocOffer, false));\n'
       'Set(varChildSubtitlesProvided, Coalesce(ThisItem.SubtitlesProvided, false));')
if t_.count(old) != 1:
    sys.exit('! row select Legal lines not found')
t_ = t_.replace(old, 'Set(varDocFramework, false); Set(varDocSpecific, false); Set(varDocOffer, false);')
app.set(RS, 'RS_CRowSelect', 'OnSelect', like(t, t_), expect=t)

S, N = 'ChildValidScreen', 'CV_BtnSaveArchive'
t = app.rule(S, N, 'OnSelect')
t_ = nl(t)
pat = (r'(PreexistingProvided: varChildPreexistingProvided),\n *SubtitlesProvided: varChildSubtitlesProvided,\n *DocFramework: varDocFramework,'
       r'\n *DocSpecific: varDocSpecific,\n *DocOffer: varDocOffer')
if len(re.findall(pat, t_)) != 1:
    sys.exit('! media list record Legal fields not found')
t_ = re.sub(pat, r'\1', t_)
a = t_.index('// The Legal tab confirmations are Yes/No columns.')
a = t_.rfind('\n', 0, a) + 1
b = t_.index('UpdateIf(colArchives, ArchiveId = varCurrentChildId, {SPId: savedMedia.ID});')
b = t_.rfind('\n', 0, b) + 1
t_ = t_[:a] + t_[b:]
if re.search(r'DocFramework|DocOffer|SubtitlesProvided', t_):
    sys.exit('! save button still mentions the Legal answers')
app.set(S, N, 'OnSelect', like(t, t_), expect=t)
app.save()

dsp = f'{NEW}/References/DataSources.json'
ds = json.load(open(dsp, encoding='utf-8'))
med = [x for x in ds['DataSources'] if x['Name'] == 'AV-CD-Mediafiles'][0]
mk = list(med['DataEntityMetadataJson'])[0]
meta = json.loads(med['DataEntityMetadataJson'][mk])
items = meta['schema']['items']
for col in ('SubtitlesProvided', 'DocFramework', 'DocSpecific', 'DocOffer'):
    del items['properties'][col]
    med['ConnectedDataSourceInfoNameMapping'].pop(col, None)
    for k in ('propertiesDisplayOrder', 'propertiesCompactDisplayOrder', 'propertiesTabularDisplayOrder'):
        if col in items['x-ms-displayFormat'][k]:
            items['x-ms-displayFormat'][k].remove(col)
med['DataEntityMetadataJson'][mk] = json.dumps(meta, separators=(',', ':'), ensure_ascii=False)
jwrite(ds, dsp)

# ---------------------------------------------------------------- 4. export / print screens as in FINAL_2
for scr in ('HomePrintScreen', 'PrintVideoDetailScreen', 'PrintPhotoDetailScreen', 'PrintPodcastDetailScreen'):
    shutil.copyfile(up.map[scr], app.map[scr])
    shutil.copyfile(os.path.join(UP, 'Src', f'{scr}.pa.yaml'), os.path.join(NEW, 'Src', f'{scr}.pa.yaml'))

# ---------------------------------------------------------------- control count + save time
def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)

app = App(NEW)
cnt = Counter(c['Template']['Name'] for s in app.map if s != 'App' for c in walk(app.doc(s)['TopParent']))
p = open(f'{NEW}/Properties.json', encoding='utf-8').read()
for k, v in cnt.items():
    p = re.sub(rf'("{k}": )\d+', rf'\g<1>{v}', p, count=1)
open(f'{NEW}/Properties.json', 'w', encoding='utf-8', newline='').write(p)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL29 built')
