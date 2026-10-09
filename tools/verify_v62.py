#!/usr/bin/env python3
"""Static checks for v62 against v61: podcast attachment filters read varAttachRecord."""
import json, re, sys, zipfile
import yaml
from paload import PaLoader

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v62-podcast-filter.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-v61-dash-list1.msapp'
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


# ---- v62: podcast attachment filters ----
check(changed == ['ChildInfoScreen', 'ChildMetaScreen'], f'changed: {changed}')
diff = []
for scr in changed:
    oc = {c['Name']: c for c in walk(old[scr])}
    for c in walk(new[scr]):
        for r in c['Rules']:
            if rule(oc[c['Name']], r['Property']) != r['InvariantScript']:
                diff.append((c['Name'], r['Property']))
check(sorted(diff) == [('CI_PodcastVisual', 'Items'), ('CM_AudioFiles', 'Items')], f'changed rules: {diff}')
for scr, name, exts in (('ChildInfoScreen', 'CI_PodcastVisual', ('.jpg', '.jpeg', '.png')),
                        ('ChildMetaScreen', 'CM_AudioFiles', ('.mp3', '.wav', '.m4a', '.aac'))):
    c = {k['Name']: k for k in walk(new[scr])}[name]
    it = rule(c, 'Items')
    o = rule({k['Name']: k for k in walk(old[scr])}[name], 'Items')
    check('Parent.Default' not in re.sub(r'//.*', '', it) and 'Filter(varAttachRecord.Attachments,' in it, f'{name} source')
    check(it.count('(') == it.count(')'), f'{name} brackets')
    code = re.sub(r'//.*', '', it)
    check(code.count('Lower(DisplayName)') == len(exts), f'{name} conditions')
    for e in exts:
        check(f'EndsWith(Lower(DisplayName), "{e}")' in code, f'{name} misses {e}')
    check(flat(re.sub(r'//.*', '', o)).replace('Parent.Default', 'varAttachRecord.Attachments') == flat(code), f'{name} filter otherwise unchanged')
    card = {k['Name']: k for k in walk(new[scr])}[c['Parent']]
    check(rule(card, 'Update') == f'{name}.Attachments', f'{name} card Update')
# nothing else in the app filters a card default by an attachment column
for s, tp in new.items():
    for c in walk(tp):
        for r in c['Rules']:
            check(not re.search(r'Filter\(\s*Parent\.Default', r['InvariantScript']), f'{s}.{c["Name"]}.{r["Property"]} filters Parent.Default')

print(f'{n - len(fails)}/{n} checks passed')
for f in fails[:40]:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
