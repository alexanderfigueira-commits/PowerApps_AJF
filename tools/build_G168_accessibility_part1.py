#!/usr/bin/env python3
"""FINAL179 on FINAL178 - accessibility, part 1 of 3: decorative controls.
The checker treats a control as interactive as soon as it carries an OnSelect rule, even OnSelect = false (the default, which Studio does not write to the YAML).
750 labels, rectangles, images, icons and circles carried that rule and nothing else: they were reported as controls with no tab stop, no visible focus and no accessible label.
The rule (exactly 'false') is removed from them; controls with a real action keep theirs. Nothing changes on screen or in behaviour."""
import datetime, os, re, shutil
from payaml import App
from acc_common import *
SRC, NEW = 'newV40', 'newV41'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
n = 0; yaml_lines = 0
by_type = {}
for scr in list(app.map):
    for node in walk(app.doc(scr)['TopParent']):
        if node is app.doc(scr)['TopParent']: continue
        t = ttype(node)
        if t not in DECOR: continue
        r = [x for x in node['Rules'] if x['Property'] == 'OnSelect']
        if r and lf(r[0]['InvariantScript']).strip() == 'false':
            yaml_lines += drop_rule(app, scr, node['Name'], 'OnSelect', 'false')
            n += 1; by_type[t] = by_type.get(t, 0) + 1
print('OnSelect = false removed from', n, 'controls', by_type, '| YAML lines removed:', yaml_lines)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL179 built')
