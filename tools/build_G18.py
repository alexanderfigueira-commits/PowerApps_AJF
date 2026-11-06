#!/usr/bin/env python3
"""FINAL28 on FINAL27: the Legal answers ModelRelease ("persons appear") and Preexisting ("pre-existing material used") are not
relevant and are removed as stored data.

* no longer stored in / read from AV-CD-Mediafiles (second tolerant save, media list record, request loader, media row select,
  template copy); the warning names only the four columns that remain;
* the two Export rows (Persons appear / Pre-existing material used) are deleted from the three print pages and the rows below move up;
* the two properties are removed from the cached SharePoint schema.
The Legal tab keeps its checkboxes for the "forms provided" / "annex provided" follow-ups (those columns already existed): when a media
file is reopened the "persons appear" / "pre-existing" ticks follow from those answers.
"""
import datetime, json, os, re, shutil, sys
from collections import Counter
from payaml import App, find, CTL_RE, _indent
from jio import jwrite

SRC, NEW = 'newG17', 'newG18'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)


def ysrc(s):
    return os.path.join(NEW, 'Src', f'{s}.pa.yaml')


def sub_once(text, old, new, what):
    if text.count(old) != 1:
        sys.exit(f'! {what}: {text.count(old)} matches')
    return text.replace(old, new)


# ---------------------------------------------------------------- 1. CV_BtnSaveArchive
S, N = 'ChildValidScreen', 'CV_BtnSaveArchive'
t = app.rule(S, N, 'OnSelect')
n = t
n = re.sub(r'\r?\n *ModelRelease: varChildModelRelease,', '', n, count=1)
n = re.sub(r'\r?\n *Preexisting: varChildPreexisting,', '', n, count=1)
# second Patch: remaining four, last one without comma handled by regex on the list
n = sub_once(n, 'The Legal tab confirmations are six Yes/No columns', 'The Legal tab confirmations are Yes/No columns', 'comment')
n = sub_once(n, 'Check that the Yes/No columns ModelRelease, Preexisting, SubtitlesProvided,', 'Check that the Yes/No columns SubtitlesProvided,', 'warning')
n = sub_once(n, 'DocFramework, DocSpecific and DocOffer exist', 'DocFramework, DocSpecific and DocOffer exist', 'warning2')
# the two lines now left in the second Patch and the colArchives record
n2 = re.sub(r'\r?\n *ModelRelease: varChildModelRelease,?', '', n)
n2 = re.sub(r'\r?\n *Preexisting: varChildPreexisting,?', '', n2)
n = n2
if re.search(r'\bModelRelease\b|\bPreexisting\b', n):
    sys.exit('! CV_BtnSaveArchive still mentions the two columns')
if re.search(r'\{\s*SubtitlesProvided', n) is None and 'SubtitlesProvided: varChildSubtitlesProvided' not in n:
    sys.exit('! second Patch lost SubtitlesProvided')
app.set(S, N, 'OnSelect', n, expect=t)

# ---------------------------------------------------------------- 2. RequesDetailScreen loader + row select
RS = 'RequesDetailScreen'
for c, p in (('RS_CRowSelect', 'OnSelect'), (None, 'OnVisible')):
    t = app.rule(RS, c, p)
    n = t
    if c == 'RS_CRowSelect':
        n = sub_once(n, 'Set(varChildModelRelease, Coalesce(ThisItem.ModelRelease, false));',
                     'Set(varChildModelRelease, Coalesce(ThisItem.ModelReleaseProvided, false));', 'row select model')
        n = sub_once(n, 'Set(varChildPreexisting, Coalesce(ThisItem.Preexisting, false));',
                     'Set(varChildPreexisting, Coalesce(ThisItem.PreexistingProvided, false));', 'row select pre')
    else:
        n = re.sub(r'\r?\n *ModelRelease: Coalesce\(ModelRelease, false\),', '', n)
        n = re.sub(r'\r?\n *Preexisting: Coalesce\(Preexisting, false\),', '', n)
        if re.search(r'\bModelRelease\b|\bPreexisting\b', n):
            sys.exit('! OnVisible still mentions the two columns')
    app.set(RS, c, p, n, expect=t)

# ---------------------------------------------------------------- 3. ChildInfoScreen template copy (two places, same text)
CI = 'ChildInfoScreen'
yp = ysrc(CI)
y = open(yp, encoding='utf-8').read()
y2 = y.replace('Coalesce(varTplCandidate.ModelRelease, false) Or Coalesce(varTplCandidate.ModelReleaseProvided, false)',
               'Coalesce(varTplCandidate.ModelReleaseProvided, false)')
y2 = y2.replace('Coalesce(varTplCandidate.Preexisting, false) Or Coalesce(varTplCandidate.PreexistingRightsProvided, false)',
                'Coalesce(varTplCandidate.PreexistingRightsProvided, false)')
for ctl in ('CI_TplRowBg', 'CI_TplConfirmOK'):
    t = app.rule(CI, ctl, 'OnSelect')
    if t is None:
        continue
    n = t.replace('Coalesce(varTplCandidate.ModelRelease, false) Or Coalesce(varTplCandidate.ModelReleaseProvided, false)',
                  'Coalesce(varTplCandidate.ModelReleaseProvided, false)')
    n = n.replace('Coalesce(varTplCandidate.Preexisting, false) Or Coalesce(varTplCandidate.PreexistingRightsProvided, false)',
                  'Coalesce(varTplCandidate.PreexistingRightsProvided, false)')
    if n != t:
        app.set(CI, ctl, 'OnSelect', n, expect=t)
app.save()
y3 = open(yp, encoding='utf-8').read()
if re.search(r'varTplCandidate\.(ModelRelease|Preexisting)\b', y3):
    sys.exit('! ChildInfoScreen still reads the two columns')

# ---------------------------------------------------------------- 4. print pages: delete rows 50/51, re-chain
for scr, pre in (('PrintVideoDetailScreen', 'PVD'), ('PrintPhotoDetailScreen', 'PPD'), ('PrintPodcastDetailScreen', 'PPoD')):
    doc = app.doc(scr)
    tp = doc['TopParent']
    v50_y = app.rule(scr, f'{pre}_Val50', 'Y')
    if f'{pre}_Val5' in v50_y or ' + If(' not in v50_y:
        sys.exit(f'! {scr}: Val50 anchor changed: {v50_y}')
    # the row after the two (Val52 / Val53) was chained to Val51 -> chain it to what Val50 was chained to
    exp = f'{pre}_Val51.Y + If({pre}_Val51.Visible, {pre}_Val51.Height + 3, 0)'
    def walk0(c):
        yield c
        for k in c.get('Children', []):
            yield from walk0(k)
    fol = [c['Name'] for c in walk0(tp) if any(r['Property'] == 'Y' and r['InvariantScript'] == exp for r in c['Rules'])]
    if len(fol) != 1:
        sys.exit(f'! {scr}: {len(fol)} rows chained to Val51: {fol}')
    app.set(scr, fol[0], 'Y', v50_y, expect=exp)
    # section Y/visibility formulas that listed the two values
    def walk(c):
        yield c
        for k in c.get('Children', []):
            yield from walk(k)
    for c in walk(tp):
        if c['Name'] in (f'{pre}_Lbl50', f'{pre}_Val50', f'{pre}_Lbl51', f'{pre}_Val51'):
            continue
        for r in c['Rules']:
            s_ = r['InvariantScript']
            if re.search(rf'{pre}_Val5[01]\b', s_):
                n_ = re.sub(rf',\s*{pre}_Val50\.Y \+ If\({pre}_Val50\.Visible, {pre}_Val50\.Height \+ 3, 0\)', '', s_)
                n_ = re.sub(rf',\s*{pre}_Val51\.Y \+ If\({pre}_Val51\.Visible, {pre}_Val51\.Height \+ 3, 0\)', '', n_)
                n_ = re.sub(rf'\s*Or\s*{pre}_Val5[01]\.Visible', '', n_)
                if re.search(rf'{pre}_Val5[01]\b', n_):
                    sys.exit(f'! {scr}.{c["Name"]}.{r["Property"]}: reference to Val50/51 left: {n_[:200]}')
                app.set(scr, c['Name'], r['Property'], n_, expect=s_)
    app.save()
    # delete the four controls (JSON + YAML mirror)
    gone = {f'{pre}_Lbl50', f'{pre}_Val50', f'{pre}_Lbl51', f'{pre}_Val51'}
    def strip(node):
        node['Children'] = [k for k in node.get('Children', []) if k['Name'] not in gone]
        for k in node['Children']:
            strip(k)
    strip(tp)
    for g in [c for c in tp['Children'] if c.get('IsGroupControl')]:
        if gone & set(g.get('GroupedControlsKey', [])):
            g['GroupedControlsKey'] = [x for x in g['GroupedControlsKey'] if x not in gone]
    app.save()
    lines = open(ysrc(scr), encoding='utf-8').read().split('\n')
    for lab in sorted(gone):
        hit = [i for i, l in enumerate(lines) if CTL_RE.match(l) and CTL_RE.match(l).group(1) == lab]
        if len(hit) != 1:
            sys.exit(f'! {lab}: {len(hit)} YAML blocks')
        a = hit[0]; mi = _indent(lines[a]); b = len(lines)
        for i in range(a + 1, len(lines)):
            if lines[i].strip() and _indent(lines[i]) <= mi:
                b = i; break
        del lines[a:b]
    open(ysrc(scr), 'w', encoding='utf-8').write('\n'.join(lines))
app._json = {}

# ---------------------------------------------------------------- 5. cached schema
dsp = f'{NEW}/References/DataSources.json'
ds = json.load(open(dsp, encoding='utf-8'))
med = [x for x in ds['DataSources'] if x['Name'] == 'AV-CD-Mediafiles'][0]
mk = list(med['DataEntityMetadataJson'])[0]
meta = json.loads(med['DataEntityMetadataJson'][mk])
items = meta['schema']['items']
for col in ('ModelRelease', 'Preexisting'):
    if col not in items['properties']:
        sys.exit(f'! {col} not in the cached schema')
    del items['properties'][col]
    med['ConnectedDataSourceInfoNameMapping'].pop(col, None)
    for k in ('propertiesDisplayOrder', 'propertiesCompactDisplayOrder', 'propertiesTabularDisplayOrder'):
        lst = items['x-ms-displayFormat'][k]
        if col in lst:
            lst.remove(col)
med['DataEntityMetadataJson'][mk] = json.dumps(meta, separators=(',', ':'), ensure_ascii=False)
jwrite(ds, dsp)

# ---------------------------------------------------------------- control count + save time
def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)

app = App(NEW)
cnt = Counter(c['Template']['Name'] for s in app.map if s != 'App' for c in walk(app.doc(s)['TopParent']))
p = open(f'{NEW}/Properties.json', encoding='utf-8').read()
for k, v in cnt.items():
    p = re.sub(rf'("{k}": )\d+', rf'\g<1>{v}', p, count=1)
open(f'{NEW}/Properties.json', 'w', encoding='utf-8', newline='').write(p)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL28 built')
