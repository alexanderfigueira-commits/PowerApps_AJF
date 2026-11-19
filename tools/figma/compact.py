import json, re
data = json.load(open('all.json'))
ICON = {'Icon.Note':'N','Icon.Information':'i','Icon.Reload':'R','Icon.GlobeNotConnected':'!','Icon.Clock':'C','Icon.NextArrow':'>','Icon.Bell':'B','Icon.Edit':'E','Icon.Check':'v','Icon.BackArrow':'<','Icon.Save':'S','Icon.AddLibrary':'+'}
def compact(d):
    pal = []
    def ci(c):
        if c is None: return -1
        c = [int(c[0]), int(c[1]), int(c[2]), round(float(c[3]), 2)]
        if c not in pal: pal.append(c)
        return pal.index(c)
    def fi(c):
        if c is None or c[3] == 0: return -1
        return ci(c)
    bg = ci(d['fill'] or [255, 255, 255, 1])
    o = []
    for op in d['ops']:
        if op[0] == 'gal':
            o.append(['g', op[1], op[2], op[3], op[4], 0]); continue
        t, x, y, w, h, fill, col, bcol, bth, rad, text, size, wt, al, va, name, icon, row = op
        ing = 1 if row >= 0 else 0
        if t == 'rectangle': o.append(['r', x, y, w, h, fi(fill), fi(bcol) if bth else -1, int(bth), int(rad), ing]); continue
        if t == 'label':
            if not (text or (fill and fill[3] > 0)): continue
            o.append(['l', x, y, w, h, fi(fill), ci(col), text or '', int(size), wt, al, va, ing]); continue
        if t == 'button':
            o.append(['b', x, y, w, h, fi(fill), ci(col), fi(bcol) if bth else -1, int(bth), int(rad), text or '', int(size), wt, ing]); continue
        if t in ('text', 'combobox', 'dropdown', 'datepicker'):
            kind = 2 if t == 'datepicker' else 1 if t in ('combobox', 'dropdown') else 0
            o.append(['i', x, y, w, h, kind, text or '', ing]); continue
        if t == 'checkbox': o.append(['c', x, y, w, h, text or '', ing]); continue
        if t == 'image': o.append(['m', x, y, w, h, 'logo' if re.search('logo|Photo', name) else 'image', ing]); continue
        if t == 'icon': o.append(['o', x, y, w, h, ci(col), ICON.get(icon, '?'), ing]); continue
        if t == 'attachments': o.append(['m', x, y, w, h, 'attachments', ing]); continue
    return {'n': d['screen'], 'v': d['variant'], 'f': bg, 'p': pal, 'o': o}
comp = [compact(d) for d in data]
json.dump(comp, open('comp.json', 'w'), ensure_ascii=False)
tot = 0
for c in comp:
    n = len(json.dumps(c, separators=(',', ':'), ensure_ascii=False)); tot += n
    print(f"{c['n']:30s} {c['v']:40s} ops={len(c['o']):4d} chars={n}")
print('total', tot)
