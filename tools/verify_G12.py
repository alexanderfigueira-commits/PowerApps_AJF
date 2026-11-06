#!/usr/bin/env python3
"""Checks for FINAL22 against FINAL21: Add_media_icon is disabled until the draft is saved, with a helpful tooltip."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL22-add-media-after-draft.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL21-legal-columns.msapp'
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, ref = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('References/'):
            ref[f] = z.read(i)
    return js, ref


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


def bal(t):
    v = re.sub(r'(?m)^\s*//[^\n]*', '', t); v = re.sub(r'"[^"\n]*"', '""', v)
    return v.count('(') == v.count(')') and v.count('{') == v.count('}')


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
new, nref = load(PKG); old, oref = load(BASE)
check(nref == oref, 'data sources changed')
check(all(json.dumps(new[s], sort_keys=True) == json.dumps(old[s], sort_keys=True) for s in new if s != 'RequesDetailScreen'), 'another screen changed')
N = {c['Name']: c for c in walk(new['RequesDetailScreen'])}; O = {c['Name']: c for c in walk(old['RequesDetailScreen'])}
check(set(N) == set(O), 'controls added or removed')
ch = {n: sorted(p for p in set(rd(c)) | set(rd(O[n])) if rd(c).get(p) != rd(O[n]).get(p)) for n, c in N.items()}
check({k: v for k, v in ch.items() if v} == {'Add_media_icon': ['DisabledColor', 'DisplayMode', 'Tooltip'], 'RS_NewRequestHint': ['Text']}, 'only the icon and the hint changed')
r, o = rd(N['Add_media_icon']), rd(O['Add_media_icon'])
check('Coalesce(varCurrentRequest.ID, 0) > 0, DisplayMode.Edit, DisplayMode.Disabled' in r['DisplayMode'], 'enabled only once the request is saved')
check(r['OnSelect'] == o['OnSelect'], 'what the button does is unchanged')
tt = r['Tooltip']
check(bal(tt) and 'Add a media file to this request' in tt and 'Draft Save' in tt, 'tooltip: enabled text and the Draft Save instruction')
check(all(x in tt for x in ('enter the request title', 'select the DG / Agency', 'choose the production type', 'RS_Title.Text', 'HomeFilterDG.Selected.Value', 'varRequestMediaType')), 'tooltip lists what is still missing')
check(r['DisabledColor'] != 'RGBA(244, 244, 244, 1)', 'disabled icon stays visible')
check('Draft Save' in rd(N['RS_NewRequestHint'])['Text'], 'hint under the media list matches')
d = rd(N['RS_BtnDraftSave'])
check('Draft Save' in d['Text'] and 'RS_Title.Text' in d['DisplayMode'] and 'HomeFilterDG.Selected.Value' in d['DisplayMode'], 'the tooltip names the real button and its real conditions')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
