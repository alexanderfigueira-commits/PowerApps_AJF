#!/usr/bin/env python3
"""Checks for FINAL25 against FINAL24: yellow for CM_SeasonNumber, CM_EpisodeNumber, CM_Producer."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL25-yellow-podcast-producer.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL24-contacts-yellow.msapp'
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
check(all(json.dumps(new[s], sort_keys=True) == json.dumps(old[s], sort_keys=True) for s in new if s != 'ChildMetaScreen'), 'another screen changed')
N = {c['Name']: c for c in walk(new['ChildMetaScreen'])}; O = {c['Name']: c for c in walk(old['ChildMetaScreen'])}
check(set(N) == set(O), 'controls added or removed')
ch = {n: sorted(p for p in set(rd(c)) | set(rd(O[n])) if rd(c).get(p) != rd(O[n]).get(p)) for n, c in N.items()}
want = {'CM_SeasonNumber': ['BorderColor', 'BorderThickness', 'Default', 'HoverBorderColor', 'OnChange'],
        'CM_EpisodeNumber': ['BorderColor', 'BorderThickness', 'Default', 'HoverBorderColor', 'OnChange'],
        'CM_Producer': ['BorderColor', 'BorderThickness']}
check({k: v for k, v in ch.items() if v} == want, 'only the three fields changed')
for ctl, lbl, var in (('CM_SeasonNumber', 'CM_LblSeasonNumber', 'varChildSeasonNumber'), ('CM_EpisodeNumber', 'CM_LblEpisodeNumber', 'varChildEpisodeNumber')):
    r = rd(N[ctl]); cond = f'{lbl}.Visible And Coalesce(IfError(Value(Trim({ctl}.Text)), 0), 0) <= 0'
    check(f'If({cond}, RGBA(255, 204, 0, 1), RGBA(0, 18, 107, 1))' in r['BorderColor'] and r['BorderThickness'] == f'If({cond}, 3, 2)', f'{ctl}: yellow unless a number above 0')
    check(f'If({var} > 0, Text({var}), "")' in r['Default'] and r['OnChange'] == f'Set({var}, Coalesce(IfError(Value(Self.Text), 0), 0))', f'{ctl}: shows empty until a number is stored; text no longer raises an error')
    check(r['HoverBorderColor'] == 'Self.BorderColor' and all(bal(r[p]) for p in ('BorderColor', 'BorderThickness', 'Default', 'OnChange')), f'{ctl}: hover, brackets')
p = rd(N['CM_Producer']); none = 'IsBlank(varChildProducer) Or IsEmpty(Filter(CM_Producer.SelectedItems,'
check(none in p['BorderColor'] and none in p['BorderThickness'] and 'CM_LblProducer.Visible' in p['BorderColor'] and 'RGBA(255, 204, 0, 1)' in p['BorderColor'] and bal(p['BorderColor']) and bal(p['BorderThickness']), 'CM_Producer: yellow when empty by the control or by the validation value')
check(rd(O['CM_Producer'])['DefaultSelectedItems'] == p['DefaultSelectedItems'] and rd(O['CM_Producer'])['OnChange'] == p['OnChange'], 'CM_Producer: selection logic untouched')
v = open('/dev/null').read()
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
