#!/usr/bin/env python3
"""FINAL47 on FINAL46: in view mode every text input on RequesDetailScreen, ChildInfoScreen and ChildMetaScreen shows its text in
RGBA(0, 0, 0, 1).

Color becomes  If(Self.DisplayMode = DisplayMode.View, RGBA(0, 0, 0, 1), <the previous Color>)  on every text input (template "text"):
31 controls. It follows each control's own view mode (request locked, opened from a dashboard, read-only notes, Beluga reference for a
non-administrator...), not one variable. Most already had a black Color; the notes boxes used grey / dark-blue-grey, which is what changes.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG36', 'newG37'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
BLACK = 'RGBA(0, 0, 0, 1)'
n = 0
for s in ('RequesDetailScreen', 'ChildInfoScreen', 'ChildMetaScreen'):
    tp = app.doc(s)['TopParent']
    def walk(c):
        yield c
        for k in c.get('Children', []):
            yield from walk(k)
    for c in list(walk(tp)):
        if c['Template']['Name'] != 'text':
            continue
        old = app.rule(s, c['Name'], 'Color')
        if old is None:
            sys.exit(f'! {s}.{c["Name"]} has no Color rule')
        o = old.replace('\r\n', '\n')
        new = (f'If(Self.DisplayMode = DisplayMode.View, {BLACK}, {o})' if '\n' not in o and not o.lstrip().startswith('//')
               else f'If(\n    Self.DisplayMode = DisplayMode.View, {BLACK},\n' + '\n'.join('    ' + l for l in o.split('\n')) + '\n)')
        app.set(s, c['Name'], 'Color', new, expect=old)
        n += 1
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL47 built; text inputs changed:', n)
