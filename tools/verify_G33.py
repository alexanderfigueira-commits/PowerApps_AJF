#!/usr/bin/env python3
"""Checks for FINAL43 against the owner's TEST file."""
import json, re, sys, zipfile
PKG, BASE = sys.argv[1], sys.argv[2]
fails, cnt = [], 0
def check(ok, msg):
    global cnt
    cnt += 1
    if not ok: fails.append(msg)
def load(p):
    z = zipfile.ZipFile(p); js, ref = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('References/'): ref[f] = z.read(i)
    return js, ref
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
def bal(t):
    v = re.sub(r'(?m)^\s*//[^\n]*', '', t); v = re.sub(r'"[^"\n]*"', '""', v)
    return v.count('(') == v.count(')') and v.count('{') == v.count('}')
(new, nref), (old, oref) = load(PKG), load(BASE)
check(nref == oref, 'data sources unchanged')
flat = lambda js: {(s, c['Name']): {r['Property']: r['InvariantScript'] for r in c['Rules']} for s, t in js.items() for c in walk(t)}
n, o = flat(new), flat(old)
check(set(n) == set(o), "same controls: the owner's layout edits untouched")
ch = sorted((k, p) for k in n for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p) and p != 'ZIndex')
NAV = {'RequestManagementScreen': 'RM', 'HelpScreen': 'HL', 'DashboardScreen': 'DB', 'HomePrintScreen': 'HP', 'PrintPhotoDetailScreen': 'PPD', 'PrintVideoDetailScreen': 'PVD', 'PrintPodcastDetailScreen': 'PPoD',
       'RequesDetailScreen': 'RS', 'ChildInfoScreen': 'CI', 'ChildMetaScreen': 'CM', 'ChildLegalScreen': 'CL', 'ChildValidScreen': 'CV'}
exp = []
for s, p in NAV.items():
    exp += [((s, f'{p}_Menu_Panel'), 'X'), ((s, f'{p}_Menu_Panel'), 'Width'), ((s, f'{p}_Menu_Dashboard'), 'X'), ((s, f'{p}_Menu_Requests'), 'X')]
M = 'ChildMetaScreen'
exp += [((M, 'CM_BtnOpenEpisodeVisual'), q) for q in ('BorderColor', 'BorderThickness', 'Tooltip')] + [((M, 'CM_LblEpisodeVisual'), 'Text'), (('ChildLegalScreen', 'CL_DCIdValue'), 'Text'),
        (('RequesDetailScreen', 'Add_media_icon'), 'OnSelect'), (('RequesDetailScreen', 'DOA_List1RowBadge_8'), 'OnSelect'), (('ChildValidScreen', 'CV_BtnSaveArchive'), 'OnSelect')]
exp += [((s, s), 'OnVisible') for s in ('ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen')]
check(ch == sorted(exp), f'exactly the expected rules changed: extra={sorted(set(ch) - set(exp))} missing={sorted(set(exp) - set(ch))}')
# Task 1: the administrator keeps today's values; the requestor closes the Review slot
def branch(f):
    m = re.fullmatch(r'If\(varUserRole = "ADMINISTRATOR", (\d+), (\d+)\)', f)
    return (int(m.group(1)), int(m.group(2))) if m else None
for s, p in NAV.items():
    px, pw, dx, rx = (branch(n[(s, f'{p}_Menu_Panel')]['X']), branch(n[(s, f'{p}_Menu_Panel')]['Width']), branch(n[(s, f'{p}_Menu_Dashboard')]['X']), branch(n[(s, f'{p}_Menu_Requests')]['X']))
    check(None not in (px, pw, dx, rx), f'{s}: formulas')
    if None in (px, pw, dx, rx): continue
    check((px[0], pw[0], dx[0], rx[0]) == (int(o[(s, f'{p}_Menu_Panel')]['X']), int(o[(s, f'{p}_Menu_Panel')]['Width']), int(o[(s, f'{p}_Menu_Dashboard')]['X']), int(o[(s, f'{p}_Menu_Requests')]['X'])), f'{s}: administrator values unchanged')
    ex = int(o[(s, f'{p}_Menu_Export')]['X']); rv = int(o[(s, f'{p}_Menu_Review')]['X'])
    check(rx[1] + (ex - rv) + 2 == ex and px[1] + pw[1] == px[0] + pw[0] and dx[1] > px[1], f'{s}: requestor slot closed, right edge kept')
# Task 2
mb = n[(M, 'CM_BtnOpenEpisodeVisual')]
check('Coalesce(varChildSeasonNumber, 0) = 1' in mb['BorderColor'] and '255, 204, 0' in mb['BorderColor'] and 'Mandatory:' in mb['Tooltip'] and 'Optional:' in mb['Tooltip'], 'episode visual: yellow, tooltip mandatory / optional')
check('" *"' in n[(M, 'CM_LblEpisodeVisual')]['Text'] and '(optional)' in n[(M, 'CM_LblEpisodeVisual')]['Text'], 'episode visual label')
# Task 4
check(n[('ChildValidScreen', 'CV_BtnSaveArchive')]['OnSelect'].startswith('If(') and 'Coalesce(varCurrentRequest.ID, 0) = 0' in n[('ChildValidScreen', 'CV_BtnSaveArchive')]['OnSelect'] and 'CountIf(colValidations, Not(Pass)) > 0' in n[('ChildValidScreen', 'CV_BtnSaveArchive')]['OnSelect'], 'Save Media guards')
check(o[('ChildValidScreen', 'CV_BtnSaveArchive')]['OnSelect'].replace('\r\n', '\n').strip() in n[('ChildValidScreen', 'CV_BtnSaveArchive')]['OnSelect'].replace('\r\n', '\n').replace('\n    ', '\n'), 'the original save is kept inside the guard')
for s in ('ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen'):
    t = n[(s, s)]['OnVisible']
    check('never blanked while an id exists' in t and 'Coalesce(varAttachRecord.ID, 0) <> Coalesce(varCurrentChildSPId, 0),' not in t, f'{s}: id block')
check('Set(varAttachRecord, If(Coalesce(varCurrentChildSPId, 0) > 0' in n[('RequesDetailScreen', 'Add_media_icon')]['OnSelect'] and 'Set(varAttachRecord, If(Coalesce(ThisItem.SPId, 0) > 0' in n[('RequesDetailScreen', 'DOA_List1RowBadge_8')]['OnSelect'], 'record aligned at entry')
check('Text(varCurrentChildSPId)' in n[('ChildLegalScreen', 'CL_DCIdValue')]['Text'], 'card id fallback')
check(all(bal(n[k][p]) for k, p in ch), 'brackets')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
