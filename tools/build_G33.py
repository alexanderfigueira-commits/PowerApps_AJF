#!/usr/bin/env python3
"""FINAL43 on the owner's TEST file (= FINAL42 + the owner's layout edits).

Task 1  Navigation bar: a REQUESTOR no longer sees the empty slot of the hidden Review button.
        12 screens (all except ReviewScreen, which only administrators reach, and the two operational dashboards the owner laid out
        by hand, whose panel already changes by role): for a non-administrator the Dashboard and Requests buttons move right by one slot
        (76) and the panel starts 76 later (right edge unchanged). The ADMINISTRATOR values are the current ones, unchanged.
Task 2  Episode visual (CM_BtnOpenEpisodeVisual): mandatory when Season nr. = 1, otherwise optional. Mandatory + no image attached:
        yellow border; the tooltip says "Mandatory..." or "Optional..."; the label shows "*" or "(optional)". No blocking is added (owner: later).
Task 4  Attachments id: the media record of the attachments card is aligned when a media item is added or opened and is never blanked while
        an id exists; the card's ID field falls back to varCurrentChildSPId; Save Media stops with a message when the request has no id or
        a validation fails.
Task 3  not done (needs the spec).
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'up6', 'newG33'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
ADMIN = 'varUserRole = "ADMINISTRATOR"'


def nl(t):
    return t.replace('\r\n', '\n')


def like(o, t):
    return t.replace('\n', '\r\n') if '\r\n' in o else t


# ---------------------------------------------------------------- Task 1: navigation bar
SHIFT = 76
n_nav = 0
for s, t in list(app.map.items()):
    if s in ('App', 'ReviewScreen', 'Dashboard-Ope-Administrator', 'Dashboard-Ope-Requestor'):
        continue
    tp = app.doc(s)['TopParent']
    names = []
    def collect(c):
        names.append(c['Name'])
        for k in c.get('Children', []):
            collect(k)
    collect(tp)
    pre = [re.match(r'^(\w+?)_Menu_Panel$', n).group(1) for n in names if re.match(r'^(\w+?)_Menu_Panel$', n)]
    if len(pre) != 1:
        sys.exit(f'! {s}: {len(pre)} menu panels')
    p = pre[0]
    exp = {f'{p}_Menu_Panel': ('X', '686'), f'{p}_Menu_Dashboard': ('X', '705'), f'{p}_Menu_Requests': ('X', '797')}
    for c, (prop, v) in exp.items():
        if app.rule(s, c, prop) != v:
            sys.exit(f'! {s}.{c}.{prop} is {app.rule(s, c, prop)}, expected {v}')
    if app.rule(s, f'{p}_Menu_Panel', 'Width') != '424' or app.rule(s, f'{p}_Menu_Review', 'X') != '875' or app.rule(s, f'{p}_Menu_Export', 'X') != '951':
        sys.exit(f'! {s}: nav geometry differs')
    app.set(s, f'{p}_Menu_Panel', 'X', f'If({ADMIN}, 686, {686 + SHIFT})', expect='686')
    app.set(s, f'{p}_Menu_Panel', 'Width', f'If({ADMIN}, 424, {424 - SHIFT})', expect='424')
    app.set(s, f'{p}_Menu_Dashboard', 'X', f'If({ADMIN}, 705, {705 + SHIFT})', expect='705')
    app.set(s, f'{p}_Menu_Requests', 'X', f'If({ADMIN}, 797, {797 + SHIFT})', expect='797')
    n_nav += 1
print('navigation bars adjusted on', n_nav, 'screens')

# ---------------------------------------------------------------- Task 2: episode visual mandatory when Season nr. = 1
M = 'ChildMetaScreen'
MAND = 'Coalesce(varChildSeasonNumber, 0) = 1'
NOFILE = 'IsEmpty(Filter(CM_EpisodeVisual.Attachments, EndsWith(Lower(Name), ".jpg") Or EndsWith(Lower(Name), ".jpeg") Or EndsWith(Lower(Name), ".png")))'
app.set(M, 'CM_BtnOpenEpisodeVisual', 'BorderColor', f'// yellow while the episode visual is mandatory (Season nr. = 1) and no image is attached\nIf({MAND} And {NOFILE}, RGBA(255, 204, 0, 1), RGBA(56, 96, 178, 1))', expect='RGBA(56, 96, 178, 1)')
app.set(M, 'CM_BtnOpenEpisodeVisual', 'BorderThickness', f'If({MAND} And {NOFILE}, 3, 1)', expect='1')
app.set(M, 'CM_BtnOpenEpisodeVisual', 'Tooltip', f'If({MAND}, "Mandatory: an episode visual is required when Season nr. is 1.", "Optional: an episode visual is only required when Season nr. is 1.")', expect='""')
app.set(M, 'CM_LblEpisodeVisual', 'Text', f'"Episode visual" & If({MAND}, " *", " (optional)")', expect='"Episode visual"')

# ---------------------------------------------------------------- Task 4: the media item id and the attachments card
L = 'ChildLegalScreen'
app.set(L, 'CL_DCIdValue', 'Text', 'If(IsBlank(ThisItem.ID), If(Coalesce(varCurrentChildSPId, 0) > 0, Text(varCurrentChildSPId), "—"), Text(ThisItem.ID))', expect='If(IsBlank(ThisItem.ID), "—", Text(ThisItem.ID))')
RS = 'RequesDetailScreen'
t = app.rule(RS, 'Add_media_icon', 'OnSelect')
a = '// the request may have just been created: the Requests list reloads on its next visit\r\nSet(varReqDataLoaded, false);\r\nNavigate(ChildInfoScreen)'
if t.count(a) != 1:
    sys.exit('! Add_media_icon anchor not found')
app.set(RS, 'Add_media_icon', 'OnSelect', t.replace(a, '// the request may have just been created: the Requests list reloads on its next visit\r\nSet(varReqDataLoaded, false);\r\n// the attachments card starts on THIS media item\r\nSet(varAttachRecord, If(Coalesce(varCurrentChildSPId, 0) > 0, LookUp(\'AV-CD-Mediafiles\', ID = varCurrentChildSPId), Blank()));\r\nNavigate(ChildInfoScreen)'), expect=t)
t = app.rule(RS, 'DOA_List1RowBadge_8', 'OnSelect')
a = 'Set(varCurrentChildSPId, Coalesce(ThisItem.SPId, 0));'
if t.count(a) != 1:
    sys.exit('! media open handler anchor not found')
app.set(RS, 'DOA_List1RowBadge_8', 'OnSelect', t.replace(a, a + '\r\n// the attachments card starts on THIS media item\r\nSet(varAttachRecord, If(Coalesce(ThisItem.SPId, 0) > 0, LookUp(\'AV-CD-Mediafiles\', ID = ThisItem.SPId), Blank()));', 1), expect=t)
OLDB = re.compile(r"// the item's SharePoint ID: if the variable lost it, take it back from the media list\nIf\(\n    Coalesce\(varCurrentChildSPId, 0\) = 0 And .*?\);\nIf\(\n    Coalesce\(varAttachRecord\.ID, 0\) <> Coalesce\(varCurrentChildSPId, 0\),\n    Set\(varAttachRecord, LookUp\('AV-CD-Mediafiles', ID = Coalesce\(varCurrentChildSPId, 0\)\)\)\n\);", re.S)
NEWB = '''// the item's SharePoint ID: if the variable lost it, take it back from the media list, else from the record already loaded for this item
If(
    Coalesce(varCurrentChildSPId, 0) = 0,
    Set(
        varCurrentChildSPId,
        If(
            Coalesce(LookUp(colArchives, ArchiveId = varCurrentChildId).SPId, 0) > 0,
            LookUp(colArchives, ArchiveId = varCurrentChildId).SPId,
            Coalesce(varAttachRecord.ID, 0)
        )
    )
);
// the attachments record is only reloaded when the id is known and different: it is never blanked while an id exists
If(
    Coalesce(varCurrentChildSPId, 0) > 0 And Coalesce(varAttachRecord.ID, 0) <> varCurrentChildSPId,
    Set(varAttachRecord, LookUp('AV-CD-Mediafiles', ID = varCurrentChildSPId))
);'''
for s in ('ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen'):
    t = app.rule(s, None, 'OnVisible')
    n = nl(t)
    if len(OLDB.findall(n)) != 1:
        sys.exit(f'! {s}: id block found {len(OLDB.findall(n))} times')
    app.set(s, None, 'OnVisible', like(t, OLDB.sub(lambda m: NEWB, n)), expect=t)
# Save Media: stop with a clear message before anything is written
V, B = 'ChildValidScreen', 'CV_BtnSaveArchive'
t = app.rule(V, B, 'OnSelect')
n = nl(t)
guard = '''If(
    // the parent request must exist and have an id: media items are written under its request number
    Coalesce(varCurrentRequest.ID, 0) = 0,
    Notify("Save the request first (Draft Save): it has no id yet, so the media file cannot be saved.", NotificationType.Warning),
    // a missing mandatory item (including required attachments) is named, not silently skipped
    CountIf(colValidations, Not(Pass)) > 0,
    Notify("The media file cannot be saved yet: " & First(Filter(colValidations, Not(Pass))).Check & ". " & First(Filter(colValidations, Not(Pass))).Note, NotificationType.Warning),
'''
body = '\n'.join(('    ' + l) if l.strip() else l for l in n.split('\n'))
new = guard + body + '\n)'
app.set(V, B, 'OnSelect', like(t, new), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL43 built')
