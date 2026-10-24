#!/usr/bin/env python3
"""FINAL145 on TEST_11 (= FINAL144 + the user's HomePrintScreen edits, kept as they are).
 * PVD_ChkCompact (PrintVideoDetailScreen) deleted.
 * Validations tab: the Video "Language" and "Type of product" rows (and a Podcast's language) read what the dropdown shows
   (CI_Language / CI_ProductType / CM_Language .Selected) when the stored variable is still empty, and the displayed default
   is stored on every entry to the Info / Validations screens, locked or not."""
import datetime, os, re, shutil
from payaml import App, find
SRC, NEW = 'newT11', 'newV5'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

# ---- 1. PVD_ChkCompact -------------------------------------------------------------------------------------------
S = 'PrintVideoDetailScreen'
tp = app.doc(S)['TopParent']
node = find(tp, 'PVD_ChkCompact'); assert node and node['Parent'] == S and not node.get('Children')
n0 = len(tp['Children']); tp['Children'] = [c for c in tp['Children'] if c['Name'] != 'PVD_ChkCompact']; assert n0 - len(tp['Children']) == 1
app.save()
yp = f'{NEW}/Src/{S}.pa.yaml'; Y = open(yp, encoding='utf-8').read().split('\n')
i = [k for k, l in enumerate(Y) if l.rstrip('\r') == '      - PVD_ChkCompact:']; assert len(i) == 1
i = i[0]; j = i + 1
while j < len(Y) and (Y[j].strip() == '' or len(Y[j]) - len(Y[j].lstrip()) > 6): j += 1
del Y[i:j]; open(yp, 'w', encoding='utf-8', newline='').write('\n'.join(Y))
assert 'PVD_ChkCompact' not in open(yp, encoding='utf-8').read()
for f in os.listdir(f'{NEW}/Src'):
    assert 'PVD_ChkCompact' not in open(f'{NEW}/Src/{f}', encoding='utf-8').read(), f

# ---- 2. validation / defaults ------------------------------------------------------------------------------------
LANG_OLD = 'Coalesce(varChildLanguageVersions, If(varChildMediaType = "Video", "EN", "")) <> ""'
LANG_NEW = ('Coalesce(varChildLanguageVersions, If(varChildMediaType = "Video", Coalesce(CI_Language.Selected.Value, "EN"), '
            'CM_Language.Selected.Value), "") <> ""')
PROD_OLD = 'Coalesce(varChildProductType, varChildProductType1, "Clip") <> ""'
PROD_NEW = 'Coalesce(varChildProductType, varChildProductType1, CI_ProductType.Selected.Value, "Clip") <> ""'
LOCK_OLD = 'varChildMediaType = "Video" And Not(varRequestorLocked),'
LOCK_NEW = 'varChildMediaType = "Video",'

def edit(screen, control, prop, pairs):
    t = app.rule(screen, control, prop); u = t
    for old, new, cnt in pairs:
        assert u.count(old) == cnt, (screen, control, prop, old, u.count(old))
        u = u.replace(old, new)
    app.set(screen, control, prop, u, expect=t)

V = 'ChildValidScreen'
edit(V, None, 'OnVisible', [(LANG_OLD, LANG_NEW, 1), (PROD_OLD, PROD_NEW, 1), (LOCK_OLD, LOCK_NEW, 1)])
edit(V, 'CV_BtnRefresh', 'OnSelect', [(LANG_OLD, LANG_NEW, 1), (PROD_OLD, PROD_NEW, 1), (LOCK_OLD, LOCK_NEW, 1)])
edit(V, 'CV_BtnSaveArchive', 'OnSelect', [(LOCK_OLD, LOCK_NEW, 1)])
edit('ChildInfoScreen', None, 'OnVisible', [(LOCK_OLD, LOCK_NEW, 1)])
app.save()

h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL145 built')
