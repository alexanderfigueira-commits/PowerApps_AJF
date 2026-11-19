#!/usr/bin/env python3
"""FINAL173 on FINAL172. Studio listed 8 delegation warnings, all on the read-backs added in FINAL165-171: LookUp(..., ID = savedMedia.ID) (3 in Save Media) and
LookUp(..., ID = savedReq.ID) (1 in Submit). savedMedia / savedReq are With-records; a property of a With-record in a delegated condition is flagged, a plain variable is not.
Save Media has just done Set(varCurrentChildSPId, savedMedia.ID) and Submit Set(varCurrentRequest, savedReq), so the LookUps use those."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV34', 'newV35'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))

t = app.rule('ChildValidScreen', 'CV_BtnSaveArchive', 'OnSelect')
assert t.count('ID = savedMedia.ID') == 3
i_set = t.index('Set(varCurrentChildSPId, savedMedia.ID);')
assert all(m.start() > i_set for m in re.finditer(r'ID = savedMedia\.ID', t))      # all three come after the Set
app.set('ChildValidScreen', 'CV_BtnSaveArchive', 'OnSelect', t.replace('ID = savedMedia.ID', 'ID = varCurrentChildSPId'), expect=t)

t = app.rule('RequesDetailScreen', 'RS_BtnSubmitRequest', 'OnSelect')
assert t.count('ID = savedReq.ID') == 1
assert t.index('Set(varCurrentRequest, savedReq);') < t.index('ID = savedReq.ID')
app.set('RequesDetailScreen', 'RS_BtnSubmitRequest', 'OnSelect', t.replace('ID = savedReq.ID', 'ID = varCurrentRequest.ID'), expect=t)

app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL173 built')
