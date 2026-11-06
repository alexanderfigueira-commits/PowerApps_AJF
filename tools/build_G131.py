#!/usr/bin/env python3
"""FINAL142 on FINAL141: PrintVideoDetailScreen.PVD_Val20 (contract case) is 30 high, like PPD_Val16 (Photo) and PPoD_Val25 (Podcast) already are, so "Case 1 - framework / direct service contract" wraps on two lines
instead of being cut. The column below it (PVD_Val21 ...) follows (chained Y), so the media row grows by 15: row height 202 -> 217 (TemplateSize, row rule, gallery height); rows per page stay 2."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV1', 'newV2'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'PrintVideoDetailScreen'
app.set(S, 'PVD_Val20', 'Height', '30', expect='15')
app.set(S, 'PVD_Gallery', 'TemplateSize', '217', expect='202')
app.set(S, 'PVD_RowRule', 'Y', '216', expect='201')
t = app.rule(S, 'PVD_Gallery', 'Height'); assert t.count('202 * Min(') == 1
app.set(S, 'PVD_Gallery', 'Height', t.replace('202 * Min(', '217 * Min('), expect=t)
assert (740 - int(app.rule(S, 'PVD_Gallery', 'Y'))) // 217 == 2
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL142 built')
