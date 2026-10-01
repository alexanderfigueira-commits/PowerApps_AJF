#!/usr/bin/env python3
"""Static checks for v66 against friday.msapp (= v49): attachment records carry an Id."""
import json, re, sys, zipfile
import yaml
from paload import PaLoader

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v66-friday-attach-id.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else '/root/.claude/uploads/4d44a760-ee6e-5284-adba-c35ebdee79f5/0da80633-friday.msapp'
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
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
changed = sorted(s for s in new if s not in old or json.dumps(new[s], sort_keys=True) != json.dumps(old[s], sort_keys=True))


# ---- YAML mirrors JSON: no mismatch that the 24 base does not already have ----
def yaml_issues(js, ys, screen):
    out = set()
    y = yaml.load(ys[screen], Loader=PaLoader)
    doc = y['App'] if screen == 'App' else y['Screens'][screen]
    if screen == 'App':
        for p, v in (doc.get('Properties') or {}).items():
            j = rule(js['App'], p)
            if j is None or flat(str(v).lstrip('=')) != flat(j):
                out.add(f'App.{p}: YAML differs from JSON')
        return out
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


# ---- v66 ----
check(changed == ['ChildLegalScreen'], f'changed: {changed}')
diff = [(s, c['Name'], r['Property']) for s in changed for c in walk(new[s]) for r in c['Rules']
        if rule({k['Name']: k for k in walk(old[s])}[c['Name']], r['Property']) != r['InvariantScript']]
check(diff == [('ChildLegalScreen', 'CL_DCAttach', 'Update')], f'changed rules: {diff}')
u = rule({c['Name']: c for c in walk(new['ChildLegalScreen'])}['CL_DCAttach'], 'Update')
o = rule({c['Name']: c for c in walk(old['ChildLegalScreen'])}['CL_DCAttach'], 'Update')
code = re.sub(r'//.*', '', u)
check(code.count('(') == code.count(')') and code.count('{') == code.count('}'), 'brackets')
check(') As f,' in code and 'DisplayName: f.Name,' in code and 'Value: f.Value' in code, 'record shape')
check('Id: Coalesce(LookUp(varAttachRecord.Attachments, DisplayName = f.Name).Id, f.Name)' in code, 'Id')
# the merge itself (which files) is the friday one, word for word
inner = lambda t: flat(re.sub(r'//.*', '', t)[re.sub(r'//.*', '', t).index('Ungroup('):])
check(inner(u).startswith(inner(o)[:-1].rstrip(') ').rstrip()), 'merge changed')
check(flat(re.sub(r'//.*', '', o)).split('Ungroup(')[1].rsplit('files )', 1)[0] in flat(code), 'file selection changed')

print(f'{cnt - len(fails)}/{cnt} checks passed')
for f_ in fails[:40]:
    print('  FAIL', f_)
sys.exit(1 if fails else 0)
