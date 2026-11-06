#!/usr/bin/env python3
"""FINAL152 on FINAL151: submission date on the print screens and a date-range search on HomePrintScreen.
 * The header card of the three print screens (PVD/PPD/PPoD_HdrVal5, "Submitted") and the HP_Gallery column (HP_RowDate, header HP_ThSubmitted)
   already showed a date, read from StartRequestDate only. They now show the request's SubmittedOn (the date the dashboards and
   Request Management show), falling back to StartRequestDate, in dd-mm-yyyy.
 * HomePrintScreen: "SUBMITTED" From / To date pickers (HP_DateStart, HP_DateEnd) next to the status chips. The loaded requests are kept in
   colPrintAll; colPrintData (what every count, the gallery and the empty state already read) is colPrintAll narrowed to the date range,
   rebuilt on entering the screen, on each picker change and by Clear filters (which also clears the dates)."""
import datetime, os, re, shutil
from payaml import App
from hp_common import Builder
SRC, NEW = 'newV11', 'newV12'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

def date_text(rec, blank):
    return (f'If(Not(IsBlank({rec}.SubmittedOn)), Text({rec}.SubmittedOn, "dd-mm-yyyy"), '
            f'If(Not(IsBlank({rec}.StartRequestDate)), Text({rec}.StartRequestDate, "dd-mm-yyyy"), "{blank}"))')

# ---- 1. header card of the print screens, gallery column ---------------------------------------------------------
for screen, P in (('PrintVideoDetailScreen', 'PVD'), ('PrintPhotoDetailScreen', 'PPD'), ('PrintPodcastDetailScreen', 'PPoD')):
    t = app.rule(screen, f'{P}_HdrVal5', 'Text')
    assert t == 'If(IsBlank(varPrintRequest.StartRequestDate), "Not provided", Text(varPrintRequest.StartRequestDate, "dd-mm-yyyy"))', t
    app.set(screen, f'{P}_HdrVal5', 'Text', date_text('varPrintRequest', 'Not provided'), expect=t)
H = 'HomePrintScreen'
t = app.rule(H, 'HP_RowDate', 'Text')
assert t == 'If(IsBlank(ThisItem.StartRequestDate), "—", Text(ThisItem.StartRequestDate, "dd-mm-yyyy"))', t
app.set(H, 'HP_RowDate', 'Text', date_text('ThisItem', '—'), expect=t)

# ---- 2. data: colPrintAll -> colPrintData narrowed to the date range ----------------------------------------------
APPLY = '''// the submission date (SubmittedOn, else StartRequestDate) inside the From / To range; the end day is included
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
t = app.rule(H, None, 'OnVisible')
OLD = ("ClearCollect(colPrintData, 'AV-CD-Requests');\n"
       "RemoveIf(colPrintData, Not('Created By'.Email = User().Email Or (varUserRole = \"ADMINISTRATOR\" And Status.Value <> \"Draft\")));\n"
       "ClearCollect(colPrintMedia, 'AV-CD-Mediafiles')")
assert t.count(OLD) == 1
NEWV = ("ClearCollect(colPrintAll, 'AV-CD-Requests');\n"
        "RemoveIf(colPrintAll, Not('Created By'.Email = User().Email Or (varUserRole = \"ADMINISTRATOR\" And Status.Value <> \"Draft\")));\n"
        "ClearCollect(colPrintMedia, 'AV-CD-Mediafiles');\n" + APPLY)
app.set(H, None, 'OnVisible', t.replace(OLD, NEWV), expect=t)

t = app.rule(H, 'HP_BtnClear', 'OnSelect')
assert t == 'UpdateContext({locHPProductionType: "All", locHPStatus: "All"});\nReset(HP_TxtTitle);\nReset(HP_TxtRequestID)', t
app.set(H, 'HP_BtnClear', 'OnSelect',
        'UpdateContext({locHPProductionType: "All", locHPStatus: "All"});\nReset(HP_TxtTitle);\nReset(HP_TxtRequestID);\n'
        'Reset(HP_DateStart);\nReset(HP_DateEnd);\n// no dates: every loaded request\nClearCollect(colPrintData, colPrintAll)', expect=t)
app.save()

# ---- 3. the controls ---------------------------------------------------------------------------------------------
b = Builder(app, H)
b.clone('HP_LblDates', H, 'HP_ThSubmitted', {'Text': '"SUBMITTED"', 'X': '668', 'Y': '178', 'Width': '88', 'Height': '34'})
def picker(name, x, other_name, is_start):
    bad = (f'Not(IsBlank(HP_DateStart.SelectedDate)) And Not(IsBlank(HP_DateEnd.SelectedDate)) And HP_DateStart.SelectedDate > HP_DateEnd.SelectedDate')
    b.clone(name, 'RequestManagementScreen', 'HomeFilterStart', {
        'DefaultDate': 'Blank()', 'Format': '"dd-mm-yyyy"', 'X': str(x), 'Y': '178', 'Width': '160', 'Height': '34',
        'Visible': 'true', 'Size': '11',
        'BorderColor': f'If({bad}, RGBA(168, 0, 0, 1), RGBA(0, 18, 107, 1))',
        'OnChange': APPLY})
picker('HP_DateStart', 760, 'HP_DateEnd', True)
b.clone('HP_DateArrow', H, 'HP_ThSubmitted', {'Text': '"→"', 'X': '924', 'Y': '178', 'Width': '24', 'Height': '34', 'Align': 'Align.Center'})
picker('HP_DateEnd', 952, 'HP_DateStart', False)
b.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL152 built')
