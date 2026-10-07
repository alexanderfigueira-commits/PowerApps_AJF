#!/usr/bin/env python3
"""Checks for FINAL41 against the owner's FINAL: publication-date clocks, contract boxes default true, blue selected tab text."""
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
flat = lambda js: {(s, c['Name']): {r['Property']: r['InvariantScript'] for r in c['Rules']} for s, t in js.items() for c in walk(t)}
n, o = flat(new), flat(old)
check(set(n) == set(o), "same controls: the owner's edits are untouched")
ch = sorted((k, p) for k in n for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p) and p != 'ZIndex')
TAB = {'ChildInfoScreen': ['CI_Tab1', 'CI_Tab2', 'CI_Tab3', 'CI_Tab4'], 'ChildMetaScreen': ['CI_Tab1_1', 'CI_Tab2_1', 'CI_Tab3_1', 'CI_Tab4_1'],
       'ChildLegalScreen': ['CI_Tab1_2', 'CI_Tab2_2', 'CI_Tab3_2', 'CI_Tab4_2'], 'ChildValidScreen': ['CI_Tab1_3', 'CI_Tab2_3', 'CI_Tab3_3', 'CI_Tab4_3']}
exp = [(('Dashboard-Ope-Requestor', 'DOR_List1RowBell'), p) for p in ('Color', 'Tooltip', 'AccessibleLabel')] + [(('Dashboard-Ope-Administrator', 'DOA_List1RowBell'), p) for p in ('Color', 'Tooltip', 'AccessibleLabel')]
exp += [(('Dashboard-Ope-Administrator', 'Dashboard-Ope-Administrator'), 'OnVisible'), (('RequesDetailScreen', 'DOA_List1RowBadge_8'), 'OnSelect'), (('RequesDetailScreen', 'Add_media_icon'), 'OnSelect')]
SEL = {'ChildInfoScreen': 0, 'ChildMetaScreen': 1, 'ChildLegalScreen': 2, 'ChildValidScreen': 3}
for s, names in TAB.items():
    for i, c in enumerate(names):
        if i == SEL[s] and o[(s, c)]['Color'] == 'RGBA(56, 96, 178, 1)': continue
        if i != SEL[s] and o[(s, c)]['Color'] == 'RGBA(96, 104, 120, 1)': continue
        exp.append(((s, c), 'Color'))
check(ch == sorted(exp), f'exactly the expected rules changed: extra={sorted(set(ch) - set(exp))} missing={sorted(set(exp) - set(ch))}')
for k in (('Dashboard-Ope-Requestor', 'DOR_List1RowBell'), ('Dashboard-Ope-Administrator', 'DOA_List1RowBell')):
    for p in ('Color', 'Tooltip', 'AccessibleLabel'):
        t = n[k][p]
        check('PublicationStartDate' in t and not re.search(r'CaptureDate|[Ss]hooting|[Ff]ilming', t) and bal(t), f'{k[1]}.{p}')
    check('"No publication date yet"' in n[k]['Tooltip'] and 'what: "Publication date"' in n[k]['Tooltip'], f'{k[1]} texts')
COND = 'Coalesce(varCurrentRequest.Status.Value, "") in ["Processing", "Pending", "Approved", "Partially approved", "Rejected"]'
for k in (('RequesDetailScreen', 'DOA_List1RowBadge_8'), ('RequesDetailScreen', 'Add_media_icon')):
    t = n[k]['OnSelect']
    check(f'Set(varDocFramework, {COND}); Set(varDocSpecific, {COND}); Set(varDocOffer, false);' in t, f'{k[1]}: contract boxes default by status')
for s, names in TAB.items():
    cols = [n[(s, c)]['Color'] for c in names]
    check(cols == ['RGBA(56, 96, 178, 1)' if i == SEL[s] else 'RGBA(96, 104, 120, 1)' for i in range(4)], f'{s}: only the selected tab text is blue')
check(n[('ChildValidScreen', 'CI_Tab1_3')]['OnSelect'] == 'Navigate(ChildInfoScreen)', "owner's fixed tab link kept")
check(all(bal(n[k][p]) for k, p in ch), 'brackets')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
