#!/usr/bin/env python3
"""Checks for FINAL21 against FINAL20: the six Legal tab answers are stored (columns, save, reload, open, new, template copy, Export pages)."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL21-legal-columns.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL20-producers-kept.msapp'
COLS = ['ModelRelease', 'Preexisting', 'SubtitlesProvided', 'DocFramework', 'DocSpecific', 'DocOffer']
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, ds = {}, None
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f == 'References/DataSources.json':
            ds = json.loads(z.read(i).decode('utf-8-sig'))
    return js, ds


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


def bal(t):
    v = re.sub(r'(?m)^\s*//[^\n]*', '', t); v = re.sub(r'"[^"\n]*"', '""', v)
    return v.count('(') == v.count(')') and v.count('{') == v.count('}')


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
new, nds = load(PKG); old, ods = load(BASE)
N = {s: {c['Name']: c for c in walk(t)} for s, t in new.items()}; O = {s: {c['Name']: c for c in walk(t)} for s, t in old.items()}
# schema
med = lambda ds: [x for x in ds['DataSources'] if x['Name'] == 'AV-CD-Mediafiles'][0]
mp = lambda ds: json.loads(list(med(ds)['DataEntityMetadataJson'].values())[0])['schema']['items']['properties']
a, b = mp(nds), mp(ods)
check(set(a) - set(b) == set(COLS) and set(b) <= set(a) and all(a[k] == b[k] for k in b), 'schema: only the six columns added')
check(all(a[c]['type'] == 'boolean' and a[c]['x-ms-permission'] == 'read-write' for c in COLS), 'six Yes/No columns')
check(all(med(nds)['ConnectedDataSourceInfoNameMapping'].get(c) == c for c in COLS), 'name mapping')
check([x for x in nds['DataSources'] if x['Name'] != 'AV-CD-Mediafiles'] == [x for x in ods['DataSources'] if x['Name'] != 'AV-CD-Mediafiles'], 'other data sources changed')
# scope
added = {s: set(N[s]) - set(O[s]) for s in N}
exp_added = {'PrintVideoDetailScreen': {f'PVD_{k}{n}' for k in ('Lbl', 'Val') for n in (50, 51, 52, 53)},
             'PrintPhotoDetailScreen': {f'PPD_{k}{n}' for k in ('Lbl', 'Val') for n in (50, 51, 53)},
             'PrintPodcastDetailScreen': {f'PPoD_{k}{n}' for k in ('Lbl', 'Val') for n in (50, 51, 53)}}
check({s: v for s, v in added.items() if v} == exp_added and all(set(O[s]) <= set(N[s]) for s in O), 'controls added: only the Export page rows')
ch = {(s, n): sorted(p for p in set(rd(c)) | set(rd(O[s][n])) if rd(c).get(p) != rd(O[s][n]).get(p)) for s in N for n, c in N[s].items() if n in O[s]}
got = {k for k, v in ch.items() if v}
want = {('ChildValidScreen', 'CV_BtnSaveArchive'), ('RequesDetailScreen', 'RequesDetailScreen'), ('RequesDetailScreen', 'RS_CRowSelect'), ('RequesDetailScreen', 'Add_media_icon'),
        ('ChildMetaScreen', 'ChildMetaScreen'), ('ChildInfoScreen', 'CI_TplRowBg'), ('ChildInfoScreen', 'CI_TplConfirmOK')} | {(s, f'{p}_Sec41') for s, p in (('PrintVideoDetailScreen', 'PVD'), ('PrintPhotoDetailScreen', 'PPD'), ('PrintPodcastDetailScreen', 'PPoD'))}
check(got == want, f'changed: extra {sorted(got - want)} missing {sorted(want - got)}')
# save
sv = rd(N['ChildValidScreen']['CV_BtnSaveArchive'])['OnSelect']
check(all(f'{c}: {v},' in sv for c, v in (('ModelRelease', 'varChildModelRelease'), ('Preexisting', 'varChildPreexisting'), ('SubtitlesProvided', 'varChildSubtitlesProvided'), ('DocFramework', 'varDocFramework'), ('DocSpecific', 'varDocSpecific'), ('DocOffer', 'varDocOffer'))), 'Patch writes the six')
check('SubtitlesProvided: varChildSubtitlesProvided,' in sv and 'DocOffer: varDocOffer\n    })' in re.sub(r'\r?\n', '\n', sv) and bal(sv), 'media list record keeps them; brackets')
# reload / open / new / meta / template
ov = rd(N['RequesDetailScreen']['RequesDetailScreen'])['OnVisible']
check('ModelRelease: false' not in ov and 'Preexisting: false' not in ov and ov.count('Coalesce(ModelRelease, false)') == 1 and ov.count('Coalesce(Preexisting, false)') == 1
      and all(f'{c}: Coalesce({c}, false)' in ov for c in ('SubtitlesProvided', 'DocFramework', 'DocSpecific', 'DocOffer')) and bal(ov), 'reload reads all six')
rs = rd(N['RequesDetailScreen']['RS_CRowSelect'])['OnSelect']
check(all(x in rs for x in ('Set(varDocFramework, Coalesce(ThisItem.DocFramework, false))', 'Set(varDocSpecific, Coalesce(ThisItem.DocSpecific, false))', 'Set(varDocOffer, Coalesce(ThisItem.DocOffer, false))', 'Set(varChildSubtitlesProvided, Coalesce(ThisItem.SubtitlesProvided, false))', 'Set(varChildModelRelease, Coalesce(ThisItem.ModelRelease, false))', 'Set(varChildPreexisting, Coalesce(ThisItem.Preexisting, false))')), 'opening a row loads all six')
check('Set(varChildSubtitlesProvided, false);' in rd(N['RequesDetailScreen']['Add_media_icon'])['OnSelect'], 'new item: subtitles cleared (others already were)')
check('varChildSubtitlesProvided' not in rd(N['ChildMetaScreen']['ChildMetaScreen'])['OnVisible'] and 'varVideoMetaChildId' not in rd(N['ChildMetaScreen']['ChildMetaScreen'])['OnVisible'], 'Metadata tab no longer resets subtitles')
for c in ('CI_TplRowBg', 'CI_TplConfirmOK'):
    t = rd(N['ChildInfoScreen'][c])['OnSelect']
    check('Coalesce(varTplCandidate.ModelRelease, false) Or Coalesce(varTplCandidate.ModelReleaseProvided, false)' in t and 'Coalesce(varTplCandidate.Preexisting, false) Or Coalesce(varTplCandidate.PreexistingRightsProvided, false)' in t and bal(t), f'template copy {c}')
# export pages
for S, P, last in (('PrintVideoDetailScreen', 'PVD', 26), ('PrintPhotoDetailScreen', 'PPD', 37), ('PrintPodcastDetailScreen', 'PPoD', 37)):
    n = N[S]
    check(all(rd(n[f'{P}_Val{k}'])['AutoHeight'] == 'true' and float(rd(n[f'{P}_Val{k}'])['X']) == 1054 for k in exp_added[S] and [int(re.sub(r'\D', '', x)) for x in exp_added[S] if 'Val' in x]), f'{S}: new rows grow with their text, in the Legal column')
    ys = rd(n[f'{P}_Sec41'])['Y']
    check(all(f'{P}_Val{k}.Y' in ys for k in (50, 51, 53)) and bal(ys), f'{S}: full-width block starts under the new rows')
    check('ThisItem.ModelRelease' in rd(n[f'{P}_Val50'])['Text'] and 'ThisItem.Preexisting' in rd(n[f'{P}_Val51'])['Text'] and 'ThisItem.DocFramework' in rd(n[f'{P}_Val53'])['Text'], f'{S}: values')
check('ThisItem.SubtitlesProvided' in rd(N['PrintVideoDetailScreen']['PVD_Val52'])['Text'], 'Video page: subtitles')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
