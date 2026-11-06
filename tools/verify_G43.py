#!/usr/bin/env python3
"""Checks for FINAL53 against FINAL52: only the two contact '+' buttons, the two comboboxes' OnChange and the screen OnVisible changed."""
import json, sys, zipfile
def load(p):
    z = zipfile.ZipFile(p); out = {}; ref = {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            t = json.loads(z.read(i).decode('utf-8-sig'))['TopParent']
            def w(c):
                out[(t['Name'], c['Name'])] = {r['Property']: r['InvariantScript'] for r in c['Rules']}
                for k in c.get('Children', []): w(k)
            w(t)
        elif f.startswith('References/'): ref[f] = z.read(i)
    return out, ref
(n, nr), (o, orf) = load(sys.argv[1]), load(sys.argv[2])
S = 'RequesDetailScreen'
fails = []
if nr != orf: fails.append('data sources changed')
if set(n) != set(o): fails.append('controls differ')
ch = sorted((k, p) for k in n if k in o for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p))
exp = sorted([((S, b), p) for b in ('RS_DetailsToggle_contrator', 'RS_DetailsToggle_contrator_1') for p in ('DisplayMode', 'OnSelect', 'Tooltip')]
             + [((S, 'RS_Owner'), 'OnChange'), ((S, 'RS_Contractor'), 'OnChange'), ((S, S), 'OnVisible')])
if ch != exp: fails.append(f'unexpected changes {ch}')
for b, c, f in (('RS_DetailsToggle_contrator_1', 'RS_Owner', 'locOwnerNoMatch'), ('RS_DetailsToggle_contrator', 'RS_Contractor', 'locContractorNoMatch')):
    d = n[(S, b)]['DisplayMode']
    for need in (f'{c}.SelectedItems', 'varRequestorLocked', f, f'{c}.SearchText', 'DisplayMode.Disabled'):
        if need not in d: fails.append(f'{b} DisplayMode lacks {need}')
print('FAIL' if fails else 'PASS'); [print(' -', x) for x in fails]; sys.exit(1 if fails else 0)
