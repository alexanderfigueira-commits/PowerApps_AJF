#!/usr/bin/env python3
"""FINAL159 on FINAL158: Studio reported 5 x "No type found for variable 'varChildPhotographerSel'" (App.OnStart, addMediaItem,
DOA_List1RowBadge_8, CI_TplRowBg, CI_TplConfirmOK). With the people picker gone, the only thing still setting that variable was
Set(varChildPhotographerSel, Blank()), which gives it no type. Nothing reads it any more, so those 5 statements are removed."""
import datetime, glob, json, os, re, shutil
from payaml import App
SRC, NEW = 'newV20', 'newV21'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
PAT = re.compile(r'Set\(varChildPhotographerSel, Blank\(\)\);[ \t]*(\r*\n[ \t]*)?')

def strip(t):
    return PAT.sub('', t)

todo = [('ChildInfoScreen', 'CI_TplRowBg', 'OnSelect'), ('ChildInfoScreen', 'CI_TplConfirmOK', 'OnSelect'),
        ('RequesDetailScreen', 'addMediaItem', 'OnSelect'), ('RequesDetailScreen', 'DOA_List1RowBadge_8', 'OnSelect')]
for screen, ctl, prop in todo:
    t = app.rule(screen, ctl, prop)
    assert len(PAT.findall(t)) == 1, (screen, ctl, prop)
    app.set(screen, ctl, prop, strip(t), expect=t)

# App.OnStart: its YAML is shaped differently (App: / Properties: / OnStart), so JSON and YAML are written here
tp = app.doc('App')['TopParent']
r = [x for x in tp['Rules'] if x['Property'] == 'OnStart'][0]
assert len(PAT.findall(r['InvariantScript'])) == 1
r['InvariantScript'] = strip(r['InvariantScript'])
app.save()
yp = f'{NEW}/Src/App.pa.yaml'
y = open(yp, encoding='utf-8', newline='').read()
assert len(PAT.findall(y)) == 1
open(yp, 'w', encoding='utf-8', newline='').write(strip(y))

for f in glob.glob(f'{NEW}/Controls/*.json') + glob.glob(f'{NEW}/Src/*.yaml'):
    assert 'varChildPhotographerSel' not in open(f, encoding='utf-8').read(), f
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL159 built')
