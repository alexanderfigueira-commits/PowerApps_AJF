import json, glob, re, math
COND = re.compile(r'^If\(locPrinting And Coalesce\(varCompactPrint, false\), (\d+), (\d+)\)$')
def two(v, default=None):
    v = (v or '').strip()
    m = COND.match(v)
    if m: return int(m.group(1)), int(m.group(2))
    if re.fullmatch(r'\d+', v): return int(v), int(v)
    return default
def line_h(size): return math.ceil(size * 1.3333 * 1.40)
def cpl(size, width): return max(4, int((width - 12) / (size * 1.3333 * 0.57) * 0.92))
def text_lines(text, size, width): return max(1, math.ceil(len(text) / cpl(size, width)))
def load(tree, screen):
    for f in glob.glob(f'{tree}/Controls/*.json'):
        j = json.load(open(f, encoding='utf-8-sig'))
        if j['TopParent']['Name'] == screen: return j['TopParent']
def R(n): return {x['Property']: x['InvariantScript'].replace('\r\n', '\n') for x in n['Rules']}
def walk(n):
    yield n
    for c in n.get('Children', []): yield from walk(c)
def analyse(tree, screen, prefix):
    tp = load(tree, screen)
    g = [n for n in walk(tp) if n['Name'] == f'{prefix}_Gallery'][0]
    el = {}
    for n in list(walk(g))[1:]:
        if n['Template']['Name'] != 'label': continue
        r = R(n); el[n['Name']] = r
    # original absolute Y (all visible)
    memo = {}
    def y(name):
        if name in memo: return memo[name]
        v = el[name]['Y'].strip()
        if re.fullmatch(r'\d+', v): res = int(v)
        else:
            m = re.fullmatch(r'(\w+)\.Y(?: \+ If\(\1\.Visible, \1\.Height, 0\))?', v)
            assert m, (name, v)
            a = m.group(1); res = y(a) + (int(el[a]['Height']) if '+' in v else 0)
        memo[name] = res; return res
    items = []
    for name, r in el.items():
        kind = 'cap' if name.endswith('RowCaption') else 'sec' if '_Sec' in name else 'lbl' if '_Lbl' in name else 'val' if '_Val' in name else '?'
        xs = two(r.get('X')); ws = two(r.get('Width')); ss = two(r.get('Size'))
        items.append(dict(name=name, kind=kind, y=y(name), h=int(r['Height']), xc=xs[0], xf=xs[1], wc=ws[0], wf=ws[1], sc=ss[0], sf=ss[1],
                          text=r.get('Text', ''), vis=r.get('Visible', 'true')))
    for it in items: it['col'] = 0 if it['xf'] < 430 else 1 if it['xf'] < 860 else 2
    return tp, g, items
