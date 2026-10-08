#!/usr/bin/env python3
"""FINAL64 on FINAL63: the photographer is mandatory (Photo): '*' on CM_LblPhotographer, yellow border on CM_Photographer while empty, and a
validation row 'Photographer provided (Photo only)' in both copies of the Validations checklist."""
import datetime, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG53', 'newG54'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
CM, CV = 'ChildMetaScreen', 'ChildValidScreen'
o = app.rule(CM, 'CM_LblPhotographer', 'Text'); assert o == '"Name of the photographer"'
app.set(CM, 'CM_LblPhotographer', 'Text', '"Name of the photographer *"', expect=o)
EMPTY = 'CM_LblPhotographer.Visible And (IsBlank(varChildPhotographer) Or IsEmpty(Filter(CM_Photographer.SelectedItems, Not(IsBlank(Trim(Coalesce(DisplayName, "")))) Or Not(IsBlank(Trim(Coalesce(Mail, "")))))))'
o = app.rule(CM, 'CM_Photographer', 'BorderColor')
app.set(CM, 'CM_Photographer', 'BorderColor', f'// yellow while this mandatory field is empty\nIf({EMPTY}, RGBA(255, 204, 0, 1), RGBA(0, 18, 107, 1))', expect=o)
o = app.rule(CM, 'CM_Photographer', 'BorderThickness')
app.set(CM, 'CM_Photographer', 'BorderThickness', f'If({EMPTY}, 3, 2)', expect=o)
# validation rows
MSG = 'Select the photographer on the Metadata tab.'
ROW = '{Check: "Photographer provided (Photo only)", Pass: varChildMediaType <> "Photo" Or (Not(IsBlank(varChildPhotographer)) And varChildPhotographer <> ""), Note: "' + MSG + '"},'
anchor = re.compile(r'(\{Check: "Contracting authority provided \(Photo only\)",\s*Pass: [^\n]*(?:\n\s*Note: "[^"]*"|, Note: "[^"]*")\},)')
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
hits = 0
for c in list(walk(app.doc(CV)['TopParent'])):
    for r in c['Rules']:
        s = r['InvariantScript']
        if 'Contracting authority provided (Photo only)' not in s: continue
        n = s.replace('\r\n', '\n'); m = anchor.search(n)
        if not m: sys.exit('! anchor in ' + c['Name'])
        ls = n.rfind('\n', 0, m.start()) + 1
        sep = '\n' + re.match(r'[ \t]*', n[ls:m.start()]).group(0) if '\n' in m.group(1) else ' '
        n = n.replace(m.group(1), m.group(1) + sep + ROW, 1)
        app.set(CV, c['Name'] if c['Name'] != CV else None, r['Property'], n.replace('\n', '\r\n') if '\r\n' in s else n, expect=s); hits += 1
print('validation rows added:', hits); assert hits == 2
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL64 built')
