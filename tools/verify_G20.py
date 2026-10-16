#!/usr/bin/env python3
"""Checks for FINAL30 against the user's FINAL_3: only the media-id handling changed."""
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
new, nref = load(PKG); old, oref = load(BASE)
check(nref == oref, 'data sources unchanged')
flat = lambda js: {(s, c['Name']): {r['Property']: r['InvariantScript'] for r in c['Rules'] if r['Property'] != 'ZIndex'} for s, t in js.items() for c in walk(t)}
n, o = flat(new), flat(old)
ch = sorted((k, p) for k in n for p in set(n[k]) | set(o.get(k, {})) if n[k].get(p) != o.get(k, {}).get(p))
exp = sorted([(('ChildValidScreen', 'CV_BtnSaveArchive'), 'OnSelect')] + [((s, s), 'OnVisible') for s in ('ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen')])
check(ch == exp, f'only the 5 expected rules changed: {ch}')
check(set(n) == set(o), 'same controls')
sv = n[('ChildValidScreen', 'CV_BtnSaveArchive')]['OnSelect']
check('Coalesce(existingRec.SPId, varCurrentChildSPId, 0)' not in sv and 'If(Coalesce(existingRec.SPId, 0) > 0' in sv, 'media list write: 0 never wins')
check('spId: If(' in sv and 'Coalesce(varCurrentChildSPId, 0)' in sv, 'spId falls back to varCurrentChildSPId')
check('attachments panel was not loaded' in sv and 'SubmitForm(CL_FormAttach)' in sv, 'submit kept, warning added')
check(bal(sv), 'save button brackets')
for s in ('ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen'):
    t = n[(s, s)]['OnVisible']
    check('Set(varCurrentChildSPId, LookUp(colArchives' in t and t.index('Set(varCurrentChildSPId, LookUp(colArchives') < t.index('Set(varAttachRecord'), f'{s}: id restored before the record is read')
    check(bal(t), f'{s} brackets')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
