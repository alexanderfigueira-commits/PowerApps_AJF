#!/usr/bin/env python3
"""Checks for FINAL20 against FINAL19: the Metadata tab no longer blanks Producer / Executive producer."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL20-producers-kept.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL19-script-shotlist.msapp'
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
N = {s: {c['Name']: c for c in walk(t)} for s, t in new.items()}; O = {s: {c['Name']: c for c in walk(t)} for s, t in old.items()}
check({s: set(N[s]) for s in N} == {s: set(O[s]) for s in O}, 'controls added or removed')
ch = {(s, n): sorted(p for p in set(rd(c)) | set(rd(O[s][n])) if rd(c).get(p) != rd(O[s][n]).get(p)) for s in N for n, c in N[s].items()}
check({k: v for k, v in ch.items() if v} == {('ChildMetaScreen', 'ChildMetaScreen'): ['OnVisible']}, 'only ChildMetaScreen.OnVisible changed')
nv, ov = rd(N['ChildMetaScreen']['ChildMetaScreen'])['OnVisible'], rd(O['ChildMetaScreen']['ChildMetaScreen'])['OnVisible']
check(not re.search(r'varChildProducer|varChildExecProducer|varPodMetaChildId', nv), 'no reset of Producer / Executive producer / Podcast guard left')
exp = ov.replace('    Set(varChildProducer, "");\n    Set(varChildExecProducer, "");\n    Set(varChildSubtitlesProvided, false));', '    Set(varChildSubtitlesProvided, false));')
exp = exp.replace('If(varChildMediaType = "Podcast" And varPodMetaChildId <> varCurrentChildId,\n    Set(varPodMetaChildId, varCurrentChildId);\n    Set(varChildProducer, "");\n    Set(varChildExecProducer, ""));\n', '')
check(nv == exp, 'only the producer resets removed')
check(nv.count('(') == nv.count(')'), 'brackets')
check('Set(varChildSubtitlesProvided, false)' in nv and 'varVideoMetaChildId' in nv and 'varAttachRecord' in nv and 'locShowEpisodeVisual' in nv, 'rest of OnVisible kept')
# a new item is still cleared, an opened one is still loaded
add = rd(N['RequesDetailScreen']['Add_media_icon'])['OnSelect']; sel = rd(N['RequesDetailScreen']['RS_CRowSelect'])['OnSelect']
check('Set(varChildExecProducer, "")' in add and 'Set(varChildProducer, "")' in add and 'Set(varChildProducerSel, Blank())' in add, 'new media file: producers cleared by Add_media_icon')
check('Set(varChildExecProducer, Coalesce(ThisItem.ExecProducer, ""))' in sel and 'Set(varChildProducerSel, ThisItem.Producer)' in sel and 'Set(varChildProducer, Concat(ThisItem.Producer, DisplayName, ", "))' in sel, 'opened media file: producers loaded from the item')
sv = rd(N['ChildValidScreen']['CV_BtnSaveArchive'])['OnSelect']
check('ExecProducerName: varChildExecProducer' in sv and 'Producer: If(IsBlank(varChildProducerSel)' in sv, 'save writes both')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
