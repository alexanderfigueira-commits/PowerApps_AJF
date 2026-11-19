#!/usr/bin/env python3
"""Checks for FINAL16 against FINAL15: the administrator can approve as archive only (ReviewScreen)."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL16-archive-only-approval.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL15-badge-colours.msapp'
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, ref, src = {}, {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('References/'):
            ref[f] = z.read(i)
        elif f.startswith('Src/'):
            src[f] = z.read(i).decode('utf-8')
    return js, ref, src


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
def bal(t):
    v = re.sub(r'(?m)^\s*//[^\n]*', '', t); v = re.sub(r'"[^"\n]*"', '""', v)
    return v.count('(') == v.count(')') and v.count('{') == v.count('}')


new, nref, nsrc = load(PKG); old, oref, _ = load(BASE)
RV = 'ReviewScreen'
check(nref == oref, 'data sources changed')
check(all(json.dumps(new[s], sort_keys=True) == json.dumps(old[s], sort_keys=True) for s in new if s != RV), 'another screen changed')
N = {c['Name']: c for c in walk(new[RV])}; O = {c['Name']: c for c in walk(old[RV])}
check(set(N) - set(O) == {'RV_ArchiveOnly'} and set(O) <= set(N), 'only RV_ArchiveOnly added')
ch = {n: sorted(p for p in set(rd(c)) | set(rd(O[n])) if rd(c).get(p) != rd(O[n]).get(p)) for n, c in N.items() if n in O}
check({k: v for k, v in ch.items() if v} == {'RV_BtnApprove': ['DisplayMode', 'OnSelect', 'Text'], 'RV_RejectHint': ['Text']}, 'only the approve button and the hint changed')
ck = rd(N['RV_ArchiveOnly'])
check(ck['Default'] == 'Coalesce(varReviewProject.ArchivedOnly, false)' and 'ADMINISTRATOR' in ck['Visible'] and 'ADMINISTRATOR' in ck['DisplayMode'], 'checkbox: shows the saved value, administrators only')
check(ck['Text'] == '"Archive only: the conditions for publication are not met"', 'checkbox text')
check(float(ck['X']) >= 860 and float(ck['X']) + float(ck['Width']) <= 1340 and 500 <= float(ck['Y']) and float(ck['Y']) + float(ck['Height']) <= 560, 'checkbox in the free space next to the assignee box')
check(rd(N['RV_Assignee'])['ZIndex'] == ck['ZIndex'], 'stacking level of the assignee box')
check('ZIndex' not in ' '.join(nsrc.values()), 'no ZIndex lines in the YAML mirror')
ap, oa = rd(N['RV_BtnApprove']), rd(O['RV_BtnApprove'])
t = ap['OnSelect']
NEWARCH = 'RV_ArchiveOnly.Value And Not(Coalesce(varReviewProject.ArchivedOnly, false))'
check('ArchivedOnly: RV_ArchiveOnly.Value' in t and f'ReviewerComments: If({NEWARCH}, Trim(varReviewComment), varReviewProject.ReviewerComments)' in t, 'Approve saves ArchivedOnly and the reason')
check(t.index("Patch('AV-CD-Requests'") < t.index("Patch(\n                'AV-CD-Notes'".replace('\n                ', '')) if False else t.index("'AV-CD-Notes'") > t.index("Patch('AV-CD-Requests'"), 'note after the request is saved')
check("Defaults('AV-CD-Notes')" in t and '<b>Approved - archive only</b>' in t and 'AuthorRole: {Value: "Administrator"}' in t, 'reason added to the notes')
check(t.index("'AV-CD-Notes'") < t.index('Set(varReviewProject, Blank())'), 'note written before the request is closed')
check(bal(t) and all(bal(ap[p]) for p in ('DisplayMode', 'Text')) and bal(rd(N['RV_RejectHint'])['Text']), 'brackets')
check(f'Not({NEWARCH} And IsBlank(Trim(varReviewComment)))' in ap['DisplayMode'] and 'Status.Value = "Processing"' in ap['DisplayMode'], 'reason required only when archive-only is turned on; still only in Processing')
stripped = t
for blk in (r'\n *// "archive only": saved with the decision[^\n]*\n *ArchivedOnly: RV_ArchiveOnly\.Value,\n *ReviewerComments: [^\n]*\n',):
    pass
check(oa['OnSelect'].split()[0:5] == t.split()[0:5], 'Approve still starts the same')
check('"Partially approved"' in t and 'MediaApproved = true' in t and 'Status: {Value:' in t, 'partial approval logic kept')
check('Approved as archive only' in t and 'requestor is notified' in t, 'confirmation message')
check('✓  Approve · Archive' in ap['Text'] and '"✓  Approve"' in ap['Text'], 'button text')
check('archive-only' in rd(N['RV_RejectHint'])['Text'] and 'A reviewer comment is required before rejecting.' in rd(N['RV_RejectHint'])['Text'], 'hint keeps the reject text')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
