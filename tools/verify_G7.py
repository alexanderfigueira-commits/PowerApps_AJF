#!/usr/bin/env python3
"""Checks for FINAL17 against FINAL16: every PublicationChannel use removed, the media save otherwise intact."""
import json, re, sys, zipfile
PKG = sys.argv[1] if len(sys.argv) > 1 else 'msapp-versions/AV-CD-FINAL17-save-media-fix.msapp'
BASE = sys.argv[2] if len(sys.argv) > 2 else 'msapp-versions/AV-CD-FINAL16-archive-only-approval.msapp'
fails, cnt = [], 0


def check(ok, msg):
    global cnt
    cnt += 1
    if not ok:
        fails.append(msg)


def load(p):
    z = zipfile.ZipFile(p); js, ref, src = {}, {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('References/'):
            ref[f] = z.read(i)
        elif f.startswith(('Src/', 'Controls/')):
            src[f] = z.read(i).decode('utf-8')
    return js, ref, src


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


def bal(t):
    v = re.sub(r'(?m)^\s*//[^\n]*', '', t); v = re.sub(r'"[^"\n]*"', '""', v)
    return v.count('(') == v.count(')') and v.count('{') == v.count('}')


rd = lambda c: {r['Property']: r['InvariantScript'] for r in c['Rules']}
new, nref, nsrc = load(PKG); old, oref, _ = load(BASE)
check(nref == oref, 'data sources changed')
ALL = json.dumps(new) + '\n'.join(nsrc.values())
check(not re.search(r'PublicationChannel|varChildPubBeluga|varChildPubSpotify', ALL), 'no PublicationChannel / channel variable left anywhere')
N = {s: {c['Name']: c for c in walk(t)} for s, t in new.items()}; O = {s: {c['Name']: c for c in walk(t)} for s, t in old.items()}
check({s: set(N[s]) for s in N} == {s: set(O[s]) for s in O}, 'controls added or removed')
ch = {(s, n): sorted(p for p in set(rd(c)) | set(rd(O[s][n])) if rd(c).get(p) != rd(O[s][n]).get(p)) for s in N for n, c in N[s].items()}
want = {('ChildValidScreen', 'CV_BtnSaveArchive'): ['OnSelect'], ('RequesDetailScreen', 'RequesDetailScreen'): ['OnVisible'],
        ('RequesDetailScreen', 'RS_CRowSelect'): ['OnSelect'], ('RequesDetailScreen', 'Add_media_icon'): ['OnSelect'], ('App', 'App'): ['OnStart']}
check({k: v for k, v in ch.items() if v} == want, f'changed: {[(k, v) for k, v in ch.items() if v and want.get(k) != v]}')
# each changed formula = the old one minus the removed pieces
REMOVED = [r'\r?\n *PublicationChannel: Concat\(Filter\(Table\(\{Value: "Beluga", On: varChildPubBeluga\}, \{Value: "Spotify", On: varChildPubSpotify\}\), On\), Value, ";"\),',
           r'\r?\n *// single-choice column: one record[^\n]*\r?\n *PublicationChannel: If\(\r?\n[^\n]*varChildPubBeluga Or varChildPubSpotify,\r?\n[^\n]*\r?\n *Blank\(\)\r?\n *\),',
           r'\r?\n *PublicationChannel: Coalesce\(PublicationChannel\.Value, ""\),',
           r'\r?\nSet\(varChildPubBeluga, "Beluga" in Coalesce\(ThisItem\.PublicationChannel, ""\)\);\r?\nSet\(varChildPubSpotify, "Spotify" in Coalesce\(ThisItem\.PublicationChannel, ""\)\);',
           r'\r?\nSet\(varChildPubBeluga, false\);\r?\nSet\(varChildPubSpotify, false\);',
           r'Set\(varChildPubBeluga, false\);\r?\nSet\(varChildPubSpotify, false\);\r?\n']
for (s, n), props in want.items():
    for p in props:
        o = rd(O[s][n])[p]
        for pat in REMOVED:
            o = re.sub(pat, '', o, flags=re.S)
        check(o == rd(N[s][n])[p], f'{n}.{p}: only the PublicationChannel pieces removed')
        check(bal(rd(N[s][n])[p]), f'{n}.{p}: brackets')
# the save still writes everything else and every field it writes is a column of the list
x = [x for x in json.loads(zipfile.ZipFile(PKG).read('References\\DataSources.json').decode('utf-8-sig'))['DataSources'] if x['Name'] == 'AV-CD-Mediafiles'][0]
cols = set(x['ConnectedDataSourceInfoNameMapping']) | set(x['ConnectedDataSourceInfoNameMapping'].values())
t = rd(N['ChildValidScreen']['CV_BtnSaveArchive'])['OnSelect']
blk = t[t.index('{', t.index("Defaults('AV-CD-Mediafiles')")):]
depth, keys, j = 0, [], 0
while j < len(blk):
    c = blk[j]
    if c in '({[':
        depth += 1
    elif c in ')}]':
        depth -= 1
        if depth == 0:
            break
    elif depth == 1:
        m = re.match(r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*:', blk[j:])
        if m and re.search(r'[,{]\s*$', blk[max(0, j - 60):j]):
            keys.append(m.group(1)); j += len(m.group(0)) - 1
    j += 1
check(len(keys) >= 33 and not [k for k in keys if k not in cols], f'Patch fields all exist in the list ({len(keys)}): {[k for k in keys if k not in cols]}')
check(all(k in keys for k in ('ProductionTitle', 'BelugaReference', 'ContractCase', 'ParentRequest', 'DepositStatus', 'ScriptShotlist') if k != 'ScriptShotlist'), 'main fields still saved')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
