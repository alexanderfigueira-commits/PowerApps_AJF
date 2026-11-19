#!/usr/bin/env python3
"""FINAL86 on FINAL85: CL_DCAttach.Update compiled with errors in FINAL83-85 (the extra With / Coalesce(LookUp(...), varAttachRecord) / Filter(Ungroup(..))
broke the typing of rec.Attachments: 'specified column is not accessible', 'LookUp has invalid arguments', 'DisplayName isn't valid'). Back to the
formula of FINAL82 (typed from varAttachRecord, as when it compiled) with the one safe fix kept: the Id of a new episode visual is looked up by the name
it is saved under (f.pre & f.Name), not the bare name."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG75', 'newG76'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
good = App('newG72').rule('ChildLegalScreen', 'CL_DCAttach', 'Update')     # FINAL82: the version that compiled
old = 'Id: Coalesce(LookUp(varAttachRecord.Attachments, DisplayName = f.Name).Id, f.pre & f.Name),'
assert good.count(old) == 1
fixed = good.replace(old, 'Id: Coalesce(LookUp(varAttachRecord.Attachments, DisplayName = f.pre & f.Name).Id, f.pre & f.Name),')
app = App(NEW)
app.set('ChildLegalScreen', 'CL_DCAttach', 'Update', fixed)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL86 built')
