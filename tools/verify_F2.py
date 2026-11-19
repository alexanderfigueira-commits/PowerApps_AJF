#!/usr/bin/env python3
"""Checks for FINAL_2 against the user's FINAL_1: Review -> request detail -> back arrow."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL_2-review-nav.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else '/root/.claude/uploads/4d44a760-ee6e-5284-adba-c35ebdee79f5/44e19860-Central_Deposit_Ticket_System_FINAL_1.msapp'
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js = {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
    return js


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
new, old = load(PKG), load(BASE)
N = {s: {c['Name']: c for c in walk(t)} for s, t in new.items()}
O = {s: {c['Name']: c for c in walk(t)} for s, t in old.items()}
changed = sorted((s, n, p) for s in new for n, c in N[s].items() for p in set(rd(c)) | set(rd(O[s].get(n, {'Rules': []})))
                 if rd(c).get(p) != rd(O[s].get(n, {'Rules': []})).get(p))
want = sorted([('ReviewScreen', 'RV_RequestIDNav', p) for p in ('OnSelect', 'Text', 'Visible')] +
              [('ReviewScreen', 'RV_RequestIDNav_Gallery', 'OnSelect'),
               ('RequesDetailScreen', 'BackButton_ReviewScreen', 'Visible'), ('RequesDetailScreen', 'BackButton_ReviewScreen', 'OnSelect')] +
              [('Dashboard-Ope-Administrator', f'DOA_List{i}RowNumber', 'OnSelect') for i in (1, 2, 3)] +
              [('Dashboard-Ope-Requestor', f'DOR_List{i}RowNumber', 'OnSelect') for i in (1, 2, 3)] +
              [('RequestManagementScreen', n, 'OnSelect') for n in ('HomeRowSelect', 'DOA_List1RowBadge_5', 'HomeBtnNew')])
check(changed == want, f'changed rules: {changed}')
check(all(set(N[s]) == set(O[s]) for s in new), 'controls added or removed')
# every Navigate into RequesDetailScreen and its locFromReview value
for s in new:
    for n, c in N[s].items():
        for p, v in rd(c).items():
            for m in re.finditer(r'Navigate\(\s*RequesDetailScreen[^{]*\{([^}]*)\}', v):
                ctx = m.group(1)
                if n in ('RV_RequestIDNav', 'RV_RequestIDNav_Gallery'):
                    check('locFromReview: true' in ctx, f'{n}: not locFromReview: true')
                elif s.startswith('Child'):
                    check('locFromReview' not in ctx, f'{s}.{n}: return from a media tab must keep the value')
                else:
                    check('locFromReview: false' in ctx, f'{s}.{n}: fresh entry without locFromReview: false')
rv = N['ReviewScreen']
a = rd(rv['RV_RequestIDNav'])
check('ThisItem' not in a['OnSelect'] and 'ThisItem' not in a['Text'], 'RV_RequestIDNav still uses ThisItem')
check('LookUp(colRevReqs, ID = varReviewProject.ID)' in a['OnSelect'] and 'colOpeReqs' not in a['OnSelect'], 'RV_RequestIDNav source')
check(a['Text'].count('varReviewProject.RequestNumber') == 2 and a['Visible'] == 'Not(IsBlank(varReviewProject))', 'RV_RequestIDNav text / visible')
g = rd(rv['RV_RequestIDNav_Gallery'])['OnSelect']
check('LookUp(colRevReqs, ID = ThisItem.ID)' in g and 'colOpeReqs' not in g and 'Set(varReviewProject, req)' in g, 'gallery pill')
b = rd(N['RequesDetailScreen']['BackButton_ReviewScreen'])
check(re.sub(r'//[^\n]*', '', b['Visible']).strip() == 'Coalesce(locFromReview, false)', 'back arrow Visible')
check('Set(varReviewFromRow, true)' in b['OnSelect'] and 'Navigate(ReviewScreen' in b['OnSelect'], 'back arrow OnSelect')
check([r['Category'] for r in N['RequesDetailScreen']['BackButton_ReviewScreen']['Rules'] if r['Property'] == 'OnSelect'] == ['Behavior'], 'OnSelect category')
check('Coalesce(varReviewFromRow, false) And Not(IsBlank(varReviewProject))' in rd(rv['ReviewScreen'])['OnVisible'], 'ReviewScreen keeps the selection')
for s, n, p in want:
    v = re.sub(r'//[^\n]*', '', rd(N[s][n])[p])
    check(v.count('(') == v.count(')') and v.count('{') == v.count('}'), f'{n}.{p} brackets')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
