#!/usr/bin/env python3
"""v72 = the user's 28-03-v3.msapp + the dashboard work of v68, v70 and v71 (not v69's menu).

Checks: every screen but the two dashboards equals v3; both dashboards equal v71's,
except the Requestor dashboard menu, which stays as in v3 (v69 is not applied).
Plus the package checks of pack_final (YAML = JSON, Children keys).
"""
import json, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v72-v3-dashboards.msapp'
V3 = sys.argv[2] if len(sys.argv) > 2 else '/root/.claude/uploads/4d44a760-ee6e-5284-adba-c35ebdee79f5/3cda6c98-28-03-v3.msapp'
V71 = sys.argv[3] if len(sys.argv) > 3 else 'msapp-versions/AV-CD-v71-row-notes-icon.msapp'
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js = {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
    return js


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


def shape(tp):
    """name -> (template, parent, rules, group keys): what the app shows, without ids."""
    return {c['Name']: (c['Template']['Name'], c.get('Parent'),
                        sorted((r['Property'], r['InvariantScript']) for r in c['Rules']),
                        c.get('GroupedControlsKey')) for c in walk(tp)}


new, v3, v71 = load(PKG), load(V3), load(V71)
A, R = 'Dashboard-Ope-Administrator', 'Dashboard-Ope-Requestor'
check(sorted(new) == sorted(v3), 'screens differ from v3')
for s in new:
    if s in (A, R):
        continue
    check(shape(new[s]) == shape(v3[s]), f'{s} differs from v3')
check(shape(new[A]) == shape(v71[A]), 'Administrator dashboard differs from v71')
n, o, m = shape(new[R]), shape(v71[R]), shape(v3[R])
menu = {k for k in set(n) | set(o) if 'Nav' in k or k == 'DOR_menu_2'}
check({k: v for k, v in n.items() if k not in menu} == {k: v for k, v in o.items() if k not in menu},
      'Requestor dashboard (menu aside) differs from v71')
check({k: v for k, v in n.items() if k in menu} == {k: v for k, v in m.items() if k in menu},
      'Requestor dashboard menu differs from v3')
uids = [c['ControlUniqueId'] for tp in new.values() for c in walk(tp)]
check(len(uids) == len(set(uids)), 'duplicate ControlUniqueId')
names = [c['Name'] for tp in new.values() for c in walk(tp)]
check(len(names) == len(set(names)), 'duplicate names')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
