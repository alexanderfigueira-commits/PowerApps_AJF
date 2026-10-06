#!/usr/bin/env python3
"""FINAL32 on FINAL31: the unambiguous small fixes found by the full audit (typos, wording, label spacing, tooltips, Export ID search).

* typos: "clipbaoard" (2 places), "Contrator";
* the Cancel / Save buttons of the Contact Extra pop-up both had the tooltip "Save draft";
* "Contact Saved:" -> "Contact saved:"; "(required to pending or reject)" -> "(required to send back or reject)";
* a missing space before the * on three required labels;
* leftover "archive" wording -> "media file" (template picker, row title, AI warning, caption hint, print titles, Help text);
  the data sentinel "New archive" and the feature name "Archiving only" are kept;
* Export (HomePrintScreen): the Request ID search compared the typed text with the SharePoint item ID (and ignored it when it contained
  a dash, e.g. 26-0034). It now matches the start of the request number, like the Request Management screen.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG21', 'newG22'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
n_ch = 0


def rep(s, c, p, old, new, count=1):
    global n_ch
    t = app.rule(s, c, p)
    if t is None or t.count(old) != count:
        sys.exit(f'! {s}.{c}.{p}: expected {count} x {old!r}, found {None if t is None else t.count(old)}')
    app.set(s, c, p, t.replace(old, new), expect=t)
    n_ch += 1


# the typo is in two controls' OnSelect
import json
tp = app.doc('RequesDetailScreen')['TopParent']
def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)
for c in list(walk(tp)):
    for r in c['Rules']:
        if 'clipbaoard' in r['InvariantScript']:
            rep('RequesDetailScreen', c['Name'], r['Property'], 'clipbaoard', 'clipboard')
rep('RequesDetailScreen', 'RS_DetailsToggle_contrator', 'Tooltip', 'Contrator', 'Contractor')
app.set('RequesDetailScreen', 'RS_btnCancelContact', 'Tooltip', '"Cancel"', expect='"Save draft"')
app.set('RequesDetailScreen', 'RS_btnSaveContact', 'Tooltip', '"Save contact"', expect='"Save draft"')
rep('RequesDetailScreen', 'RS_btnSaveContact', 'OnSelect', '"Contact Saved: "', '"Contact saved: "')
rep('ReviewScreen', 'RV_LblComment', 'Text', 'required to pending or reject', 'required to send back or reject')
rep('RequesDetailScreen', 'RS_LblContractor', 'Text', '(Contractor)*', '(Contractor) *')
rep('RequesDetailScreen', 'RS_ArchivesSection', 'Text', 'Media files*', 'Media files *')
rep('ChildInfoScreen', 'CI_LblPodcastVisual', 'Text', 'Podcast visual*', 'Podcast visual *')
# wording
rep('RequesDetailScreen', 'RS_CRowTitle', 'Text', 'untitled archive', 'untitled media file')
rep('ChildInfoScreen', 'CI_TplRowTitle', 'Text', 'Untitled archive', 'Untitled media file')
rep('ChildInfoScreen', 'CI_TplTitle', 'Text', 'Use previous archive as template', 'Use previous media file as template')
rep('ChildInfoScreen', 'CI_TplEmpty', 'Text', ' archives yet.', ' media files yet.')
rep('ChildMetaScreen', 'CM_Caption', 'HintText', 'photo archive', 'photo')
rep('ChildMetaScreen', 'CM_AIWarningText', 'Text', 'This archive will fail', 'This media file will fail')
rep('PrintPhotoDetailScreen', 'PPD_Lbl1', 'Text', 'Archive / production title', 'Media file / production title')
rep('PrintVideoDetailScreen', 'PVD_Lbl1', 'Text', 'Archive / production title', 'Media file / production title')
rep('HelpScreen', 'HL_About', 'Text', 'one or more archives by', 'one or more media files by')
# Export: Request ID search
OLD = 'Not(IsNumeric(HP_TxtRequestID.Text)) Or ID = Value(HP_TxtRequestID.Text)'
NEWF = 'StartsWith(RequestNumber, HP_TxtRequestID.Text)'
tp = app.doc('HomePrintScreen')['TopParent']
hits = 0
for c in list(walk(tp)):
    for r in c['Rules']:
        k = r['InvariantScript'].count(OLD)
        if k:
            rep('HomePrintScreen', c['Name'], r['Property'], OLD, NEWF, k)
            hits += k
if hits != 15:
    sys.exit(f'! expected 15 Request ID filters, found {hits}')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL32 built, rule edits:', n_ch)
