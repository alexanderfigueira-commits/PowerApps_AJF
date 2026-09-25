#!/usr/bin/env python3
"""Static checks for v55 against v54: administrator / requestor notes in pop-ups."""
import json, re, sys, zipfile
import yaml
from paload import PaLoader

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v55-notes-popups.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-v54-card-order.msapp'
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
check(changed == ['RequesDetailScreen'], f'unexpected screens changed: {changed}')

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


# ---- v55: notes in two pop-ups ----
S = 'RequesDetailScreen'
nc = {c['Name']: c for c in walk(new[S])}
oc = {c['Name']: c for c in walk(old[S])}
added = sorted(set(nc) - set(oc))
want = sorted(f'{p}{k}' for p in ('RS_AdminNotes', 'RS_RequestorNotes')
              for k in ('Open', 'Backdrop', 'Panel', 'Title', 'Hint', 'Cancel', 'Save'))
check(added == want, f'added controls: {added}')
check(not (set(oc) - set(nc)), 'controls removed')
top_old = max(int(rule(c, 'ZIndex')) for c in oc.values() if c['Parent'] == S and (rule(c, 'ZIndex') or '').isdigit())
box = lambda k: tuple(int(rule(nc[k], q)) for q in ('X', 'Y', 'Width', 'Height'))
for p, show in (('RS_AdminNotes', 'locShowAdminNotes'), ('RS_RequestorNotes', 'locShowRequestorNotes')):
    check(rule(nc[p], 'Visible') == show, f'{p} not in its pop-up')
    check(flat(rule(nc[p], 'OnChange')).endswith('false') and 'Patch' not in rule(nc[p], 'OnChange'), f'{p} still saves on change')
    check(rule(nc[p + 'Open'], 'OnSelect') == f'UpdateContext({{{show}: true}})', f'{p}Open')
    px, py, pw, ph = box(p + 'Panel')
    for k in ('Title', 'Hint', 'Cancel', 'Save', ''):
        x, y, w, h = box(p + k)
        check(px <= x and py <= y and x + w <= px + pw and y + h <= py + ph, f'{p}{k} outside its panel')
        check(int(rule(nc[p + k], 'ZIndex')) > top_old, f'{p}{k} under older controls')
        check(show in rule(nc[p + k], 'Visible'), f'{p}{k} visibility')
    sv = rule(nc[p + 'Save'], 'OnSelect')
    check(cat(nc[p + 'Save'], 'OnSelect') == 'Behavior' and sv.count('(') == sv.count(')'), f'{p}Save formula')
    check(f'{p}.Text' in sv and 'UpdateContext' in sv and ' + ' not in sv, f'{p}Save content')
    check(f'Reset({p})' in rule(nc[p + 'Cancel'], 'OnSelect'), f'{p}Cancel must discard')
    check(box(p + 'Open')[:2] == (int(rule(oc[p], 'X')), int(rule(oc[p], 'Y'))), f'{p}Open not in the old box place')
for nm in ('RS_BtnDraftSave', 'RS_BtnDraftSave_1', 'RS_BtnSubmitRequest', 'RS_BtnResubmitRequest'):
    check(rule(nc[nm], 'OnSelect') == rule(oc[nm], 'OnSelect'), f'{nm} changed')
    check('RS_AdminNotes.Text' in rule(nc[nm], 'OnSelect') and 'RS_RequestorNotes.Text' in rule(nc[nm], 'OnSelect'), f'{nm} lost notes')
ov = rule(new[S], 'OnVisible')
check('locShowAdminNotes: false' in ov and 'locShowRequestorNotes: false' in ov, 'pop-ups not closed on open')

print(f'{n - len(fails)}/{n} checks passed')
for f in fails[:40]:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
