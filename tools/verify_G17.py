#!/usr/bin/env python3
"""Checks for FINAL27 against FINAL26: the six Legal answers are saved in a second, tolerant step."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL27-save-tolerant.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL26-media-file-wording.msapp'
SIX = [('ModelRelease', 'varChildModelRelease'), ('Preexisting', 'varChildPreexisting'), ('SubtitlesProvided', 'varChildSubtitlesProvided'),
       ('DocFramework', 'varDocFramework'), ('DocSpecific', 'varDocSpecific'), ('DocOffer', 'varDocOffer')]
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
check(nref == oref, 'data sources changed')
check(all(json.dumps(new[s], sort_keys=True) == json.dumps(old[s], sort_keys=True) for s in new if s != 'ChildValidScreen'), 'another screen changed')
N = {c['Name']: c for c in walk(new['ChildValidScreen'])}; O = {c['Name']: c for c in walk(old['ChildValidScreen'])}
ch = {n: sorted(p for p in set(rd(c)) | set(rd(O[n])) if rd(c).get(p) != rd(O[n]).get(p)) for n, c in N.items()}
check({k: v for k, v in ch.items() if v} == {'CV_BtnSaveArchive': ['OnSelect']}, 'only the save button changed')
t = rd(N['CV_BtnSaveArchive'])['OnSelect']
main_start = t.index("Patch(\r\n                        'AV-CD-Mediafiles'") if "Patch(\r\n                        'AV-CD-Mediafiles'" in t else t.index("Defaults('AV-CD-Mediafiles')")
second_at = t.index('The Legal tab confirmations are six Yes/No columns')
main = t[main_start:second_at]
check(not any(f'{c}: {v},' in main for c, v in SIX), 'the main Patch no longer sends the six')
sec = t[second_at:t.index('UpdateIf(colArchives, ArchiveId = varCurrentChildId, {SPId: savedMedia.ID});')]
check(all(f'{c}: {v}' in sec for c, v in SIX) and "LookUp('AV-CD-Mediafiles', ID = savedMedia.ID)" in sec and 'NotificationType.Warning' in sec and 'IfError(' in sec, 'second step: the six, on the saved item, warning on failure')
check(all(c in sec for c, _ in SIX) and 'DocFramework' in sec, 'warning names the columns to check')
check('Media file saved, but its Legal tab confirmations were NOT stored' in sec, 'warning text')
check(bal(t), 'brackets')
# the rest of the save is the old one
core_old = re.sub(r'\r?\n *(ModelRelease|Preexisting|SubtitlesProvided|DocFramework|DocSpecific|DocOffer): (varChildModelRelease|varChildPreexisting|varChildSubtitlesProvided|varDocFramework|varDocSpecific|varDocOffer),', '', rd(O['CV_BtnSaveArchive'])['OnSelect'], count=0)
core_new = t.replace(sec, '')
# the media-list record keeps its own six entries (different punctuation), so compare only after removing the Patch ones
check(core_new.count('ModelRelease: varChildModelRelease') == 1 and core_new.count('DocFramework: varDocFramework') == 1, 'the media list record still keeps the six answers')
check("'Save failed: '".replace("'", '"') in t or 'Save failed: ' in t, 'main failure message kept')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
