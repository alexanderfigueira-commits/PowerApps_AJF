#!/usr/bin/env python3
"""FINAL208 on FINAL207. PDF page header all left-aligned (line 1: title · request · ID · type · status, line 2: creator · DG ·
submitted · assignee); footer centred on the page."""
import datetime, os, re, shutil
from payaml import App, find, block_span
SRC, NEW = 'newV69', 'newV70'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)
def delete(scr, name):
    tp = app.doc(scr)['TopParent']; g = [c for c in tp['Children'] if any(k['Name'] == name for k in c.get('Children', []))][0]
    g['Children'] = [c for c in g['Children'] if c['Name'] != name]; app.save()
    yf = f'{NEW}/Src/{scr}.pa.yaml'; L = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
    s, e = block_span(L, name); del L[s:e]; open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(L))
for scr, p, typ in (('PrintVideoDetailScreen', 'PVD', 'Video'), ('PrintPodcastDetailScreen', 'PPoD', 'Podcast'), ('PrintPhotoDetailScreen', 'PPD', 'Photo')):
    setp(scr, f'{p}_PgHdrTitle', 'Width', '1278')
    setp(scr, f'{p}_PgHdrTitle', 'Text', (
        'With(\n    {t: Coalesce(varPrintRequest.RequestTitle, "Untitled request")\n'
        '        & "     ·     Request " & Coalesce(varPrintRequest.RequestNumber, "—") & "  ·  ID " & Text(varPrintRequest.ID)\n'
        f'        & "  ·  {typ}  ·  " & Coalesce(varPrintRequest.Status.Value, "Draft")}},\n'
        '    If(Len(t) > 120, Left(t, 119) & "…", t)\n)'))
    delete(scr, f'{p}_PgHdrRef')
    setp(scr, f'{p}_PgFooter', 'Align', 'Align.Center')
p_ = f'{NEW}/Properties.json'
raw = open(p_, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
t = re.sub(r'("label"\s*:\s*)(\d+)', lambda mm: mm.group(1) + str(int(mm.group(2)) - 3), t, count=1)
open(p_, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL208 built')
