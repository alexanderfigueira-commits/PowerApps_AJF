#!/usr/bin/env python3
"""FINAL21 on FINAL20: the Legal tab answers that had no column are stored.

New Yes/No columns on AV-CD-Mediafiles (added to the app's cached schema; they must exist in the SharePoint list):
  ModelRelease        persons appear (a model release is needed)
  Preexisting         pre-existing material is used
  SubtitlesProvided   subtitles are provided (Video)
  DocFramework        Case 1: signed framework contract confirmed
  DocSpecific         Case 1: signed specific contract confirmed
  DocOffer            Case 1: offer / quotation confirmed
* CV_BtnSaveArchive: written in the Patch and kept in the media list record;
* RequesDetailScreen: read back on reload (ModelRelease / Preexisting were hard-coded false), loaded by RS_CRowSelect,
  SubtitlesProvided cleared for a new item;
* ChildMetaScreen.OnVisible: no longer resets SubtitlesProvided (it would wipe the loaded value);
* ChildInfoScreen (template copy, two places): the template's real ModelRelease / Preexisting are used, as well as the old
  "provided" values;
* Export detail pages: Legal & Documents shows them too.
"""
import datetime, json, os, re, shutil, sys
from collections import Counter
from payaml import App, find
from hp_common import Builder
from jio import jwrite

SRC, NEW = 'newG10', 'newG11'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
COLS = ['ModelRelease', 'Preexisting', 'SubtitlesProvided', 'DocFramework', 'DocSpecific', 'DocOffer']


def put(s, n, p, v, cat='Design'):
    c = find(app.doc(s)['TopParent'], n)
    if not [r for r in c['Rules'] if r['Property'] == p]:
        c['Rules'].append({'Property': p, 'Category': cat, 'InvariantScript': v, 'RuleProviderType': 'Unknown'})
        c.setdefault('ControlPropertyState', []).append(p)
    app.set(s, n, p, v)


def edit(screen, ctl, prop, fn):
    t = app.rule(screen, ctl, prop)
    n = fn(t)
    if n == t:
        sys.exit(f'! {screen}.{ctl}.{prop}: no change made')
    app.set(screen, ctl, prop, n, expect=t)


def sub1(t, old, new, count=1):
    if t.count(old) != count:
        sys.exit(f'! {old!r}: {t.count(old)} found, expected {count}')
    return t.replace(old, new)


# ---------------------------------------------------------------- 1. schema
dsp = f'{NEW}/References/DataSources.json'
ds = json.load(open(dsp, encoding='utf-8'))
med = [x for x in ds['DataSources'] if x['Name'] == 'AV-CD-Mediafiles'][0]
mk = list(med['DataEntityMetadataJson'])[0]
meta = json.loads(med['DataEntityMetadataJson'][mk])
props = meta['schema']['items']['properties']
if any(c in props for c in COLS):
    sys.exit('! one of the columns is already in the schema')
yesno = [v for k, v in props.items() if v.get('type') == 'boolean' and not k.startswith('{') and v.get('x-ms-permission') == 'read-write'][0]
for c in COLS:
    props[c] = dict(yesno, title=c)
fmt = meta['schema']['items']['x-ms-displayFormat']
for k in ('propertiesDisplayOrder', 'propertiesCompactDisplayOrder', 'propertiesTabularDisplayOrder'):
    lst = fmt[k]
    at = lst.index('{Attachments}') if '{Attachments}' in lst else len(lst)
    lst[at:at] = COLS
med['DataEntityMetadataJson'][mk] = json.dumps(meta, separators=(',', ':'), ensure_ascii=False)
med['ConnectedDataSourceInfoNameMapping'].update({c: c for c in COLS})
jwrite(ds, dsp)

# ---------------------------------------------------------------- 2. save
def save(t):
    # the record kept in the media list
    t = sub1(t, 'PreexistingProvided: varChildPreexistingProvided\r\n    })',
             'PreexistingProvided: varChildPreexistingProvided,\r\n        SubtitlesProvided: varChildSubtitlesProvided,\r\n'
             '        DocFramework: varDocFramework,\r\n        DocSpecific: varDocSpecific,\r\n        DocOffer: varDocOffer\r\n    })')
    # the Patch to SharePoint
    m = re.search(r'(\r?\n)( *)PreexistingRightsProvided: varChildPreexistingProvided,', t)
    if not m or len(re.findall(r'PreexistingRightsProvided: varChildPreexistingProvided,', t)) != 1:
        sys.exit('! save: Patch anchor')
    add = ''.join(f'{m.group(1)}{m.group(2)}{c}: {v},' for c, v in (
        ('ModelRelease', 'varChildModelRelease'), ('Preexisting', 'varChildPreexisting'), ('SubtitlesProvided', 'varChildSubtitlesProvided'),
        ('DocFramework', 'varDocFramework'), ('DocSpecific', 'varDocSpecific'), ('DocOffer', 'varDocOffer')))
    return t[:m.end()] + add + t[m.end():]


edit('ChildValidScreen', 'CV_BtnSaveArchive', 'OnSelect', save)

# ---------------------------------------------------------------- 3. reload / open / new
def reload(t):
    t = sub1(t, 'ModelRelease: false,', 'ModelRelease: Coalesce(ModelRelease, false),')
    t = sub1(t, 'Preexisting: false,', 'Preexisting: Coalesce(Preexisting, false),')
    m = re.search(r'(PreexistingProvided: Coalesce\(\s*PreexistingRightsProvided,\s*false\s*\))', t)
    if not m:
        sys.exit('! reload anchor')
    nl = '\r\n' + ' ' * 24 if '\r\n' in t else '\n' + ' ' * 24
    add = ',' + ','.join(f'{nl}{c}: Coalesce({c}, false)' for c in ('SubtitlesProvided', 'DocFramework', 'DocSpecific', 'DocOffer'))
    return t[:m.end()] + add + t[m.end():]


edit('RequesDetailScreen', None, 'OnVisible', reload)
edit('RequesDetailScreen', 'RS_CRowSelect', 'OnSelect', lambda t: sub1(
    t, 'Set(varDocFramework, false); Set(varDocSpecific, false); Set(varDocOffer, false);',
    'Set(varDocFramework, Coalesce(ThisItem.DocFramework, false)); Set(varDocSpecific, Coalesce(ThisItem.DocSpecific, false)); '
    'Set(varDocOffer, Coalesce(ThisItem.DocOffer, false));\nSet(varChildSubtitlesProvided, Coalesce(ThisItem.SubtitlesProvided, false));'))
edit('RequesDetailScreen', 'Add_media_icon', 'OnSelect', lambda t: sub1(
    t, 'Set(varChildPreexisting, false);', 'Set(varChildPreexisting, false);\r\nSet(varChildSubtitlesProvided, false);'))
edit('ChildMetaScreen', None, 'OnVisible', lambda t: sub1(
    t, 'If(varChildMediaType = "Video" And varVideoMetaChildId <> varCurrentChildId,\n    Set(varVideoMetaChildId, varCurrentChildId);\n    Set(varChildSubtitlesProvided, false));\n', ''))
# template copy (two places): the template's own answers
edit('ChildInfoScreen', 'CI_TplRowBg', 'OnSelect', lambda t: sub1(
    sub1(t, 'Set(varChildModelRelease, Coalesce(varTplCandidate.ModelReleaseProvided, false));',
         'Set(varChildModelRelease, Coalesce(varTplCandidate.ModelRelease, false) Or Coalesce(varTplCandidate.ModelReleaseProvided, false));'),
    'Set(varChildPreexisting, Coalesce(varTplCandidate.PreexistingRightsProvided, false));',
    'Set(varChildPreexisting, Coalesce(varTplCandidate.Preexisting, false) Or Coalesce(varTplCandidate.PreexistingRightsProvided, false));'))
edit('ChildInfoScreen', 'CI_TplConfirmOK', 'OnSelect', lambda t: sub1(
    sub1(t, 'Set(varChildModelRelease, Coalesce(varTplCandidate.ModelReleaseProvided, false));',
         'Set(varChildModelRelease, Coalesce(varTplCandidate.ModelRelease, false) Or Coalesce(varTplCandidate.ModelReleaseProvided, false));'),
    'Set(varChildPreexisting, Coalesce(varTplCandidate.PreexistingRightsProvided, false));',
    'Set(varChildPreexisting, Coalesce(varTplCandidate.Preexisting, false) Or Coalesce(varTplCandidate.PreexistingRightsProvided, false));'))
app.save()

# ---------------------------------------------------------------- 4. Export pages: Legal & Documents shows them
NEWROWS = {  # number: (label, value formula, video only)
    50: ('Persons appear (model release)', 'If(ThisItem.ModelRelease, "✅  Yes", "⛔  No")', False),
    51: ('Pre-existing material used', 'If(ThisItem.Preexisting, "✅  Yes", "⛔  No")', False),
    52: ('Subtitles provided', 'If(ThisItem.SubtitlesProvided, "✅  Yes", "⛔  No")', True),
    53: ('Contract confirmations', 'If(Left(Coalesce(First(ThisItem.ContractCase).Value, ""), 6) = "Case 1", "Framework " & If(ThisItem.DocFramework, "✅", "⛔") '
                                  '& "  ·  Specific " & If(ThisItem.DocSpecific, "✅", "⛔") & "  ·  Offer " & If(ThisItem.DocOffer, "✅", "⛔"), "Not required")', False),
}
for S, P, last in (('PrintVideoDetailScreen', 'PVD', 26), ('PrintPhotoDetailScreen', 'PPD', 37), ('PrintPodcastDetailScreen', 'PPoD', 37)):
    G = f'{P}_Gallery'
    nm = lambda kind, n: f'{P}_{kind}{n}'
    rows = {n: v for n, v in NEWROWS.items() if not v[2] or P == 'PVD'}
    b = Builder(app, S)
    for n, (lab, val, _) in rows.items():
        b.clone(nm('Lbl', n), S, nm('Lbl', 1), {'Text': f'"{lab}"'}, parent=G)
        b.clone(nm('Val', n), S, nm('Val', 1), {'Text': val, 'Color': 'RGBA(30, 34, 44, 1)'}, parent=G)
    b.save()
    prev = nm('Val', last)
    for n in rows:
        c, lb = nm('Val', n), nm('Lbl', n)
        app.set(S, c, 'X', '1054'); app.set(S, c, 'Width', '240'); app.set(S, c, 'AutoHeight', 'true'); app.set(S, c, 'VerticalAlign', 'VerticalAlign.Top')
        app.set(S, c, 'Y', f'{prev}.Y + If({prev}.Visible, {prev}.Height + 3, 0)'); put(S, c, 'Visible', 'true')
        app.set(S, lb, 'X', '872'); app.set(S, lb, 'Width', '180'); app.set(S, lb, 'Y', f'{c}.Y'); app.set(S, lb, 'VerticalAlign', 'VerticalAlign.Top')
        put(S, lb, 'Visible', f'{c}.Visible')
        prev = c
    # the full-width block starts under the tallest column: include the new values
    tx = nm('Sec', 41)
    y = app.rule(S, tx, 'Y')
    vals = list(dict.fromkeys(re.findall(rf'\b({P}_Val\d+)\.Y', y))) + [nm('Val', n) for n in rows]
    bottom = 'Max(' + ', '.join(f'{v}.Y + If({v}.Visible, {v}.Height + 3, 0)' for v in vals) + ') + 6'
    app.set(S, tx, 'Y', bottom)
    app.save()

# ---------------------------------------------------------------- control count + save time
def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


cnt = Counter(c['Template']['Name'] for s in app.map if s != 'App' for c in walk(app.doc(s)['TopParent']))
p = open(f'{NEW}/Properties.json', encoding='utf-8').read()
for k, v in cnt.items():
    p = re.sub(rf'("{k}": )\d+', rf'\g<1>{v}', p, count=1)
open(f'{NEW}/Properties.json', 'w', encoding='utf-8', newline='').write(p)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL21 built')
