#!/usr/bin/env python3
"""FINAL232 on FINAL231. Font size of the modern date pickers: 13 in Request Management (asked); elsewhere the size of the other
fields of that screen: Export (HomePrintScreen, text boxes 13) 11 -> 13; Info (ChildInfoScreen, the podcast fields shown with
these dates are 13) 14 -> 13; Metadata (ChildMetaScreen, fields 11) already 11, unchanged."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV93', 'newV94'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))


def setp(scr, ctl, prop, val, old):
    t = app.rule(scr, ctl, prop); assert t is not None and t.strip() == old, (scr, ctl, prop, t)
    app.set(scr, ctl, prop, val, expect=t)


for scr, ctls, old, new in (('RequestManagementScreen', ('HomeFilterStart', 'HomeFilterEnd'), '11', '13'),
                            ('HomePrintScreen', ('HP_DateStart', 'HP_DateEnd'), '11', '13'),
                            ('ChildInfoScreen', ('CI_CaptureDate', 'CI_ProductionEndDate', 'CI_PubStartDate', 'CI_PubEndDate'), '14', '13')):
    for c in ctls:
        setp(scr, c, 'Size', new, old)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL232 built')
