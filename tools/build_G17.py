#!/usr/bin/env python3
"""FINAL27 on FINAL26: a missing Legal-tab column no longer blocks "Save Media".

The six Legal answers (ModelRelease, Preexisting, SubtitlesProvided, DocFramework, DocSpecific, DocOffer) were part of the one
Patch to AV-CD-Mediafiles, so a single column missing in the SharePoint list made SharePoint refuse the whole save
("The specified column 'DocFramework' does not exist"). They are now saved by a second Patch right after the main one: the media
file is always saved, and if that second step fails a warning names the cause and the six columns to check.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG16', 'newG17'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, N = 'ChildValidScreen', 'CV_BtnSaveArchive'
t = app.rule(S, N, 'OnSelect')
SIX = [('ModelRelease', 'varChildModelRelease'), ('Preexisting', 'varChildPreexisting'), ('SubtitlesProvided', 'varChildSubtitlesProvided'),
       ('DocFramework', 'varDocFramework'), ('DocSpecific', 'varDocSpecific'), ('DocOffer', 'varDocOffer')]
# 1. out of the main Patch (the record kept in the media list keeps them)
block = ''.join(rf'\r?\n *{c}: {v},' for c, v in SIX)
pat = r'(PreexistingRightsProvided: varChildPreexistingProvided,)' + block
if len(re.findall(pat, t)) != 1:
    sys.exit('! the six fields are not where expected in the Patch')
n = re.sub(pat, r'\1', t)
# 2. a second, tolerant Patch right after the main one
anchor = 'UpdateIf(colArchives, ArchiveId = varCurrentChildId, {SPId: savedMedia.ID});'
if n.count(anchor) != 1:
    sys.exit('! anchor after the Patch not found')
ind = ' ' * 16
second = (f'// The Legal tab confirmations are six Yes/No columns. A column missing in the list must not block saving the media file:\r\n'
          f'{ind}// they are saved in a second step, and a warning says so if it fails.\r\n'
          f'{ind}IfError(\r\n{ind}    Patch(\r\n{ind}        \'AV-CD-Mediafiles\',\r\n{ind}        LookUp(\'AV-CD-Mediafiles\', ID = savedMedia.ID),\r\n{ind}        {{\r\n'
          + ',\r\n'.join(f'{ind}            {c}: {v}' for c, v in SIX) + f'\r\n{ind}        }}\r\n{ind}    ),\r\n'
          f'{ind}    Notify(\r\n{ind}        "Media file saved, but its Legal tab confirmations were NOT stored: " & FirstError.Message\r\n'
          f'{ind}            & " Check that the Yes/No columns ModelRelease, Preexisting, SubtitlesProvided, DocFramework, DocSpecific and DocOffer exist in AV-CD-Mediafiles.",\r\n'
          f'{ind}        NotificationType.Warning\r\n{ind}    )\r\n{ind});\r\n{ind}')
n = n.replace(anchor, second + anchor)
app.set(S, N, 'OnSelect', n, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL27 built')
