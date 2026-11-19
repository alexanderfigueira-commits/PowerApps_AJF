#!/usr/bin/env python3
"""FINAL157, last step: the compact print layout is eliminated (the normal one prints fine).
 * PPD_ChkCompact / PPoD_ChkCompact deleted (PVD_ChkCompact went in FINAL145).
 * every If(locPrinting And Coalesce(varCompactPrint, false), <compact>, <full>) on the three print screens becomes <full>,
   so no formula refers to varCompactPrint any more."""
import datetime, glob, json, os, re, shutil
from payaml import App, find, block_span
SRC, NEW = 'newV18', 'newV19'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
PRE = 'If(locPrinting And Coalesce(varCompactPrint, false), '

def split_top(s):
    """top-level comma split (strings and brackets respected)"""
    out, depth, cur, i, instr = [], 0, '', 0, False
    while i < len(s):
        c = s[i]
        if instr:
            cur += c
            if c == '"':
                if s[i + 1:i + 2] == '"': cur += '"'; i += 1
                else: instr = False
        elif c == '"': instr = True; cur += c
        elif c in '([{': depth += 1; cur += c
        elif c in ')]}': depth -= 1; cur += c
        elif c == ',' and depth == 0: out.append(cur); cur = ''
        else: cur += c
        i += 1
    out.append(cur)
    return out

# ---- 1. the two checkboxes -----------------------------------------------------------------------------------------------
for screen, name in (('PrintPhotoDetailScreen', 'PPD_ChkCompact'), ('PrintPodcastDetailScreen', 'PPoD_ChkCompact')):
    tp = app.doc(screen)['TopParent']
    node = find(tp, name)
    assert node and node['Parent'] == screen and not node.get('Children'), name
    assert not any(name in (g.get('GroupedControlsKey') or []) for g in tp['Children'] if g.get('IsGroupControl')), name
    n0 = len(tp['Children']); tp['Children'] = [c for c in tp['Children'] if c['Name'] != name]; assert n0 - len(tp['Children']) == 1
app.save()
for screen, name in (('PrintPhotoDetailScreen', 'PPD_ChkCompact'), ('PrintPodcastDetailScreen', 'PPoD_ChkCompact')):
    yp = f'{NEW}/Src/{screen}.pa.yaml'
    L = open(yp, encoding='utf-8', newline='').read().replace('\r\n', '\n').replace('\r', '\n').split('\n')
    s, e = block_span(L, name)
    del L[s:e]
    open(yp, 'w', encoding='utf-8', newline='').write('\n'.join(L))
app = App(NEW)

# ---- 2. the compact geometry ---------------------------------------------------------------------------------------------
n = 0
for screen in ('PrintPhotoDetailScreen', 'PrintVideoDetailScreen', 'PrintPodcastDetailScreen'):
    tp = app.doc(screen)['TopParent']
    def walk(x):
        yield x
        for c in x.get('Children', []): yield from walk(c)
    for c in walk(tp):
        for r in c['Rules']:
            t = r['InvariantScript']
            if 'varCompactPrint' not in t: continue
            assert t.startswith(PRE) and t.endswith(')'), (screen, c['Name'], r['Property'], t)
            parts = split_top(t[len(PRE):-1])
            assert len(parts) == 2 and 'varCompactPrint' not in parts[1], (screen, c['Name'], r['Property'], parts)
            app.set(screen, c['Name'], r['Property'], parts[1].strip(), expect=t); n += 1
app.save()
print('compact formulas replaced by the full value:', n)
for f in glob.glob(f'{NEW}/Controls/*.json') + glob.glob(f'{NEW}/Src/*.yaml'):
    s = open(f, encoding='utf-8').read()
    assert 'varCompactPrint' not in s and 'ChkCompact' not in s, f
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL157 (compact print removed) built')
