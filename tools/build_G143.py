#!/usr/bin/env python3
"""FINAL154 on FINAL153 (dashboards).
 1. Row buttons of the two operational dashboards at size 11, like DOA_List1RowNumber: every RowNumber and every RowBadge
    (the status chip is made 92 x 22 with no vertical padding, so 11 pt fits: "Processing" is the longest text).
    The menu buttons of the top bar (size 10) are not touched.
 2. The row date was empty: the dashboards read SubmittedOn, which nothing ever filled in. The label now reads SubmittedOn, else
    StartRequestDate, else Created; its tooltip said "Submitted on" but showed Modified; its vertical padding (5 + 5 in a 20 px label,
    Overflow hidden) clipped the text. And Submit / Resubmit now record SubmittedOn (first submission date, kept on resubmission).
 3. DOA_List1Counter (circle + number) is 27 x 22 (was 20 x 19)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV13', 'newV14'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
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
print('FINAL154 built')
