#!/usr/bin/env python3
"""Checks for FINAL13 against FINAL12: EN/Clip defaults, Export detail pages (one readable file per page,
Legal & Docs + file names, pager, PDF buttons), Export list paging."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL13-export-pages.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL12-coassignee-yellow.msapp'
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
N = {s: {c['Name']: c for c in walk(t)} for s, t in new.items()}
O = {s: {c['Name']: c for c in walk(t)} for s, t in old.items()}
SCREENS = ['ChildInfoScreen', 'HomePrintScreen', 'PrintVideoDetailScreen', 'PrintPhotoDetailScreen', 'PrintPodcastDetailScreen']
bal = lambda t: (lambda v: v.count('(') == v.count(')') and v.count('{') == v.count('}'))(re.sub(r'//[^\n]*', '', t))
check(nref == oref, 'data sources changed')
check(all(json.dumps(new[s], sort_keys=True) == json.dumps(old[s], sort_keys=True) for s in new if s not in SCREENS), 'another screen changed')
# ---- A
ci = {n: [p for p in set(rd(c)) | set(rd(O['ChildInfoScreen'][n])) if rd(c).get(p) != rd(O['ChildInfoScreen'][n]).get(p)] for n, c in N['ChildInfoScreen'].items()}
check({k: v for k, v in ci.items() if v} == {'ChildInfoScreen': ['OnVisible']} and set(N['ChildInfoScreen']) == set(O['ChildInfoScreen']), 'ChildInfoScreen: only OnVisible changed')
ov = rd(new['ChildInfoScreen'])['OnVisible']
check('Set(varChildLanguageVersions, "EN")' in ov and 'Set(varChildProductType, "Clip")' in ov and 'Not(varRequestorLocked)' in ov and bal(ov), 'EN / Clip stored')
# ---- B
for S, P, avail in (('PrintVideoDetailScreen', 'PVD', 520), ('PrintPhotoDetailScreen', 'PPD', 520), ('PrintPodcastDetailScreen', 'PPoD', 472)):
    n = N[S]; G = n[f'{P}_Gallery']
    kids = {c['Name']: c for c in G['Children'] if c['Template']['Name'] == 'label'}
    vals = {k: rd(c) for k, c in kids.items() if '_Val' in k}
    check(all(v.get('AutoHeight') == 'true' for v in vals.values()), f'{S}: every value grows with its text')
    check(all(float(v['X']) + float(v['Width']) <= 1302 for v in vals.values()), f'{S}: values inside the page width')
    alltext = ' '.join(v['Text'] for v in vals.values())
    for key in ('ContractCase,', 'ContractCase1Sub', 'NoThirdPartyRights', 'ModelReleaseProvided', 'MusicUsed', 'MusicLicenseProvided', 'PreexistingRightsProvided'):
        check(key in alltext, f'{S}: Legal item {key}')
    check('ThisItem.Attachments' in alltext and 'DisplayName' in alltext, f'{S}: attached file names')
    check('Legal & Documents' in ' '.join(rd(c)['Text'] for k, c in kids.items() if '_Sec' in k), f'{S}: Legal & Documents section')
    check('more media file' not in json.dumps(new[S]) and 'one printed page holds' not in json.dumps(new[S]), f'{S}: old per-page cut-off text gone')
    gr = rd(G)
    check(gr['Items'].rstrip().endswith('LastN(FirstN(colPrintReqMedia, Min(Max(Coalesce(locPrintPage, 1), 1), CountRows(colPrintReqMedia))), 1)') and gr['TemplateSize'] == gr['Height'] == str(avail), f'{S}: one file per page')
    check(rd(kids[f'{P}_RowRule'] if f'{P}_RowRule' in kids else n[f'{P}_RowRule'])['Y'] == str(avail - 1), f'{S}: row rule at the page bottom')
    for nm in ('PagePrev', 'PageNext', 'BtnPdfAll'):
        check(f'{P}_{nm}' in n, f'{S}: {nm} exists')
    check('PDF(' in rd(n[f'{P}_BtnPrint'])['OnSelect'] and 'Print()' not in rd(n[f'{P}_BtnPrint'])['OnSelect'], f'{S}: PDF this file')
    ra = rd(n[f'{P}_BtnPdfAll'])['OnSelect']
    check('Sequence(CountRows(colPrintReqMedia))' in ra and 'Download(PDF(' in ra and 'locPrintPage: 1' in ra, f'{S}: PDF all files')
    check('File ' in rd(n[f'{P}_More'])['Text'], f'{S}: page label')
    check('locPrintPage: 1' in rd(new[S])['OnVisible'], f'{S}: starts on file 1')
    check(all(rd(n[f'{P}_HdrVal{i}'])['Height'] == '34' for i in range(7)), f'{S}: header values wrap')
    # references and brackets
    for c in walk(new[S]):
        for r in c['Rules']:
            t = re.sub(r'//[^\n]*', '', r['InvariantScript'])
            if not bal(t):
                check(False, f'{S}.{c["Name"]}.{r["Property"]} brackets')
            for m in re.finditer(rf'\b({P}_[A-Za-z]+\d*)\.(?:Y|Height|Visible)\b', t):
                if m[1] not in n:
                    check(False, f'{S}.{c["Name"]}: missing {m[1]}')
    # columns: no two values of different columns share an X band
    xs = sorted({(float(v['X']), float(v['X']) + float(v['Width'])) for k, v in vals.items() if float(v['Width']) < 400})
    check(all(a[1] <= b[0] for a, b in zip(xs, xs[1:])), f'{S}: three columns do not overlap')
# ---- C
hp = N['HomePrintScreen']
gi, gh = rd(hp['HP_Gallery'])['Items'], rd(hp['HP_Gallery'])['Height']
check('LastN(FirstN(rows, pg * 8)' in gi and 'locHPPage' in gi and bal(gi), 'list: 8 per page')
check('Max(52, 52 *' in gh and bal(gh), 'list: gallery height follows the page')
check('locHPPage: 1' in rd(new['HomePrintScreen'])['OnVisible'], 'list: starts on page 1')
check('Download(PDF(HomePrintScreen))' in rd(hp['HP_BtnDownload'])['OnSelect'] and 'Not(locHPPrinting)' in rd(hp['HP_BtnDownload'])['Visible'], 'list: PDF this page')
check('Sequence(pages)' in rd(hp['HP_BtnDownloadAll'])['OnSelect'] and bal(rd(hp['HP_BtnDownloadAll'])['OnSelect']), 'list: PDF all pages')
check(all(k in hp for k in ('HP_PagePrev', 'HP_PageNext', 'HP_PageLbl')), 'list: pager exists')
filters = ['HP_BtnAllMedia', 'HP_BtnPhoto', 'HP_BtnVideo', 'HP_BtnPodcast', 'HP_BtnStatusAll', 'HP_BtnStatusDraft', 'HP_BtnStatusProcessing', 'HP_BtnStatusPending', 'HP_BtnStatusApproved', 'HP_BtnStatusRejected', 'HP_BtnClear']
check(all(rd(hp[f])['OnSelect'].startswith('UpdateContext({locHPPage: 1});') for f in filters), 'list: filters go back to page 1')
check(float(rd(hp['HP_Gallery'])['Y']) + 52 * 8 <= float(rd(hp['HP_Footer'])['Y']), 'list: 8 rows fit above the footer')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
