#!/usr/bin/env python3
"""Checks for FINAL24 against FINAL23: RS_Owner / RS_Contractor yellow when nothing real is picked."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL24-contacts-yellow.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL23-message-read.msapp'
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
want = {c: ['BorderColor', 'BorderThickness', 'DefaultSelectedItems', 'HoverBorderColor'] for c in ('RS_Owner', 'RS_Contractor')}
check({k: v for k, v in ch.items() if v} == want, 'only the two contact fields changed')
for ctl, lbl, typ, src in (('RS_Owner', 'RS_LblOwner', 'DG/Agency', 'DG_Agency_Contact'), ('RS_Contractor', 'RS_LblContractor', 'Contractor', 'Contractor_Contact')):
    r = rd(N[ctl])
    nothing = f'IsEmpty(Filter({ctl}.SelectedItems, Not(IsBlank(Trim(Coalesce(DisplayName, "")))) Or Not(IsBlank(Trim(Coalesce(Mail, ""))))))'
    for p in ('BorderColor', 'BorderThickness'):
        check(nothing in r[p] and 'IsBlank(manual)' in r[p] and f'ContactType = "{typ}"' in r[p] and f'{lbl}.Visible' in r[p] and bal(r[p]), f'{ctl}.{p}: yellow when no real contact and no manual one')
    check('RGBA(255, 204, 0, 1)' in r['BorderColor'] and r['BorderThickness'].endswith(', 3, 2)'), f'{ctl}: yellow, thickness 3')
    check(f'ForAll(Filter(varCurrentRequest.{src}, Not(IsBlank(Email))) As p,' in r['DefaultSelectedItems'] and bal(r['DefaultSelectedItems']), f'{ctl}: blank placeholder person no longer selected')
    check(r['HoverBorderColor'] == 'Self.BorderColor', f'{ctl}: yellow stays under the mouse')
    check(rd(O[ctl])['Items'] == r['Items'] and rd(O[ctl])['OnChange'] == r['OnChange'], f'{ctl}: items and change logic untouched')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
