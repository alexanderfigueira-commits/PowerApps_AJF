#!/usr/bin/env python3
"""FINAL226 on FINAL225. Legal & Docs attachments: required only for Case 1, or for Cases 2-6 when "Signed framework contract
(optional)" is ticked (and the documents do not travel by FTP). In Cases 2-6 without that tick, attaching files is optional,
whatever else is ticked (release forms, music licence, pre-existing annex, subtitles).
Opening a media file of a submitted request, the framework contract counts as signed automatically only for Case 1; in Cases 2-6
the box shows what was saved, so it is not ticked (and the attachment not required) unless the requestor ticked it."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV87', 'newV88'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))


def rep(scr, ctl, prop, old, new, count=1):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    assert t.count(old) == count, (scr, ctl, prop, t.count(old), old[:80])
    app.set(scr, ctl, prop, t.replace(old, new), expect=t)


OLD_DOCS = ('(Left(Coalesce(varChildContractCase, ""), 6) = "Case 1" Or Coalesce(varDocFramework, false) Or Coalesce(varDocSpecific, false)'
            ' Or Coalesce(varDocOffer, false) Or (Coalesce(varChildModelRelease, false) And Coalesce(varChildModelReleaseProvided, false))'
            ' Or ((varChildMediaType = "Video" Or varChildMediaType = "Podcast") And ((Coalesce(varChildMusicUsed, false) And Coalesce(varChildMusicLicenceProvided, false))'
            ' Or (Coalesce(varChildPreexisting, false) And Coalesce(varChildPreexistingProvided, false))))'
            ' Or (varChildMediaType = "Video" And Coalesce(varChildSubtitlesProvided, false)))')
NEW_DOCS = '(Left(Coalesce(varChildContractCase, ""), 6) = "Case 1" Or Coalesce(varDocFramework, false))'
OLDN = ('Note: "A document is marked on the Legal & Docs tab but nothing is attached. Attach the file(s) on the Legal & Docs tab, '
        'or tick the FTP option if they travel with the media."')
NEWN = ('Note: "Case 1, or a ticked signed framework contract, needs its documents: attach them on the Legal & Docs tab, '
        'or tick the FTP option if they travel with the media."')
for ctl, prop in ((None, 'OnVisible'), ('CV_BtnRefresh', 'OnSelect')):
    rep('ChildValidScreen', ctl, prop, OLD_DOCS, NEW_DOCS)
    rep('ChildValidScreen', ctl, prop, OLDN, NEWN)
CL = 'ChildLegalScreen'
rep(CL, 'CL_DCAttachKey', 'Text', OLD_DOCS, NEW_DOCS)
rep(CL, 'CL_DCAttachKey', 'Text', '// required only when a document is marked above and the documents do not travel by FTP',
    '// required for Case 1, or Cases 2-6 with the signed framework contract ticked, unless the documents travel by FTP')
rep(CL, 'CL_DCAttachValue', 'BorderColor', OLD_DOCS, NEW_DOCS)
rep(CL, 'CL_DCAttachValue', 'BorderColor', '// yellow while a marked document has no file', '// yellow while a required attachment is missing')
rep(CL, 'CL_DCAttachValue', 'BorderThickness', OLD_DOCS, NEW_DOCS)
rep('RequesDetailScreen', 'DOA_List1RowBadge_8', 'OnSelect',
    '// the framework and specific contracts count as confirmed once the request was submitted\n'
    'Set(varDocFramework, Coalesce(ThisItem.FrameworkContractSigned, false) Or (Coalesce(varCurrentRequest.Status.Value, "") in',
    '// the framework and specific contracts count as confirmed once the request was submitted (the framework contract only for\n'
    '// Case 1: in Cases 2-6 it is optional and the box shows what was saved)\n'
    'Set(varDocFramework, Coalesce(ThisItem.FrameworkContractSigned, false) Or (Left(varChildContractCase, 6) = "Case 1" And Coalesce(varCurrentRequest.Status.Value, "") in')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL226 built')
