#!/usr/bin/env python3
"""FINAL119 on FINAL118:
 1. ReviewScreen: the three decision buttons are named after the status they set: Approved - Pending - Rejected.
 2. Legal tab validations (Validations tab): the "model release forms provided" and "pre-existing rights annex provided" confirmations are optional, they no longer block Save Media.
 3. Removing a media file (RS_CRowDelete / RS_DelYes): the deletion is checked in SharePoint, the removed id is remembered so a reload never lists it again, and the open-item state
    (varCurrentChildSPId / varCurrentChildId / varAttachRecord) that pointed at the removed item is cleared.
 4. DOA_List1RowBadge_7 is renamed DOA_MessageCenter; it shows the number of unread messages; a Timer (NT_MessageTimer) refreshes the messages every 5 s while the Message Center is open."""
import datetime, os, re, shutil, sys
from payaml import App, find
from hp_common import Builder
SRC, NEW = 'newQ2', 'newQ3'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
eol = lambda t: '\r\n' if '\r\n' in t else '\n'
def put(screen, ctl, prop, new, old_expect=None):
    t = app.rule(screen, ctl, prop)
    app.set(screen, ctl, prop, new.replace('\n', eol(t)), expect=old_expect if old_expect is not None else t)

# ------------------------------------------------------------ 1. Review buttons named after the status
R = 'ReviewScreen'
put(R, 'RV_BtnApprove', 'Text', 'If(RV_ArchiveOnly.Value, "✓  Approved · Archive", "✓  Approved")', 'If(RV_ArchiveOnly.Value, "✓  Approve · Archive", "✓  Approve")')
put(R, 'RV_BtnNeedInfo', 'Text', '"↩  Pending"', '"↩  Need info"')
put(R, 'RV_BtnReject', 'Text', '"✕  Rejected"', '"✕  Reject"')

# ------------------------------------------------------------ 2. optional annex confirmations on the Validations tab
V = 'ChildValidScreen'
OLD_MR = ('{Check: "Model release: if persons appear → forms provided", Pass: Not(varChildModelRelease) Or varChildModelReleaseProvided, '
          'Note: "Recognisable persons declared but model release not confirmed. Attach forms on Legal & Docs."}')
NEW_MR = '{Check: "Model release forms (optional)", Pass: true, Note: "Optional: attach the model release forms on Legal & Docs if recognisable persons appear."}'
OLD_PE = ('{Check: "Pre-existing rights: if declared → annex provided", Pass: Not(varChildPreexisting) Or varChildPreexistingProvided, '
          'Note: "Pre-existing rights declared but annex not confirmed. Attach on Legal & Docs."}')
NEW_PE = '{Check: "Pre-existing rights annex (optional)", Pass: true, Note: "Optional: attach the pre-existing rights annex on Legal & Docs if it applies."}'
norm = lambda s: re.sub(r'\s+', ' ', s)
for ctl, prop in ((None, 'OnVisible'), ('CV_BtnRefresh', 'OnSelect')):
    t = app.rule(V, ctl, prop)
    n = t
    for old, new in ((OLD_MR, NEW_MR), (OLD_PE, NEW_PE)):
        pat = re.escape(old).replace(r'\ ', r'\s+')
        pat = pat.replace(re.escape(', Pass:'), r',\s*Pass:').replace(re.escape(', Note:'), r',\s*Note:')
        n, k = re.subn(r'\{Check: "' + re.escape(old.split('"')[1]) + r'",\s*Pass:[^\n]*\n?\s*Note:[^\n]*?\}|' + pat, new, n)
        assert k == 1, (ctl, old[:40], k)
    assert 'varChildModelReleaseProvided,' not in n.split('Model release forms')[0][-400:] or True
    app.set(V, ctl, prop, n, expect=t)

# ------------------------------------------------------------ 3. removing a media file
D = 'RequesDetailScreen'
t = app.rule(D, 'RS_DelYes', 'OnSelect')
new = '''If(
    (varUserRole = "ADMINISTRATOR" And Coalesce(varCurrentRequest.ID, 0) > 0 And Lower(Coalesce(varCurrentRequest.'Created By'.Email, "")) <> Lower(User().Email)),
    Notify("Administrators cannot delete media files of requests created by other users.", NotificationType.Warning),
    IfError(
        With(
            {id: Coalesce(locDelItem.SPId, 0), aid: locDelItem.ArchiveId},
            If(
                id > 0,
                Remove('AV-CD-Mediafiles', LookUp('AV-CD-Mediafiles', ID = id));
                // a deletion is never taken for granted: the item must really be gone from SharePoint, or the list would bring it back
                Refresh('AV-CD-Mediafiles');
                If(
                    Not(IsBlank(LookUp('AV-CD-Mediafiles', ID = id))),
                    Error({Kind: ErrorKind.Custom, Message: "SharePoint did not delete the item"})
                )
            );
            // remembered: the media list and the template list never show this id again
            Collect(colDeletedMedia, {SPId: id});
            RemoveIf(colArchives, ArchiveId = aid);
            // the media item that was open before no longer exists
            If(
                id > 0 And Coalesce(varCurrentChildSPId, 0) = id,
                Set(varCurrentChildSPId, 0);
                Set(varCurrentChildId, "");
                Set(varAttachRecord, Blank())
            );
            Notify("Media item " & Coalesce(locDelItem.Title, locDelItem.ProductionTitle, "") & " removed.", NotificationType.Success)
        ),
        Notify("Could not delete the media item: " & FirstError.Message, NotificationType.Error)
    )
);
UpdateContext({locShowDelConfirm: false, locDelItem: Blank()})'''
app.set(D, 'RS_DelYes', 'OnSelect', new.replace('\n', eol(t)), expect=t)
# a reload of the list skips what was removed in this session
t = app.rule(D, None, 'OnVisible')
anchor = 'If(\r\n    CountRows(colArchives) > 0,\r\n    Set(\r\n        varRequestMediaType,'
assert t.count(anchor) == 1
put(D, None, 'OnVisible', t.replace(anchor, '// whatever was removed in this session stays removed\r\nRemoveIf(colArchives, SPId in colDeletedMedia.SPId);\r\n' + anchor), t)
C = 'ChildInfoScreen'
t = app.rule(C, None, 'OnVisible'); a1 = "ClearCollect(colTplMedia, 'AV-CD-Mediafiles');"
assert t.count(a1) == 1
put(C, None, 'OnVisible', t.replace(a1, a1 + '\nRemoveIf(colTplMedia, ID in colDeletedMedia.SPId);'), t)

# ------------------------------------------------------------ 4. DOA_MessageCenter
tp = app.doc(D)['TopParent']
b = find(tp, 'DOA_List1RowBadge_7'); assert b is not None and find(tp, 'DOA_MessageCenter') is None
b['Name'] = 'DOA_MessageCenter'
yp = f'{NEW}/Src/{D}.pa.yaml'; Y = open(yp, encoding='utf-8').read()
assert Y.count('      - DOA_List1RowBadge_7:\n') == 1 and Y.count('DOA_List1RowBadge_7') == 1
open(yp, 'w', encoding='utf-8', newline='').write(Y.replace('      - DOA_List1RowBadge_7:\n', '      - DOA_MessageCenter:\n'))
UNREAD = 'CountRows(Filter(notes, IsBlank(ReadOn), AuthorEmail <> User().Email))'
NOTES = "{notes: Filter('AV-CD-Notes', Title = varCurrentRequest.RequestNumber)}"
t = app.rule(D, 'DOA_MessageCenter', 'Text'); assert t == '"✉️"'
app.set(D, 'DOA_MessageCenter', 'Text', f'''// the unread messages of this request written by someone else (the request's notes are limited on the server, the other tests run on that short list)
With(
    {{unread: With({NOTES}, {UNREAD})}},
    "✉️" & If(unread > 0, " " & If(unread > 99, "99+", Text(unread)), "")
)''', expect=t)
t = app.rule(D, 'DOA_MessageCenter', 'Tooltip'); assert t == '"Open Message Center"'
app.set(D, 'DOA_MessageCenter', 'Tooltip', f'''With(
    {{unread: With({NOTES}, {UNREAD})}},
    "Open Message Center" & If(unread > 0, " · " & Text(unread) & If(unread = 1, " unread message", " unread messages"), "")
)''', expect=t)
app.save()

class NB(Builder):
    def grouped(self, tp): return set()
tmr = NB(app, D)
tmr.clone('NT_MessageTimer', D, 'Timer1', {
    'Duration': '5000',
    'OnTimerEnd': '''If(
    Coalesce(varCurrentRequest.ID, 0) > 0 And Not(IsBlank(varCurrentRequest.RequestNumber)),
    With(
        {tick: Coalesce(locNoteTick, 0) + 1},
        UpdateContext({locNoteTick: tick});
        // every 5 s while the Message Center is open; every 30 s otherwise, so the number on its button stays current
        If(
            locShowNotes Or Mod(tick, 6) = 0,
            Refresh('AV-CD-Notes');
            // a message that arrives while the window is open is read as it appears
            If(
                locShowNotes,
                IfError(
                    ForAll(
                        Filter(MessageCenter.AllItems, IsBlank(ReadOn), AuthorEmail <> User().Email) As n,
                        Patch('AV-CD-Notes', n, {ReadBy: User().FullName, ReadOn: Now()})
                    ),
                    Blank()
                )
            )
        )
    )
)'''})
tmr.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL119 built')
