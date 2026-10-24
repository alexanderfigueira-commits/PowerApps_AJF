import json, re, glob, os, sys
from collections import defaultdict
TREE = sys.argv[1]

def clean(t):
    """drop comments and string contents (keep the quotes), keep everything else"""
    out = []; i = 0; n = len(t); instr = False
    while i < n:
        c = t[i]
        if instr:
            if c == '"':
                if i + 1 < n and t[i + 1] == '"': i += 2; continue
                instr = False; out.append('"')
            i += 1; continue
        if c == '"': instr = True; out.append('"'); i += 1; continue
        if c == '/' and i + 1 < n and t[i + 1] == '/':
            while i < n and t[i] != '\n': i += 1
            continue
        if c == '/' and i + 1 < n and t[i + 1] == '*':
            j = t.find('*/', i + 2); i = n if j < 0 else j + 2; continue
        out.append(c); i += 1
    return ''.join(out)

def match_paren(t, i):   # t[i] == '('
    d = 0
    for j in range(i, len(t)):
        if t[j] == '(': d += 1
        elif t[j] == ')':
            d -= 1
            if d == 0: return j
    return len(t) - 1

def record_keys(rec):    # top-level keys of {a: 1, b: {c: 2}}
    keys = []; d = 0; i = 0; start = True
    s = rec.strip()
    if s.startswith('{'): s = s[1:]
    d = 0; buf = ''
    for ch in s:
        if ch in '({[': d += 1
        elif ch in ')}]': d -= 1
        if d == 0 and ch == ',':
            keys.append(buf); buf = ''
        else: buf += ch
    keys.append(buf)
    res = []
    for k in keys:
        m = re.match(r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*:', k)
        if m: res.append(m.group(1))
    return res

writes = defaultdict(list)    # name -> [(kind, where)]
reads = defaultdict(list)
rules = []
for f in sorted(glob.glob(f'{TREE}/Controls/*.json')):
    d = json.load(open(f, encoding='utf-8'))
    screen = d['TopParent']['Name']
    def walk(n):
        yield n
        for c in n.get('Children', []): yield from walk(c)
    for n in walk(d['TopParent']):
        for r in n['Rules']:
            rules.append((screen, n['Name'], r['Property'], clean(r['InvariantScript'])))

# pass 1: writes
wpos = defaultdict(set)   # rule index -> set of (start,end) of identifier occurrences that are write targets
for idx, (scr, ctl, prop, t) in enumerate(rules):
    for m in re.finditer(r'\b(Set)\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,', t):
        writes[m.group(2)].append(('global', f'{scr}.{ctl}.{prop}')); wpos[idx].add(m.start(2))
    for m in re.finditer(r'\b(Collect|ClearCollect|Clear|RemoveIf|UpdateIf|Remove|Patch)\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*[,)]', t):
        nm = m.group(2)
        if nm.startswith('col'):
            writes[nm].append(('collection', f'{scr}.{ctl}.{prop}')); wpos[idx].add(m.start(2))
    for m in re.finditer(r'\bUpdateContext\s*\(', t):
        e = match_paren(t, m.end() - 1)
        inner = t[m.end():e]
        for k in record_keys(inner):
            writes[k].append(('context', f'{scr}.{ctl}.{prop}'))
            for mm in re.finditer(r'(?<![A-Za-z0-9_])' + re.escape(k) + r'\s*:', inner):
                wpos[idx].add(m.end() + mm.start())
    for m in re.finditer(r'\bNavigate\s*\(', t):
        e = match_paren(t, m.end() - 1)
        inner = t[m.end():e]
        b = inner.find('{')
        if b >= 0:
            rec = inner[b:]
            for k in record_keys(rec):
                writes[k].append(('navigate-context', f'{scr}.{ctl}.{prop}'))
                for mm in re.finditer(r'(?<![A-Za-z0-9_])' + re.escape(k) + r'\s*:', rec):
                    wpos[idx].add(m.end() + b + mm.start())

names = set(writes)
# pass 2: reads
for idx, (scr, ctl, prop, t) in enumerate(rules):
    for nm in names:
        for m in re.finditer(r'(?<![A-Za-z0-9_.])' + re.escape(nm) + r'(?![A-Za-z0-9_])', t):
            if m.start() in wpos[idx]: continue
            # a record key inside some other record literal (e.g. {Title: x}) is not a read of a variable called Title
            if re.match(r'\s*:', t[m.end():]) and writes[nm][0][0] in ('context', 'navigate-context') is False: pass
            reads[nm].append(f'{scr}.{ctl}.{prop}')

unused = sorted(n for n in names if not reads[n])
print('screens/rules scanned:', len(rules), '| names written:', len(names))
kinds = defaultdict(list)
for n in names: kinds[writes[n][0][0]].append(n)
for k, v in kinds.items(): print(f'  {k}: {len(v)}')
print('\nSET BUT NEVER READ:')
for n in unused:
    w = writes[n]
    print(f'  {n:34} {w[0][0]:16} written {len(w)}x, first in {w[0][1]}')
json.dump({n: {'writes': writes[n], 'reads': reads[n]} for n in names}, open('ana/usage.json', 'w'), indent=1)
