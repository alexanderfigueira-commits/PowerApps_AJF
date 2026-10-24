#!/usr/bin/env python3
"""Static checks for v48 (24.msapp + print navigation + podcast attachment forms)."""
import json, re, sys, zipfile
import yaml
from paload import PaLoader

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-v48-podcast-forms.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'AV-CD-24.msapp'  # the 24.msapp you sent
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

changed = sorted(s for s in new if json.dumps(new[s], sort_keys=True) != json.dumps(old[s], sort_keys=True))
check(changed == ['ChildInfoScreen', 'ChildLegalScreen', 'ChildMetaScreen', 'ChildValidScreen',
                  'HomePrintScreen', 'PrintPhotoDetailScreen', 'PrintPodcastDetailScreen',
                  'PrintVideoDetailScreen'], f'unexpected screens changed: {changed}')

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


# ---- TASK 3 reverted: print screens keep the 24 layout ----
LAYOUT = ('X', 'Y', 'Width', 'Height', 'Size', 'Visible', 'TemplateSize', 'OnSelect')
for s in ('PrintVideoDetailScreen', 'PrintPodcastDetailScreen', 'PrintPhotoDetailScreen'):
    check(rule(new[s], 'Width') is None and rule(new[s], 'Height') is None, f'{s} has an A4 size')
    on = {c['Name']: c for c in walk(old[s])}
    nn = {c['Name']: c for c in walk(new[s])}
    check(set(on) == set(nn), f'{s}: controls added/removed')
    for name, c in nn.items():
        for p in LAYOUT:
            check(flat(rule(c, p)).replace('varPrintRequest', 'gblPrintRequest')
                  .replace('colPrintReqMedia', 'X') ==
                  flat(rule(on[name], p)).replace(
                      'Filter( colPrintMedia, ParentRequest = gblPrintRequest.RequestNumber )', 'X'),
                  f'{s}.{name}.{p} layout changed')
    for c in walk(new[s]):
        for r in c['Rules']:
            check('gblPrintRequest' not in r['InvariantScript'] and 'colPrintMedia' not in r['InvariantScript'],
                  f'{s}.{c["Name"]}.{r["Property"]}: old print variable')

# ---- TASK 2 ----
ch = rule(ctl['HP_RowChevron'][0][1], 'OnSelect')
check('Set(varPrintRequest, ThisItem)' in ch and 'MediaType).Value' in ch, 'chevron formula')
for s in ('PrintVideoDetailScreen', 'PrintPodcastDetailScreen', 'PrintPhotoDetailScreen'):
    check(f'Navigate({s}' in ch, f'chevron misses {s}')
    check("Filter('AV-CD-Mediafiles', ParentRequest = varPrintRequest.RequestNumber)" in rule(new[s], 'OnVisible'),
          f'{s} OnVisible filter')

# ---- TASK 1 ----
cl = {c['Name']: c for c in walk(new['ChildLegalScreen'])}
for S, p, value, form, card, gal, show in (
        ('ChildInfoScreen', 'CI', 'CI_PodcastVisual', 'CI_FormPodcastVisual', 'CI_DCPodcastVisual', 'CI_Gallery', 'locShowPodcastVisual'),
        ('ChildMetaScreen', 'CM', 'CM_AudioFiles', 'CM_FormAudioFiles', 'CM_DCAudioFiles', 'CM_Gallery', 'locShowAudioFiles')):
    sc = {c['Name']: c for c in walk(new[S])}
    f, v, cd = sc[form], sc[value], sc[card]
    check(f['Template']['Name'] == 'form' and f['Parent'] == S, f'{form} is not a screen-level form')
    check(v['Template']['Name'] == 'attachments' and v['Parent'] == card and cd['Parent'] == form,
          f'{value} is not in {card} in {form}')
    check(value not in [k['Name'] for k in sc[gal]['Children']], f'{value} still in {gal}')
    for prop in ('DataSource', 'Item', 'DefaultMode'):
        check(rule(f, prop) == rule(cl['CL_FormAttach'], prop), f'{form}.{prop} differs from CL_FormAttach')
    check(rule(cd, 'DataField') == '"{Attachments}"', f'{card} DataField')
    check(rule(cd, 'Update') == f'{value}.Attachments', f'{card}.Update')
    check(rule(cd, 'DisplayMode') == rule(cl['CL_DCAttach'], 'DisplayMode'), f'{card}.DisplayMode')
    check('Filter(Parent.Default,' in rule(v, 'Items'), f'{value}.Items is not a filter of the card default')
    check('SubmitForm' not in json.dumps(new[S]), f'{S} submits a form')
    vis = f'{show} And varChildMediaType = "Podcast"'
    for nme in (f'{p}_AttachShade', f'{p}_AttachPanel', f'{p}_LblAttachPanel', f'{p}_AttachFor',
                f'{p}_AttachHint', form, f'{p}_AttachClose'):
        check(rule(sc[nme], 'Visible') == vis, f'{nme}.Visible')
    check(rule(sc[f'{p}_BtnOpenAttach'], 'OnSelect') == f'UpdateContext({{{show}: true}})', f'{p} open button')
    check(sc[f'{p}_BtnOpenAttach']['Parent'] == gal, f'{p}_BtnOpenAttach not in the gallery')
    check(rule(sc[f'{p}_AttachClose'], 'OnSelect') == f'UpdateContext({{{show}: false}})', f'{p} close button')
    # the panel draws above every other control on the tab
    top = [c for c in new[S]['Children']]
    zs = {c['Name']: int(rule(c, 'ZIndex')) for c in top if (rule(c, 'ZIndex') or '').isdigit()}
    mine = {f'{p}_AttachShade', f'{p}_AttachPanel', f'{p}_LblAttachPanel', f'{p}_AttachFor',
            f'{p}_AttachHint', form, f'{p}_AttachNeedSave', f'{p}_AttachClose'}
    others = max(z for k, z in zs.items() if k not in mine)
    check(min(zs[k] for k in mine) > others, f'{S}: panel under other controls')

upd = rule(cl['CL_DCAttach'], 'Update')
for need in ('CI_PodcastVisual.Attachments', 'CM_AudioFiles.Attachments', 'CL_DCAttachValue.Attachments',
             'varAttachRecord.Attachments.DisplayName', 'Ungroup('):
    check(need in upd, f'CL_DCAttach.Update misses {need}')
check(upd.count('(') == upd.count(')'), 'CL_DCAttach.Update parentheses')
subs = [(s, c['Name']) for s, tp in new.items() for c in walk(tp) for r in c['Rules']
        if 'SubmitForm(' in r['InvariantScript']]
check(subs == [('ChildValidScreen', 'CV_BtnSaveArchive')], f'SubmitForm used by {subs}')
refs = {'CI_PodcastVisual': 0, 'CM_AudioFiles': 0}
for s, tp in new.items():
    for c in walk(tp):
        for r in c['Rules']:
            for k in refs:
                refs[k] += len(re.findall(rf'\b{k}\b', r['InvariantScript']))
check(all(refs.values()), f'references: {refs}')
for s, name in (('ChildInfoScreen', 'CI_LblMissing'), ('ChildValidScreen', 'CV_BtnRefresh')):
    t = rule({c['Name']: c for c in walk(new[s])}[name], 'Text' if s == 'ChildInfoScreen' else 'OnSelect')
    check('Filter(CI_PodcastVisual.Attachments' in t, f'{name}: podcast visual check not on the new form')

print(f'{n - len(fails)}/{n} checks passed')
for f in fails[:40]:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
