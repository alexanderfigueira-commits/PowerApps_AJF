#!/usr/bin/env python3
"""Checks for FINAL_3 against FINAL_2: 2-digit media numbers, yellow borders, labels removed."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL_3-mandatory-yellow.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL_2-review-nav.msapp'
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, ys = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('Src/'):
            ys[f[4:-8]] = z.read(i).decode('utf-8')
    return js, ys


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
new, ny = load(PKG); old, _ = load(BASE)
N = {s: {c['Name']: c for c in walk(t)} for s, t in new.items()}
O = {s: {c['Name']: c for c in walk(t)} for s, t in old.items()}
LABELS = {'RequesDetailScreen': 'RS_LblMissing', 'ChildInfoScreen': 'CI_LblMissing', 'ChildMetaScreen': 'CM_LblMissing', 'ChildLegalScreen': 'CL_LblMissing'}
for s, l in LABELS.items():
    check(l not in N[s] and f'- {l}:' not in ny[s], f'{l} still there')
alltext = json.dumps(new) + '\n'.join(ny.values())
for l in LABELS.values():
    check(not re.search(r'\b' + l + r'\b', alltext), f'{l} still referenced')
check(not re.search(r'Still to complete', json.dumps(new)), '"Still to complete" text left')
# changed rules
FIELDS = {'RequesDetailScreen': ['RS_Title', 'HomeFilterDG', 'RS_Owner', 'RS_Contractor', 'RS_ChildrenCard'],
          'ChildInfoScreen': ['CI_Title', 'CI_PodcastTitle', 'CI_PodcastDesc', 'CI_CaptureDate', 'CI_ProductType', 'CI_BtnOpenAttach', 'CI_Language'],
          'ChildMetaScreen': ['CM_ProdEnd', 'CM_PubStartV', 'CM_PubEndV', 'CM_SeasonNumber', 'CM_EpisodeNumber', 'CM_EpisodeTitleP',
                              'CM_EpisodeSummary', 'CM_Caption', 'CM_Language', 'CM_Authority', 'CM_Producer'],
          'ChildLegalScreen': ['CL_Case', 'CL_DCAttachValue']}
want = sorted([(s, f, p) for s, fs in FIELDS.items() for f in fs for p in ('BorderColor', 'BorderThickness')] +
              [('RequesDetailScreen', 'Add_media_icon', 'OnSelect'), ('ChildValidScreen', 'CV_BtnSaveArchive', 'OnSelect')])
changed = sorted((s, n, p) for s in new for n, c in N[s].items() if n in O[s]
                 for p in set(rd(c)) | set(rd(O[s][n])) if rd(c).get(p) != rd(O[s][n]).get(p))
check(changed == want, f'changed rules: {[c for c in changed if c not in want]} / missing {[w for w in want if w not in changed]}')
check(all(set(N[s]) == set(O[s]) - {LABELS.get(s)} for s in new), 'controls added or removed beyond the labels')
for s, fs in FIELDS.items():
    lab = rd(O[s][LABELS[s]])['Text']
    for f in fs:
        a, b = rd(N[s][f]), rd(O[s][f])
        m = re.match(r'If\((.+), 3, (.+)\)$', a['BorderThickness'], re.S)
        check(m is not None and m.group(2) == b['BorderThickness'], f'{f}: thickness')
        if m:
            test = m.group(1)
            check(' '.join(test.split()) in ' '.join(lab.split()), f'{f}: test not from the deleted label')
            check('RGBA(255, 204, 0, 1)' in a['BorderColor'] and test in a['BorderColor'], f'{f}: yellow colour')
            if f != 'CL_DCAttachValue':
                check(re.sub(r'//[^\n]*\n', '', a['BorderColor']) == f'If({test}, RGBA(255, 204, 0, 1), {b["BorderColor"]})', f'{f}: colour formula')
        for p in ('BorderColor', 'BorderThickness'):
            v = re.sub(r'//[^\n]*', '', a[p]); check(v.count('(') == v.count(')'), f'{f}.{p} brackets')
cl = rd(N['ChildLegalScreen']['CL_DCAttachValue'])['BorderColor']
check('Not(IsBlank(Parent.Error)), Color.Red' in cl and 'Parent.BorderColor)' in cl, 'VTT box keeps its error border')
# media numbers
am = rd(N['RequesDetailScreen']['Add_media_icon'])['OnSelect']
check(am.count('"0000"') == 3 and all(f'RequestNumber: Right(Text(Year(Today())), 2) & "-" & Text({k}, "0000")' in am
      for k in ('varNextReqSeq', 'varNextReqSeq + 1', 'varNextReqSeq + 2')), 'request numbers changed')
check(all(f'CD_MediaNumber: rn & "-" & Text({k}, "00")' in am for k in ('n0', 'n0 + 1', 'n0 + 2')), 'Add_media_icon: 2 digits')
check('Value(Mid(lastMed, Len(rn) + 2))' in am and 'Right(lastMed, 4)' not in am, 'Add_media_icon: last number read')
cv = rd(N['ChildValidScreen']['CV_BtnSaveArchive'])['OnSelect']
check('Value(Mid(lastMed, Len(rn) + 2)), 0)) + 1, "00")' in cv and 'Right(lastMed, 4)' not in cv, 'CV_BtnSaveArchive: 2 digits')
for t in (am, cv):
    v = re.sub(r'//[^\n]*', '', t); check(v.count('(') == v.count(')'), 'brackets')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
