#!/usr/bin/env python3
"""FINAL169 on FINAL168. The Requests list shows "(hh:mm)" under Submitted and Updated.
 - Submitted reads SubmittedOn, a Date-only SharePoint column that the app filled with Today(): its time is always 00:00, so "(00:00)" was a placeholder
   (and nothing at all when SubmittedOn is empty). Submit / Resubmit now write Now(); the list shows the time only when the stored value has one, so it
   becomes real once the column is switched to "Date and time" in SharePoint (a date-only column keeps just the day).
 - HomePrintScreen's From / To range compared SubmittedOn <= the end day at 00:00, which would drop a request submitted that day once SubmittedOn has a time:
   the end day is included as it already is for StartRequestDate and Created.
 - Both date labels pass an explicit "en-US" language to Text(), so month names and format codes are the same on every user's regional settings."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV30', 'newV31'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))

R = 'RequestManagementScreen'
t = app.rule(R, 'HomeRowAssignee_1', 'Text')
old = 'Text(ThisItem.SubmittedOn, "dd mmm \'yy  (hh:mm)")'
assert t.count(old) == 1, t
new = ('If(\n    IsBlank(ThisItem.SubmittedOn),\n    "",\n    Text(\n        ThisItem.SubmittedOn,\n'
       '        "dd mmm \'yy" & If(Hour(ThisItem.SubmittedOn) = 0 And Minute(ThisItem.SubmittedOn) = 0, "", "  (hh:mm)"),\n        "en-US"\n    )\n)')
app.set(R, 'HomeRowAssignee_1', 'Text', t.replace(old, new), expect=t)
t = app.rule(R, 'HomeRowAssignee_2', 'Text')
old = 'Text(ThisItem.Created, "dd mmm \'yy  (hh:mm)")'
assert t.count(old) == 1, t
app.set(R, 'HomeRowAssignee_2', 'Text', t.replace(old, 'Text(ThisItem.Created, "dd mmm \'yy  (hh:mm)", "en-US")'), expect=t)

D = 'RequesDetailScreen'
for ctl in ('RS_BtnSubmitRequest', 'RS_BtnResubmitRequest'):
    t = app.rule(D, ctl, 'OnSelect')
    old = 'SubmittedOn: Coalesce(varCurrentRequest.SubmittedOn, Today())'
    assert t.count(old) == 1
    app.set(D, ctl, 'OnSelect', t.replace(old, 'SubmittedOn: Coalesce(varCurrentRequest.SubmittedOn, Now())'), expect=t)

H = 'HomePrintScreen'
old = 'Not(IsBlank(SubmittedOn)), SubmittedOn <= HP_DateEnd.SelectedDate,'
new = 'Not(IsBlank(SubmittedOn)), SubmittedOn < DateAdd(HP_DateEnd.SelectedDate, 1, TimeUnit.Days),'
for scr, ctl in ((H, None), (H, 'HP_DateStart'), (H, 'HP_DateEnd')):
    prop = 'OnVisible' if ctl is None else 'OnChange'
    t = app.rule(scr, ctl, prop)
    assert t.count(old) == 1, (ctl, prop)
    app.set(scr, ctl, prop, t.replace(old, new), expect=t)

app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL169 built')
