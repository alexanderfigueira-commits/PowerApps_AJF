#!/usr/bin/env python3
"""FINAL175 on FINAL174. App checker, Performance (what is safe to correct):
 1. "Inefficient text input" (5): DelayOutput = true on HP_TxtTitle, HP_TxtRequestID, HomeFilterRequestName, HomeFilterRequestID, HomeFilterBeluga.
 2. "Use AllItemsCount instead of CountRows with AllItems" (24 uses): CountRows(Gallery.AllItems) -> Gallery.AllItemsCount.
 3. "Event rule references a control on another screen":
    - the Export menu button of 15 screens did ClearCollect(colPrintData, HomeGallery.AllItems) (a gallery of RequestManagementScreen) before opening HomePrintScreen, whose OnVisible
      loads its own colPrintData from scratch: the line only forced RequestManagementScreen to load early and is removed;
    - the template pickers' Reset(CM_Producer) / Reset(CM_PhotographerName) (ChildMetaScreen) become a flag, varMetaReset, that ChildMetaScreen.OnVisible acts on.
 Left alone and why: Validations of ChildValidScreen read attachment boxes of other screens (needs the attachments flow rebuilt), collections initialised once (a named formula
 would change when the data is read), ClearCollect of whole lists (data row limit already at its maximum, 2000), screens with many controls."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV36', 'newV37'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
import glob, json
H, R = 'HomePrintScreen', 'RequestManagementScreen'

# 1. DelayOutput
for scr, ctl in ((H, 'HP_TxtTitle'), (H, 'HP_TxtRequestID'), (R, 'HomeFilterRequestName'), (R, 'HomeFilterRequestID'), (R, 'HomeFilterBeluga')):
    t = app.rule(scr, ctl, 'DelayOutput'); assert t == 'false', (ctl, t)
    app.set(scr, ctl, 'DelayOutput', 'true', expect=t)

# walk every rule of every screen
CNT = re.compile(r'CountRows\(\s*([A-Za-z_]\w*)\.AllItems\s*\)')
EXP = re.compile(r'ClearCollect\(colPrintData, HomeGallery\.AllItems\);\s*')
RST = re.compile(r'Reset\(CM_Producer\);\s*Reset\(CM_PhotographerName\);')
n_cnt = n_exp = n_rst = 0
exp_names = []
for scr, path in app.map.items():
    if scr == 'App': continue
    d = app.doc(scr)
    def walk(n):
        yield n
        for c in n.get('Children', []): yield from walk(c)
    for n in walk(d['TopParent']):
        ctl = None if n is d['TopParent'] else n['Name']
        for r in list(n['Rules']):
            t = r['InvariantScript'].replace('\r\n', '\n')
            u = t
            u, a = CNT.subn(lambda m: m.group(1) + '.AllItemsCount', u); n_cnt += a
            if ctl and ctl.endswith('Menu_Export') or (ctl and ctl in ('DOA_Menu_Export_1', 'DOA_Menu_Export')):
                u, b = EXP.subn('', u); n_exp += b; exp_names.append((scr, ctl)) if b else None
            if ctl in ('CI_TplConfirmOK', 'CI_TplRowUse'):
                u, c = RST.subn('Set(varMetaReset, true);', u); n_rst += c
            if u != t:
                app.set(scr, ctl, r['Property'], u, expect=t)
print('AllItemsCount:', n_cnt, '| Export lines removed:', n_exp, '| template Resets:', n_rst)
print(exp_names)
assert n_cnt == 24 and n_exp == 15 and n_rst == 2, (n_cnt, n_exp, n_rst)

# the flag is acted on by the owning screen
t = app.rule('ChildMetaScreen', None, 'OnVisible')
add = ('\n// a template applied on the Info tab asks for these two boxes to be read again from their variables\n'
       'If(varMetaReset, Reset(CM_Producer); Reset(CM_PhotographerName); Set(varMetaReset, false))')
assert 'varMetaReset' not in t
app.set('ChildMetaScreen', None, 'OnVisible', t.rstrip().rstrip(';') + ';' + add, expect=t)

app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL175 built')
