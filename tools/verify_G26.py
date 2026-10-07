#!/usr/bin/env python3
"""Checks for FINAL36 against FINAL35: the template copy on ChildInfoScreen."""
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
flat = lambda js: {(s, c['Name']): {r['Property']: r['InvariantScript'] for r in c['Rules'] if r['Property'] != 'ZIndex'} for s, t in js.items() for c in walk(t)}
n, o = flat(new), flat(old)
ch = sorted((k, p) for k in n for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p))
S = 'ChildInfoScreen'
exp = sorted([((S, 'CI_TplConfirmOK'), 'OnSelect'), ((S, 'CI_TplRowBg'), 'OnSelect'), ((S, 'CI_BtnTemplate'), 'OnSelect'), ((S, 'CI_BtnTemplate'), 'DisplayMode'),
              ((S, 'CI_TplGallery'), 'Items'), ((S, 'CI_TplRowTitle'), 'Text'), ((S, 'CI_TplRowMeta'), 'Text'), ((S, 'CI_TplSubtitle'), 'Text')])
check(ch == exp, f'only the template controls changed: {ch}')
ok_, bg = n[(S, 'CI_TplConfirmOK')]['OnSelect'], n[(S, 'CI_TplRowBg')]['OnSelect']
sets = lambda t: sorted(re.findall(r'Set\((var\w+),', t))
check([x for x in sets(bg) if x not in ('varTplCandidate', 'varShowTplConfirm', 'varShowTemplatePicker')] == [x for x in sets(ok_) if x not in ('varShowTplConfirm', 'varShowTemplatePicker')], 'both paths copy the same variables')
check('Set(varChildTitle,' not in ok_ and 'Set(varChildTitle,' not in bg and 'Set(varChildTitle1, Coalesce(varTplCandidate.ProductionTitle' in ok_, 'title goes to varChildTitle1, not the media number')
check('varChildTitle <>' not in bg and 'varChildTitle1' in bg.split('Set(varShowTplConfirm, true)')[0], 'overwrite check uses varChildTitle1')
check('CreditContact' in ok_ and 'ProductionPlace' in ok_ and 'ReferenceLinks' in ok_ and 'Tags' in ok_ and 'FTPPath' in ok_ and 'NoThirdPartyRights' in ok_ and 'ProductType' in ok_, 'Info fields copied')
sch = json.dumps(json.loads(nref['References/DataSources.json'].decode('utf-8-sig')))
fields = set(re.findall(r'varTplCandidate\.(\w+)', ok_ + bg))
check(all(f in sch for f in fields), f'columns exist in the schema: {sorted(f for f in fields if f not in sch)}')
check('Reset(CI_TplSearch)' in n[(S, 'CI_BtnTemplate')]['OnSelect'] and 'Set(varTplSearch, "")' in n[(S, 'CI_BtnTemplate')]['OnSelect'], 'search reset on open')
it = n[(S, 'CI_TplGallery')]['Items']
check('ProductionTitle' in it and 'varCurrentChildSPId' in it, 'search by title; own item excluded')
check('varRequestorLocked' in n[(S, 'CI_BtnTemplate')]['DisplayMode'], 'locked requestor cannot use it')
check(all(bal(n[k][p]) for k, p in ch), 'brackets')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
