#!/usr/bin/env python3
"""FINAL84 on FINAL83: the six new Yes/No columns of AV-CD-Mediafiles are saved by Save Media and read back when a media item is opened:
  FrameworkContractSigned <- varDocFramework (CL_ChkFramework)      SpecificContractSigned <- varDocSpecific (CL_ChkSpecific)
  OfferProvided           <- varDocOffer (CL_ChkOffer)              ModelRelease           <- varChildModelRelease (CL_ChkModel)
  PreexistingRights       <- varChildPreexisting (CL_ChkPreexisting) SubtitlesProvided     <- varChildSubtitlesProvided (CL_ChkSubtitles)
The embedded schema of the data source (References/DataSources.json) gets the six columns (boolean; internal name = display name, as for
NoThirdPartyRights), so the formulas compile before the connection is refreshed in Studio."""
import datetime, json, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG73', 'newG74'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
COLS = ['FrameworkContractSigned', 'SpecificContractSigned', 'OfferProvided', 'ModelRelease', 'PreexistingRights', 'SubtitlesProvided']
# ---- 1. embedded schema ----
dp = f'{NEW}/References/DataSources.json'
raw = open(dp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); txt = raw.decode('utf-8-sig')
d = json.loads(txt)
ds = [x for x in d['DataSources'] if x.get('Name') == 'AV-CD-Mediafiles'][0]
key, meta = next(iter(ds['DataEntityMetadataJson'].items()))
m = json.loads(meta)
props = m['schema']['items']['properties']
tmpl = props['NoThirdPartyRights']
for c in COLS:
    assert c not in props
    p = json.loads(json.dumps(tmpl)); p['title'] = c; props[c] = p
fmt = m['schema']['items']['x-ms-displayFormat']
for lst in ('propertiesDisplayOrder', 'propertiesCompactDisplayOrder', 'propertiesTabularDisplayOrder'):
    L = fmt[lst]
    at = L.index('{Attachments}') if '{Attachments}' in L else len(L)
    L[at:at] = COLS
ds['DataEntityMetadataJson'][key] = json.dumps(m, separators=(',', ':'), ensure_ascii=False)
for c in COLS: ds['ConnectedDataSourceInfoNameMapping'][c] = c
indent = 2 if '\n  "' in txt else None
out = json.dumps(d, ensure_ascii=False, indent=indent, separators=(',', ': ') if indent else (',', ':'))
if '\r\n' in txt: out = out.replace('\n', '\r\n')
open(dp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out)
# ---- 2. formulas ----
app = App(NEW)
RS, CV = 'RequesDetailScreen', 'ChildValidScreen'
def edit(screen, ctl, prop, fn, label):
    t = app.rule(screen, ctl, prop); n = fn(t)
    if n == t: sys.exit('! no change: ' + label)
    app.set(screen, ctl, prop, n, expect=t); print('ok', label)
SAVE = ('NoThirdPartyRights: varChildNoThirdParty,\r\n            FrameworkContractSigned: varDocFramework,\r\n            SpecificContractSigned: varDocSpecific,\r\n'
        '            OfferProvided: varDocOffer,\r\n            ModelRelease: varChildModelRelease,\r\n            PreexistingRights: varChildPreexisting,\r\n'
        '            SubtitlesProvided: varChildSubtitlesProvided,')
def save(t):
    a = 'NoThirdPartyRights: varChildNoThirdParty,'
    assert t.count(a) == 2, t.count(a)           # the media list record and the SharePoint Patch
    return t.replace(a, SAVE)
edit(CV, 'CV_BtnSaveArchive', 'OnSelect', save, 'Save Media (list record + Patch)')
def load_rows(t):
    m = re.search(r'PreexistingProvided: Coalesce\(\s*PreexistingRightsProvided,\s*false\s*\)', t)
    assert m
    add = ',\r\n' + ',\r\n'.join(f'                {c}: Coalesce({c}, false)' for c in COLS)
    return t[:m.end()] + add + t[m.end():]
edit(RS, None, 'OnVisible', load_rows, 'media list load')
def open_row(t):
    n = t
    n, k1 = re.subn(r'Set\(varDocFramework, (Coalesce\(varCurrentRequest\.Status\.Value, ""\) in \[[^\]]*\])\);', r'Set(varDocFramework, Coalesce(ThisItem.FrameworkContractSigned, false) Or (\1));', n)
    n, k2 = re.subn(r'Set\(varDocSpecific, (Coalesce\(varCurrentRequest\.Status\.Value, ""\) in \[[^\]]*\])\);', r'Set(varDocSpecific, Coalesce(ThisItem.SpecificContractSigned, false) Or (\1));', n)
    n, k3 = re.subn(r'Set\(varDocOffer, false\);', 'Set(varDocOffer, Coalesce(ThisItem.OfferProvided, false));', n)
    n, k4 = re.subn(r'Set\(varChildModelRelease, Coalesce\(ThisItem\.ModelReleaseProvided, false\)\);', 'Set(varChildModelRelease, Coalesce(ThisItem.ModelRelease, false) Or Coalesce(ThisItem.ModelReleaseProvided, false));', n)
    n, k5 = re.subn(r'Set\(varChildPreexisting, Coalesce\(ThisItem\.PreexistingProvided, false\)\);', 'Set(varChildPreexisting, Coalesce(ThisItem.PreexistingRights, false) Or Coalesce(ThisItem.PreexistingProvided, false));', n)
    n, k6 = re.subn(r'(Set\(varChildPreexistingProvided, Coalesce\(ThisItem\.PreexistingProvided, false\)\);)', r'\1\r\nSet(varChildSubtitlesProvided, Coalesce(ThisItem.SubtitlesProvided, false));', n)
    assert (k1, k2, k3, k4, k5, k6) == (1, 1, 1, 1, 1, 1), (k1, k2, k3, k4, k5, k6)
    return n
edit(RS, 'DOA_List1RowBadge_8', 'OnSelect', open_row, 'open media row')
RESET = 'Set(varChildPhotographer, "");'
edit('App', None, 'OnStart', lambda t: t.replace(RESET, RESET + ' Set(varChildSubtitlesProvided, false);', 1), 'App reset')
edit(RS, 'addMediaItem', 'OnSelect', lambda t: t.replace(RESET, RESET + ' Set(varChildSubtitlesProvided, false);', 1), 'new media reset')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL84 built')
