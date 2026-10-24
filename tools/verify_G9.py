#!/usr/bin/env python3
"""Checks for FINAL19 against FINAL17: yellow borders on the starred Metadata / Info fields + ScriptShotlist saved and reloaded."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL19-script-shotlist.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL17-save-media-fix.msapp'
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
N = {s: {c['Name']: c for c in walk(t)} for s, t in new.items()}; O = {s: {c['Name']: c for c in walk(t)} for s, t in old.items()}
check({s: set(N[s]) for s in N} == {s: set(O[s]) for s in O}, 'controls added or removed')
ch = {(s, n): sorted(p for p in set(rd(c)) | set(rd(O[s][n])) if rd(c).get(p) != rd(O[s][n]).get(p)) for s in N for n, c in N[s].items()}
want = {('ChildMetaScreen', n): ['BorderColor', 'BorderThickness'] for n in ('CM_ShootDate', 'CM_PlacePhoto', 'CM_Credits', 'CM_ProdEnd', 'CM_PubStartV', 'CM_PubEndV')}
want.update({('ChildInfoScreen', 'CI_Description'): ['BorderColor', 'BorderThickness'], ('ChildMetaScreen', 'ChildMetaScreen'): ['OnVisible'],
             ('ChildValidScreen', 'CV_BtnSaveArchive'): ['OnSelect'], ('RequesDetailScreen', 'RequesDetailScreen'): ['OnVisible'],
             ('RequesDetailScreen', 'RS_CRowSelect'): ['OnSelect'], ('RequesDetailScreen', 'Add_media_icon'): ['OnSelect']})
check({k: v for k, v in ch.items() if v} == want, f'changed: {[(k, v) for k, v in ch.items() if v and want.get(k) != v]} / missing {[k for k in want if k not in {k for k, v in ch.items() if v}]}')
# ---- yellow
Y = 'RGBA(255, 204, 0, 1)'
for s, ctl, lbl, test in (('ChildMetaScreen', 'CM_ShootDate', 'CM_LblShootDate', 'IsBlank(varChildCaptureDate) Or IsBlank(CM_ShootDate.SelectedDate)'),
                          ('ChildMetaScreen', 'CM_PlacePhoto', 'CM_LblPlacePhoto', 'IsBlank(Trim(CM_PlacePhoto.Text))'),
                          ('ChildMetaScreen', 'CM_Credits', 'CM_LblCredits', 'IsBlank(Trim(CM_Credits.Text))'),
                          ('ChildInfoScreen', 'CI_Description', 'CI_LblDescription', 'IsBlank(Trim(CI_Description.Text))')):
    r = rd(N[s][ctl]); cond = f'{lbl}.Visible And Right(Trim({lbl}.Text), 1) = "*" And ({test})'
    check(f'If({cond}, {Y}, RGBA(0, 18, 107, 1))' in r['BorderColor'] and r['BorderThickness'] == f'If({cond}, 3, 2)', f'{ctl}: yellow while empty (only when the label has its star)')
    check(bal(r['BorderColor']) and bal(r['BorderThickness']), f'{ctl}: brackets')
for ctl, lbl, var in (('CM_ProdEnd', 'CM_LblProdEnd', 'varChildProductionEndDate'), ('CM_PubStartV', 'CM_LblPubStartV', 'varChildPublicationStartDate'), ('CM_PubEndV', 'CM_LblPubEndV', 'varChildPublicationEndDate')):
    r = rd(N['ChildMetaScreen'][ctl]); cond = f'{lbl}.Visible And (IsBlank({var}) Or IsBlank({ctl}.SelectedDate))'
    check(cond in r['BorderColor'] and r['BorderThickness'] == f'If({cond}, 3, 2)' and Y in r['BorderColor'], f'{ctl}: yellow when the value or the control is empty')
# ---- script
sv, osv = rd(N['ChildValidScreen']['CV_BtnSaveArchive'])['OnSelect'], rd(O['ChildValidScreen']['CV_BtnSaveArchive'])['OnSelect']
check(sv.count('ScriptShotlist: varChildScript,') == 2 and re.sub(r'\r?\n *ScriptShotlist: varChildScript,', '', sv) == osv and bal(sv), 'save: ScriptShotlist in the media record and in the Patch, nothing else changed')
ov, oo = rd(N['RequesDetailScreen']['RequesDetailScreen'])['OnVisible'], rd(O['RequesDetailScreen']['RequesDetailScreen'])['OnVisible']
check(ov.count('ScriptShotlist: Coalesce(ScriptShotlist, ""),') == 1 and re.sub(r'\r?\n *ScriptShotlist: Coalesce\(ScriptShotlist, ""\),', '', ov) == oo and bal(ov), 'reload: ScriptShotlist read back')
rs, ors = rd(N['RequesDetailScreen']['RS_CRowSelect'])['OnSelect'], rd(O['RequesDetailScreen']['RS_CRowSelect'])['OnSelect']
check('Set(varChildScript, Coalesce(ThisItem.ScriptShotlist, ""));' in rs and rs.replace('\nSet(varChildScript, Coalesce(ThisItem.ScriptShotlist, ""));', '') == ors, 'open row: script loaded')
ad, oad = rd(N['RequesDetailScreen']['Add_media_icon'])['OnSelect'], rd(O['RequesDetailScreen']['Add_media_icon'])['OnSelect']
check(ad.count('Set(varChildScript, "");') == 1 and re.sub(r'(\r?\n)Set\(varChildScript, ""\);', '', ad) == oad, 'new item: script empty')
mv, omv = rd(N['ChildMetaScreen']['ChildMetaScreen'])['OnVisible'], rd(O['ChildMetaScreen']['ChildMetaScreen'])['OnVisible']
check('varChildScript' not in mv and omv.replace('\n    Set(varChildScript, "");', '') == mv, 'Metadata tab no longer wipes the script')
x = [x for x in json.loads(zipfile.ZipFile(PKG).read('References\\DataSources.json').decode('utf-8-sig'))['DataSources'] if x['Name'] == 'AV-CD-Mediafiles'][0]
check('ScriptShotlist' in x['ConnectedDataSourceInfoNameMapping'].values(), 'ScriptShotlist is a column of the media list')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
