#!/usr/bin/env python3
"""FINAL20 on FINAL19: Producer and Executive producer are no longer blanked by the Metadata tab.

ChildMetaScreen.OnVisible blanked varChildProducer / varChildExecProducer the first time the tab was opened for each
Video or Podcast media file. A saved file therefore reopened with an empty Executive producer (and a Producer that the
Validations tab no longer saw), and the next save overwrote SharePoint with blanks. Not needed: a new media file is
cleared by Add_media_icon, and opening a row sets them from the saved item (RS_CRowSelect).
Removed: the two resets of the Video block and the whole Podcast block. The Video block keeps its one other reset
(varChildSubtitlesProvided), unchanged.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG9', 'newG10'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
t = app.rule('ChildMetaScreen', None, 'OnVisible')
video = '''    Set(varChildProducer, "");
    Set(varChildExecProducer, "");
    Set(varChildSubtitlesProvided, false));'''
pod = '''If(varChildMediaType = "Podcast" And varPodMetaChildId <> varCurrentChildId,
    Set(varPodMetaChildId, varCurrentChildId);
    Set(varChildProducer, "");
    Set(varChildExecProducer, ""));
'''
if t.count(video) != 1 or t.count(pod) != 1:
    sys.exit('! OnVisible is not the expected text')
n = t.replace(video, '    Set(varChildSubtitlesProvided, false));').replace(pod, '')
if re.search(r'varChildProducer|varChildExecProducer|varPodMetaChildId', n):
    sys.exit('! still mentions the producers')
app.set('ChildMetaScreen', None, 'OnVisible', n, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL20 built')
