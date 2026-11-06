#!/usr/bin/env python3
"""FINAL19 on FINAL18: the Video "Script / Shotlist" (ChildMetaScreen, CM_Script) is saved to ScriptShotlist and comes back.

* CV_BtnSaveArchive: ScriptShotlist in the Patch to AV-CD-Mediafiles and in the media record kept in colArchives;
* RequesDetailScreen.OnVisible: ScriptShotlist read back into colArchives;
* RS_CRowSelect: opening a media row loads varChildScript; Add_media_icon starts a new item with it empty;
* ChildMetaScreen.OnVisible: no longer blanks varChildScript the first time the tab is opened for an item
  (that wiped a script that had just been loaded).
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG8', 'newG9'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)


def edit(screen, ctl, prop, fn):
    t = app.rule(screen, ctl, prop)
    n = fn(t)
    if n == t:
        sys.exit(f'! {screen}.{ctl}.{prop}: no change made')
    app.set(screen, ctl, prop, n, expect=t)


def after(t, pat, add, count):
    found = len(re.findall(pat, t))
    if found != count:
        sys.exit(f'! {pat!r}: {found} found, expected {count}')
    return re.sub(pat, lambda m: m.group(0) + add(m), t)


# save: the record kept in the media list (first "Notes: varChildNotes,") and the Patch to SharePoint (second)
def save(t):
    pat = r'(\r?\n)( *)Notes: varChildNotes,'
    if len(re.findall(pat, t)) != 2:
        sys.exit('! save: expected 2 x Notes: varChildNotes')
    return re.sub(pat, lambda m: m.group(0) + m.group(1) + m.group(2) + 'ScriptShotlist: varChildScript,', t)


edit('ChildValidScreen', 'CV_BtnSaveArchive', 'OnSelect', save)
# media list loaded from SharePoint
edit('RequesDetailScreen', None, 'OnVisible', lambda t: after(t, r'(\r?\n)( *)MediaApproved: Coalesce\(MediaApproved, false\),',
                                                                lambda m: m.group(1) + m.group(2) + 'ScriptShotlist: Coalesce(ScriptShotlist, ""),', 1))
# opening a row / starting a new item
edit('RequesDetailScreen', 'RS_CRowSelect', 'OnSelect', lambda t: after(t, r'Set\(varChildNotes, Coalesce\(ThisItem\.Notes, ""\)\);',
                                                                          lambda m: '\nSet(varChildScript, Coalesce(ThisItem.ScriptShotlist, ""));', 1))
edit('RequesDetailScreen', 'Add_media_icon', 'OnSelect', lambda t: after(t, r'(\r?\n)Set\(varChildNotes, ""\);',
                                                                           lambda m: m.group(1) + 'Set(varChildScript, "");', 1))
# the Metadata tab no longer wipes it
def meta(t):
    pat = r'\n    Set\(varChildScript, ""\);'
    if len(re.findall(pat, t)) != 1:
        sys.exit('! ChildMetaScreen.OnVisible: reset not found')
    return re.sub(pat, '', t)


edit('ChildMetaScreen', None, 'OnVisible', meta)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL19 built')
