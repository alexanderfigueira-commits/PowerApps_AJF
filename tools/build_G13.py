#!/usr/bin/env python3
"""FINAL23 on FINAL22: read tracking for Message Center (the ✉️ button DOA_List1RowBadge_7 and its pop-up).

* The notes loader (RequesDetailScreen.OnVisible and NT_BtnAdd) flags NNew = a note from the other side (Administrator <->
  Requestor) whose ReadOn is still empty.
* DOA_List1RowBadge_7 (✉️): shows the unread count, red while there is something unread; opening it reloads the notes,
  remembers the new ones (locNewNotes) and saves ReadOn / ReadBy on them (marks them as read), then opens Message Center as before.
* MessageCenter rows: NT_ReadStatus under each message: "● New" (unread when opened), "Not read yet", "✓ Read by X on date".
"""
import datetime, os, re, shutil, sys
from payaml import App, find
from hp_common import Builder

SRC, NEW = 'newG12', 'newG13'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RS = 'RequesDetailScreen'
RED, GREEN, GREY = 'RGBA(193, 40, 40, 1)', 'RGBA(22, 128, 80, 1)', 'RGBA(140, 148, 160, 1)'

# the loader and the marking code written for FINAL_4 (same notes structure)
src = open('build_F4.py', encoding='utf-8').read()
seg = src[src.index("LOADER = '''"):src.index('def swap_loader')]
ns = {'re': re}
exec(seg, ns)
LOADER, MARK, OLD_RE = ns['LOADER'], ns['MARK'], ns['OLD_RE']


def put(s, n, p, v, cat='Design'):
    c = find(app.doc(s)['TopParent'], n)
    if not [r for r in c['Rules'] if r['Property'] == p]:
        c['Rules'].append({'Property': p, 'Category': cat, 'InvariantScript': v, 'RuleProviderType': 'Unknown'})
        c.setdefault('ControlPropertyState', []).append(p)
    app.set(s, n, p, v)


def swap_loader(ctl, prop):
    t = app.rule(RS, ctl, prop)
    m = list(OLD_RE.finditer(t))
    if len(m) != 1 or "'AV-CD-Notes'" not in m[0].group(0):
        sys.exit(f'! {ctl}.{prop}: {len(m)} notes loaders')
    m = m[0]
    col = m.start() - (t.rfind('\n', 0, m.start()) + 1)
    n = t[:m.start()] + LOADER.replace('\n', '\n' + ' ' * col) + t[m.end():]
    app.set(RS, ctl, prop, n, expect=t)


swap_loader(None, 'OnVisible')
swap_loader('NT_BtnAdd', 'OnSelect')

# ---- the ✉️ button
B = 'DOA_List1RowBadge_7'
old = {p: app.rule(RS, B, p) for p in ('Text', 'Fill', 'Color', 'Size', 'Tooltip', 'OnSelect')}
if old['Text'] != '"✉️"' or 'locShowNotes: true' not in old['OnSelect']:
    sys.exit('! the Message Center button changed')
N = 'CountRows(Filter(colReqNotes, NNew))'
app.set(RS, B, 'Text', f'With({{n: {N}}}, "✉️" & If(n > 0, " " & n, ""))', expect=old['Text'])
app.set(RS, B, 'Fill', f'If({N} > 0, {RED}, {old["Fill"]})', expect=old['Fill'])
app.set(RS, B, 'Color', f'If({N} > 0, RGBA(255, 255, 255, 1), {old["Color"]})', expect=old['Color'])
app.set(RS, B, 'Size', f'If({N} > 0, 14, {old["Size"]})', expect=old['Size'])
app.set(RS, B, 'Tooltip', f'With({{n: {N}}}, If(n > 0, n & If(n = 1, " unread note", " unread notes") & ". Opening Message Center marks them as read.", {old["Tooltip"]}))', expect=old['Tooltip'])
app.set(RS, B, 'OnSelect', '// reload the notes, keep the new ones to highlight, mark them as read, then open Message Center\n' + LOADER + ';\n' + MARK + old['OnSelect'], expect=old['OnSelect'])
app.save()

# ---- status under every message
tp = app.doc(RS)['TopParent']
for n, v in (('Title1', 'Y'), ('Title1', 'X'), ('Title1', 'Width')):
    if not app.rule(RS, n, v):
        sys.exit(f'! {n}.{v} missing')
if app.rule(RS, 'MessageCenter', 'Items') != "Filter('AV-CD-Notes', Title = varCurrentRequest.RequestNumber)":
    sys.exit('! MessageCenter no longer reads AV-CD-Notes directly')
WHEN = ('If(\n        Hour(ThisItem.ReadOn) = 0 And Minute(ThisItem.ReadOn) = 0,\n        Text(ThisItem.ReadOn, DateTimeFormat.ShortDate),\n'
        '        Text(ThisItem.ReadOn, DateTimeFormat.ShortDateTime)\n    )')
b = Builder(app, RS)
b.clone('NT_ReadStatus', RS, 'Body1_1', {
    'Text': ('// New = unread when Message Center was opened (now saved as read)\nIf(\n    ThisItem.ID in locNewNotes.Value,\n    "●  New",\n'
             '    IsBlank(ThisItem.ReadOn),\n    "Not read yet",\n'
             '    "✓  Read" & If(IsBlank(ThisItem.ReadBy), "", " by " & ThisItem.ReadBy) & " on " & ' + WHEN + '\n)'),
    'Color': f'If(ThisItem.ID in locNewNotes.Value, {RED}, IsBlank(ThisItem.ReadOn), {GREY}, {GREEN})',
    'Size': '9', 'Height': '18', 'X': 'Title1.X', 'Width': 'Title1.Width', 'Y': 'Title1.Y + Title1.Height + 2',
}, parent='MessageCenter')
b.save()
put(RS, 'NT_ReadStatus', 'FontWeight', 'If(ThisItem.ID in locNewNotes.Value, FontWeight.Semibold, FontWeight.Normal)')
app.save()

h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
from collections import Counter


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


cnt = Counter(c['Template']['Name'] for s in app.map if s != 'App' for c in walk(app.doc(s)['TopParent']))
p = open(f'{NEW}/Properties.json', encoding='utf-8').read()
for k, v in cnt.items():
    p = re.sub(rf'("{k}": )\d+', rf'\g<1>{v}', p, count=1)
open(f'{NEW}/Properties.json', 'w', encoding='utf-8', newline='').write(p)
print('FINAL23 built')
