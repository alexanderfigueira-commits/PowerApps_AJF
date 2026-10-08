#!/usr/bin/env python3
"""Checks for FINAL51 against FINAL50: only RS_Owner / RS_Contractor search properties changed."""
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
fails = []
if nr != orf: fails.append('data sources changed')
if set(n) != set(o): fails.append('controls differ')
ch = {(k, p) for k in n if k in o for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p) and p != 'ZIndex'}
allowed = {'InputTextPlaceholder', 'DisplayFields', 'SearchFields', 'Items', 'DefaultSelectedItems', 'SearchItems'}
for (k, p) in ch:
    if k[1] not in ('RS_Owner', 'RS_Contractor') or p not in allowed: fails.append(f'unexpected {k} {p}')
for c in ('RS_Owner', 'RS_Contractor'):
    r = n[('RequesDetailScreen', c)]
    if r['InputTextPlaceholder'] != '"Search by user ID or email or last and first name"': fails.append(c + ' placeholder')
    if r['DisplayFields'] != '["DisplayName","Mail"]': fails.append(c + ' display')
    if r['SearchFields'] != '["DisplayName","GivenName","Surname","MailNickname","Mail"]': fails.append(c + ' search')
    if 'MailNickname: o.MailNickname' not in r['Items']: fails.append(c + ' items columns')
    if len({p for (k, p) in ch if k[1] == c}) != 6: fails.append(c + ' not all six properties changed')
print('FAIL' if fails else 'PASS'); [print(' -', f) for f in fails]; sys.exit(1 if fails else 0)
