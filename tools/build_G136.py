#!/usr/bin/env python3
"""FINAL147 on FINAL146: with "Subtitles are provided" ticked, the VTT file is optional.
 * CL_LblVTT: no asterisk, "(optional)".
 * CL_DCAttachValue: yellow border only while nothing at all is attached (legal annexes), no longer for a missing .vtt.
 * Validations: the VTT row passes (kept as an optional row); SRT files are still refused."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV6', 'newV7'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

L = 'ChildLegalScreen'
t = app.rule(L, 'CL_LblVTT', 'Text')
app.set(L, 'CL_LblVTT', 'Text', t.replace('VTT subtitle file(s) *   - attach', 'VTT subtitle file(s) (optional)   - attach'), expect=t)
VTT_CLAUSE = ' Or (CL_LblVTT.Visible And CountRows(Filter(CL_DCAttachValue.Attachments, EndsWith(Lower(Name), ".vtt"))) = 0)'
for prop in ('BorderColor', 'BorderThickness'):
    t = app.rule(L, 'CL_DCAttachValue', prop); assert t.count(VTT_CLAUSE) == 1, prop
    u = t.replace(VTT_CLAUSE, '').replace('yellow while no file is attached or a mandatory VTT file is missing', 'yellow while no file is attached')
    app.set(L, 'CL_DCAttachValue', prop, u, expect=t)

V = 'ChildValidScreen'
OLD_CHECK = '"VTT subtitle file attached (Video, if subtitles provided)"'
NEW_CHECK = '"VTT subtitle file (optional)"'
NOTE_OLD = 'Note: "Subtitles marked as provided - attach at least one .vtt file on the Legal & Docs tab."'
NOTE_NEW = 'Note: "Optional: attach the .vtt subtitle file(s) on Legal & Docs if subtitles are provided."'
for ctl, prop in ((None, 'OnVisible'), ('CV_BtnRefresh', 'OnSelect')):
    t = app.rule(V, ctl, prop)
    m = re.search(r'Pass:\s*varChildMediaType <> "Video" Or Not\(varChildSubtitlesProvided\)[^\n]*?,\s*Note: "Subtitles marked as provided[^"]*"', t)
    assert m and t.count(OLD_CHECK) == 1, (ctl, prop)
    u = t[:m.start()] + 'Pass: true,' + (' ' if '\n' not in t[m.start():m.end()] else '\n             ') + NOTE_NEW + t[m.end():]
    u = u.replace(OLD_CHECK, NEW_CHECK)
    app.set(V, ctl, prop, u, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL147 built')
