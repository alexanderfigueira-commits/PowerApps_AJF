#!/usr/bin/env python3
"""FINAL176 on FINAL174 (isolated: NOT on FINAL175, so it can be tested on its own).
Removes the variables Studio lists as unused (app-UnusedVariables) plus the unused collection colDGOptions:
MyProfile, varRequestOwnerEmail, varChildDescription, varChildProductionPlace, varChildCredits, varChildEpisodeSummary, varChildSeriesTitle, varChildLinks, varChildFTPPath,
varPendingMediaType, varConfirmed, varKpiMyMonthTotal, varKpiMyMonthSuccess, varKpiAllMonthTotal, varKpiAllMonthSuccess, varNavArm, currentIndex (the global; the screen's
context variable of the same name stays), varChildEpisodeTitle1, varFilterRequestName, varRequestContractor, varRequestDescription1, and colDGOptions."""
import datetime, os, re, shutil
from payaml import App, _fmt
SRC, NEW = 'newV36', 'newV38'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))

VARS = ('MyProfile varRequestOwnerEmail varChildDescription varChildProductionPlace varChildCredits varChildEpisodeSummary varChildSeriesTitle varChildLinks varChildFTPPath '
        'varPendingMediaType varConfirmed varKpiMyMonthTotal varKpiMyMonthSuccess varKpiAllMonthTotal varKpiAllMonthSuccess varNavArm currentIndex varChildEpisodeTitle1 '
        'varFilterRequestName varRequestContractor varRequestDescription1').split()
STARTS = [re.compile(r'(?<![A-Za-z0-9_.])Set\(\s*' + v + r'\s*,') for v in VARS] + \
         [re.compile(r'(?<![A-Za-z0-9_.])(ClearCollect|Collect)\(\s*colDGOptions\s*,')]


def match_paren(t, i):
    d = 0; instr = False; j = i
    while j < len(t):
        c = t[j]
        if instr:
            if c == '"':
                if j + 1 < len(t) and t[j + 1] == '"': j += 2; continue
                instr = False
        else:
            if c == '"': instr = True
            elif c in '({[': d += 1
            elif c in ')}]':
                d -= 1
                if d == 0: return j
        j += 1
    raise SystemExit('unbalanced')


def remove_statements(t):
    """drop every statement matching STARTS; returns (new text, count)"""
    n = 0
    while True:
        hit = None
        for rx in STARTS:
            m = rx.search(t)
            if m and (hit is None or m.start() < hit.start()): hit = m
        if not hit: return t, n
        s = hit.start()
        e = match_paren(t, t.index('(', s)) + 1          # just after the closing parenthesis
        after = re.match(r'[ \t]*;[ \t]*', t[e:])
        if after:                                           # a statement followed by ';'
            e2 = e + after.end()
            ls = t.rfind('\n', 0, s) + 1
            if t[ls:s].strip() == '' and t[e2:e2 + 1] == '\n':   # it had its own line: drop the line
                s, e2 = ls, e2 + 1
            t = t[:s] + t[e2:]
        else:                                               # the last statement: drop the ';' before it
            pre = re.search(r';[ \t]*\n?[ \t]*$', t[:s])
            if pre:
                t = t[:pre.start()] + t[e:]
            else:                                           # the only statement
                t = t[:s] + 'false' + t[e:]
        n += 1


total = 0
changed = []
for scr in list(app.map):
    if scr == 'App': continue
    d = app.doc(scr)
    def walk(n):
        yield n
        for c in n.get('Children', []): yield from walk(c)
    for n in walk(d['TopParent']):
        ctl = None if n is d['TopParent'] else n['Name']
        for r in list(n['Rules']):
            t = r['InvariantScript'].replace('\r\n', '\n')
            u, k = remove_statements(t)
            if k:
                app.set(scr, ctl, r['Property'], u, expect=t); total += k; changed.append((scr, ctl, r['Property'], k))

# App.OnStart: the App's YAML keeps its properties one level deeper, so JSON and YAML are written here
doc = app.doc('App'); tp = doc['TopParent']
rule = [r for r in tp['Rules'] if r['Property'] == 'OnStart'][0]
t = rule['InvariantScript'].replace('\r\n', '\n')
u, k = remove_statements(t)
rule['InvariantScript'] = u
yf = os.path.join(NEW, 'Src', 'App.pa.yaml')
lines = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').replace('\r', '\n').split('\n')
s = next(i for i, l in enumerate(lines) if l == '    OnStart: |-')
e = next(i for i in range(s + 1, len(lines)) if lines[i].strip() and len(lines[i]) - len(lines[i].lstrip()) == 4)
old_body = '\n'.join(l[6:] if l.strip() else '' for l in lines[s + 1:e]).rstrip('\n')
assert old_body == ('=' + t).rstrip('\n'), 'App.OnStart YAML and JSON differ before the edit'
lines[s:e] = _fmt('OnStart', u, 4)
open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
total += k; changed.append(('App', None, 'OnStart', k))
print('statements removed:', total)
for c in changed: print('  ', c)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL176 built')
