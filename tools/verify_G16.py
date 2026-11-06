#!/usr/bin/env python3
"""Checks for FINAL26 against FINAL25: checklist wording "media file" instead of "archive"."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL26-media-file-wording.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL25-yellow-podcast-producer.msapp'
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


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
new, nref = load(PKG); old, oref = load(BASE)
check(nref == oref, 'data sources changed')
check(all(json.dumps(new[s], sort_keys=True) == json.dumps(old[s], sort_keys=True) for s in new if s != 'ChildValidScreen'), 'another screen changed')
N = {c['Name']: c for c in walk(new['ChildValidScreen'])}; O = {c['Name']: c for c in walk(old['ChildValidScreen'])}
check(set(N) == set(O), 'controls added or removed')
ch = {n: sorted(p for p in set(rd(c)) | set(rd(O[n])) if rd(c).get(p) != rd(O[n]).get(p)) for n, c in N.items()}
check({k: v for k, v in ch.items() if v} == {'ChildValidScreen': ['OnVisible'], 'CV_BtnRefresh': ['OnSelect'], 'CV_OverallStatus': ['Text']}, 'only the checklist definitions and the status line changed')
for nm, prop in (('ChildValidScreen', 'OnVisible'), ('CV_BtnRefresh', 'OnSelect')):
    t, o = rd(N[nm])[prop], rd(O[nm])[prop]
    check('Media file title is provided' in t and 'This media file cannot be submitted.' in t and 'on this media file (Photo only)' in t, f'{nm}: new wording')
    check(not re.search(r'Archive title is provided|This archive cannot|on this archive', t), f'{nm}: old wording gone')
    check(t.replace('Media file title is provided', 'Archive title is provided').replace('This media file cannot', 'This archive cannot').replace('on this media file (Photo only)', 'on this archive (Photo only)') == o, f'{nm}: nothing else changed')
    check(t.count('(Photo only)') == o.count('(Photo only)') and t.count('"New archive"') == o.count('"New archive"'), f'{nm}: filter markers and the "New archive" placeholder kept')
check('Press Save Media to add to your request.' in rd(N['CV_OverallStatus'])['Text'] and rd(N['CV_BtnSaveArchive'])['Text'].startswith('"Save Media'), 'status line names the real button')
check(rd(N['CV_ChecklistGallery'])['Items'] == rd(O['CV_ChecklistGallery'])['Items'], 'gallery filter untouched')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
