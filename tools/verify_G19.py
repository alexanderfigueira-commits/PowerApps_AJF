#!/usr/bin/env python3
"""Checks for FINAL29: the uploaded FINAL_2 + only the changes the user chose."""
import json, re, sys, zipfile
PKG = sys.argv[1]
UP = sys.argv[2]   # the uploaded FINAL_2
F28 = sys.argv[3] if len(sys.argv) > 3 else 'msapp-versions/AV-CD-FINAL28-legal-cleanup.msapp'
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
            ref[f] = z.read(i).decode('utf-8-sig')
    return js, ref


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


def flat(js):
    return {(s, c['Name']): {r['Property']: r['InvariantScript'] for r in c['Rules'] if r['Property'] != 'ZIndex'} for s, t in js.items() for c in walk(t)}


def bal(t):
    v = re.sub(r'(?m)^\s*//[^\n]*', '', t); v = re.sub(r'"[^"\n]*"', '""', v)
    return v.count('(') == v.count(')') and v.count('{') == v.count('}')


new, nref = load(PKG); up, uref = load(UP); f28, _ = load(F28)
n, u, f = flat(new), flat(up), flat(f28)
# not chosen -> exactly as in the upload
for scr in ('HomePrintScreen', 'PrintVideoDetailScreen', 'PrintPhotoDetailScreen', 'PrintPodcastDetailScreen', 'RequestManagementScreen'):
    check({k: v for k, v in n.items() if k[0] == scr} == {k: v for k, v in u.items() if k[0] == scr}, f'{scr} equals the upload')
check(not any(re.search(r'NNew|locNewNotes|ReadOn', json.dumps(v)) for k, v in n.items()), 'no notes-read pieces left')
check(('RequesDetailScreen', 'NT_ReadStatus') not in n, 'NT_ReadStatus gone')
for k in (('RequesDetailScreen', 'DOA_List1RowBadge_7'), ('RequesDetailScreen', 'NT_BtnAdd')):
    check(n[k] == u[k], f'{k[1]} as in the upload')
check(not any(re.search(r'DocFramework: |SubtitlesProvided: ', v.get('OnSelect', '') + v.get('OnVisible', '')) for k, v in n.items() if k[0] in ('ChildValidScreen', 'RequesDetailScreen')), 'Legal answers not saved or loaded')
sch = nref['References/DataSources.json']
check(not any(c in sch for c in ('"DocFramework"', '"SubtitlesProvided"', '"DocSpecific"', '"DocOffer"')), 'Legal columns not in the schema')
check('"CoAssignee"' in sch and '"ArchivedOnly"' in sch, 'CoAssignee and ArchivedOnly in the schema')
# chosen -> as in FINAL28
for k in (('ReviewScreen', 'RV_Assignee'), ('ReviewScreen', 'RV_ArchiveOnly'), ('RequesDetailScreen', 'RS_Archive'), ('RequesDetailScreen', 'Add_media_icon'), ('RequesDetailScreen', 'RS_Owner'),
          ('RequesDetailScreen', 'RS_Contractor'), ('RequesDetailScreen', 'RS_CRowBadge'), ('ChildMetaScreen', 'CM_ShootDate'), ('ChildMetaScreen', 'CM_Producer'), ('ChildMetaScreen', 'CM_EpisodeNumber'),
          ('ChildValidScreen', 'CV_OverallStatus'), ('ChildValidScreen', 'CV_BtnRefresh'), ('ChildInfoScreen', 'ChildInfoScreen')):
    check(n.get(k) == f.get(k), f'{k[1]} as in FINAL28')
sv = n[('ChildValidScreen', 'CV_BtnSaveArchive')]['OnSelect']
check('PublicationChannel' not in sv and 'ScriptShotlist: varChildScript' in sv, 'save: no PublicationChannel, ScriptShotlist saved')
check('ModelRelease:' not in sv and 'Preexisting:' not in sv, 'ModelRelease / Preexisting not saved')
check(all(bal(r) for v in n.values() for r in v.values()), 'all rules balanced')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for x in fails:
    print('  FAIL', x)
sys.exit(1 if fails else 0)
