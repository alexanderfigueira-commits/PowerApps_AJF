#!/usr/bin/env python3
"""FINAL77 on the user's TEST_2: SaveButton sits behind addMediaItem (same spot, lower ZIndex) and runs RS_BtnDraftSave's OnSelect.
Before the draft is saved (no request id) only SaveButton shows (with the Icon2 arrow that says to save first); once saved, SaveButton and
Icon2 disappear and addMediaItem appears."""
import datetime, json, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG67', 'newG67out'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
from payaml import find
CAT = {'OnSelect': 'Behavior', 'Tooltip': 'Design', 'Visible': 'Design'}
def ensure(ctl, prop):
    c = find(app.doc(S)['TopParent'], ctl)
    if not any(r['Property'] == prop for r in c['Rules']):
        c['Rules'].append({'Property': prop, 'Category': CAT[prop], 'InvariantScript': '', 'RuleProviderType': 'Unknown'})
        st = c.setdefault('ControlPropertyState', [])
        if all(isinstance(e, str) for e in st): st.append(prop)
for ctl, prop in (('SaveButton', 'OnSelect'), ('SaveButton', 'Tooltip'), ('SaveButton', 'Visible'), ('Icon2', 'Visible'), ('addMediaItem', 'Visible')): ensure(ctl, prop)
ax = {p: app.rule(S, 'addMediaItem', p) for p in ('X', 'Y', 'Width', 'Height')}
for p, v in ax.items(): app.set(S, 'SaveButton', p, v)                # exactly under addMediaItem
app.set(S, 'SaveButton', 'OnSelect', app.rule(S, 'RS_BtnDraftSave', 'OnSelect'))
app.set(S, 'SaveButton', 'DisplayMode', app.rule(S, 'RS_BtnDraftSave', 'DisplayMode'))
app.set(S, 'SaveButton', 'Tooltip', '"Save the draft: media items can be added once it is saved"')
NOTSAVED = 'Not(varViewOnly) And Not(varRequestorLocked) And (IsBlank(varCurrentRequest) Or Coalesce(varCurrentRequest.ID, 0) <= 0)'
app.set(S, 'SaveButton', 'Visible', NOTSAVED)
app.set(S, 'Icon2', 'Visible', 'SaveButton.Visible')
app.set(S, 'addMediaItem', 'Visible', 'Coalesce(varCurrentRequest.ID, 0) > 0')
app.save()
# stacking: SaveButton and its arrow go behind addMediaItem (Z 82), below every pop-up
jp = [os.path.join(NEW, 'Controls', f) for f in os.listdir(f'{NEW}/Controls') if '"RequesDetailScreen"' in open(os.path.join(NEW, 'Controls', f), encoding='utf-8-sig').read()[:400]][0]
raw = open(jp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); crlf = b'\r\n' in raw
d = json.loads(raw.decode('utf-8-sig'))
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
z_add = None
for c in walk(d['TopParent']):
    if c['Name'] == 'addMediaItem': z_add = int([r for r in c['Rules'] if r['Property'] == 'ZIndex'][0]['InvariantScript'])
for c in walk(d['TopParent']):
    if c['Name'] in ('SaveButton', 'Icon2'):
        r = [x for x in c['Rules'] if x['Property'] == 'ZIndex'][0]; r['InvariantScript'] = str(z_add - 1)
        for e in c.get('ControlPropertyState', []):
            if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString'): e['AutoRuleBindingString'] = str(z_add - 1)
out = json.dumps(d, ensure_ascii=False, indent=2)
open(jp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out.replace('\n', '\r\n') if crlf else out)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL77 built; addMediaItem Z', z_add)
