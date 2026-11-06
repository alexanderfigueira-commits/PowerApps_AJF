#!/usr/bin/env python3
"""Checks for FINAL28 against FINAL27: ModelRelease and Preexisting are gone as stored data."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL28-legal-cleanup.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL27-save-tolerant.msapp'
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, ref, yml = {}, {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('References/'):
            ref[f] = z.read(i).decode('utf-8-sig')
        elif f.startswith('Src/'):
            yml[f] = z.read(i).decode('utf-8-sig')
    return js, ref, yml


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


def bal(t):
    v = re.sub(r'(?m)^\s*//[^\n]*', '', t); v = re.sub(r'"[^"\n]*"', '""', v)
    return v.count('(') == v.count(')') and v.count('{') == v.count('}')


BARE = re.compile(r'(?<![A-Za-z0-9_])(ModelRelease|Preexisting)(?![A-Za-z0-9_])')
new, nref, ny = load(PKG); old, oref, oy = load(BASE)
# 1. the two column names appear nowhere as columns: not in any rule, YAML mirror or schema
hits = [(s, c['Name'], r['Property']) for s, tp in new.items() for c in walk(tp) for r in c['Rules']
        if BARE.search(re.sub(r'varChild(ModelRelease|Preexisting)', '', r['InvariantScript']))]
check(not hits, f'a rule still mentions the two columns: {hits[:3]}')
yh = [f for f, t in ny.items() if BARE.search(re.sub(r'varChild(ModelRelease|Preexisting)', '', t))]
check(not yh, f'YAML mirror still mentions the two columns: {yh}')
check(not any(BARE.search(t) for t in nref.values()), 'cached schema still has the two columns')
check(all(BARE.search(t) for t in [oref['References/DataSources.json']]), 'sanity: FINAL27 had them in the schema')
# 2. the four remaining Legal columns are still saved
N = {c['Name']: c for c in walk(new['ChildValidScreen'])}
t = {r['Property']: r['InvariantScript'] for r in N['CV_BtnSaveArchive']['Rules']}['OnSelect']
sec = t[t.index('Legal tab confirmations'):t.index('UpdateIf(colArchives, ArchiveId = varCurrentChildId, {SPId: savedMedia.ID});')]
for c, v in (('SubtitlesProvided', 'varChildSubtitlesProvided'), ('DocFramework', 'varDocFramework'), ('DocSpecific', 'varDocSpecific'), ('DocOffer', 'varDocOffer')):
    check(f'{c}: {v}' in sec, f'second step still saves {c}')
check('NotificationType.Warning' in sec and 'IfError(' in sec and "LookUp('AV-CD-Mediafiles', ID = savedMedia.ID)" in sec, 'second step kept')
check('PreexistingRightsProvided: varChildPreexistingProvided' in t and 'ModelReleaseProvided: varChildModelReleaseProvided' in t, 'the Provided answers are still saved')
check(bal(t), 'save button brackets')
# 3. the Legal tab still works on the variables
L = {c['Name']: c for c in walk(new['ChildLegalScreen'])}
check('varChildModelRelease' in {r['Property']: r['InvariantScript'] for r in L['CL_ChkModel']['Rules']}['OnCheck'], 'Legal checkbox unchanged')
# 4. loader/row select read the Provided answers
rs = {c['Name']: c for c in walk(new['RequesDetailScreen'])}
sel = {r['Property']: r['InvariantScript'] for r in rs['RS_CRowSelect']['Rules']}['OnSelect']
check('Set(varChildModelRelease, Coalesce(ThisItem.ModelReleaseProvided, false))' in sel and 'Set(varChildPreexisting, Coalesce(ThisItem.PreexistingProvided, false))' in sel, 'row select derives the ticks from the Provided answers')
# 5. Export rows gone and nothing refers to them
for scr, pre in (('PrintVideoDetailScreen', 'PVD'), ('PrintPhotoDetailScreen', 'PPD'), ('PrintPodcastDetailScreen', 'PPoD')):
    names = {c['Name'] for c in walk(new[scr])}
    check(not names & {f'{pre}_Lbl50', f'{pre}_Val50', f'{pre}_Lbl51', f'{pre}_Val51'}, f'{scr}: rows deleted')
    check(not any(re.search(rf'{pre}_Val5[01]\b', r['InvariantScript']) for c in walk(new[scr]) for r in c['Rules']), f'{scr}: no reference to the deleted rows')
    check(not re.search(rf'{pre}_(Lbl|Val)5[01]\b', ny[f'Src/{scr}.pa.yaml']), f'{scr}: YAML mirror clean')
    check(len(names) == len({c['Name'] for c in walk(old[scr])}) - 4, f'{scr}: exactly 4 controls fewer')
    check(all(bal(r['InvariantScript']) for c in walk(new[scr]) for r in c['Rules']), f'{scr}: brackets')
# 6. nothing else changed
changed = [s for s in new if json.dumps(new[s], sort_keys=True) != json.dumps(old[s], sort_keys=True)]
check(set(changed) <= {'ChildValidScreen', 'RequesDetailScreen', 'ChildInfoScreen', 'PrintVideoDetailScreen', 'PrintPhotoDetailScreen', 'PrintPodcastDetailScreen'}, f'unexpected screens changed: {changed}')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
