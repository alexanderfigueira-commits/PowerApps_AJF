#!/usr/bin/env python3
"""Checks for FINAL33 against FINAL32: FTP path required marker + Export loads its own data."""
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
exp = sorted([(('ChildInfoScreen', 'CI_LblFTPPath'), 'Text'), (('ChildInfoScreen', 'CI_FTPPath'), 'BorderColor'), (('ChildInfoScreen', 'CI_FTPPath'), 'BorderThickness'), (('HomePrintScreen', 'HomePrintScreen'), 'OnVisible')])
check(ch == exp, f'only the 4 expected rules changed: {ch}')
check(set(n) == set(o), 'same controls')
fp = n[('ChildInfoScreen', 'CI_FTPPath')]
check('255, 204, 0' in fp['BorderColor'] and 'IsBlank(Trim(CI_FTPPath.Text))' in fp['BorderColor'] and fp['BorderThickness'].startswith('If('), 'FTP yellow when empty')
check(n[('ChildInfoScreen', 'CI_LblFTPPath')]['Text'] == '"FTP delivery path *"', 'FTP label has the *')
ov = n[('HomePrintScreen', 'HomePrintScreen')]['OnVisible']
check("ClearCollect(colPrintData, 'AV-CD-Requests')" in ov and 'RemoveIf(colPrintData' in ov and 'ClearCollect(colPrintMedia' in ov and 'locHPStatus: "All"' in ov, 'Export loads requests itself')
check('varUserRole = "ADMINISTRATOR" And Status.Value <> "Draft"' in ov and "'Created By'.Email = User().Email" in ov, 'same visibility rule as Request Management')
check(all(bal(n[k][p]) for k, p in ch), 'brackets')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
