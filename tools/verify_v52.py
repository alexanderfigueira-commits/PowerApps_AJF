#!/usr/bin/env python3
"""Static checks for v52 against v51: HomeGallery role rules (opening status, no drafts for admins)."""
import json, re, sys, zipfile
import yaml
from paload import PaLoader

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v52-home-rules.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-v51-print-header.msapp'
fails, n = [], 0


def check(ok, msg):
    global n
    n += 1
    if not ok:
        fails.append(msg)


def load(path):
    z = zipfile.ZipFile(path)
    js, ys = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig'))
            js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('Src/') and f.endswith('.pa.yaml'):
            ys[f[4:-8]] = z.read(i).decode('utf-8')
    return js, ys


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


def rule(c, p):
    m = [r for r in c['Rules'] if r['Property'] == p]
    return m[0]['InvariantScript'] if m else None


def cat(c, p):
    m = [r['Category'] for r in c['Rules'] if r['Property'] == p]
    return m[0] if m else None


def flat(t):
    return ' '.join((t or '').split())


new, ny = load(PKG)
old, _ = load(BASE)
ctl = {}
for s, tp in new.items():
    for c in walk(tp):
        ctl.setdefault(c['Name'], []).append((s, c))

# ---- package integrity ----
dups = [k for k, v in ctl.items() if len(v) > 1]
check(not dups, f'control names used twice: {dups}')
uids = [c['ControlUniqueId'] for tp in new.values() for c in walk(tp)]
check(len(uids) == len(set(uids)), 'duplicate ControlUniqueId')
for s, tp in new.items():
    for c in walk(tp):
        for k in c.get('Children', []):
            check(k['Parent'] == c['Name'], f'{s}.{k["Name"]} Parent is {k["Parent"]}, not {c["Name"]}')
        check('Children' in c, f'{s}.{c["Name"]} has no Children key')
        for r in c['Rules']:
            if r['Property'].startswith('On'):
                check(r['Category'] == 'Behavior', f'{s}.{c["Name"]}.{r["Property"]} not Behavior')

PRINT_SCREENS = ['PrintPhotoDetailScreen', 'PrintPodcastDetailScreen', 'PrintVideoDetailScreen']
changed = sorted(s for s in new if json.dumps(new[s], sort_keys=True) != json.dumps(old[s], sort_keys=True))
check(changed == ['RequestManagementScreen'], f'unexpected screens changed: {changed}')

# ---- YAML mirrors JSON: no mismatch that the 24 base does not already have ----
def yaml_issues(js, ys, screen):
    out = set()
    doc = yaml.load(ys[screen], Loader=PaLoader)['Screens'][screen]
    ymap, ykids = {screen: doc.get('Properties', {})}, {screen: []}

    def yw(parent, kids):
        for k in kids or []:
            (name, body), = k.items()
            ymap[name] = body.get('Properties', {}) or {}
            ykids.setdefault(parent, []).append(name)
            ykids.setdefault(name, [])
            yw(name, body.get('Children'))
    yw(screen, doc.get('Children'))
    for c in walk(js[screen]):
        if c['Template']['Name'] == 'galleryTemplate' or c.get('IsGroupControl'):
            continue
        if c['Name'] not in ymap:
            out.add(f'{c["Name"]} missing in YAML')
            continue
        jk = sorted(k['Name'] for k in c.get('Children', [])
                    if k['Template']['Name'] != 'galleryTemplate' and not k.get('IsGroupControl'))
        if c is not js[screen] and jk != sorted(ykids.get(c['Name'], [])):
            out.add(f'{c["Name"]}: YAML children differ')
        for p, v in ymap[c['Name']].items():
            j = rule(c, p)
            if j is None or flat(str(v).lstrip('=')) != flat(j):
                out.add(f'{c["Name"]}.{p}: YAML differs from JSON')
    return out


_, oy = load(BASE)
for s_ in changed:
    base = yaml_issues(old, oy, s_) if s_ in oy else set()
    for issue in sorted(yaml_issues(new, ny, s_) - base):
        check(False, f'{s_}: {issue}')
    check(True, f'{s_} yaml')


# ---- v52: HomeGallery role rules ----
S = 'RequestManagementScreen'
NEWC = "'Created By'.Email = User().Email Or (varUserRole = \"ADMINISTRATOR\" And Status.Value <> \"Draft\")"
oc = {c['Name']: c for c in walk(old[S])}
diff, clauses = [], 0
for c in walk(new[S]):
    for r in c['Rules']:
        t = r['InvariantScript']
        check("varUserRole = \"ADMINISTRATOR\" Or 'Created By'.Email" not in flat(t), f'{c["Name"]}.{r["Property"]}: old role clause')
        clauses += flat(t).count(NEWC)
        if rule(oc[c['Name']], r['Property']) != t:
            diff.append((c['Name'], r['Property']))
        check(t.count('(') == t.count(')') and t.count('{') == t.count('}') and t.count('[') == t.count(']'),
              f'{c["Name"]}.{r["Property"]} brackets')
check(clauses == 12, f'{clauses} visibility clauses (11 + the opening rule)')
check(len(diff) == 12, f'{len(diff)} rules changed')
ov = rule(new[S], 'OnVisible')
check('["Processing", "Pending"]' in ov and '["Pending", "Draft", "Processing"]' in ov, 'role order')
check(ov.index('The list opens') < ov.index('A status handed over from the dashboard'), 'dashboard hand-over must win')
check('varFilter = "All" And IsBlank(locProdTypeFilter) And IsBlank(varNavFilter)' in ov, 'only with All Status + All Media')
check('Status.Value = varFilter' not in ov.split('The list opens')[1].split('A status handed')[0], 'status must not filter the opening check')

print(f'{n - len(fails)}/{n} checks passed')
for f in fails[:40]:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
