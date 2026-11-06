#!/usr/bin/env python3
"""FINAL174 on FINAL173. App checker, Performance: "Mutating a collection or data source inside ForAll" (5). The way it recommends: pass the ForAll result to ONE mutation call.
 - RequesDetailScreen.OnVisible: ForAll(requests' media, Collect(colArchives, {...}))  ->  Collect(colArchives, ForAll(media, {...}))
 - NT_MessageTimer.OnTimerEnd, DOA_MessageCenter.OnSelect: ForAll(unread notes, Patch(Notes, n, {...}))  ->  Patch(Notes, ForAll(unread notes, {ID: n.ID, ...}))
 - RS_BtnSubmitRequest, RS_BtnResubmitRequest: ForAll(media, Patch(Mediafiles, LookUp(...), {DepositStatus}))  ->  Patch(Mediafiles, ForAll(media, {ID: SPId, DepositStatus}))
Not changed: "Inefficient delay loading" on CL_DCAttach.Update (it reads the podcast file boxes of two other screens by design)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV35', 'newV36'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n').replace('\r', '\n'))(_rule(*a))
D = 'RequesDetailScreen'


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
            elif c == '(' or c == '{' or c == '[': d += 1
            elif c == ')' or c == '}' or c == ']':
                d -= 1
                if d == 0: return j
        j += 1
    raise SystemExit('unbalanced')


def split_top(s):
    parts, d, buf, instr, j = [], 0, '', False, 0
    while j < len(s):
        c = s[j]
        if instr:
            buf += c
            if c == '"':
                if j + 1 < len(s) and s[j + 1] == '"': buf += '"'; j += 1
                else: instr = False
        else:
            if c == '"': instr = True; buf += c
            elif c in '({[': d += 1; buf += c
            elif c in ')}]': d -= 1; buf += c
            elif c == ',' and d == 0: parts.append(buf); buf = ''
            else: buf += c
        j += 1
    parts.append(buf)
    return parts


# ---- 1. the loader --------------------------------------------------------------------------------------------------------------------
t = app.rule(D, None, 'OnVisible')
m = re.search(r'ForAll\(\s*Sort\(', t)
assert m and len(re.findall(r'ForAll\(\s*Sort\(\s*Filter\(\s*\'AV-CD-Mediafiles\'', t)) == 1
fa_open = m.start() + len('ForAll')
fa_close = match_paren(t, fa_open)
first, second = split_top(t[fa_open + 1:fa_close])[0], ','.join(split_top(t[fa_open + 1:fa_close])[1:])
second = second.strip()
assert second.startswith('Collect(') and re.match(r'Collect\(\s*colArchives\s*,\s*\{', second)
rec = second[second.index('{'):second.rindex('}') + 1]
assert second[second.rindex('}') + 1:].strip() == ')'
new = 'Collect(\n        colArchives,\n        ForAll(\n            ' + first.strip() + ',\n            ' + rec + '\n        )\n    )'
app.set(D, None, 'OnVisible', t[:m.start()] + new + t[fa_close + 1:], expect=t)

# ---- 2. read receipts -----------------------------------------------------------------------------------------------------------------
pat = re.compile(r"ForAll\(\s*(//[^\n]*\n\s*)?Filter\(MessageCenter\.AllItems, IsBlank\(ReadOn\), AuthorEmail <> User\(\)\.Email\) As n,\s*Patch\('AV-CD-Notes', n, \{ReadBy: User\(\)\.FullName, ReadOn: Now\(\)\}\)\s*\)")
for ctl, prop in (('NT_MessageTimer', 'OnTimerEnd'), ('DOA_MessageCenter', 'OnSelect')):
    t = app.rule(D, ctl, prop)
    assert len(pat.findall(t)) == 1, ctl
    def rep(mm):
        cm = (mm.group(1) or '').strip()
        return ("Patch(\n'AV-CD-Notes',\n" + (cm + '\n' if cm else '') +
                "ForAll(\nFilter(MessageCenter.AllItems, IsBlank(ReadOn), AuthorEmail <> User().Email) As n,\n{ID: n.ID, ReadBy: User().FullName, ReadOn: Now()}\n)\n)")
    app.set(D, ctl, prop, pat.sub(rep, t), expect=t)

# ---- 3. submit / resubmit -------------------------------------------------------------------------------------------------------------
pat = re.compile(r"ForAll\(\s*Filter\(colArchives, SPId > 0\),\s*Patch\(\s*'AV-CD-Mediafiles',\s*LookUp\('AV-CD-Mediafiles', ID = SPId\),\s*\{DepositStatus: Table\(\{Value: \"Pending Approval\"\}\)\}\s*\)\s*\)")
for ctl in ('RS_BtnSubmitRequest', 'RS_BtnResubmitRequest'):
    t = app.rule(D, ctl, 'OnSelect')
    assert len(pat.findall(t)) == 1, ctl
    app.set(D, ctl, 'OnSelect', pat.sub(
        "Patch(\n'AV-CD-Mediafiles',\nForAll(\nFilter(colArchives, SPId > 0),\n{ID: SPId, DepositStatus: Table({Value: \"Pending Approval\"})}\n)\n)", t), expect=t)

app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL174 built')
