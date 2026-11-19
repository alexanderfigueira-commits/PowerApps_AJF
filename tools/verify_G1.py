#!/usr/bin/env python3
"""Checks for FINAL11 against the user's FINAL10: only the "Archiving only, not publication" checkbox is wired up."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL11-archiving-only.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/Central_Deposit_Ticket_System_FINAL10.msapp'
fails, cnt = [], 0
RS = 'RequesDetailScreen'


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, other = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('References/'):
            other[f] = z.read(i)
    return js, other


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
new, nref = load(PKG); old, oref = load(BASE)
N = {s: {c['Name']: c for c in walk(t)} for s, t in new.items()}
O = {s: {c['Name']: c for c in walk(t)} for s, t in old.items()}
check(nref == oref, 'References (data sources) changed')
check(all(json.dumps(new[s], sort_keys=True) == json.dumps(old[s], sort_keys=True) for s in new if s != RS), 'another screen changed')
check(set(N[RS]) == set(O[RS]), 'controls added or removed')
changed = {}
for n, c in N[RS].items():
    a, b = rd(c), rd(O[RS][n]); d = sorted(p for p in set(a) | set(b) if a.get(p) != b.get(p))
    if d: changed[n] = d
want = {'RS_Archive': ['Default', 'DisplayMode', 'Height', 'OnCheck', 'OnUncheck', 'Text', 'Visible', 'Width', 'X', 'Y', 'ZIndex'],
        'Add_media_icon': ['OnSelect'], 'RS_BtnDraftSave': ['OnSelect'], 'RS_BtnSubmitRequest': ['OnSelect'],
        'RS_BtnResubmitRequest': ['OnSelect'], new[RS]['Name']: ['OnVisible']}
check(changed == want, f'changed: {[(k, v) for k, v in changed.items() if want.get(k) != v]} / missing {[k for k in want if k not in changed]}')
# saving
for ctl in ('Add_media_icon', 'RS_BtnDraftSave', 'RS_BtnSubmitRequest', 'RS_BtnResubmitRequest'):
    t = rd(N[RS][ctl])['OnSelect']; o = rd(O[RS][ctl])['OnSelect']
    p = len(re.findall(r"Patch\(\s*'AV-CD-Requests'\s*,\s*(?:Defaults|LookUp)", t))
    check(t.count('ArchivedOnly: varRequestArchivedOnly,') == p and p > 0, f'{ctl}: flag in every request save ({p})')
    check(re.sub(r'\n *ArchivedOnly: varRequestArchivedOnly,', '', t) == o, f'{ctl}: anything else changed')
    v = re.sub(r'//[^\n]*', '', t); check(v.count('(') == v.count(')') and v.count('{') == v.count('}'), f'{ctl}: brackets')
ov, oo = rd(new[RS])['OnVisible'], rd(old[RS])['OnVisible']
check(ov.startswith(oo) and ov.endswith('Set(varRequestArchivedOnly, Coalesce(varCurrentRequest.ArchivedOnly, false))'), 'OnVisible reads the flag')
# the checkbox
ck, oc = rd(N[RS]['RS_Archive']), rd(O[RS]['RS_Archive'])
check(ck['Text'] == '"Archiving only, not publication"' and ck['Default'] == 'varRequestArchivedOnly', 'text / default')
check(ck['DisplayMode'] == 'If(varRequestorLocked, DisplayMode.View, DisplayMode.Edit)', 'locked like the AI checkbox')
check(ck['Visible'] == 'Not(locDetailsCollapsed)', 'hides with the card')
for k, v in (('OnCheck', 'true'), ('OnUncheck', 'false')):
    t = ck[k]
    check(t.startswith(f'Set(varRequestArchivedOnly, {v});') and f'{{ArchivedOnly: {v}}}' in t and f'<> {v}' in t and t.count('(') == t.count(')'), k)
box = lambda n: (lambda r: (float(r['X']), float(r['Y']), float(r['X']) + float(r['Width']), float(r['Y']) + float(r['Height'])))(rd(N[RS][n]))
b, ai, card = box('RS_Archive'), box('RS_AICheck'), box('RS_RequestCard')
check(b[1] >= ai[3] and b[0] == ai[0], 'checkbox sits under the AI checkbox')
check(card[0] <= b[0] and b[2] <= card[2] and card[1] <= b[1] and b[3] <= card[3], 'checkbox inside the card')
z = lambda n: int(rd(N[RS][n])['ZIndex'])
check(z('RS_RequestCard') < z('RS_Archive') < min(z(n) for n in ('Rectangle1', 'NT_Backdrop', 'RS_TypePickerOverlay', 'RS_AdminNotesBackdrop')), 'checkbox is above the card, under the overlays')
check({k: v for k, v in ck.items() if k not in want['RS_Archive']} == {k: v for k, v in oc.items() if k not in want['RS_Archive']}, 'its look (colours, font) kept')
check(rd(N[RS]['RS_AICheck']) == rd(O[RS]['RS_AICheck']), 'AI checkbox untouched')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
