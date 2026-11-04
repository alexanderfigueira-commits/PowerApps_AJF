#!/usr/bin/env python3
"""FINAL188 on FINAL187. FB-12: 'Legal & Supporting documents shared via FTP' option on Legal & Docs.
New Yes/No column DocsSharedViaFTP on AV-CD-Mediafiles (var varDocsViaFTP). When ticked, the attachment-based validations
(legal annexes attached, music licence provided) pass without uploads; the confirmation ticks stay mandatory."""
import datetime, json, os, re, shutil
from payaml import App
from hp_common import Builder
SRC, NEW = 'newV49', 'newV50'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
COL = 'DocsSharedViaFTP'
# ---- embedded schema (as build_G74)
dp = f'{NEW}/References/DataSources.json'
raw = open(dp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); txt = raw.decode('utf-8-sig')
d = json.loads(txt)
ds = [x for x in d['DataSources'] if x.get('Name') == 'AV-CD-Mediafiles'][0]
key, meta = next(iter(ds['DataEntityMetadataJson'].items()))
m = json.loads(meta); props = m['schema']['items']['properties']
assert COL not in props
p = json.loads(json.dumps(props['NoThirdPartyRights'])); p['title'] = COL; props[COL] = p
fmt = m['schema']['items']['x-ms-displayFormat']
for lst in ('propertiesDisplayOrder', 'propertiesCompactDisplayOrder', 'propertiesTabularDisplayOrder'):
    L = fmt[lst]; at = L.index('{Attachments}') if '{Attachments}' in L else len(L); L[at:at] = [COL]
ds['DataEntityMetadataJson'][key] = json.dumps(m, separators=(',', ':'), ensure_ascii=False)
ds['ConnectedDataSourceInfoNameMapping'][COL] = COL
indent = 2 if '\n  "' in txt else None
out = json.dumps(d, ensure_ascii=False, indent=indent, separators=(',', ': ') if indent else (',', ':'))
if '\r\n' in txt: out = out.replace('\n', '\r\n')
open(dp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out)

app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def edit(screen, ctl, prop, fn):
    t = app.rule(screen, ctl, prop); n = fn(t)
    assert n != t, (screen, ctl, prop)
    app.set(screen, ctl, prop, n, expect=t)
def sub(t, old, new, n=1):
    assert t.count(old) == n, (old, t.count(old)); return t.replace(old, new)
RS, CV, CL, CI = 'RequesDetailScreen', 'ChildValidScreen', 'ChildLegalScreen', 'ChildInfoScreen'
# ---- resets / loads
A, B = 'Set(varChildSubtitlesProvided, false);', 'Set(varChildSubtitlesProvided, false); Set(varDocsViaFTP, false);'
doc = app.doc('App'); rl = [r for r in doc['TopParent']['Rules'] if r['Property'] == 'OnStart'][0]
rl['InvariantScript'] = sub(rl['InvariantScript'], A, B)
yf = f'{NEW}/Src/App.pa.yaml'; y = open(yf, encoding='utf-8', newline='').read()
open(yf, 'w', encoding='utf-8', newline='').write(sub(y, A, B))
edit(RS, 'addMediaItem', 'OnSelect', lambda t: sub(t, 'Set(varChildSubtitlesProvided, false);', 'Set(varChildSubtitlesProvided, false); Set(varDocsViaFTP, false);', 2))
edit(RS, 'DOA_List1RowBadge_8', 'OnSelect', lambda t: sub(t, 'Set(varChildSubtitlesProvided, Coalesce(ThisItem.SubtitlesProvided, false));',
     'Set(varChildSubtitlesProvided, Coalesce(ThisItem.SubtitlesProvided, false));\nSet(varDocsViaFTP, Coalesce(ThisItem.DocsSharedViaFTP, false));'))
edit(RS, None, 'OnVisible', lambda t: sub(t, 'SubtitlesProvided: Coalesce(SubtitlesProvided, false)', 'SubtitlesProvided: Coalesce(SubtitlesProvided, false),\n                        DocsSharedViaFTP: Coalesce(DocsSharedViaFTP, false)'))
for c in ('CI_TplRowUse', 'CI_TplConfirmOK'):
    edit(CI, c, 'OnSelect', lambda t: re.sub(r'([ \t]*)Set\(varChildSubtitlesProvided, Coalesce\(varTplCandidate\.SubtitlesProvided, false\)\);',
        lambda mm: mm.group(0) + '\n' + mm.group(1) + 'Set(varDocsViaFTP, Coalesce(varTplCandidate.DocsSharedViaFTP, false));', t))
# ---- save + audit
def save(t):
    t = sub(t, 'SubtitlesProvided: varChildSubtitlesProvided,', 'SubtitlesProvided: varChildSubtitlesProvided,\n                          DocsSharedViaFTP: varDocsViaFTP,', 2)
    a = '{n: "subtitles provided", bad: Coalesce(varChildSubtitlesProvided, false) And Not(Coalesce(chk.SubtitlesProvided, false))},'
    return sub(t, a, a + '\n                                              {n: "documents via FTP", bad: Coalesce(varDocsViaFTP, false) <> Coalesce(chk.DocsSharedViaFTP, false)},')
edit(CV, 'CV_BtnSaveArchive', 'OnSelect', save)
# ---- validations (screen OnVisible + refresh button)
def val(t):
    t = sub(t, 'Pass: CountRows(CL_DCAttachValue.Attachments) > 0 Or', 'Pass: varDocsViaFTP Or CountRows(CL_DCAttachValue.Attachments) > 0 Or')
    t = t.replace('Pass: Not(varChildMusicUsed) Or varChildMusicLicenceProvided,', 'Pass: Not(varChildMusicUsed) Or varChildMusicLicenceProvided Or varDocsViaFTP,')
    assert 'Or varDocsViaFTP,' in t
    return t
edit(CV, None, 'OnVisible', val)
edit(CV, 'CV_BtnRefresh', 'OnSelect', val)
# ---- Legal screen: checkbox + template size
edit(CL, 'CL_Gallery', 'TemplateSize', lambda t: sub(t, '+ If(varChildMediaType = "Video", 32 + If(varChildSubtitlesProvided, 120, 0), 0)',
     '+ If(varChildMediaType = "Video", 32 + If(varChildSubtitlesProvided, 120, 0), 0)\n+ 40'))
b = Builder(app, CL)
b.clone('CL_ChkDocsFTP', CL, 'CL_ChkSubtitles', {
    'Text': '"The Legal & Supporting documents marked on the list above will be shared via FTP together with the media file(s)"',
    'Default': 'Coalesce(varDocsViaFTP, false)', 'OnCheck': 'Set(varDocsViaFTP, true)', 'OnUncheck': 'Set(varDocsViaFTP, false)',
    'Visible': 'true', 'Height': '32',
    'Y': 'CL_ChkSubtitles.Y + If(CL_ChkSubtitles.Visible, CL_ChkSubtitles.Height, 0) + If(CL_LblVTT.Visible, CL_LblVTT.Height, 0) + 8'},
    parent='CL_Gallery')
b.save()
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL188 built')
