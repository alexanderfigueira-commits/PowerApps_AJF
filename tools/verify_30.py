#!/usr/bin/env python3
"""Checks for v30 against the user's v29: info icons, counters, menu, header, role tag, names.

Usage: verify_30.py [v30.msapp] [v29.msapp]
"""
import json, re, sys, zipfile

PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-30-menu-header-counters.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else '/root/.claude/uploads/4d44a760-ee6e-5284-adba-c35ebdee79f5/52259650-29.msapp'
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, ys = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('Src/') and f.endswith('.pa.yaml'):
            ys[f[4:-8]] = z.read(i).decode('utf-8')
    return js, ys


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
new, ny = load(PKG)
old, oy = load(BASE)
RM, DOA, DOR = 'RequestManagementScreen', 'Dashboard-Ope-Administrator', 'Dashboard-Ope-Requestor'
P = {'RequestManagementScreen': 'RM', 'RequesDetailScreen': 'RS', 'ChildInfoScreen': 'CI', 'ChildMetaScreen': 'CM',
     'ChildLegalScreen': 'CL', 'ChildValidScreen': 'CV', DOA: 'DOA', DOR: 'DOR', 'DashboardScreen': 'DB',
     'ReviewScreen': 'RV', 'HelpScreen': 'HL', 'HomePrintScreen': 'HP', 'PrintPhotoDetailScreen': 'PPD',
     'PrintVideoDetailScreen': 'PVD', 'PrintPodcastDetailScreen': 'PPoD'}
SCREENS = sorted(P)
check(sorted(s for s in new if s != 'App') == SCREENS, 'screen list changed')
N = {s: {c['Name']: c for c in walk(new[s])} for s in new}
O = {s: {c['Name']: c for c in walk(old[s])} for s in old}
num = lambda c, p: int(rd(c)[p])

# ---------------------------------------------------------------- package integrity
names = [c['Name'] for s in new for c in walk(new[s])]
check(len(names) == len(set(names)), 'duplicate control names')
uids = [c['ControlUniqueId'] for s in new for c in walk(new[s])]
check(len(uids) == len(set(uids)), 'duplicate ControlUniqueId')
for s in new:
    for c in walk(new[s]):
        check('Children' in c, f'{s}.{c["Name"]} has no Children key')
        for k in c.get('Children', []):
            check(k['Parent'] == c['Name'], f'{s}.{k["Name"]} parent')
        if c.get('IsGroupControl'):
            check(c['GroupedControlsKey'] and all(n in N[s] for n in c['GroupedControlsKey']), f'{s}.{c["Name"]}: group keys')
        for r in c['Rules']:
            if r['Property'].startswith('On'):
                check(r['Category'] == 'Behavior', f'{s}.{c["Name"]}.{r["Property"]} not Behavior')

# ---------------------------------------------------------------- renamed names are gone everywhere
RENAMED_OLD = ['Header_3', 'HomeAppTitle_17', 'HomeAppTitle_9', 'Logo_EC_Form_15', 'CD_Logo_9', 'HomeAppSubtitle_9',
               'Image1_16', 'HomeUserName_16', 'DOA_menu_2', 'DOA_NavPanel_MyRequestScreen_6',
               'DOA_NavBtnRequests_MyRequestScreen_6', 'DOA_NavBtnDashboard_MyRequestScreen_12',
               'DOA_NavBtnHelp_MyRequestScreen_7', 'DOA_NavBtnReview_MyRequestScreen_6',
               'DOA_NavBtnDashboard_MyRequestScreen_13', 'Group3', 'Circle1', 'Label4', 'Todo List_Gallery',
               'Label2', 'Label1', 'DOA_List1RowBadge_1']
alltext = json.dumps(new) + '\n'.join(ny.values())
for n in RENAMED_OLD:
    check(not re.search(r"(?<![\w.])'?" + re.escape(n) + r"'?(?![\w])", alltext), f'old name {n} still present')
DELETED = ['count_2', 'count_3', 'count_4', 'count_5', 'count_6', 'Circle1_1', 'Circle1_2', 'Circle1_3', 'Circle1_4',
           'Circle1_5', 'Label3_1', 'Label3_2', 'Label3_3', 'Label3_4', 'Label3_5', 'HomeAppTitle_18', 'Header_CL']
for n in DELETED:
    check(n not in names and not re.search(r'(?<![\w.])' + re.escape(n) + r'(?![\w])', alltext), f'{n} still present')

# ---------------------------------------------------------------- STEP 2: info icons
ref = N[DOA]['DOA_List1Info']
card0 = N[DOA]['DOA_List1Card']
dx, dy = num(ref, 'X') - num(card0, 'X'), num(ref, 'Y') - num(card0, 'Y')
check((dx, dy) == (12, 14), f'reference icon offset {dx},{dy}')
check(rd(ref) == rd(O[DOA]['DOA_List1Info']), 'reference icon changed')
for s, pre in ((DOA, 'DOA'), (DOR, 'DOR')):
    for i in (1, 2, 3):
        n = f'{pre}_List{i}Info'
        if n == 'DOA_List1Info':
            continue
        a, b, o = rd(N[s][n]), rd(ref), rd(O[s][n])
        skip = {'Tooltip', 'AccessibleLabel', 'ZIndex', 'X', 'Y'}
        check({k: v for k, v in a.items() if k not in skip} == {k: v for k, v in b.items() if k not in skip}, f'{n}: design differs')
        check(a['Tooltip'] == o['Tooltip'] and a['AccessibleLabel'] == o['AccessibleLabel'], f'{n}: tooltip changed')
        card = N[s][f'{pre}_List{i}Card']
        check((num(N[s][n], 'X') - num(card, 'X'), num(N[s][n], 'Y') - num(card, 'Y')) == (dx, dy), f'{n}: position')
        check(N[s][n]['Template']['Name'] == 'icon', f'{n}: control type')

# ---------------------------------------------------------------- STEP 3: counters
circ0, text0 = N[DOA]['DOA_List1CounterCircle'], N[DOA]['DOA_List1CounterText']
check(rd(circ0) == rd(O[DOA]['Circle1']), 'reference counter circle changed')
check(rd(text0)['Text'] == "Text(CountRows(DOA_List1Gallery.AllItems)) ", 'reference counter formula')
cx, cy = num(circ0, 'X') - num(card0, 'X'), num(circ0, 'Y') - num(card0, 'Y')
for s, pre in ((DOA, 'DOA'), (DOR, 'DOR')):
    for i in (1, 2, 3):
        g = next((c for c in new[s]['Children'] if c['Name'] == f'{pre}_List{i}Counter'), None)
        check(g is not None and g.get('IsGroupControl'), f'{pre}{i}: counter group')
        if g is None:
            continue
        cn, tn = f'{pre}_List{i}CounterCircle', f'{pre}_List{i}CounterText'
        check(g['GroupedControlsKey'] == [cn, tn], f'{pre}{i}: counter members')
        card = N[s][f'{pre}_List{i}Card']
        for n, refc in ((cn, circ0), (tn, text0)):
            a, b = rd(N[s][n]), rd(refc)
            skip = {'X', 'Y', 'ZIndex', 'Text'}
            check({k: v for k, v in a.items() if k not in skip} == {k: v for k, v in b.items() if k not in skip}, f'{n}: design')
            check((num(N[s][n], 'X') - num(card, 'X'), num(N[s][n], 'Y') - num(card, 'Y')) == (cx, cy), f'{n}: position')
        check(rd(N[s][tn])['Text'] == f"Text(CountRows({pre}_List{i}Gallery.AllItems)) ", f'{tn}: formula')
        # above its card and title
        check(num(N[s][cn], 'ZIndex') > max(num(N[s][f'{pre}_List{i}{p}'], 'ZIndex') for p in ('Card', 'Accent', 'Title')),
              f'{cn}: under the card')
        check(num(N[s][tn], 'ZIndex') > num(N[s][cn], 'ZIndex'), f'{tn}: under its circle')

# ---------------------------------------------------------------- STEPS 4-6: menu, header, role tag on every screen
MENU = ['Panel', 'Requests', 'Dashboard', 'Review', 'Export', 'Help']
HDR = ['Title', 'LogoEC', 'LogoCD', 'Subtitle', 'Photo', 'UserName']
mref = {k: N[DOA][f'DOA_Menu_{k}'] for k in MENU}
href = {k: N[RM][f'RM_Header_{k}'] for k in HDR}
tref = N[RM]['RM_RoleTag']
check(rd(tref) == rd(O[RM]['HomeAppTitle_17']) | {'ZIndex': rd(tref)['ZIndex']}, 'master role tag changed')
for k in HDR:
    oldn = {'Title': 'HomeAppTitle_9', 'LogoEC': 'Logo_EC_Form_15', 'LogoCD': 'CD_Logo_9', 'Subtitle': 'HomeAppSubtitle_9',
            'Photo': 'Image1_16', 'UserName': 'HomeUserName_16'}[k]
    a, b = rd(href[k]), rd(O[RM][oldn])
    check({x: y for x, y in a.items() if x != 'ZIndex'} == {x: y for x, y in b.items() if x != 'ZIndex'}, f'master header {k} changed')
check(rd(href['UserName'])['Align'] == 'Align.Right', 'master user name not right aligned')
DASH_HL = ("If(App.ActiveScreen = DashboardScreen Or App.ActiveScreen = 'Dashboard-Ope-Administrator' "
           "Or App.ActiveScreen = 'Dashboard-Ope-Requestor', RGBA(56, 96, 178, 1), RGBA(0, 0, 0, 0))")
check(rd(mref['Dashboard'])['Fill'] == DASH_HL, 'master Dashboard highlight')
check('App.ActiveScreen = HomePrintScreen' in rd(mref['Export'])['Fill'] and 'ReviewScreen' not in rd(mref['Export'])['Fill'],
      'master Export highlight')
oldm = {'Panel': 'DOA_NavPanel_MyRequestScreen_6', 'Requests': 'DOA_NavBtnRequests_MyRequestScreen_6',
        'Dashboard': 'DOA_NavBtnDashboard_MyRequestScreen_12', 'Review': 'DOA_NavBtnReview_MyRequestScreen_6',
        'Export': 'DOA_NavBtnDashboard_MyRequestScreen_13', 'Help': 'DOA_NavBtnHelp_MyRequestScreen_7'}
for k in MENU:
    a, b = rd(mref[k]), rd(O[DOA][oldm[k]])
    check({x: y for x, y in a.items() if x != 'Fill'} == {x: y for x, y in b.items() if x != 'Fill'}, f'master menu {k} changed')
check(rd(mref['Review'])['Visible'] == 'varUserRole = "ADMINISTRATOR"', 'Review role visibility')
check(rd(tref)['Visible'] == 'varUserRole = "ADMINISTRATOR"', 'role tag visibility')
SCREEN_NAMES = set(P)
for s in SCREENS:
    pre = P[s]
    tops = [c for c in new[s]['Children'] if not c.get('IsGroupControl')]
    gs = {c['Name']: c for c in new[s]['Children'] if c.get('IsGroupControl')}
    # exactly one menu, one header, one role tag
    navs = [c['Name'] for c in tops if re.search(r'NavPanel_|NavBtn|_Menu_', c['Name'])]
    check(sorted(navs) == sorted(f'{pre}_Menu_{k}' for k in MENU), f'{s}: menu controls {navs}')
    check(f'{pre}_Menu' in gs and sorted(gs[f'{pre}_Menu']['GroupedControlsKey']) == sorted(f'{pre}_Menu_{k}' for k in MENU),
          f'{s}: menu group')
    check(f'{pre}_Header' in gs and sorted(gs[f'{pre}_Header']['GroupedControlsKey']) == sorted(f'{pre}_Header_{k}' for k in HDR),
          f'{s}: header group')
    for k in MENU:
        a, b = rd(N[s][f'{pre}_Menu_{k}']), rd(mref[k])
        check({x: y for x, y in a.items() if x != 'ZIndex'} == {x: y for x, y in b.items() if x != 'ZIndex'}, f'{s}: menu {k} differs')
        for tgt in re.findall(r"Navigate\(\s*'?([\w-]+)'?", a.get('OnSelect', '')):
            check(tgt in SCREEN_NAMES, f'{s}: menu {k} navigates to unknown {tgt}')
    for k in HDR:
        a, b = rd(N[s][f'{pre}_Header_{k}']), rd(href[k])
        check({x: y for x, y in a.items() if x != 'ZIndex'} == {x: y for x, y in b.items() if x != 'ZIndex'}, f'{s}: header {k} differs')
    a = rd(N[s][f'{pre}_RoleTag'])
    check({x: y for x, y in a.items() if x != 'ZIndex'} == {x: y for x, y in rd(tref).items() if x != 'ZIndex'}, f'{s}: role tag differs')
    # no other title / logo / user-name / role-tag control left
    others = [c['Name'] for c in tops if not c['Name'].startswith((f'{pre}_Header_', f'{pre}_RoleTag')) and (
        (c['Template']['Name'] == 'label' and ((rd(c).get('Text', '').strip() in ('"Central Deposit"', '"Ticket System"'))
                                              or rd(c).get('Text', '').startswith('User().FullName')
                                              or re.fullmatch(r'"\| (Administrator|" & varUserRole)', rd(c).get('Text', '').strip())))
        or (c['Template']['Name'] == 'image' and rd(c).get('Image', '') in ('User().Image', 'cd_badge_play')
            or 'LOGO CE' in rd(c).get('Image', '') or 'logo--en' in rd(c).get('Image', '')))]
    check(not others, f'{s}: old header controls left: {others}')
    # z: menu above header and role tag; top bar below everything in the block; nothing unconditional on top
    z = {c['Name']: int(rd(c)['ZIndex']) for c in tops if rd(c).get('ZIndex', '').isdigit()}
    hz = [z[f'{pre}_Header_{k}'] for k in HDR] + [z[f'{pre}_RoleTag']]
    mz = [z[f'{pre}_Menu_{k}'] for k in MENU]
    check(min(mz) > max(z[f'{pre}_Header_{k}'] for k in HDR), f'{s}: header above the menu')
    check([z[f'{pre}_Menu_{k}'] for k in sorted(MENU, key=lambda k: int(rd(mref[k])['ZIndex']))] == sorted(mz), f'{s}: menu order')
    area = [(0, 0, 1366, 57)]
    for c in tops:
        n = c['Name']
        if n.startswith((f'{pre}_Header_', f'{pre}_Menu_', f'{pre}_RoleTag')) or n not in z:
            continue
        r_ = rd(c)
        try:
            x, y, w, h = (int(r_[p]) for p in ('X', 'Y', 'Width', 'Height'))
        except (KeyError, ValueError):
            continue
        if y >= 57 or x + w <= 0:
            continue
        vis = r_.get('Visible', 'true').strip()
        if z[n] > min(hz + mz) and vis == 'true':
            check(False, f'{s}: {n} (always visible) draws above the header/menu')
        if c['Template']['Name'] == 'rectangle' and y == 0 and w == 1366 and h in (56,):
            check(z[n] < min(hz + mz), f'{s}: top bar {n} above the header')
    # user name: right aligned (header copy)
    check(rd(N[s][f'{pre}_Header_UserName'])['Align'] == 'Align.Right', f'{s}: user name not right aligned')

# ---------------------------------------------------------------- nothing else changed
RENAME = {'Header_3': 'RM_Header', 'HomeAppTitle_17': 'RM_RoleTag', 'HomeAppTitle_9': 'RM_Header_Title',
          'Logo_EC_Form_15': 'RM_Header_LogoEC', 'CD_Logo_9': 'RM_Header_LogoCD', 'HomeAppSubtitle_9': 'RM_Header_Subtitle',
          'Image1_16': 'RM_Header_Photo', 'HomeUserName_16': 'RM_Header_UserName', 'DOA_menu_2': 'DOA_Menu',
          **{v: f'DOA_Menu_{k}' for k, v in oldm.items()}, 'Group3': 'DOA_List1Counter', 'Circle1': 'DOA_List1CounterCircle',
          'Label4': 'DOA_List1CounterText', 'Todo List_Gallery': 'DOA_List1Gallery', 'Label2': 'DOA_List1RowTitle',
          'Label1': 'DOA_List1RowDate', 'DOA_List1RowBadge_1': 'DOA_List1RowNumber'}


def ren(t):
    for o, n in RENAME.items():
        t = t.replace(f"'{o}'", n) if ' ' in o else re.sub(r"(?<![\w.'])'?" + re.escape(o) + r"'?(?![\w'])", n, t)
    return t


touched = set()
for s in SCREENS:
    pre = P[s]
    touched |= {n for n in N[s] if n.startswith((f'{pre}_Header', f'{pre}_Menu', f'{pre}_RoleTag')) or re.match(rf'{pre}_List\dCounter', n)}
touched |= {f'{p}_List{i}Info' for p in ('DOA', 'DOR') for i in (1, 2, 3)}
touched |= {'DOA_Menu_Dashboard', 'DOA_Menu_Export'}
removed = []
for s in SCREENS:
    for n, c in O[s].items():
        nn = RENAME.get(n, n)
        if nn not in N[s]:
            removed.append((s, n))
            continue
        if nn in touched or c.get('IsGroupControl') or n == s:
            continue
        a = {k: v for k, v in rd(N[s][nn]).items() if k != 'ZIndex'}
        b = {k: ren(v) for k, v in rd(c).items() if k != 'ZIndex'}
        check(a == b, f'{s}: {nn} changed')
    if s in N[s]:
        check(rd(N[s][s]) == {k: ren(v) for k, v in rd(O[s][s]).items()}, f'{s}: screen properties changed')
# every removed control is an old menu / header / counter / role tag
for s, n in removed:
    c = O[s][n]
    t = c['Template']['Name']
    ok = (re.search(r'NavPanel_|NavBtn', n) or re.match(r'(Circle1_[1-5]|Label3_[1-5]|count_[2-6]|HomeAppTitle_18)$', n)
          or c.get('IsGroupControl') or (t == 'label' and (rd(c).get('Text', '').strip() in ('"Central Deposit"', '"Ticket System"')
                                                          or rd(c).get('Text', '').startswith('User().FullName')))
          or (t == 'image' and (rd(c).get('Image') in ('User().Image', 'cd_badge_play') or 'LOGO CE' in rd(c).get('Image', '')
                                or 'logo--en' in rd(c).get('Image', ''))))
    check(ok, f'{s}: {n} removed but not a menu/header/counter control')
# relative z order of the untouched controls is kept
for s in SCREENS:
    keep = [(RENAME.get(c['Name'], c['Name']), int(rd(c)['ZIndex'])) for c in old[s]['Children']
            if not c.get('IsGroupControl') and rd(c).get('ZIndex', '').isdigit() and RENAME.get(c['Name'], c['Name']) in N[s]
            and RENAME.get(c['Name'], c['Name']) not in touched]
    after = {n: int(rd(N[s][n])['ZIndex']) for n, _ in keep}
    for (a, za), (b, zb) in zip(sorted(keep, key=lambda x: x[1]), sorted(keep, key=lambda x: x[1])[1:]):
        if za < zb:
            check(after[a] < after[b], f'{s}: z order of {a} / {b} changed')

print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails[:80]:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
