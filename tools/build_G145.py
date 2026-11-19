#!/usr/bin/env python3
"""FINAL156 on FINAL155: PPD_ChkCompact (PrintPhotoDetailScreen) and PPoD_ChkCompact (PrintPodcastDetailScreen) deleted.
With PVD_ChkCompact gone since FINAL145 nothing sets varCompactPrint any more: the print screens always use the full-size layout
(the one the published player needs). The If(locPrinting And Coalesce(varCompactPrint, false), ...) geometry formulas stay as they are."""
import datetime, os, re, shutil
from payaml import App, find, block_span
SRC, NEW = 'newV15', 'newV16'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
for screen, name in (('PrintPhotoDetailScreen', 'PPD_ChkCompact'), ('PrintPodcastDetailScreen', 'PPoD_ChkCompact')):
    tp = app.doc(screen)['TopParent']
    node = find(tp, name)
    assert node and node['Parent'] == screen and not node.get('Children'), name
    assert not node.get('Group') and not any(name in (g.get('GroupedControlsKey') or []) for g in tp['Children'] if g.get('IsGroupControl')), name
    n0 = len(tp['Children']); tp['Children'] = [c for c in tp['Children'] if c['Name'] != name]; assert n0 - len(tp['Children']) == 1
app.save()
for screen, name in (('PrintPhotoDetailScreen', 'PPD_ChkCompact'), ('PrintPodcastDetailScreen', 'PPoD_ChkCompact')):
    yp = f'{NEW}/Src/{screen}.pa.yaml'
    L = open(yp, encoding='utf-8', newline='').read().replace('\r\n', '\n').replace('\r', '\n').split('\n')
    s, e = block_span(L, name)
    del L[s:e]
    open(yp, 'w', encoding='utf-8', newline='').write('\n'.join(L))
for f in os.listdir(f'{NEW}/Src'):
    assert 'ChkCompact' not in open(f'{NEW}/Src/{f}', encoding='utf-8').read(), f
import glob
for f in glob.glob(f'{NEW}/Controls/*.json'):
    assert 'ChkCompact' not in open(f, encoding='utf-8').read(), f
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL156 built')
