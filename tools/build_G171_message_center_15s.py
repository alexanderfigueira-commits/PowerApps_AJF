#!/usr/bin/env python3
"""FINAL182 on FINAL181 (= FINAL178 + the three accessibility parts): the Message Center polling interval.
NT_MessageTimer ticked every 5 s: the notes list was refreshed on every tick while the window is open, and on every 6th tick (30 s) otherwise.
The timer now ticks every 15 s: refreshed on every tick while the window is open (15 s), every 2nd tick otherwise (30 s, unchanged)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV43', 'newV44'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
R = 'RequesDetailScreen'
t = app.rule(R, 'NT_MessageTimer', 'Duration'); assert t == '5000', t
app.set(R, 'NT_MessageTimer', 'Duration', '15000', expect=t)
t = app.rule(R, 'NT_MessageTimer', 'OnTimerEnd')
old_c = '// every 5 s while the Message Center is open; every 30 s otherwise, so the unread number above its button stays current'
old_m = 'locShowNotes Or Mod(tick, 6) = 0,'
assert t.count(old_c) == 1 and t.count(old_m) == 1
u = t.replace(old_c, '// every 15 s while the Message Center is open; every 30 s otherwise (every 2nd tick), so the unread number above its button stays current')
u = u.replace(old_m, 'locShowNotes Or Mod(tick, 2) = 0,')
app.set(R, 'NT_MessageTimer', 'OnTimerEnd', u, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL182 built')
