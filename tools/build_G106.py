#!/usr/bin/env python3
"""FINAL116 on TEST_6:
 1. the message written on the Review screen (Approve / Reject / Need info) goes to the request's Message Center (AV-CD-Notes); the old way is gone:
    ReviewerComments and the requestor 'Notes' column of AV-CD-Requests are no longer read or written anywhere (Review, Request details, the notes tooltips of the lists, dashboards),
    the legacy first entries of the thread and the two old (unreachable) notes popups are removed.
 2. the read receipt of a message: ReadOn is a DATE-ONLY column in SharePoint, so the hour was always 00:00. The receipt shows the time only when it exists; the embedded schema says date-time.
 3. podcast: 'Recording date' instead of 'Filming date'."""
import datetime, json, os, re, shutil, sys
from payaml import App, find
from jio import jwrite
SRC, NEW = 'newP1', 'newP2'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
def edit(screen, ctl, prop, fn):
    t = app.rule(screen, ctl, prop)
    if t is None: sys.exit(f'! {screen}.{ctl}.{prop} missing')
    eol = '\r\n' if '\r\n' in t else '\n'
    n = fn(t.replace('\r\n', '\n'))
    if n == t.replace('\r\n', '\n'): sys.exit(f'! no change {screen}.{ctl}.{prop}')
    app.set(screen, ctl, prop, n.replace('\n', eol), expect=t)
def sub1(old, new, count=1):
    def f(t):
        if t.count(old) != count: sys.exit(f'! expected {count} x {old[:60]!r}, found {t.count(old)}')
        return t.replace(old, new)
    return f
# ------------------------------------------------------------------ 3. labels
edit('ChildMetaScreen', 'CM_LblShootDate' if False else 'CM_LblShootDate', 'Text', lambda t: t) if False else None
def meta_label(t):
    old = 'If(varChildMediaType = "Video" Or varChildMediaType = "Podcast", "Filming date *", "Shooting date *")'
    assert t.strip() == old, t
    return 'Switch(varChildMediaType, "Video", "Filming date *", "Podcast", "Recording date *", "Shooting date *")'
# find the control that holds that label
meta = app.doc('ChildMetaScreen')['TopParent']
def find_by_text(c, needle):
    for r in c['Rules']:
        if r['Property'] == 'Text' and needle in r['InvariantScript']: return c['Name']
    for k in c.get('Children', []):
        x = find_by_text(k, needle)
        if x: return x
lbl = find_by_text(meta, '"Filming date *"'); assert lbl
edit('ChildMetaScreen', lbl, 'Text', meta_label)
edit('PrintPodcastDetailScreen', find_by_text(app.doc('PrintPodcastDetailScreen')['TopParent'], '"Filming date"'), 'Text', lambda t: t.replace('"Filming date"', '"Recording date"'))
for scr_ctl in (('RequestManagementScreen',)):
    pass
def walk_rules(screen, fn):
    d = app.doc(screen)['TopParent']
    def w(c, ctl):
        for r in list(c['Rules']):
            t = r['InvariantScript']
            nt = fn(t, r['Property'], c['Name'])
            if nt is not None and nt != t:
                eol = '\r\n' if '\r\n' in t else '\n'
                app.set(screen, ctl, r['Property'], nt.replace('\n', eol) if eol == '\r\n' else nt, expect=t)
        for k in c.get('Children', []): w(k, k['Name'])
    w(d, None)
def rm_cm(t, p, n):
    if 'Switch(First(m.MediaType).Value, "Photo", "Shooting day", "Video", "Filming date", "Capture date")' in t:
        return t.replace('Switch(First(m.MediaType).Value, "Photo", "Shooting day", "Video", "Filming date", "Capture date")', 'Switch(First(m.MediaType).Value, "Photo", "Shooting day", "Video", "Filming date", "Podcast", "Recording date", "Capture date")')
walk_rules('RequestManagementScreen', rm_cm)
# ------------------------------------------------------------------ 2. read receipt: hour
edit('RequesDetailScreen', 'NT_ReadReceipt', 'Text', sub1('Text(ThisItem.ReadOn, "dd-mm-yyyy hh:mm")',
     'Text(ThisItem.ReadOn, If(Hour(ThisItem.ReadOn) = 0 And Minute(ThisItem.ReadOn) = 0, "dd-mm-yyyy", "dd-mm-yyyy hh:mm"))'))
dp = f'{NEW}/References/DataSources.json'
raw = open(dp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); txt = raw.decode('utf-8-sig'); d = json.loads(txt)
ds = [x for x in d['DataSources'] if x.get('Name') == 'AV-CD-Notes'][0]
key, meta_ = next(iter(ds['DataEntityMetadataJson'].items())); m = json.loads(meta_)
p = m['schema']['items']['properties']['ReadOn']; assert p.get('format') == 'date'; p['format'] = 'date-time'
ds['DataEntityMetadataJson'][key] = json.dumps(m, separators=(',', ':'), ensure_ascii=False)
indent = 2 if '\n  "' in txt else None
out = json.dumps(d, ensure_ascii=False, indent=indent, separators=(',', ': ') if indent else (',', ':'))
if '\r\n' in txt: out = out.replace('\n', '\r\n')
open(dp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out)
# ------------------------------------------------------------------ 1a. Review screen: the decision message is a note
def NOTE(prefix_expr):
    return ("Patch(\n            'AV-CD-Notes',\n            Defaults('AV-CD-Notes'),\n            {\n                Title: varReviewProject.RequestNumber,\n                ParentRequest: varReviewProject.RequestNumber,\n"
            f"                NoteText: \"<b>\" & {prefix_expr} & \"</b> · \" & Substitute(Trim(varReviewComment), Char(10), \"<br>\"),\n"
            "                AuthorRole: {Value: \"Administrator\"},\n                AuthorName: User().FullName,\n                AuthorEmail: User().Email,\n                NoteDate: Now()\n            }\n        )")
REV = ("ReviewedByContact: Table({\n                Claims: \"i:0#.f|membership|\" & Lower(User().Email),\n                DisplayName: User().FullName,\n                Email: User().Email,\n                Department: \"\",\n                JobTitle: \"\",\n                Picture: \"\"\n            }),\n            ReviewedDate: Now()")
TAIL = ("Set(varReviewProject, Blank());\n    Set(varReviewComment, \"\");\n    // reload the queue from SharePoint so the handled request leaves or updates\n    Refresh('AV-CD-Requests');\n    ClearCollect(colRevReqs, 'AV-CD-Requests');\n"
        "    // RequestManagementScreen reloads on its next visit too\n    Set(varReqDataLoaded, false)")
ARCH = 'RV_ArchiveOnly.Value And Not(Coalesce(varReviewProject.ArchivedOnly, false))'
def approve(t):
    return ("IfError(\n    // the message (if any) is added to the request's Message Center first, so the notification e-mail finds it\n    If(\n        Not(IsBlank(Trim(varReviewComment))),\n        " + NOTE(f'If({ARCH}, "Approved - archive only", "Approved")') + "\n    );\n"
            "    Patch('AV-CD-Requests',\n        LookUp('AV-CD-Requests', ID = varReviewProject.ID),\n        {\n            // always \"Approved\": a request with only some media files ticked is shown as \"Partially Approved Request.\" on the dashboards (tooltip)\n"
            "            Status: {Value: \"Approved\"},\n            " + REV + ",\n            ArchivedOnly: RV_ArchiveOnly.Value,\n            AdminNotesUpdatedOn: If(Not(IsBlank(Trim(varReviewComment))), Now(), varReviewProject.AdminNotesUpdatedOn)\n        }\n    );\n"
            "    Notify(\n        If(\n            " + ARCH + ",\n            \"Approved as archive only. The reason is in the Message Center of the request and the requestor is notified.\",\n"
            "            If(With(\n                {n: CountRows(RV_ChildrenGallery.AllItems), ok: CountRows(Filter(RV_ChildrenGallery.AllItems, MediaApproved = true))},\n                ok > 0 And ok < n\n            ), \"Partially Approved Request: only the ticked media files are approved.\", \"Request approved.\")\n        ),\n        NotificationType.Success\n    );\n    " + TAIL + ",\n    Notify(\"Approve failed: \" & FirstError.Message, NotificationType.Error)\n)")
def decision(label, status, ok_msg, ok_type, fail_msg):
    def f(t):
        return ("IfError(\n    // the message is a note of the request (Message Center); it goes first, so the notification e-mail finds it\n    " + NOTE(f'"{label}"') + ";\n"
                "    Patch('AV-CD-Requests',\n        LookUp('AV-CD-Requests', ID = varReviewProject.ID),\n        {\n            Status: {Value: \"" + status + "\"},\n            AdminNotesUpdatedOn: Now(),\n            " + REV + "\n        }\n    );\n"
                f"    Notify(\"{ok_msg}\", NotificationType.{ok_type});\n    " + TAIL + f",\n    Notify(\"{fail_msg}\" & FirstError.Message, NotificationType.Error)\n)")
    return f
edit('ReviewScreen', 'RV_BtnApprove', 'OnSelect', approve)
edit('ReviewScreen', 'RV_BtnReject', 'OnSelect', decision('Rejected', 'Rejected', 'Request rejected. Your message is in the Message Center of the request.', 'Warning', 'Reject failed: '))
edit('ReviewScreen', 'RV_BtnNeedInfo', 'OnSelect', decision('More information needed', 'Pending', 'Sent back to the requestor. Your message is in the Message Center of the request.', 'Success', 'Could not send it back: '))
LASTADM = "First(Sort(Filter('AV-CD-Notes', ParentRequest = varReviewProject.RequestNumber, AuthorRole.Value = \"Administrator\"), NoteDate, SortOrder.Descending))"
edit('ReviewScreen', 'RV_ExistingComment', 'Text', lambda t: f'"Last message to the requestor: " & Coalesce(PlainText({LASTADM}.NoteText), "none")')
edit('ReviewScreen', 'RV_ExistingComment', 'Visible', lambda t: f'Not(IsBlank(varReviewProject)) And Not(IsBlank({LASTADM}))')
edit('ReviewScreen', 'RV_LblComment', 'Text', lambda t: '"Message to the requestor  (required to send back or reject; it is added to the Message Center of the request)"')
# ------------------------------------------------------------------ 1b. Request details
LASTADM_D = "First(Sort(Filter('AV-CD-Notes', ParentRequest = varCurrentRequest.RequestNumber, AuthorRole.Value = \"Administrator\"), NoteDate, SortOrder.Descending))"
def onvis(t):
    n = re.sub(r"If\(\n    Not\(IsBlank\(varCurrentRequest\)\)\n    And \(varCurrentRequest\.Status\.Value = \"Rejected\".*?NotificationType\.Warning\n    \)\n\);",
               "With(\n    {ln: " + LASTADM_D + "},\n    If(\n        Not(IsBlank(varCurrentRequest))\n        And (varCurrentRequest.Status.Value = \"Rejected\" Or varCurrentRequest.Status.Value = \"Pending\")\n        And Not(IsBlank(ln)),\n"
               "        Notify(\n            If(varCurrentRequest.Status.Value = \"Rejected\", \"Rejected by \", \"More information requested by \") & Coalesce(First(varCurrentRequest.ReviewedByContact).DisplayName, \"the reviewer\")\n"
               "            & If(IsBlank(varCurrentRequest.ReviewedDate), \"\", \" on \" & Text(varCurrentRequest.ReviewedDate, DateTimeFormat.ShortDate))\n            & \": \" & PlainText(ln.NoteText),\n            NotificationType.Warning\n        )\n    )\n);", t, count=1, flags=re.S)
    assert n != t, 'Notify block'
    n2 = re.sub(r"\n[ \t]*// notes written before the thread existed stay as the first entry of each column\n[ \t]*Filter\(\n[ \t]*Table\(\{NRole: \"Requestor\".*?NKey: 0\}\),\n[^\n]*\n[ \t]*\),\n[ \t]*Filter\(\n[ \t]*Table\(\{NRole: \"Administrator\".*?NKey: 0\}\),\n[^\n]*\n[ \t]*\),", "", n, count=1, flags=re.S)
    assert n2 != n, 'legacy entries'
    n3 = re.sub(r"\n[ \t]*Reset\(RS_AdminNotes\);\n[ \t]*Reset\(RS_RequestorNotes\);", "", n2)
    n4 = re.sub(r"\n[ \t]*locShowAdminNotes: false,", "", n3); n4 = re.sub(r"\n[ \t]*locShowRequestorNotes: false,", "", n4)
    return n4
edit('RequesDetailScreen', None, 'OnVisible', onvis)
def ntadd(t):
    n = re.sub(r"\n[ \t]*// notes written before the thread existed stay as the first entry of each column\n[ \t]*Filter\(\n[ \t]*Table\(\{NRole: \"Requestor\".*?NKey: 0\}\),\n[^\n]*\n[ \t]*\),\n[ \t]*Filter\(\n[ \t]*Table\(\{NRole: \"Administrator\".*?NKey: 0\}\),\n[^\n]*\n[ \t]*\),", "", t, count=1, flags=re.S)
    assert n != t
    return n
edit('RequesDetailScreen', 'NT_BtnAdd', 'OnSelect', ntadd)
# the label of a rejected request
rej = find_by_text(app.doc('RequesDetailScreen')['TopParent'], '"Reviewer comment: "')
edit('RequesDetailScreen', rej, 'Text', lambda t: f'"Reviewer comment: " & Coalesce(PlainText({LASTADM_D}.NoteText), "-")')
# the four old fields in the request saves
LINE = re.compile(r"\n[ \t]*[A-Za-z]+: If\([^\n]*RS_(?:Admin|Requestor)Notes\.Text[^\n]*(?=\n|$)")
removed = 0
def strip_old(t, p, n):
    global removed
    if p == 'OnSelect' and LINE.search(t):
        k = len(LINE.findall(t)); removed += k
        return LINE.sub('', t)
walk_rules('RequesDetailScreen', strip_old)
print('old note fields removed from the saves:', removed)
# delete the two old notes popups (never opened)
doc = app.doc('RequesDetailScreen'); tp = doc['TopParent']
OLD = ['RS_AdminNotesBackdrop', 'RS_AdminNotesPanel', 'RS_AdminNotesTitle', 'RS_AdminNotesHint', 'RS_AdminNotes', 'RS_AdminNotesCancel', 'RS_AdminNotesSave',
       'RS_RequestorNotesBackdrop', 'RS_RequestorNotesPanel', 'RS_RequestorNotesTitle', 'RS_RequestorNotesHint', 'RS_RequestorNotes', 'RS_RequestorNotesCancel', 'RS_RequestorNotesSave']
n0 = len(tp['Children']); tp['Children'] = [c for c in tp['Children'] if c['Name'] not in OLD]; assert n0 - len(tp['Children']) == 14
jwrite(doc, app.map['RequesDetailScreen'])
yp = f'{NEW}/Src/RequesDetailScreen.pa.yaml'; Y = open(yp, encoding='utf-8').read().split('\n')
for nm in OLD:
    i = [k for k, l in enumerate(Y) if l.rstrip('\r') == f'      - {nm}:']; assert len(i) == 1, nm
    i = i[0]; j = i + 1
    while j < len(Y) and (Y[j].strip() == '' or len(Y[j]) - len(Y[j].lstrip()) > 6): j += 1
    del Y[i:j]
open(yp, 'w', encoding='utf-8').write('\n'.join(Y))
# ------------------------------------------------------------------ 1c. the notes icons / tooltips of the lists and dashboards: the thread is the source
LR = "First(Sort(Filter('AV-CD-Notes', ParentRequest = ThisItem.RequestNumber, AuthorRole.Value = \"Requestor\"), NoteDate, SortOrder.Descending))"
LA = "First(Sort(Filter('AV-CD-Notes', ParentRequest = ThisItem.RequestNumber, AuthorRole.Value = \"Administrator\"), NoteDate, SortOrder.Descending))"
cnt = {'n': 0}
def lists(t, p, n):
    o = t
    t = t.replace(' Or Trim(PlainText(Coalesce(ThisItem.Notes, ""))) <> ""', '').replace(' Or Trim(PlainText(Coalesce(ThisItem.ReviewerComments, ""))) <> ""', '')
    t = re.sub(r"Text\(ThisItem\.RequestorNotesUpdatedOn, \"dd mmm 'yy hh:mm\" \)", f"Text({LR}.NoteDate, \"dd mmm 'yy hh:mm\")", t)
    t = re.sub(r"Text\(ThisItem\.AdminNotesUpdatedOn, \"dd mmm 'yy hh:mm\" \)", f"Text({LA}.NoteDate, \"dd mmm 'yy hh:mm\")", t)
    t = t.replace('PlainText(Coalesce(ThisItem.Notes, ""))', f'Coalesce(PlainText({LR}.NoteText), "")')
    t = t.replace('Coalesce(ThisItem.ReviewerComments, "")', f'Coalesce(PlainText({LA}.NoteText), "")')
    t = t.replace('"Central Deposit: " &  ", updated on "', '"Central Deposit, updated on "')
    if t != o: cnt['n'] += 1; return t
for scr in ('Dashboard-Ope-Administrator', 'Dashboard-Ope-Requestor', 'RequestManagementScreen'): walk_rules(scr, lists)
print('list / dashboard rules rewritten:', cnt['n'])
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL116 built')
