#!/usr/bin/env python3
"""FINAL191 on FINAL190. The leave pop-ups sit above every control of their screen (ZIndex), all five share one geometry,
and RS_BtnBackToList (Back to Request Management) opens the pop-up too."""
import datetime, os, re, shutil
from payaml import App, find
SRC, NEW = 'newV52', 'newV53'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
for scr, p in (('ChildInfoScreen', 'CI'), ('ChildMetaScreen', 'CM'), ('ChildLegalScreen', 'CL'), ('ChildValidScreen', 'CV'), ('RequesDetailScreen', 'RS')):
    tp = app.doc(scr)['TopParent']
    def z(n):
        v = [x for x in n['Rules'] if x['Property'] == 'ZIndex']
        return int(v[0]['InvariantScript']) if v else 0
    nodes = [c for c in tp['Children']]
    mx = max(z(c) for c in nodes if '_Leave' not in c['Name'])
    def deep(n):
        yield n
        for c in n.get('Children', []): yield from deep(c)
    mx = max(mx, max(z(n) for n in deep(tp) if '_Leave' not in n['Name']))
    for i, k in enumerate(['Shade', 'Panel', 'Text', 'Discard', 'Back', 'Save']):
        c = find(tp, f'{p}_Leave{k}')
        r = [x for x in c['Rules'] if x['Property'] == 'ZIndex'][0]
        r['InvariantScript'] = str(mx + 1 + i)
    print(scr, 'max', mx)
t = app.rule('RequesDetailScreen', 'RS_BtnBackToList', 'OnSelect')
ask = 'Set(varLeaveTo, "Requests"); Set(varLeaveFrom, App.ActiveScreen); Set(varLeaveAsk, true)'
app.set('RequesDetailScreen', 'RS_BtnBackToList', 'OnSelect', f'If(varViewOnly Or varRequestorLocked Or locShowTypePicker, {t.strip()}, {ask})', expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL191 built')
