#!/usr/bin/env python3
"""v30 from the user's v29 (29.msapp): one info-icon / counter design on the dashboards,
one menu, one header and one role tag on every screen, and clear control names.

Approved choices (reply "OK as proposed"):
  1. Header = Header_3 (RequestManagementScreen) WITHOUT its six menu controls; the menu
     is DOA_menu_2 on every screen, RequestManagementScreen included.
  2. The menu's right end overlaps the user-name box by ~21 px; nothing is moved, the
     menu sits above the header so its buttons stay clickable.
  3. Menu highlight: Dashboard lights on the three dashboards, Export on the print
     screens (App.ActiveScreen), in the copies AND in the master.
  4. Step 6 copies HomeAppTitle_17, the "| Administrator" role tag (admins only).
  5. ChildLegalScreen's second header (Header_CL) is removed with Header_10.
Naming: <P>_Menu*, <P>_Header*, <P>_RoleTag, <P>_List<N>Counter* with the screen prefixes
below; the masters and the odd TODO names get the same pattern as the last step.
"""
import copy, datetime, json, os, re, shutil, sys
from payaml import App, find, CTL_RE, _indent
from hdr29 import role_of

SRC, NEW = 'b29', 'new30'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RM, DOA, DOR = 'RequestManagementScreen', 'Dashboard-Ope-Administrator', 'Dashboard-Ope-Requestor'
P = {'RequestManagementScreen': 'RM', 'RequesDetailScreen': 'RS', 'ChildInfoScreen': 'CI', 'ChildMetaScreen': 'CM',
     'ChildLegalScreen': 'CL', 'ChildValidScreen': 'CV', DOA: 'DOA', DOR: 'DOR', 'DashboardScreen': 'DB',
     'ReviewScreen': 'RV', 'HelpScreen': 'HL', 'HomePrintScreen': 'HP', 'PrintPhotoDetailScreen': 'PPD',
     'PrintVideoDetailScreen': 'PVD', 'PrintPodcastDetailScreen': 'PPoD'}
SCREENS = [s for s in app.map if s != 'App']
if set(SCREENS) != set(P):
    sys.exit(f'! screens: {sorted(set(SCREENS) ^ set(P))}')
for s in SCREENS:
    app.doc(s)                                    # keep every screen in memory


# ------------------------------------------------------------------ helpers
def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


def top(s):
    return app.doc(s)['TopParent']


def ctl(s, n):
    c = find(top(s), n)
    if c is None:
        sys.exit(f'! {s}: {n} not found')
    return c


def rule(c, p):
    m = [r for r in c['Rules'] if r['Property'] == p]
    return m[0]['InvariantScript'] if m else None


def ysrc(s):
    return os.path.join(app.path, 'Src', f'{s}.pa.yaml')


def ylines(s):
    return open(ysrc(s), encoding='utf-8').read().split('\n')


def ywrite(s, lines):
    open(ysrc(s), 'w', encoding='utf-8').write('\n'.join(lines))


def is_ctl_line(l, name):
    m = CTL_RE.match(l)
    return (m and m.group(1) == name) or l.strip() in (f'- {name}:', f"- '{name}':", f'- "{name}":')


def yblock(lines, name):
    hit = [i for i, l in enumerate(lines) if is_ctl_line(l, name)]
    if len(hit) != 1:
        sys.exit(f'! {name}: {len(hit)} YAML blocks')
    s = hit[0]
    mi = _indent(lines[s])
    e = len(lines)
    for i in range(s + 1, len(lines)):
        if lines[i].strip() and _indent(lines[i]) <= mi:
            e = i
            break
    while e - 1 > s and not lines[e - 1].strip():
        e -= 1
    return s, e


_ids = {'uid': 0, 'poi': 0}


def fresh_ids():
    if not _ids['uid']:
        for s in SCREENS + ['App']:
            for c in walk(top(s)):
                _ids['uid'] = max(_ids['uid'], int(c['ControlUniqueId']))
                _ids['poi'] = max(_ids['poi'], int(c['PublishOrderIndex']))
    _ids['uid'] += 1
    _ids['poi'] += 1
    return str(_ids['uid']), _ids['poi']


def groups(s):
    return [c for c in top(s)['Children'] if c.get('IsGroupControl')]


def delete(s, names):
    """Delete top-level controls (JSON + YAML) and drop them from groups; empty groups go."""
    names = set(names)
    tp = top(s)
    missing = names - {c['Name'] for c in tp['Children']}
    if missing:
        sys.exit(f'! {s}: cannot delete {sorted(missing)}')
    tp['Children'] = [c for c in tp['Children'] if c['Name'] not in names]
    for g in groups(s):
        keep = [n for n in g['GroupedControlsKey'] if n not in names]
        if len(keep) != len(g['GroupedControlsKey']):
            if keep:
                g['GroupedControlsKey'] = keep
            else:
                tp['Children'] = [c for c in tp['Children'] if c is not g]
                DELETED_GROUPS.setdefault(s, []).append(g['Name'])
    lines = ylines(s)
    for n in names:
        a, b = yblock(lines, n)
        del lines[a:b]
    ywrite(s, lines)


def clone(src_s, src_n, dst_s, new_n, group, overrides):
    """Copy a top-level control (no children) to dst_s as new_n, member of `group`."""
    d = ctl(src_s, src_n)
    if d.get('Children'):
        sys.exit(f'! {src_n} has children')
    if find(top(dst_s), new_n) or new_n in ALL_NAMES:
        sys.exit(f'! {new_n} already used')
    c = copy.deepcopy(d)
    c['Name'], c['Parent'] = new_n, dst_s
    c['ControlUniqueId'], c['PublishOrderIndex'] = fresh_ids()
    top(dst_s)['Children'].append(c)
    ALL_NAMES.add(new_n)
    # YAML: the donor block, renamed, in the new group, appended to the screen
    src = ylines(src_s)
    a, b = yblock(src, src_n)
    blk = src[a:b]
    blk[0] = blk[0].replace(src_n, new_n, 1)
    ind = ' ' * (_indent(blk[0]) + 4)
    blk = [l for l in blk if not re.match(r'^\s*Group:\s', l)]
    ci = next(i for i, l in enumerate(blk) if l.strip().startswith('Control:'))
    if group:
        blk.insert(ci + 1, f'{ind}Group: {group}')
    base = _indent(src[a])
    dst = ylines(dst_s)
    tgt = next(_indent(l) for l in dst if CTL_RE.match(l) and _indent(l) > 0)   # screen children indent
    blk = [(' ' * (tgt - base) + l) if l.strip() else l for l in blk] if tgt >= base else \
          [l[base - tgt:] if l.strip() else l for l in blk]
    end = len(dst)
    while end and not dst[end - 1].strip():
        end -= 1
    dst[end:end] = blk
    ywrite(dst_s, dst)
    for p, v in overrides.items():
        if rule(c, p) is None:
            c['Rules'].append({'Property': p, 'Category': 'Design', 'InvariantScript': v, 'RuleProviderType': 'Unknown'})
            c.setdefault('ControlPropertyState', []).append(p)
        app.set(dst_s, new_n, p, v)
    return c


def new_group(src_s, src_g, dst_s, new_n, members):
    g = copy.deepcopy(ctl(src_s, src_g))
    if new_n in ALL_NAMES:
        sys.exit(f'! {new_n} already used')
    g['Name'], g['Parent'] = new_n, dst_s
    g['ControlUniqueId'], g['PublishOrderIndex'] = fresh_ids()
    g['GroupedControlsKey'] = list(members)
    top(dst_s)['Children'].append(g)
    ALL_NAMES.add(new_n)
    return g


def setz(s, n, z):
    c = ctl(s, n)
    if rule(c, 'ZIndex') is None:
        c['Rules'].append({'Property': 'ZIndex', 'Category': 'Design', 'InvariantScript': str(z), 'RuleProviderType': 'Unknown'})
        c.setdefault('ControlPropertyState', []).append('ZIndex')
    app.set(s, n, 'ZIndex', str(z))


def group_z(s, n, z):
    """groups have no YAML node: their ZIndex lives in the JSON only"""
    g = ctl(s, n)
    if not g.get('IsGroupControl'):
        sys.exit(f'! {n} is not a group')
    next(r for r in g['Rules'] if r['Property'] == 'ZIndex')['InvariantScript'] = str(z)


def zint(c):
    v = rule(c, 'ZIndex')
    return int(v) if v and v.strip().isdigit() else None


ALL_NAMES = {c['Name'] for s in SCREENS + ['App'] for c in walk(top(s))}
DELETED_GROUPS = {}
REPORT = {'deleted': {}, 'created': {}}

# ================================================================== STEP 2: info icons
REF_INFO = ctl(DOA, 'DOA_List1Info')
card0 = ctl(DOA, 'DOA_List1Card')
DX = int(rule(REF_INFO, 'X')) - int(rule(card0, 'X'))
DY = int(rule(REF_INFO, 'Y')) - int(rule(card0, 'Y'))
KEEP_INFO = {'Tooltip', 'AccessibleLabel', 'ZIndex', 'X', 'Y'}
for s, pre, i in ((DOA, 'DOA', 2), (DOA, 'DOA', 3), (DOR, 'DOR', 1), (DOR, 'DOR', 2), (DOR, 'DOR', 3)):
    n = f'{pre}_List{i}Info'
    c = ctl(s, n)
    if c['Template']['Name'] != REF_INFO['Template']['Name']:
        sys.exit(f'! {n} is not an icon')
    for r in REF_INFO['Rules']:
        if r['Property'] in KEEP_INFO:
            continue
        if rule(c, r['Property']) != r['InvariantScript']:
            if rule(c, r['Property']) is None:
                c['Rules'].append(dict(r))
                c.setdefault('ControlPropertyState', []).append(r['Property'])
            app.set(s, n, r['Property'], r['InvariantScript'])
    card = ctl(s, f'{pre}_List{i}Card')
    app.set(s, n, 'X', str(int(rule(card, 'X')) + DX))
    app.set(s, n, 'Y', str(int(rule(card, 'Y')) + DY))
app.save()

# ================================================================== STEP 3: counters
C_CIRC, C_TEXT = ctl(DOA, 'Circle1'), ctl(DOA, 'Label4')
CX = int(rule(C_CIRC, 'X')) - int(rule(card0, 'X'))
CY = int(rule(C_CIRC, 'Y')) - int(rule(card0, 'Y'))
if 'Todo List_Gallery' not in rule(C_TEXT, 'Text'):
    sys.exit('! Label4 does not count the TODO gallery')
OLD_COUNTERS = {(DOA, 'DOA', 2): 'count_2', (DOA, 'DOA', 3): 'count_3', (DOR, 'DOR', 1): 'count_4',
                (DOR, 'DOR', 2): 'count_5', (DOR, 'DOR', 3): 'count_6'}
for (s, pre, i), old in OLD_COUNTERS.items():
    g = next(x for x in groups(s) if x['Name'] == old)
    circ, lab = [ctl(s, n) for n in g['GroupedControlsKey'] if ctl(s, n)['Template']['Name'] == 'circle'], \
                [ctl(s, n) for n in g['GroupedControlsKey'] if ctl(s, n)['Template']['Name'] == 'label']
    if len(circ) != 1 or len(lab) != 1:
        sys.exit(f'! {old}: not one circle + one label')
    gal = f'{pre}_List{i}Gallery'
    if rule(lab[0], 'Text').strip() != f'Text(CountRows({gal}.AllItems))':
        sys.exit(f'! {old} does not count {gal}: {rule(lab[0], "Text")}')
    zc, zl = zint(circ[0]), zint(lab[0])
    card = ctl(s, f'{pre}_List{i}Card')
    x, y = int(rule(card, 'X')) + CX, int(rule(card, 'Y')) + CY
    delete(s, [circ[0]['Name'], lab[0]['Name']])
    REPORT['deleted'].setdefault(s, []).append(f'{old} ({circ[0]["Name"]}, {lab[0]["Name"]})')
    cn, tn = f'{pre}_List{i}CounterCircle', f'{pre}_List{i}CounterText'
    clone(DOA, 'Circle1', s, cn, f'{pre}_List{i}Counter', {'X': str(x), 'Y': str(y), 'ZIndex': str(zc)})
    clone(DOA, 'Label4', s, tn, f'{pre}_List{i}Counter',
          {'X': str(x), 'Y': str(y), 'ZIndex': str(zl),
           'Text': rule(C_TEXT, 'Text').replace("'Todo List_Gallery'", gal)})
    new_group(DOA, 'Group3', s, f'{pre}_List{i}Counter', [cn, tn])
    group_z(s, f'{pre}_List{i}Counter', zl)
    app.save()

# ================================================================== STEPS 4-6: menu, header, role tag
MENU_ROLE = {'panel': 'Panel', 'requests': 'Requests', 'dashboard': 'Dashboard', 'review': 'Review',
             'export': 'Export', 'help': 'Help'}


def menu_role(c):
    n, t = c['Name'], rule(c, 'Text') or ''
    if 'NavPanel_' in n: return 'panel'
    if 'NavBtnRequests_' in n: return 'requests'
    if 'NavBtnReview_' in n: return 'review'
    if 'NavBtnHelp_' in n: return 'help'
    if 'NavBtnDashboard_' in n: return 'export' if 'Export' in t else 'dashboard'


DOA_MENU = {menu_role(ctl(DOA, n)): n for n in next(g for g in groups(DOA) if g['Name'] == 'DOA_menu_2')['GroupedControlsKey']}
if sorted(DOA_MENU) != sorted(MENU_ROLE):
    sys.exit(f'! DOA_menu_2 roles {sorted(DOA_MENU)}')
MENU_ORDER = sorted(DOA_MENU, key=lambda k: zint(ctl(DOA, DOA_MENU[k])))      # lowest first
HDR3 = next(g for g in groups(RM) if g['Name'] == 'Header_3')
RM_PARTS = {}
for n in HDR3['GroupedControlsKey']:
    k = role_of(ctl(RM, n))
    if k != 'menu':
        RM_PARTS[k] = n
if sorted(RM_PARTS) != sorted(['Title', 'Subtitle', 'LogoEC', 'LogoCD', 'Photo', 'UserName']):
    sys.exit(f'! Header_3 parts {sorted(RM_PARTS)}')
HDR_ORDER = sorted(RM_PARTS, key=lambda k: zint(ctl(RM, RM_PARTS[k])))
# the Dashboard / Export highlight: the screens each item stands for
HL_DASH = ('If(App.ActiveScreen = DashboardScreen Or App.ActiveScreen = \'Dashboard-Ope-Administrator\' '
           'Or App.ActiveScreen = \'Dashboard-Ope-Requestor\', RGBA(56, 96, 178, 1), RGBA(0, 0, 0, 0))')
HL_EXPORT = ('If(App.ActiveScreen = HomePrintScreen Or App.ActiveScreen = PrintPhotoDetailScreen '
             'Or App.ActiveScreen = PrintVideoDetailScreen Or App.ActiveScreen = PrintPodcastDetailScreen, '
             'RGBA(56, 96, 178, 1), RGBA(0, 0, 0, 0))')
old_hl = {'dashboard': 'If(App.ActiveScreen = DashboardScreen, RGBA(56, 96, 178, 1), RGBA(0, 0, 0, 0))',
          'export': 'If(App.ActiveScreen = ReviewScreen, RGBA(56, 96, 178, 1), RGBA(0, 0, 0, 0))'}
for k, v in (('dashboard', HL_DASH), ('export', HL_EXPORT)):
    app.set(DOA, DOA_MENU[k], 'Fill', v, expect=old_hl[k])
app.save()

for s in SCREENS:
    pre = P[s]
    tp = top(s)
    tops = [c for c in tp['Children'] if not c.get('IsGroupControl')]
    old_menu = [c for c in tops if role_of(c) == 'menu'] if s != DOA else []
    if s == RM:
        old_hdr = []
    else:
        old_hdr = [c for c in tops if role_of(c) in ('Title', 'Subtitle', 'LogoEC', 'LogoCD', 'Photo', 'UserName', 'RoleTag')]
    if s != DOA and len(old_menu) != 6:
        sys.exit(f'! {s}: {len(old_menu)} menu controls')
    # the ZIndex slots the new block takes: the old main header + menu (+ role tag); a second
    # header (ChildLegalScreen's Header_CL) is removed but gives no slots
    cl_extra = set(next((g['GroupedControlsKey'] for g in groups(s) if g['Name'] == 'Header_CL'), []))
    slots = sorted(zint(c) for c in old_menu + old_hdr if c['Name'] not in cl_extra)
    if s == RM:
        slots = sorted(slots + [zint(ctl(RM, n)) for n in RM_PARTS.values()] + [zint(ctl(RM, 'HomeAppTitle_17'))])
    # delete
    gone = [c['Name'] for c in old_menu + old_hdr]
    if gone:
        delete(s, gone)
        REPORT['deleted'].setdefault(s, []).extend(gone)
    # paste: header (not on RM), role tag (not on RM), menu (not on DOA)
    block = []
    if s != RM:
        members = []
        for k in HDR_ORDER:
            n = f'{pre}_Header_{k}'
            clone(RM, RM_PARTS[k], s, n, f'{pre}_Header', {})
            members.append(n)
        new_group(RM, 'Header_3', s, f'{pre}_Header', [f'{pre}_Header_{k}' for k in HDR_ORDER])
        block += members
        clone(RM, 'HomeAppTitle_17', s, f'{pre}_RoleTag', None, {})
        block.append(f'{pre}_RoleTag')
    else:
        block += [RM_PARTS[k] for k in HDR_ORDER] + ['HomeAppTitle_17']
    if s != DOA:
        mem = []
        for k in MENU_ORDER:
            n = f'{pre}_Menu_{MENU_ROLE[k]}'
            clone(DOA, DOA_MENU[k], s, n, f'{pre}_Menu', {})
            mem.append(n)
        new_group(DOA, 'DOA_menu_2', s, f'{pre}_Menu', [f'{pre}_Menu_{MENU_ROLE[k]}' for k in MENU_ORDER])
        block += mem
    REPORT['created'][s] = block
    # z: the block fills the old slots in order (header, role tag, menu on top); if it needs
    # more slots than it had, the controls above it move up to make room
    need = len(block) - len(slots)
    if need > 0:
        hi = max(slots)
        for c in [c for c in top(s)['Children'] if not c.get('IsGroupControl')]:
            z = zint(c)
            if z is not None and z > hi and c['Name'] not in block:
                setz(s, c['Name'], z + need)
        slots += list(range(hi + 1, hi + 1 + need))
    elif need < 0:
        slots = slots[:len(block)]
    for n, z in zip(block, sorted(slots)):
        setz(s, n, z)
    for g in groups(s):
        if g['Name'] in (f'{pre}_Header', f'{pre}_Menu'):
            group_z(s, g['Name'], max(zint(ctl(s, m)) for m in g['GroupedControlsKey']))
    app.save()

# the header group keeps only the header on RequestManagementScreen (its menu moved out above)
if [n for n in HDR3['GroupedControlsKey'] if n not in RM_PARTS.values()]:
    sys.exit('! Header_3 still lists menu controls')
app.save()

# ================================================================== naming (last step)
RENAME = {
    RM: {'Header_3': 'RM_Header', 'HomeAppTitle_17': 'RM_RoleTag',
         **{RM_PARTS[k]: f'RM_Header_{k}' for k in RM_PARTS}},
    DOA: {'DOA_menu_2': 'DOA_Menu', **{DOA_MENU[k]: f'DOA_Menu_{MENU_ROLE[k]}' for k in DOA_MENU},
          'Group3': 'DOA_List1Counter', 'Circle1': 'DOA_List1CounterCircle', 'Label4': 'DOA_List1CounterText',
          'Todo List_Gallery': 'DOA_List1Gallery', 'Label2': 'DOA_List1RowTitle', 'Label1': 'DOA_List1RowDate',
          'DOA_List1RowBadge_1': 'DOA_List1RowNumber'},
}
flat_ren = {o: n for m in RENAME.values() for o, n in m.items()}
for o, n in flat_ren.items():
    if n in ALL_NAMES:
        sys.exit(f'! rename target {n} already used')


def ren_script(t):
    for o, n in flat_ren.items():
        if ' ' in o:
            t = t.replace(f"'{o}'", n)
        else:
            t = re.sub(r"(?<![\w.'])'?" + re.escape(o) + r"'?(?![\w'])", n, t)
    return t


for s in SCREENS + ['App']:
    for c in walk(top(s)):
        if c['Name'] in flat_ren:
            c['Name'] = flat_ren[c['Name']]
        if c.get('Parent') in flat_ren:
            c['Parent'] = flat_ren[c['Parent']]
        if c.get('GroupedControlsKey'):
            c['GroupedControlsKey'] = [flat_ren.get(x, x) for x in c['GroupedControlsKey']]
        for r in c['Rules']:
            r['InvariantScript'] = ren_script(r['InvariantScript'])
        for e in c.get('ControlPropertyState', []):
            if isinstance(e, dict) and e.get('AutoRuleBindingString'):
                e['AutoRuleBindingString'] = ren_script(e['AutoRuleBindingString'])
    lines = ylines(s)
    out = []
    for l in lines:
        m = re.match(r'^(\s*- )(.+?)(:\s*)$', l)
        if m and m.group(2).strip("'\"") in flat_ren:
            l = m.group(1) + flat_ren[m.group(2).strip("'\"")] + m.group(3)
        m = re.match(r'^(\s*Group: )(\S+)\s*$', l)
        if m and m.group(2) in flat_ren:
            l = m.group(1) + flat_ren[m.group(2)]
        elif not re.match(r'^\s*- ', l):
            l = ren_script(l)
        out.append(l)
    ywrite(s, out)
app.save()

# ------------------------------------------------------------------ control counts + save time
from collections import Counter
cnt = Counter(c['Template']['Name'] for s in SCREENS for c in walk(top(s)))
p = open(f'{NEW}/Properties.json', encoding='utf-8').read()
old = json.loads(p)['ControlCount']
for k, v in cnt.items():
    if k in old:
        p, n = re.subn(rf'("{k}": )\d+', rf'\g<1>{v}', p, count=1)
open(f'{NEW}/Properties.json', 'w', encoding='utf-8', newline='').write(p)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"',
           '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
json.dump({'report': REPORT, 'deleted_groups': DELETED_GROUPS, 'renamed': RENAME}, open('report_30.json', 'w'), indent=1)
print('v30 built')
