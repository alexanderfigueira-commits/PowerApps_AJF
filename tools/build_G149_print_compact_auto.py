#!/usr/bin/env python3
"""FINAL160 on TEST_14 (= FINAL159 + the user's small edits, all kept).
The compact print layout is back, and now chosen by itself:
 * the three print screens get back their If(locPrinting And Coalesce(varCompactPrint, false), <compact>, <full>) geometry
   (the 696 formulas of FINAL152, verified one by one against what TEST_14 has as the full value);
 * nothing to tick: each print screen sets varCompactPrint when it opens:
       Param("print") = "full"    -> full size       (forced, e.g. link ...&print=full)
       Param("print") = "compact" -> compact         (forced)
       otherwise                  -> compact when the URL has no tenantId (Power Apps Studio preview, where the page is enlarged by the
                                     window scale and the full layout is cut on the right), full size in the published app.
 The three Compact checkboxes stay deleted."""
import datetime, glob, json, os, re, shutil
from payaml import App, screens
SRC, NEW, REF152 = 'newT14', 'newV22', 'newV12'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
PRE = 'If(locPrinting And Coalesce(varCompactPrint, false), '

def split_top(s):
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

def rules(path):
    out = {}
    for s, f in screens(path).items():
        d = json.load(open(f, encoding='utf-8'))
        def walk(n):
            yield n
            for c in n.get('Children', []): yield from walk(c)
        for n in walk(d['TopParent']):
            for r in n['Rules']: out[(s, n['Name'], r['Property'])] = r['InvariantScript']
    return out

old = rules(REF152)
cur = rules(SRC)
n = 0
for (s, c, p), t in sorted(old.items()):
    if not t.startswith(PRE): continue
    parts = split_top(t[len(PRE):-1])
    assert len(parts) == 2
    have = cur[(s, c, p)]
    assert ' '.join(have.split()) == ' '.join(parts[1].split()), (s, c, p, have, parts[1])      # the full value is what is there now
    app.set(s, c, p, t, expect=have); n += 1
print('compact geometry restored:', n)

SET = '''// the compact geometry is for prints made from Studio's preview (the page there gets the screen enlarged by the window scale and the full
// layout is cut on the right); the published app prints full size. &print=full or &print=compact in the app link forces one of them.
Set(varCompactPrint, Switch(Param("print"), "full", false, "compact", true, IsBlank(Param("tenantId"))));
'''
for screen in ('PrintPhotoDetailScreen', 'PrintVideoDetailScreen', 'PrintPodcastDetailScreen'):
    t = app.rule(screen, None, 'OnVisible')
    assert t.startswith('// media rows of the request chosen on HomePrintScreen'), screen
    app.set(screen, None, 'OnVisible', SET + t, expect=t)
app.save()
for f in glob.glob(f'{NEW}/Controls/*.json'):
    assert 'ChkCompact' not in open(f, encoding='utf-8').read(), f
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL160 built')
