#!/usr/bin/env python3
"""FINAL114 on TEST_5 (FINAL113 stays on standby):
 1. a Video's Language and Type of product count as their displayed default (EN / Clip) everywhere: the dropdowns' Default is explicit, the Metadata language box shows EN too,
    the Validations rows accept the default, and the default is stored after the lock is recomputed (was stale at the head of the Validations OnVisible).
 2. the Requestor dashboard's shared-link Timer (DOA_DeepLinkTimer) lost all its rules in the Studio re-saves: it is rebuilt from the working one of the administrator dashboard."""
import datetime, os, re, shutil, sys
from payaml import App, find
from hp_common import Builder
from jio import jwrite
SRC, NEW = 'newN1', 'newN2'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
# ---------------------------------------------------------------- 1. defaults
app.set('ChildInfoScreen', 'CI_Language', 'Default', 'Coalesce(varChildLanguageVersions, "EN")', expect='varChildLanguageVersions')
app.set('ChildInfoScreen', 'CI_ProductType', 'Default', 'Coalesce(varChildProductType, varChildProductType1, "Clip")', expect='Coalesce(varChildProductType, varChildProductType1)')
old = 'If(IsBlank(varChildLanguageVersions) Or varChildLanguageVersions = "", Table(), Table({Value: varChildLanguageVersions}))'
new = 'If(IsBlank(varChildLanguageVersions) Or varChildLanguageVersions = "", If(varChildMediaType = "Video", Table({Value: "EN"}), Table()), Table({Value: varChildLanguageVersions}))'
app.set('ChildMetaScreen', 'CM_Language', 'DefaultSelectedItems', new, expect=old)
V = 'ChildValidScreen'
LANG_OLD = '(varChildMediaType <> "Video" And varChildMediaType <> "Podcast") Or (Not(IsBlank(varChildLanguageVersions)) And varChildLanguageVersions <> "")'
LANG_NEW = '(varChildMediaType <> "Video" And varChildMediaType <> "Podcast") Or Coalesce(varChildLanguageVersions, If(varChildMediaType = "Video", "EN", "")) <> ""'
PT_OLD = 'varChildMediaType <> "Video" Or (Not(IsBlank(Coalesce(varChildProductType, varChildProductType1))) And Coalesce(varChildProductType, varChildProductType1) <> "")'
PT_NEW = 'varChildMediaType <> "Video" Or Coalesce(varChildProductType, varChildProductType1, "Clip") <> ""'
STORE = ('// a Video\'s Language and Type of product dropdowns show EN / Clip while nothing is stored: store what is shown\n'
         'If(\n    varChildMediaType = "Video" And Not(varRequestorLocked),\n'
         '    If(Coalesce(varChildLanguageVersions, "") = "", Set(varChildLanguageVersions, Coalesce(CI_Language.Selected.Value, "EN")));\n'
         '    If(Coalesce(varChildProductType, varChildProductType1, "") = "", Set(varChildProductType, Coalesce(CI_ProductType.Selected.Value, "Clip")))\n);\n')
hits = {'lang': 0, 'pt': 0}
def scan(c, ctl):
    for r in c['Rules']:
        t = r['InvariantScript']
        if LANG_OLD in t or PT_OLD in t:
            eol = '\r\n' if '\r\n' in t else '\n'; n = t.replace('\r\n', '\n')
            hits['lang'] += n.count(LANG_OLD); hits['pt'] += n.count(PT_OLD)
            n = n.replace(LANG_OLD, LANG_NEW).replace(PT_OLD, PT_NEW)
            if r['Property'] == 'OnVisible' and ctl is None:
                # the default is stored once the lock is fresh (the store used to run first, with the previous screen's lock)
                assert n.startswith(STORE), 'OnVisible head'
                n = n[len(STORE):]
                anchor = 'Set(varNavArm, "");\n'
                assert n.count(anchor) == 1
                n = n.replace(anchor, anchor + STORE)
            app.set(V, ctl, r['Property'], n.replace('\n', eol), expect=t)
    for k in c.get('Children', []): scan(k, k['Name'])
scan(app.doc(V)['TopParent'], None)
assert hits['lang'] == hits['pt'] and hits['lang'] >= 2, hits
print('validation rows changed:', hits)
app.save()
# ---------------------------------------------------------------- 2. the Requestor dashboard's deep-link Timer
RQ, AD, TM = 'Dashboard-Ope-Requestor', 'Dashboard-Ope-Administrator', 'DOA_DeepLinkTimer_1'
dq = app.doc(RQ); tq = dq['TopParent']
n0 = len(tq['Children']); tq['Children'] = [c for c in tq['Children'] if c['Name'] != 'DOA_DeepLinkTimer']; assert n0 - len(tq['Children']) == 1
jwrite(dq, app.map[RQ])
yp = f'{NEW}/Src/{RQ}.pa.yaml'; Y = open(yp, encoding='utf-8').read().split('\n')
i = [k for k, l in enumerate(Y) if l.rstrip('\r') == '      - DOA_DeepLinkTimer:']; assert len(i) == 1
i = i[0]; j = i + 1
while j < len(Y) and (Y[j].strip() == '' or len(Y[j]) - len(Y[j].lstrip()) > 6): j += 1
del Y[i:j]; open(yp, 'w', encoding='utf-8').write('\n'.join(Y))
class NB(Builder):
    def grouped(self, tp): return set()
bq = NB(app, RQ); bq.clone('DOA_DeepLinkTimer', AD, TM, {}); bq.save()
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL114 built')
