#!/usr/bin/env python3
"""FINAL61 on the user's TEST_1: 'Name of the photographer' on ChildMetaScreen (Photo only), a people picker in CM_Gallery to the right of
Contracting authority, wired end to end like Producer: AV-CD-Mediafiles.Photographer (Person, multi) <-> varChildPhotographerSel /
varChildPhotographer <-> colArchives. Optional (no yellow border, no validation row)."""
import datetime, json, os, re, shutil, sys
from payaml import App
from hp_common import Builder
SRC, NEW = 'newG51', 'newG51out'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
CM, G = 'ChildMetaScreen', 'CM_Gallery'
b = Builder(app, CM)
PHOTO = 'varChildMediaType = "Photo"'
lbl = b.clone('CM_LblPhotographer', CM, 'CM_LblProducer', {'Text': '"Name of the photographer"', 'Visible': PHOTO, 'X': '700', 'Y': '78', 'Width': '295'}, parent=G)
cmb = b.clone('CM_Photographer', CM, 'CM_Producer', {
    'Visible': PHOTO, 'X': '700', 'Y': '104', 'Width': '295',
    'BorderColor': 'RGBA(0, 18, 107, 1)', 'BorderThickness': '2',
    'DefaultSelectedItems': 'If(IsBlank(varChildPhotographerSel), Blank(), ForAll(varChildPhotographerSel As p, {DisplayName: p.DisplayName, Mail: p.Mail}))',
    'DisplayFields': '["DisplayName","Mail"]', 'SearchFields': '["DisplayName","GivenName","Surname","MailNickname","Mail"]',
    'InputTextPlaceholder': '"Search by user ID or email or last and first name"',
    'OnChange': 'Set(varChildPhotographerSel, Self.SelectedItems); Set(varChildPhotographer, Concat(Self.SelectedItems, DisplayName, ", "))'}, parent=G)
b.save()
# stacking above the other fields of the gallery (set after b.save() so ZIndex stays out of the YAML mirror)
def set_z(c, z):
    r = [x for x in c['Rules'] if x['Property'] == 'ZIndex'][0]; r['InvariantScript'] = str(z)
    for e in c.get('ControlPropertyState', []):
        if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString'): e['AutoRuleBindingString'] = str(z)
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
mx = max(int([r for r in c['Rules'] if r['Property'] == 'ZIndex'][0]['InvariantScript']) for c in walk(b.tp) if any(r['Property'] == 'ZIndex' for r in c['Rules']) and c['Name'] not in ('CM_LblPhotographer', 'CM_Photographer'))
set_z(lbl, mx + 1); set_z(cmb, mx + 2)
app.save()
# ---- wiring ----
PH = 'Photographer: If(IsBlank(varChildPhotographerSel), Blank(), ForAll(varChildPhotographerSel As u, {Claims: "i:0#.f|membership|" & Lower(u.Mail), DisplayName: u.DisplayName, Email: u.Mail, Department: "", JobTitle: "", Picture: ""})),'
def edit(screen, ctl, prop, fn, label):
    o = app.rule(screen, ctl, prop); n = fn(o)
    if n == o: sys.exit('! no change: ' + label)
    app.set(screen, ctl, prop, n, expect=o); print('ok', label)
RESET = 'Set(varChildPhotographerSel, Blank()); Set(varChildPhotographer, "");'
def add_after(anchor, extra):
    def f(t):
        if t.count(anchor) != 1: sys.exit(f'! anchor {anchor!r} x{t.count(anchor)}')
        return t.replace(anchor, anchor + ' ' + extra)
    return f
edit('App', None, 'OnStart', add_after('Set(varChildProducerSel, Blank());', RESET), 'App.OnStart reset')
edit('RequesDetailScreen', 'Add_media_icon', 'OnSelect', add_after('Set(varChildProducerSel, Blank());', RESET), 'new media reset')
def open_row(t):
    a = 'Set(varChildProducer, Concat(ThisItem.Producer, DisplayName, ", "));'
    if t.count(a) != 1: sys.exit('! open row anchor')
    nl = '\r\n' if '\r\n' in t else '\n'
    return t.replace(a, a + nl + '                    Set(varChildPhotographerSel, ThisItem.Photographer);' + nl + '                    Set(varChildPhotographer, Concat(ThisItem.Photographer, DisplayName, ", "));')
edit('RequesDetailScreen', 'DOA_List1RowBadge_8', 'OnSelect', open_row, 'open media row')
def load_rows(t):
    m = re.search(r'Producer: ForAll\(\s*Producer As p,\s*\{[^}]*\}\s*\),', t)
    if not m: sys.exit('! colArchives Producer block')
    blk = m.group(0)
    return t.replace(blk, blk + '\r\n                        ' + blk.replace('Producer', 'Photographer') if False else blk + ('\r\n' if '\r\n' in t else '\n') + '                        ' + blk.replace('Producer: ForAll(', 'Photographer: ForAll(').replace('Producer As p', 'Photographer As p'), 1)
edit('RequesDetailScreen', None, 'OnVisible', load_rows, 'colArchives load')
def save_rows(t):
    t = t.replace('Producer: varChildProducerSel,', 'Producer: varChildProducerSel, Photographer: varChildPhotographerSel,', 1)
    m = re.search(r'Producer: If\(IsBlank\(varChildProducerSel\), Blank\(\), ForAll\(varChildProducerSel As u, \{[^}]*\}\)\),', t)
    if not m: sys.exit('! patch Producer block')
    return t.replace(m.group(0), m.group(0) + ' ' + PH, 1)
edit('ChildValidScreen', 'CV_BtnSaveArchive', 'OnSelect', save_rows, 'Save Media')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL61 built')
