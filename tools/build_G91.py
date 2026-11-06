#!/usr/bin/env python3
"""FINAL101 on TEST_4: Legal screen: the hint paragraph under the title is deleted (the form moves up into its place) and the attachment tooltip tells that a file can be clicked to download;
RequesDetailScreen: SaveButton (save draft) moves to X=463, Y=73."""
import datetime, os, re, shutil
from payaml import App, find
from jio import jwrite
SRC, NEW = 'newJ1', 'newJ2'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
L = 'ChildLegalScreen'
# delete CL_AttachHint (JSON + YAML)
doc = app.doc(L); tp = doc['TopParent']
n0 = len(tp['Children']); tp['Children'] = [c for c in tp['Children'] if c['Name'] != 'CL_AttachHint']; assert n0 - len(tp['Children']) == 1
yp = f'{NEW}/Src/{L}.pa.yaml'
Y = open(yp, encoding='utf-8').read().split('\n')
i = [k for k, l in enumerate(Y) if l.rstrip('\r') == '      - CL_AttachHint:']; assert len(i) == 1
i = i[0]; j = i + 1
while j < len(Y) and (Y[j].strip() == '' or len(Y[j]) - len(Y[j].lstrip()) > 6): j += 1
del Y[i:j]; open(yp, 'w', encoding='utf-8').write('\n'.join(Y))
# the space it took goes to the form (it ended at Y=190 + 65)
old = app.rule(L, 'CL_FormAttach', 'Y'); assert old == 'If(IsBlank(varAttachRecord), 278, 250)'
app.set(L, 'CL_FormAttach', 'Y', 'If(IsBlank(varAttachRecord), 222, 194)', expect=old)
app.set(L, 'CL_AttachNeedSave', 'Y', '194', expect='260')
# attachment tooltip
app.set(L, 'CL_DCAttachValue', 'Tooltip',
        '"Click on an attached file to open or download it" & If(Self.DisplayMode = DisplayMode.View, " (view mode: files can be downloaded, not changed)", "")',
        expect='Parent.DisplayName')
# save draft button
R = 'RequesDetailScreen'
app.set(R, 'SaveButton', 'X', '463', expect='1196')
app.set(R, 'SaveButton', 'Y', '73', expect='460')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL101 built')
