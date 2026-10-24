#!/usr/bin/env python3
"""FINAL155 on FINAL154.
 1. Dashboards: every Notes icon (DOA_List1/2/3RowNotes, DOR_List1/2/3RowNotes) shows in its tooltip the status line it had
    ("No notes" / "New notes to check" / "Notes sent") followed by ONLY the last message written on the request
    (any author): who, when, text (plain text, 280 characters at most). DOA_List1RowNotes no longer lists the last message of each side.
 2. HomePrintScreen: the From / To search found nothing when the request had neither SubmittedOn nor StartRequestDate (a blank date never
    passes a range). The submission date is now SubmittedOn, else StartRequestDate, else Created (always there) in the range filter,
    in HP_RowDate and in the header card of the three print screens."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV14', 'newV15'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

# ---- 1. notes tooltips -------------------------------------------------------------------------------------------------
LAST = '''With(
    {n: First(Sort(Filter('AV-CD-Notes', ParentRequest = ThisItem.RequestNumber), NoteDate, SortOrder.Descending))},
    If(
        IsBlank(n),
        "",
        Char(10) & Char(10) & "Last message · " & Coalesce(n.AuthorName, "—") & " (" & Coalesce(n.AuthorRole.Value, "") & ") · " & Text(Coalesce(n.NoteDate, n.Created), "dd mmm 'yy hh:mm")
            & Char(10) & Left(PlainText(Coalesce(n.NoteText, "")), 280) & If(Len(PlainText(Coalesce(n.NoteText, ""))) > 280, "…", "")
    )
)'''
def status(P):
    # DOA: amber when the requestor wrote last; DOR: amber when the administrator wrote last
    a, b, ta, tb = ('reqHas', 'admHas', 'reqAt', 'admAt') if P == 'DOA' else ('admHas', 'reqHas', 'admAt', 'reqAt')
    return f'''With(
    {{
        reqHas: Not(IsBlank(ThisItem.RequestorNotesUpdatedOn)),
        admHas: Not(IsBlank(ThisItem.AdminNotesUpdatedOn)),
        reqAt: Coalesce(ThisItem.RequestorNotesUpdatedOn, DateTime(2000, 1, 1, 0, 0, 0)),
        admAt: Coalesce(ThisItem.AdminNotesUpdatedOn, DateTime(2000, 1, 1, 0, 0, 0))
    }},
    If(
        Not({b}) And Not({a}),
        "No notes",
        If({a} And (Not({b}) Or {ta} > {tb}), "New notes to check", "Notes sent")
    )
)'''
for P, S in (('DOA', 'Dashboard-Ope-Administrator'), ('DOR', 'Dashboard-Ope-Requestor')):
    for i in (1, 2, 3):
        c = f'{P}_List{i}RowNotes'
        t = app.rule(S, c, 'Tooltip')
        norm = ' '.join(t.split())
        assert norm.startswith(' '.join(status(P).split())[:200]), c        # the status line is the one we know
        app.set(S, c, 'Tooltip', status(P) + ' & ' + LAST, expect=t)

# ---- 2. HomePrintScreen date --------------------------------------------------------------------------------------------
H = 'HomePrintScreen'
OLD_APPLY = '''// the submission date (SubmittedOn, else StartRequestDate) inside the From / To range; the end day is included
ClearCollect(
    colPrintData,
    Filter(
        colPrintAll,
        IsBlank(HP_DateStart.SelectedDate)
            Or (Not(IsBlank(SubmittedOn)) And SubmittedOn >= HP_DateStart.SelectedDate)
            Or (IsBlank(SubmittedOn) And StartRequestDate >= HP_DateStart.SelectedDate),
        IsBlank(HP_DateEnd.SelectedDate)
            Or (Not(IsBlank(SubmittedOn)) And SubmittedOn <= HP_DateEnd.SelectedDate)
            Or (IsBlank(SubmittedOn) And StartRequestDate < DateAdd(HP_DateEnd.SelectedDate, 1, TimeUnit.Days))
    )
)'''
NEW_APPLY = '''// the submission date (SubmittedOn, else StartRequestDate, else Created) inside the From / To range; the end day is included
ClearCollect(
    colPrintData,
    Filter(
        colPrintAll,
        IsBlank(HP_DateStart.SelectedDate)
            Or If(
                Not(IsBlank(SubmittedOn)), SubmittedOn >= HP_DateStart.SelectedDate,
                Not(IsBlank(StartRequestDate)), StartRequestDate >= HP_DateStart.SelectedDate,
                Created >= HP_DateStart.SelectedDate
            ),
        IsBlank(HP_DateEnd.SelectedDate)
            Or If(
                Not(IsBlank(SubmittedOn)), SubmittedOn <= HP_DateEnd.SelectedDate,
                Not(IsBlank(StartRequestDate)), StartRequestDate < DateAdd(HP_DateEnd.SelectedDate, 1, TimeUnit.Days),
                Created < DateAdd(HP_DateEnd.SelectedDate, 1, TimeUnit.Days)
            )
    )
)'''
t = app.rule(H, None, 'OnVisible'); assert t.count(OLD_APPLY) == 1
app.set(H, None, 'OnVisible', t.replace(OLD_APPLY, NEW_APPLY), expect=t)
for c in ('HP_DateStart', 'HP_DateEnd'):
    t = app.rule(H, c, 'OnChange'); assert t == OLD_APPLY, c
    app.set(H, c, 'OnChange', NEW_APPLY, expect=t)

def dtext(rec, fmt='dd-mm-yyyy'):
    return (f'If(Not(IsBlank({rec}.SubmittedOn)), Text({rec}.SubmittedOn, "{fmt}"), '
            f'If(Not(IsBlank({rec}.StartRequestDate)), Text({rec}.StartRequestDate, "{fmt}"), Text({rec}.Created, "{fmt}")))')
t = app.rule(H, 'HP_RowDate', 'Text'); assert 'ThisItem.StartRequestDate' in t and '"—"' in t, t
app.set(H, 'HP_RowDate', 'Text', dtext('ThisItem'), expect=t)
for screen, P in (('PrintVideoDetailScreen', 'PVD'), ('PrintPhotoDetailScreen', 'PPD'), ('PrintPodcastDetailScreen', 'PPoD')):
    t = app.rule(screen, f'{P}_HdrVal5', 'Text'); assert '"Not provided"' in t, t
    app.set(screen, f'{P}_HdrVal5', 'Text', dtext('varPrintRequest'), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL155 built')
