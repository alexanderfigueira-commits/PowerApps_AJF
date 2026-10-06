#!/usr/bin/env python3
"""Checks for FINAL23 against FINAL22: read tracking for Message Center (DOA_List1RowBadge_7 and its pop-up)."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL23-message-read.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL22-add-media-after-draft.msapp'
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, ref = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('References/'):
            ref[f] = z.read(i)
    return js, ref


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


def bal(t):
    v = re.sub(r'(?m)^\s*//[^\n]*', '', t); v = re.sub(r'"[^"\n]*"', '""', v)
    return v.count('(') == v.count(')') and v.count('{') == v.count('}')


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
new, nref = load(PKG); old, oref = load(BASE)
RS = 'RequesDetailScreen'
check(nref == oref, 'data sources changed')
check(all(json.dumps(new[s], sort_keys=True) == json.dumps(old[s], sort_keys=True) for s in new if s != RS), 'another screen changed')
N = {c['Name']: c for c in walk(new[RS])}; O = {c['Name']: c for c in walk(old[RS])}
check(set(N) - set(O) == {'NT_ReadStatus'} and set(O) <= set(N), 'only NT_ReadStatus added')
ch = {n: sorted(p for p in set(rd(c)) | set(rd(O[n])) if rd(c).get(p) != rd(O[n]).get(p)) for n, c in N.items() if n in O}
check({k: v for k, v in ch.items() if v} == {RS: ['OnVisible'], 'NT_BtnAdd': ['OnSelect'], 'DOA_List1RowBadge_7': ['Color', 'Fill', 'OnSelect', 'Size', 'Text', 'Tooltip']}, f'changed: {[k for k, v in ch.items() if v]}')
check(N['NT_ReadStatus']['Parent'] == 'MessageCenter', 'NT_ReadStatus is in the Message Center gallery')
# schema has the read columns
x = [x for x in json.loads(zipfile.ZipFile(PKG).read('References\\DataSources.json').decode('utf-8-sig'))['DataSources'] if x['Name'] == 'AV-CD-Notes'][0]
check({'ReadOn', 'ReadBy'} <= set(x['ConnectedDataSourceInfoNameMapping'].values()), 'ReadOn / ReadBy are columns of AV-CD-Notes')
# loaders
ov, bt = rd(N[RS])['OnVisible'], rd(N['NT_BtnAdd'])['OnSelect']
for nm, t in (('OnVisible', ov), ('NT_BtnAdd', bt)):
    check('NNew: noteSide <> "" And AuthorRole.Value <> noteSide And IsBlank(ReadOn)' in t and 'rc <> "" And Not(inThread)' in t and bal(t), f'{nm}: loader flags unread notes')
core = lambda t: ' '.join(re.sub(r'//[^\n]*', '', t[t.index('If(\n') if 'If(\n' in t else 0:t.index('Clear(colReqNotes)')]).split())
b = rd(N['DOA_List1RowBadge_7'])
check('NNew: noteSide <> "" And AuthorRole.Value <> noteSide And IsBlank(ReadOn)' in b['OnSelect'], 'button: reloads the notes first')
o = b['OnSelect']
i = [o.index(k) for k in ('ClearCollect(', 'UpdateContext({locNewNotes:', '{ReadOn: Now(), ReadBy: User().FullName}', 'UpdateIf(colReqNotes, NNew, {NNew: false})', 'UpdateContext({locShowNotes: true})')]
check(i == sorted(i), 'button: reload -> remember new -> save as read -> clear flag -> open')
check(o.rstrip().endswith("UpdateContext({ currentIndex: If(currentIndex >= CountRows(MessageCenter.AllItems), 1, currentIndex + 1) });") and bal(o), 'button: its original behaviour kept')
check('CountRows(Filter(colReqNotes, NNew))' in b['Text'] and 'CountRows(Filter(colReqNotes, NNew))' in b['Fill'] and 'unread note' in b['Tooltip'] and all(bal(b[p]) for p in ('Text', 'Fill', 'Color', 'Size', 'Tooltip')), 'button: unread count, red, tooltip')
st = rd(N['NT_ReadStatus'])
check(all(k in st['Text'] for k in ('locNewNotes.Value', 'ThisItem.ReadOn', 'ThisItem.ReadBy', '"●  New"', '"Not read yet"', 'Hour(ThisItem.ReadOn) = 0')) and bal(st['Text']), 'status text: New / Not read yet / Read by on date (date-only safe)')
check(st['X'] == 'Title1.X' and st['Width'] == 'Title1.Width' and st['Y'] == 'Title1.Y + Title1.Height + 2' and st['Align'] == rd(N['Body1_1'])['Align'], 'status sits under its message')
check(rd(N['MessageCenter']) == rd(O['MessageCenter']), 'Message Center gallery itself unchanged')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
