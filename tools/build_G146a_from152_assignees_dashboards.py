#!/usr/bin/env python3
"""FINAL157 on FINAL152 (the user asked to go back to FINAL152 and add two things):
 A. ReviewScreen, RV_Assignee: only the administrators of AV-CD-RolesPermissionsList can be picked (as in FINAL153, part 1; the Photographer
    free-text change of FINAL153 is NOT included).
 B. The dashboard changes of FINAL154: row buttons at size 11, row date fixed (SubmittedOn / StartRequestDate / Created, Submit records
    SubmittedOn), DOA_List1Counter 27 x 22."""
import datetime, json, os, re, shutil
from payaml import App
SRC, NEW = 'newV12', 'newV17'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

def edit(screen, control, prop, subs):
    t = app.rule(screen, control, prop); u = t
    for pat, new, cnt in subs:
        found = len(re.findall(pat, u, re.S))
        assert found == cnt, (screen, control, prop, pat, found)
        u = re.sub(pat, lambda m: new, u, flags=re.S)
    app.set(screen, control, prop, u, expect=t)

# ---- 1. assignees ------------------------------------------------------------------------------------------------
R = 'ReviewScreen'
t = app.rule(R, None, 'OnVisible')
assert t.rstrip().endswith('Set(varReviewFromRow, false)')
app.set(R, None, 'OnVisible', t.rstrip() + ''';
// who can be picked as assignee / co-assignee: the administrators of the roles list, not every contact
ClearCollect(
    colReviewAdmins,
    Sort(
        ForAll(
            Filter('AV-CD-RolesPermissionsList', Role.Value = "ADMINISTRATOR"),
            {DisplayName: UserEmail.DisplayName, Mail: UserEmail.Email}
        ),
        DisplayName
    )
)''', expect=t)
for prop, old, new in (
        ('Items', 'Office365Users.SearchUserV2({searchTerm: Self.SearchText, top: 20}).value', 'colReviewAdmins'),
        ('SearchItems', 'Office365Users.SearchUserV2({searchTerm: Self.SearchText, top: 20}).value',
         'Search(colReviewAdmins, RV_Assignee.SearchText, DisplayName, Mail)'),
        ('InputTextPlaceholder', '"Search people: assignee, and co-assignee when needed (max 2)…"',
         '"Search administrators: assignee, and co-assignee when needed (max 2)…"')):
    t = app.rule(R, 'RV_Assignee', prop); assert t == old, (prop, t)
    app.set(R, 'RV_Assignee', prop, new, expect=t)


SCR = {'DOA': 'Dashboard-Ope-Administrator', 'DOR': 'Dashboard-Ope-Requestor'}

def chain(fmt_date, fmt_time):
    return ('If(Not(IsBlank(ThisItem.SubmittedOn)), Text(ThisItem.SubmittedOn, "%s"), '
            'If(Not(IsBlank(ThisItem.StartRequestDate)), Text(ThisItem.StartRequestDate, "%s"), Text(ThisItem.Created, "%s")))'
            % (fmt_date, fmt_time, fmt_time))

def setp(screen, ctl, prop, new, old=None):
    t = app.rule(screen, ctl, prop)
    if old is not None:
        assert t == old, (ctl, prop, t)
    if t != new:
        app.set(screen, ctl, prop, new, expect=t)

for P, S in SCR.items():
    for i in (1, 2, 3):
        # --- buttons -------------------------------------------------------------------------------------------------
        setp(S, f'{P}_List{i}RowNumber', 'Size', '11')
        b = f'{P}_List{i}RowBadge'
        x, y = int(app.rule(S, b, 'X')), int(app.rule(S, b, 'Y'))
        setp(S, b, 'Size', '11'); setp(S, b, 'Width', '92'); setp(S, b, 'Height', '22')
        setp(S, b, 'X', str(x - 12)); setp(S, b, 'Y', str(y - 2))
        for p, v in (('PaddingTop', '0'), ('PaddingBottom', '0'), ('PaddingLeft', '3'), ('PaddingRight', '3')):
            setp(S, b, p, v)
        # --- date ----------------------------------------------------------------------------------------------------
        d = f'{P}_List{i}RowDate'
        if P == 'DOR' and i in (1, 2):
            text = 'If(\n    ThisItem.Status.Value = "Draft",\n    "Created " & Text(ThisItem.Created, "dd mmm \'yy"),\n    "Submitted " & ' + chain("dd mmm 'yy", "dd mmm 'yy") + '\n)'
            tip = ('If(\n    ThisItem.Status.Value = "Draft",\n    "Created on: " & Text(ThisItem.Created, "dd mmm \'yy (hh:mm)"),\n    "Submitted on: " & '
                   + chain("dd mmm 'yy", "dd mmm 'yy (hh:mm)") + '\n)')
        else:
            text = chain("dd mmm 'yy", "dd mmm 'yy")
            tip = '"Submitted on: " & Char(10) & ' + chain("dd mmm 'yy", "dd mmm 'yy (hh:mm)")
        setp(S, d, 'Text', text); setp(S, d, 'Tooltip', tip)
        setp(S, d, 'PaddingTop', '0'); setp(S, d, 'PaddingBottom', '0')

# --- counter -------------------------------------------------------------------------------------------------------------
S = SCR['DOA']
for c in ('DOA_List1CounterCircle', 'DOA_List1CounterText'):
    assert (app.rule(S, c, 'X'), app.rule(S, c, 'Y'), app.rule(S, c, 'Width'), app.rule(S, c, 'Height')) == ('431', '159', '20', '19'), c
    setp(S, c, 'Width', '27'); setp(S, c, 'Height', '22'); setp(S, c, 'X', '428'); setp(S, c, 'Y', '158')

# --- record the submission date --------------------------------------------------------------------------------------------
D = 'RequesDetailScreen'
for ctl in ('RS_BtnSubmitRequest', 'RS_BtnResubmitRequest'):
    t = app.rule(D, ctl, 'OnSelect')
    pat = re.compile(r'(Status: \{Value: "Processing"\})(\s*\n)(\s*\})')
    assert len(pat.findall(t)) == 1, ctl
    u = pat.sub(lambda m: m.group(1) + ',' + m.group(2).replace('\n', '\n', 1) + '                                  // the first submission date is kept on a resubmission\n                                  SubmittedOn: Coalesce(varCurrentRequest.SubmittedOn, Today())' + m.group(2) + m.group(3), t)
    app.set(D, ctl, 'OnSelect', u, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL157 built')
