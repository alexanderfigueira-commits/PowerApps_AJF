#!/usr/bin/env python3
"""FINAL170 on FINAL169. The SharePoint column ScriptShotlist is single-line text, 255 characters at most: a longer Script / Shotlist made the whole Save Media fail.
The box CM_Script (Metadata tab, Video) now stops at 255 characters and its label counts them (turns red at the limit)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV31', 'newV32'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
M = 'ChildMetaScreen'
t = app.rule(M, 'CM_Script', 'MaxLength'); assert t == '', repr(t)
app.set(M, 'CM_Script', 'MaxLength', '255', expect=t)
t = app.rule(M, 'CM_LblScript', 'Text'); assert t == '"Script / Shotlist"', t
app.set(M, 'CM_LblScript', 'Text', '"Script / Shotlist  (" & Len(Coalesce(varChildScript, "")) & " / 255 characters)"', expect=t)
t = app.rule(M, 'CM_LblScript', 'Color')
assert t == 'If(varRequestorLocked, RGBA(0, 0, 0, 1), RGBA(60, 66, 80, 1))', t
app.set(M, 'CM_LblScript', 'Color', 'If(Len(Coalesce(varChildScript, "")) >= 255, RGBA(193, 40, 40, 1), If(varRequestorLocked, RGBA(0, 0, 0, 1), RGBA(60, 66, 80, 1)))', expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL170 built')
