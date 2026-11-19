#!/usr/bin/env python3
"""FINAL193 on FINAL192. Validations: the click-to-fix did nothing because the formula sat on the gallery control, while the
runtime reads a gallery's OnSelect from its template (still 'false'). The navigation now lives on the row labels themselves
(CV_RowFix, CV_RowCheck, CV_RowNote, CV_RowIcon); the useless gallery rule is removed."""
import copy, datetime, os, re, shutil
from payaml import App, find, _fmt
SRC, NEW = 'newV54', 'newV55'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
CV = 'ChildValidScreen'
tp = app.doc(CV)['TopParent']
g = find(tp, 'CV_ChecklistGallery')
rule = [r for r in g['Rules'] if r['Property'] == 'OnSelect']; assert len(rule) == 1
GO = rule[0]['InvariantScript'].replace('\r\n', '\n')
assert GO.startswith('// a failed check opens the tab')
g['Rules'].remove(rule[0])
yf = f'{NEW}/Src/{CV}.pa.yaml'
L = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
# remove the gallery's OnSelect block from the YAML
i0 = next(i for i, l in enumerate(L) if l == '      - CV_ChecklistGallery:')
s = next(i for i in range(i0, len(L)) if L[i] == '            OnSelect: |-')
e = next(i for i in range(s + 1, len(L)) if L[i].strip() and len(L[i]) - len(L[i].lstrip()) <= 12)
del L[s:e]
# add OnSelect to the four row labels (JSON rule + YAML lines, inserted in alphabetical position)
proto = [r for r in find(tp, 'CV_BtnRefresh')['Rules'] if r['Property'] == 'OnSelect'][0]
for name in ('CV_RowFix', 'CV_RowCheck', 'CV_RowNote', 'CV_RowIcon'):
    c = find(tp, name); assert c and not [r for r in c['Rules'] if r['Property'] == 'OnSelect'], name
    nr = copy.deepcopy(proto); nr['InvariantScript'] = GO; c['Rules'].append(nr)
    b0 = next(i for i, l in enumerate(L) if l == f'            - {name}:')
    p0 = next(i for i in range(b0, len(L)) if L[i] == '                Properties:')
    ind = 18
    j = p0 + 1
    while j < len(L) and L[j].startswith(' ' * ind) and (len(L[j]) - len(L[j].lstrip()) > ind or L[j].strip().split(':')[0] < 'OnSelect'):
        j += 1
    L[j:j] = _fmt('OnSelect', GO, ind)
open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(L))
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL193 built')
