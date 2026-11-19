#!/usr/bin/env python3
"""Checks for FINAL37 against FINAL36: view-only request details from the dashboard IDs; Beluga reference visible."""
import json, re, sys, zipfile
PKG, BASE = sys.argv[1], sys.argv[2]
fails, cnt = [], 0
def check(ok, msg):
    global cnt
    cnt += 1
    if not ok: fails.append(msg)
def load(p):
    z = zipfile.ZipFile(p); js, ref = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('References/'): ref[f] = z.read(i)
    return js, ref
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
def bal(t):
    v = re.sub(r'(?m)^\s*//[^\n]*', '', t); v = re.sub(r'"[^"\n]*"', '""', v)
    return v.count('(') == v.count(')') and v.count('{') == v.count('}')
(new, nref), (old, oref) = load(PKG), load(BASE)
check(nref == oref, 'data sources unchanged')
flat = lambda js: {(s, c['Name']): {r['Property']: r['InvariantScript'] for r in c['Rules'] if r['Property'] != 'ZIndex'} for s, t in js.items() for c in walk(t)}
n, o = flat(new), flat(old)
check(set(n) == set(o), 'same controls')
ch = sorted((k, p) for k in n for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p))
RS = 'RequesDetailScreen'; CI = 'ChildInfoScreen'
exp = sorted([(('App', 'App'), 'OnStart'), ((RS, RS), 'OnVisible'), ((CI, CI), 'OnVisible'), (('ChildMetaScreen', 'ChildMetaScreen'), 'OnVisible'), (('ChildLegalScreen', 'ChildLegalScreen'), 'OnVisible'),
              (('ChildValidScreen', 'ChildValidScreen'), 'OnVisible'), (('RequestManagementScreen', 'RequestManagementScreen'), 'OnVisible'), (('ReviewScreen', 'ReviewScreen'), 'OnVisible')]
             + [(('Dashboard-Ope-Requestor', f'DOR_List{i}RowNumber'), 'OnSelect') for i in (1, 2, 3)] + [(('Dashboard-Ope-Administrator', f'DOA_List{i}RowNumber'), 'OnSelect') for i in (1, 2, 3)]
             + [((RS, c), 'DisplayMode') for c in ('RS_TypeIconBtn', 'Add_media_icon', 'RS_AdminNotes', 'RS_RequestorNotes', 'NT_Input', 'NT_BtnAdd', 'RS_CRowApproved', 'RS_CRowDelete')]
             + [((RS, c), 'Visible') for c in ('RS_BtnDraftSave', 'RS_BtnSubmitRequest', 'RS_BtnResubmitRequest', 'RS_AdminNotesSave', 'RS_RequestorNotesSave')]
             + [((RS, 'RS_CardTitle'), 'Text'), ((CI, 'CI_Notes'), 'DisplayMode'), ((CI, 'CI_BelugaRef'), 'DisplayMode'), ((CI, 'CI_BelugaRef'), 'Visible'), ((CI, 'CI_LblBeluga'), 'Visible')])
check(ch == exp, f'exactly the expected rules changed: extra={sorted(set(ch) - set(exp))} missing={sorted(set(exp) - set(ch))}')
for s in (RS, CI, 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen'):
    t = n[(s, s)]['OnVisible']
    check('varViewOnly' in t.split('varRequestorLocked', 1)[1][:200], f'{s}: lock includes view-only')
for k, p in ch:
    if p == 'OnSelect' and k[1].endswith('RowNumber'):
        t = n[k][p]
        check(t.index('Set(varViewOnly, true)') < t.index('Navigate(RequesDetailScreen'), f'{k[1]} sets the flag before navigating')
check('Set(varViewOnly, false)' in n[('RequestManagementScreen', 'RequestManagementScreen')]['OnVisible'] and 'Set(varViewOnly, false)' in n[('ReviewScreen', 'ReviewScreen')]['OnVisible'] and 'Set(varViewOnly, false)' in n[('App', 'App')]['OnStart'], 'flag reset in Request Management, Review and OnStart')
check(n[(CI, 'CI_BelugaRef')]['Visible'] == 'true' and 'varViewOnly Or varUserRole <> "ADMINISTRATOR"' in n[(CI, 'CI_BelugaRef')]['DisplayMode'], 'Beluga visible to all, editable by admin only, never in view-only')
# every other Navigate to the request screen from a non-dashboard screen leaves the flag false: they all come after RM / Review OnVisible
others = [(k, p) for k in n for p in n[k] if 'Navigate(RequesDetailScreen' in n[k][p] and not k[0].startswith('Dashboard-Ope') and k[0] not in ('ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen')]
check(all(k[0] in ('RequestManagementScreen', 'ReviewScreen') for k, p in others), f'other entries are only RM / Review: {sorted(set(k[0] for k, p in others))}')
check(all(bal(n[k][p]) for k, p in ch), 'brackets')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
