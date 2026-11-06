#!/usr/bin/env python3
"""FINAL48 on FINAL47: in view mode the field labels (the text above each field) are black too.

Owner's screenshot: the values were already RGBA(0, 0, 0, 1); the labels above them were RGBA(60, 66, 80, 1). On RequesDetailScreen,
ChildInfoScreen and ChildMetaScreen every field label (controls named *_Lbl*, without the panel / section headings) now uses
If(varRequestorLocked, RGBA(0, 0, 0, 1), <previous colour>): varRequestorLocked is the app's view mode (request opened from a dashboard
ID, or locked for a requestor). Edit mode is unchanged.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG37', 'newG38'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
BLACK = 'RGBA(0, 0, 0, 1)'
done = []
for s in ('RequesDetailScreen', 'ChildInfoScreen', 'ChildMetaScreen'):
    tp = app.doc(s)['TopParent']
    def walk(c):
        yield c
        for k in c.get('Children', []):
            yield from walk(k)
    for c in list(walk(tp)):
        n = c['Name']
        if c['Template']['Name'] != 'label' or not re.match(r'^(RS|CI|CM)_Lbl\w+$', n) or re.search(r'Panel|Section|SavedHead', n):
            continue
        old = app.rule(s, n, 'Color')
        if old is None:
            continue
        o = old.replace('\r\n', '\n')
        new = (f'If(varRequestorLocked, {BLACK}, {o})' if '\n' not in o and not o.lstrip().startswith('//')
               else f'If(\n    varRequestorLocked, {BLACK},\n' + '\n'.join('    ' + l for l in o.split('\n')) + '\n)')
        app.set(s, n, 'Color', new, expect=old)
        done.append((s, n))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL48 built; labels changed:', len(done))
for s, n in done: print('  ', s[:9], n)
