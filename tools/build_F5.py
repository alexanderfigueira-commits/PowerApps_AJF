#!/usr/bin/env python3
"""FINAL_5 on the user's Central_Deposit_Ticket_System_FINAL061026.msapp.

A. Notes read / unread on RequesDetailScreen (the user already created ReadOn / ReadBy in the list).
   The notes loader (4 copies) flags notes from the other side that are still unread (NNew);
   opening the pop-up remembers them (locNewNotes, shown as "New") and saves ReadOn / ReadBy;
   the two notes buttons show "n new" with a red border; new label NT_ReadStatus in each note.
B. ReviewScreen: RV_Comment is also saved to AV-CD-Notes (Approve / Reject / Need info) so it
   shows in the notes pop-up.
C. ChildInfoScreen: a Video's Language and Type-of-product dropdowns show their first item
   (EN / Clip) but nothing stored it, so the Validations tab saw them empty. OnVisible now
   stores the displayed default.
D. RequestManagementScreen: the default "To" date was Today() = today 00:00, and the list keeps
   Created <= that, so every request created today was hidden. It is now the end of today.
   Submit / Resubmit also open the list on Processing, where the request now is.
"""
import datetime, json, os, re, shutil, sys
from collections import Counter
from payaml import App, find
from hp_common import Builder
from jio import jwrite

SRC, NEW = 'f0610', 'newF5'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RS, RV = 'RequesDetailScreen', 'ReviewScreen'
RED, GREEN, GREY = 'RGBA(193, 40, 40, 1)', 'RGBA(22, 128, 80, 1)', 'RGBA(140, 148, 160, 1)'


def put(s, n, p, v, cat='Design'):
    c = find(app.doc(s)['TopParent'], n)
    if not [r for r in c['Rules'] if r['Property'] == p]:
        c['Rules'].append({'Property': p, 'Category': cat, 'InvariantScript': v, 'RuleProviderType': 'Unknown'})
        c.setdefault('ControlPropertyState', []).append(p)
    app.set(s, n, p, v)


# ---------------------------------------------------------------- 1. schema (already refreshed by the user)
ds = json.load(open(f'{NEW}/References/DataSources.json', encoding='utf-8'))
notes = [x for x in ds['DataSources'] if x['Name'] == 'AV-CD-Notes'][0]
props = json.loads(list(notes['DataEntityMetadataJson'].values())[0])['schema']['items']['properties']
if 'ReadOn' not in props or 'ReadBy' not in props:
    sys.exit('! AV-CD-Notes has no ReadOn / ReadBy in the app')
DATE_ONLY = props['ReadOn'].get('format') == 'date'

# ---------------------------------------------------------------- 2. loader
LOADER = '''If(
    Coalesce(varCurrentRequest.ID, 0) > 0,
    With(
        {
            // the side of the thread the current user is on; notes from the other side can be new for them
            noteSide: If(
                varUserRole = "ADMINISTRATOR",
                "Administrator",
                If(Lower(varCurrentRequest.'Created By'.Email) = Lower(User().Email), "Requestor", "")
            )
        },
        ClearCollect(
            colReqNotes,
            ForAll(
                Filter('AV-CD-Notes', ParentRequest = varCurrentRequest.RequestNumber),
                {
                    NRole: AuthorRole.Value,
                    NAuthor: Coalesce(AuthorName, "-"),
                    NDate: Coalesce(NoteDate, Created),
                    NText: PlainText(Coalesce(NoteText, "")),
                    NKey: ID,
                    // not read yet by the side it was written for
                    NNew: noteSide <> "" And AuthorRole.Value <> noteSide And IsBlank(ReadOn)
                }
            )
        )
    );
    // notes written before the thread existed stay as the first entry of each column
    Collect(
        colReqNotes,
        Filter(
            Table({NRole: "Requestor", NAuthor: Coalesce(varCurrentRequest.'Created By'.DisplayName, "Requestor"), NDate: DateTime(1900, 1, 1, 0, 0, 0), NText: PlainText(Coalesce(varCurrentRequest.Notes, "")), NKey: 0, NNew: false}),
            Not(IsBlank(Trim(PlainText(Coalesce(varCurrentRequest.Notes, "")))))
        )
    );
    // a reviewer comment saved on ReviewScreen is also a note in the thread: count it once
    With(
        {rc: Lower(Substitute(Substitute(Substitute(Coalesce(varCurrentRequest.ReviewerComments, ""), Char(13), ""), Char(10), ""), " ", ""))},
        With(
            {inThread: Not(IsBlank(LookUp(colReqNotes, NKey > 0 And EndsWith(Lower(Substitute(Substitute(Substitute(NText, Char(13), ""), Char(10), ""), " ", "")), rc))))},
            Collect(
                colReqNotes,
                Filter(
                    Table({NRole: "Administrator", NAuthor: "Central Deposit", NDate: DateTime(1900, 1, 1, 0, 0, 0), NText: Coalesce(varCurrentRequest.ReviewerComments, ""), NKey: 0, NNew: false}),
                    rc <> "" And Not(inThread)
                )
            )
        )
    ),
    Clear(colReqNotes)
)'''

MARK = '''// unread notes from the other side show as "New" in the pop-up, then are saved as read
UpdateContext({locNewNotes: ForAll(Filter(colReqNotes, NNew), NKey)});
IfError(
    ForAll(
        Filter(colReqNotes, NNew) As nn,
        Patch('AV-CD-Notes', LookUp('AV-CD-Notes', ID = nn.NKey), {ReadOn: Now(), ReadBy: User().FullName})
    ),
    Notify("The notes could not be marked as read: " & FirstError.Message, NotificationType.Warning)
);
UpdateIf(colReqNotes, NNew, {NNew: false});
'''

OLD_RE = re.compile(r'If\(\s*Coalesce\(varCurrentRequest\.ID, 0\) > 0,\s*ClearCollect\(\s*colReqNotes,.*?Clear\(colReqNotes\)\s*\)', re.S)


def swap_loader(ctl, prop):
    t = app.rule(RS, ctl, prop)
    m = list(OLD_RE.finditer(t))
    if len(m) != 1:
        sys.exit(f'! {ctl}.{prop}: {len(m)} notes loaders')
    m = m[0]
    if 'ForAll(' not in m.group(0) or "'AV-CD-Notes'" not in m.group(0):
        sys.exit(f'! {ctl}.{prop}: loader does not read AV-CD-Notes')
    col = m.start() - (t.rfind('\n', 0, m.start()) + 1)
    block = LOADER.replace('\n', '\n' + ' ' * col)
    n = t[:m.start()] + block + t[m.end():]
    app.set(RS, ctl, prop, n, expect=t)
    return n


swap_loader(None, 'OnVisible')
swap_loader('NT_BtnAdd', 'OnSelect')
for btn, role in (('RS_AdminNotesOpen', 'administrator'), ('RS_RequestorNotesOpen', 'requestor')):
    n = swap_loader(btn, 'OnSelect')
    tail = 'UpdateContext({locShowNotes: true})'
    if not n.endswith(tail):
        sys.exit(f'! {btn}: does not end with opening the pop-up')
    app.set(RS, btn, 'OnSelect', n[:-len(tail)] + MARK + tail, expect=n)
    t = app.rule(RS, btn, 'Text')
    old = f'{{n: CountRows(Filter(colReqNotes, Lower(NRole) = "{role}"))}}'
    if t.count(old) != 1 or t.count('"💬  " & n & If(n = 1, " note", " notes")') != 1:
        sys.exit(f'! {btn}.Text changed')
    nt = t.replace(old, f'{{n: CountRows(Filter(colReqNotes, Lower(NRole) = "{role}")), nNew: CountRows(Filter(colReqNotes, Lower(NRole) = "{role}", NNew))}}')
    nt = nt.replace('"💬  " & n & If(n = 1, " note", " notes")',
                    '"💬  " & n & If(n = 1, " note", " notes") & If(nNew > 0, "  ·  " & nNew & " new", "")')
    app.set(RS, btn, 'Text', nt, expect=t)
    unread = f'CountRows(Filter(colReqNotes, Lower(NRole) = "{role}", NNew)) > 0'
    bc, bt = app.rule(RS, btn, 'BorderColor'), app.rule(RS, btn, 'BorderThickness')
    app.set(RS, btn, 'BorderColor', f'// red while there are notes you have not read yet\nIf({unread}, {RED}, {bc})', expect=bc)
    app.set(RS, btn, 'BorderThickness', f'If({unread}, 2, {bt})', expect=bt)
    tt = app.rule(RS, btn, 'Tooltip')
    app.set(RS, btn, 'Tooltip',
            f'If({unread}, "You have unread notes. Opening them marks them as read.", "Open the notes of this request")',
            expect=tt)
app.save()

# ---------------------------------------------------------------- 2b. read status per note
b = Builder(app, RS)
for n, v in (('Title1', 'Y'), ('Title1', 'X'), ('Title1', 'Width')):
    if not app.rule(RS, n, v):
        sys.exit(f'! {n}.{v} missing')
if app.rule(RS, 'Body1_1', 'Align') != 'If(ThisItem.AuthorRole.Value = "Administrator", Align.Right, Align.Left)':
    sys.exit('! Body1_1.Align changed')
if 'Items' not in {r['Property'] for r in find(app.doc(RS)['TopParent'], 'Gallery1')['Rules']} or \
        app.rule(RS, 'Gallery1', 'Items') != "Filter('AV-CD-Notes', Title = varCurrentRequest.RequestNumber)":
    sys.exit('! Gallery1 no longer reads AV-CD-Notes directly')
WHEN = ('If(\n'
        '        Hour(ThisItem.ReadOn) = 0 And Minute(ThisItem.ReadOn) = 0,\n'
        '        Text(ThisItem.ReadOn, DateTimeFormat.ShortDate),\n'
        '        Text(ThisItem.ReadOn, DateTimeFormat.ShortDateTime)\n'
        '    )')
b.clone('NT_ReadStatus', RS, 'Body1_1', {
    'Text': ('// New = unread when this pop-up was opened (now saved as read)\n'
             'If(\n'
             '    ThisItem.ID in locNewNotes.Value,\n'
             '    "●  New",\n'
             '    IsBlank(ThisItem.ReadOn),\n'
             '    "Not read yet",\n'
             '    "✓  Read" & If(IsBlank(ThisItem.ReadBy), "", " by " & ThisItem.ReadBy) & " on " & ' + WHEN + '\n'
             ')'),
    'Color': f'If(ThisItem.ID in locNewNotes.Value, {RED}, IsBlank(ThisItem.ReadOn), {GREY}, {GREEN})',
    'Size': '9',
    'Height': '18',
    'X': 'Title1.X',
    'Width': 'Title1.Width',
    'Y': 'Title1.Y + Title1.Height + 2',
}, parent='Gallery1')
b.save()
put(RS, 'NT_ReadStatus', 'FontWeight', 'If(ThisItem.ID in locNewNotes.Value, FontWeight.Semibold, FontWeight.Normal)')
app.save()

# ---------------------------------------------------------------- 3. reviewer comment -> note
NOTE = '''// the comment is also a note of the request (AV-CD-Notes): the requestor sees it in the notes pop-up
If(
    Not(IsBlank(Trim(varReviewComment))),
    IfError(
        Patch(
            'AV-CD-Notes',
            Defaults('AV-CD-Notes'),
            {
                Title: varReviewProject.RequestNumber,
                ParentRequest: varReviewProject.RequestNumber,
                NoteText: "<b>%s</b> · " & Substitute(Trim(varReviewComment), Char(10), "<br>"),
                AuthorRole: {Value: "Administrator"},
                AuthorName: User().FullName,
                AuthorEmail: User().Email,
                NoteDate: Now()
            }
        ),
        Notify("The comment could not be added to the notes: " & FirstError.Message, NotificationType.Warning)
    )
);
'''
for btn, label in (('RV_BtnApprove', 'Approved'), ('RV_BtnReject', 'Rejected'), ('RV_BtnNeedInfo', 'More information needed')):
    t = app.rule(RV, btn, 'OnSelect')
    at = t.find('\n    Notify(')
    if at < 0 or t.count("Patch('AV-CD-Requests'") != 1 or t.find("Patch('AV-CD-Requests'") > at:
        sys.exit(f'! {btn}: request patch / first Notify not where expected')
    blk = '\n' + '\n'.join(('    ' + l) if l else l for l in (NOTE % label).rstrip('\n').split('\n'))
    n = t[:at] + blk + t[at:]
    if btn == 'RV_BtnApprove':           # Reject / Need info already set it
        if 'AdminNotesUpdatedOn' in n or n.count('ReviewedDate: Now()') != 1:
            sys.exit('! RV_BtnApprove: patch fields changed')
        ind = re.search(r'\n( *)ReviewedDate: Now\(\)', n).group(1)
        n = n.replace('ReviewedDate: Now()',
                      f'ReviewedDate: Now(),\n{ind}// the dashboards\' notes icon reads this date\n'
                      f'{ind}AdminNotesUpdatedOn: If(IsBlank(Trim(varReviewComment)), varReviewProject.AdminNotesUpdatedOn, Now())')
    elif 'AdminNotesUpdatedOn: Now()' not in n:
        sys.exit(f'! {btn}: AdminNotesUpdatedOn missing')
    app.set(RV, btn, 'OnSelect', n, expect=t)
lt = app.rule(RV, 'RV_LblComment', 'Text')
app.set(RV, 'RV_LblComment', 'Text',
        '"Reviewer comment  (required to pending or reject)  ·  saved as a note for the requestor"',
        expect=lt)
put(RV, 'RV_Comment', 'Tooltip', '"Saved with your decision and added to the request\'s notes (AV-CD-Notes)"')
app.save()

# ---------------------------------------------------------------- C. Video defaults stored
CI = 'ChildInfoScreen'
t = app.rule(CI, None, 'OnVisible')
tail = 'UpdateContext({locShowVisualPreview: false})'
if not t.endswith(tail):
    sys.exit('! ChildInfoScreen.OnVisible does not end as expected')
app.set(CI, None, 'OnVisible', t + ''';
// A Video's Language and Type of product dropdowns show their first item (EN / Clip) while nothing is
// stored yet. Store what is shown, or the Validations tab sees them empty until they are re-selected.
If(
    varChildMediaType = "Video" And Not(varRequestorLocked),
    If(Coalesce(varChildLanguageVersions, "") = "", Set(varChildLanguageVersions, "EN"));
    If(Coalesce(varChildProductType, varChildProductType1, "") = "", Set(varChildProductType, "Clip"))
)''', expect=t)
app.save()

# ---------------------------------------------------------------- D. Requests Management
RM = 'RequestManagementScreen'
t = app.rule(RM, None, 'OnVisible')
old = 'Set(varFilterEndDate, Today());'
if t.count(old) != 1:
    sys.exit('! RequestManagementScreen: default end date not found')
app.set(RM, None, 'OnVisible', t.replace(old, '// end of today: Created has a time of day, so plain Today() (00:00) hid everything created today\n    Set(varFilterEndDate, Today() + Time(23, 59, 59));'), expect=t)
for btn in ('RS_BtnSubmitRequest', 'RS_BtnResubmitRequest'):
    t = app.rule(RS, btn, 'OnSelect')
    m = list(re.finditer(r'\n( *)Navigate\(RequestManagementScreen\)', t))
    if len(m) != 1:
        sys.exit(f'! {btn}: Navigate not found')
    ind = m[0].group(1)
    app.set(RS, btn, 'OnSelect', t[:m[0].start()] + f'\n{ind}// open the list on the status the request is in now\n{ind}Set(varNavFilter, "Processing");' + t[m[0].start():], expect=t)
app.save()

# ---------------------------------------------------------------- control count + save time


def walk(c):
    yield c
    for k in c.get('Children', []):
        yield from walk(k)


cnt = Counter(c['Template']['Name'] for s in app.map if s != 'App' for c in walk(app.doc(s)['TopParent']))
p = open(f'{NEW}/Properties.json', encoding='utf-8').read()
for k, v in cnt.items():
    p = re.sub(rf'("{k}": )\d+', rf'\g<1>{v}', p, count=1)
open(f'{NEW}/Properties.json', 'w', encoding='utf-8', newline='').write(p)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL_5 built')
