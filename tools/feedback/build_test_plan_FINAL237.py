#!/usr/bin/env python3
"""Test plan for the changes of 18-19 Nov 2026: FINAL207 to FINAL237 (tested on FINAL237)."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter
OUT = '/home/user/PowerApps_AJF/docs/testing/AV-CD-Test-Plan-FINAL237.xlsx'
NAVY = '00126B'; HEAD = PatternFill('solid', fgColor=NAVY); WHITE = Font(bold=True, color='FFFFFF', name='Arial', size=10)
BASE = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True)
thin = Side(style='thin', color='C8CDD7'); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical='top')
R, A, B = 'REQUESTOR', 'ADMINISTRATOR', 'REQUESTOR / ADMINISTRATOR'
T = []  # (area, version, role, pre, steps, expected, priority)
def t(*a): T.append(a)

# ---------------------------------------------------------------- setup
t('Setup', 'FINAL223', A, 'Studio access', 'Open FINAL237 in Power Apps Studio and open the App Checker.',
  'No formula errors (the 6 errors of HomeFilterStart_Txt / HomeFilterEnd_Txt are gone). Old performance warnings may remain; no delegation warning on the print screens.', 'High')
t('Setup', 'FINAL207/214', A, 'Power Automate access', 'Check that flow AVCD_SavePrintPDF 1.0.0.2 is imported and on, that it writes to /AVCDExports and that the app lists it (Power Automate pane).',
  'Flow on, folder /AVCDExports (not /AVCDExports/Forms/...), flow visible in the app.', 'High')
t('Setup', 'FINAL210', A, 'Site owner rights', 'Check that requestors have Read on the library AV-CD-Exports and that the app has AV-CD-Exports as a data source.',
  'A requestor can open a link of the library; the print sheets load without "data source" errors.', 'High')
t('Setup', 'All', B, 'Published app', 'Run every test below in Play mode (or the published app), starting from Request Management / Export, not by opening a screen directly in Studio.',
  'OnVisible formulas run (pre-filled contact and DG, print sheet lookups).', 'High')

# ---------------------------------------------------------------- new request
t('New Request - layout', 'FINAL221', R, 'Request Management > New request', 'Look at the request screen; type 6-7 lines in Request description.',
  'Description box about 5 lines high (scrolls beyond); contacts below it; Save draft / Add media / media table moved down; nothing overlaps.', 'High')
t('New Request - layout', 'FINAL221', R, 'Request with 5 or more media files', 'Look at the media table.',
  'About 2-3 rows visible and a scroll bar for the others; header row (REF, TITLE, PHOTOS, VALIDATION, STATUS, APPROVED, ACTION) aligned.', 'High')
t('New Request - layout', 'FINAL221', R, 'New request', 'Open the type picker, the contact "+" pop-up, the leave pop-up (menu click) and the Draft saved pop-up.',
  'All pop-ups still centred and above everything; none moved with the layout.', 'Medium')
t('New Request - contacts', 'FINAL225/227', B, 'Request Management > New request', 'Look at Contact (Official DG/Agency) and Contact (Contractor).',
  'Your own name is already selected in Contact (Official DG/Agency); Contact (Contractor) is empty.', 'High')
t('New Request - contacts', 'FINAL225/227', R, 'New request with the pre-selected owner', 'Remove your name, pick another person, Save draft; reopen the request.',
  'The owner saved is the one on screen (the other person); your name is not added back.', 'High')
t('New Request - contacts', 'FINAL225', R, 'Existing request with saved contacts', 'Open it from Request Management.',
  'The saved contacts show; your name is not added to them.', 'High')
t('New Request - contacts', 'FINAL221', R, 'Draft with title, DG, owner, media files complete; no contractor', 'Look at Submit (and Resubmit on a Pending request).',
  'Contact (Contractor) has no "*" and no yellow border; Submit / Resubmit are enabled without a contractor.', 'High')
t('New Request - contacts', 'FINAL221/227', R, 'New request, owner pre-selected and not touched', 'Save draft, add a media file, go to Validations.',
  '"Owner / point of contact set on the request" passes.', 'High')
t('New Request - DG', 'FINAL230', B, 'User whose Microsoft 365 department is COMM.A.4.007', 'Request Management > New request; hover DG / Agency.',
  'DG / Agency shows "COMM - Communication"; tooltip "Filled in from your department in Microsoft 365 (COMM.A.4.007). You can change it."', 'High')
t('New Request - DG', 'FINAL230', R, 'New request with DG pre-selected', 'Pick another DG, Save draft; reopen the request.',
  'The DG picked is saved and shown; it is not replaced by your department.', 'High')
t('New Request - DG', 'FINAL227/230', B, 'Existing request of another DG', 'Open it.', 'Its own DG shows (not your department).', 'High')
t('New Request - DG', 'FINAL227/230', B, 'If available: an account whose department matches no DG of the list', 'New request; hover DG / Agency.',
  'DG / Agency empty with the yellow border (no longer the first DG, AGRI); Save draft disabled until a DG is picked; tooltip shows the department read.', 'Medium')
t('New Request - DG', 'FINAL230', R, 'REQUESTOR account (DG list limited to the own DG)', 'New request.', 'The own DG is pre-selected and is in the list.', 'Medium')
t('New Request - buttons', 'FINAL215', R, 'New request', 'Look at "Save draft" with the title or DG empty, then filled; hover it.',
  'Disabled until title and DG are filled; tooltip says what is missing / last saved.', 'Medium')
t('New Request - buttons', 'FINAL215', R, 'New request, title and DG filled', 'Click Save draft.',
  'Pop-up "Draft saved" with "Add media file" and "Later"; the empty table shows "Add the first media file"; Add media file is enabled.', 'High')

# ---------------------------------------------------------------- message center / request management
t('Message Center', 'FINAL231', A, 'Request in Processing, administrator', 'Open the Message Center on the request screen.',
  'The panel ends above the decision bar: message to the requestor, Approved, Pending, Rejected fully visible.', 'High')
t('Message Center', 'FINAL231', A, 'Message Center open', 'Write a message and send it; then type a decision comment and click Pending.',
  'The message box and send button work in their new place; the decision works with the Message Center open.', 'High')
t('Message Center', 'FINAL231', R, 'Requestor request (Draft or Pending)', 'Open the Message Center, send a message.', 'Layout correct, nothing cut, message sent.', 'Medium')
t('Request Management', 'FINAL231', B, 'One request without notes, one with notes', 'Hover the notes icon of each row.',
  'Without notes: "No notes". With notes: "New notes to check" or "Notes sent" and the last message (author, role, date, text).', 'High')
t('Request Management', 'FINAL224/232', B, 'Filters shown', 'Open the From / To date filters, pick dates, then a From later than To.',
  'Pickers white, black text, size 13; the list is filtered; red border when From > To.', 'High')

# ---------------------------------------------------------------- date pickers
t('Date pickers', 'FINAL216/224', R, 'Media file of each type (Info and Metadata tabs)', 'Click each date field, pick a date, save the media file and reopen it.',
  'One click opens the calendar and picks the date; date shown in black on white; value saved and shown again after reopening.', 'High')
t('Date pickers', 'FINAL224', R, 'Mandatory date empty (Shooting / Filming / Recording, Publication start / end)', 'Look at the field; then pick a date.',
  'Empty: "Select a date" and yellow border; after picking, normal border.', 'High')
t('Date pickers', 'FINAL224', B, 'Request opened in reading mode', 'Look at the date fields.', 'Light grey like the other read-only fields; date readable.', 'Medium')
t('Date pickers', 'FINAL232/236/237', B, 'Each screen', 'Compare the date text size with the other fields.',
  'Request Management 13, Export 13, Info 13, Metadata 13 (Shooting, Production end, Publication start, Publication end).', 'Medium')
t('Date pickers', 'FINAL224', B, 'Any date field', 'Note the date format shown.',
  'Short format of the user language (en-GB: dd/mm/yyyy). The dd-mm-yyyy labels of FINAL217 are hidden (known, by design).', 'Low')
t('Date pickers', 'FINAL216', R, 'Video or Podcast', 'Set publication end before publication start; production end before filming date.',
  'The Validations rows for both checks fail as before.', 'Medium')
t('Date pickers', 'FINAL216/232', A, 'Export screen', 'Use the start / end date filters.', 'List filtered; red border when start > end.', 'Medium')

# ---------------------------------------------------------------- media list, long texts
t('Media list', 'FINAL218', A, 'Request with one Ready and one incomplete media file', 'Look at the APPROVED column; hover the incomplete one.',
  'Ready: box can be ticked. Incomplete: box empty, disabled, tooltip explains why.', 'High')
t('Long texts', 'FINAL217', R, 'Photo / Video / Podcast media file', 'Type in Description, Description of the podcast, Photo caption up to 500 characters.',
  'Counter "(n / 500)" on the label from about 400; typing stops at 500.', 'High')
t('Long texts', 'FINAL220', R, 'Any long text box', 'Reach the limit (500 for Description / Podcast description / Photo caption; 255 for Episode summary / Script / Credits); then delete one character.',
  'At the limit a red line at the bottom: "Maximum N characters. For longer texts, upload a text file in Legal & Docs or share it via FTP"; it disappears after deleting.', 'High')

# ---------------------------------------------------------------- legal & docs
t('Legal & Docs', 'FINAL226', R, 'Case 6 (or 2-5), framework contract NOT ticked, no file, FTP option not ticked', 'Look at the attachments; go to Validations.',
  '"Attachments (optional)", no yellow border; "Legal annexes and supporting documents attached" passes; the media file can be saved.', 'High')
t('Legal & Docs', 'FINAL226', R, 'Case 2-6 with "Signed framework contract (optional)" ticked, no file', 'Look at the attachments; go to Validations; click Fix.',
  '"Attachments *" with yellow border; the row fails ("Case 1, or a ticked signed framework contract, needs its documents..."); Fix opens Legal & Docs.', 'High')
t('Legal & Docs', 'FINAL226', R, 'Same as above', 'Tick the FTP option ("... shared via FTP together with the media file(s)").', 'Attachment optional again; the row passes.', 'High')
t('Legal & Docs', 'FINAL226', R, 'Case 1, no file, FTP not ticked', 'Go to Validations.', 'Attachment required (row fails) as before.', 'High')
t('Legal & Docs', 'FINAL226', R, 'Case 2-6, framework not ticked', 'Tick music + music licence provided, model release provided, pre-existing provided, subtitles.',
  'None of them makes the attachment mandatory (the music rule "if music used -> documentation provided" still applies).', 'Medium')
t('Legal & Docs', 'FINAL226', R, 'Submitted request back in Pending; media file in Case 6 saved without framework', 'Open the media file > Legal & Docs.',
  'Framework box not ticked; attachment optional. (Case 1 media files still count the contracts as signed.)', 'Medium')
t('Legal & Docs', 'FINAL226', R, 'Submitted request; new media file added', 'Pick Case 6.',
  'Known behaviour: the framework box starts ticked; untick it to make the attachment optional.', 'Low')

# ---------------------------------------------------------------- print / PDF
t('Print - preview', 'FINAL207/212/235', B, 'Export > a request with 3+ media files', 'Click "Preview Print".',
  'Solid blue screen with "Preparing the preview" and three animated dots; the pages being prepared are not visible; then the PDF preview opens.', 'High')
t('Print - layout', 'FINAL208/233-235', B, 'PDF preview open (2 media per page)', 'Look at the top of each page.',
  'Small brand block centred at the top (EC logo, Central Deposit, Ticket System on dark blue); under it, left-aligned: title · request · ID · type · status, and created by · DG · submitted · assignee; nothing overlaps.', 'High')
t('Print - layout', 'FINAL212', B, 'PDF preview open', 'Look at the bottom of each page.', 'Footer centred: "AV Central Deposit Ticket System · ... · Page x of y".', 'Medium')
t('Print - layout', 'FINAL204/219', B, 'PDF preview, checkbox "Print full descriptions" not ticked', 'Count the media files per page.', '2 media files per page; an odd last page has one.', 'High')
t('Print - layout', 'FINAL219', B, '"Print full descriptions" ticked', 'Preview again.', '1 media file per page, header and footer on every page, 12 pt texts.', 'High')
t('Print - full texts', 'FINAL228', B, 'Photo with Description and Photo caption near 500 characters', 'Preview in both modes.',
  'Both texts complete (no "…"); field names "Description" and "Photo caption / Short Description" complete; nothing over the footer; smaller font only when needed.', 'High')
t('Print - full texts', 'FINAL228', B, 'Video with a long Description; Podcast with long Description and Summary of the episode', 'Preview in both modes.',
  'All texts complete, names not cut, nothing over the footer.', 'High')
t('Print - full texts', 'FINAL228', B, 'Media file with short texts', 'Preview.', 'Normal sizes (10 pt in 2 per page, 12 pt in 1 per page).', 'Medium')
t('Print - full texts', 'FINAL228', B, 'Description typed with line breaks', 'Preview.', 'All lines shown; nothing over the footer.', 'Low')
t('Print - save', 'FINAL207/213', B, 'PDF preview open (as REQUESTOR, then as ADMINISTRATOR)', 'Click Print in the preview.',
  '"Saving the PDF" box, then a pop-up with "Open / download" and the link; the PDF opens with all pages.', 'High')
t('Print - save', 'FINAL221/214', A, 'PDF saved', 'Open AV-CD-Exports.',
  'File named <request date yyyymmdd>-<number>_<Type>.pdf, e.g. 26-0006 created 18-11-2026 -> 20261118-0006_Photo.pdf.', 'High')
t('Print - save', 'FINAL214', B, 'PDF already saved', 'Pop-up > New preview > Print again.',
  'The same file is replaced (version history in SharePoint shows the previous one); the link opens the new copy, not a cached one.', 'High')
t('Print - download', 'FINAL210/221', B, 'PDF saved earlier (other session or other user)', 'Open the print sheet of that request.',
  'The button reads "Download PDF" and opens the pop-up with the link.', 'High')
t('Print - download', 'FINAL221', B, 'Request whose PDF was saved before FINAL221 (old name 26-0006_Photo.pdf)', 'Open its print sheet.',
  'The old PDF is still found ("Download PDF"); a new Print creates 20261118-0006_Photo.pdf.', 'Medium')
t('Print - screen', 'FINAL228/233', B, 'Print sheet without preview', 'Browse the pages with the arrows.',
  'Screen sheet as before: no brand block, no full-width rows (they are only in the PDF).', 'Medium')

# ---------------------------------------------------------------- regression
for typ in ('Photo', 'Video', 'Podcast'):
    t('Regression', 'All', B, f'{typ} request', 'Create the request (pre-filled owner and DG), add a media file, fill all tabs, validate, Save Media, submit; as administrator approve with the Message Center open; preview and print the PDF.',
      'Whole flow works end to end; statuses, notes and PDF as described above.', 'High')

wb = Workbook()
s = wb.active; s.title = 'Summary'
s['A1'] = 'AV Central Deposit - Test plan (FINAL237)'; s['A1'].font = Font(name='Arial', size=14, bold=True, color=NAVY)
s['A2'] = 'Changes of 18-19 Nov 2026: FINAL207 to FINAL237, tested on FINAL237. Fill column "Result" in the Tests sheet; this summary updates.'; s['A2'].font = BASE
for i, h in enumerate(['Result', 'Count', '% of tests'], 1):
    c = s.cell(row=4, column=i, value=h); c.fill = HEAD; c.font = WHITE; c.border = BOX
N = len(T); last = N + 1
for r, res in enumerate(['Pass', 'Fail', 'Blocked', 'Not run'], 5):
    s.cell(row=r, column=1, value=res)
    if res == 'Not run':
        s.cell(row=r, column=2, value=f'=COUNTA(Tests!A2:A{last})-SUM(B5:B7)')
    else:
        s.cell(row=r, column=2, value=f'=COUNTIF(Tests!J2:J{last},"{res}")')
    s.cell(row=r, column=3, value=f'=IF(COUNTA(Tests!A2:A{last})=0,0,B{r}/COUNTA(Tests!A2:A{last}))').number_format = '0%'
    for col in (1, 2, 3): s.cell(row=r, column=col).border = BOX; s.cell(row=r, column=col).font = BASE
s.cell(row=9, column=1, value='Total').font = BOLD; s.cell(row=9, column=2, value=f'=COUNTA(Tests!A2:A{last})').font = BOLD
s.cell(row=11, column=1, value='High-priority not passed').font = BOLD
s.cell(row=11, column=2, value=f'=COUNTIFS(Tests!I2:I{last},"High",Tests!J2:J{last},"<>Pass")').font = BOLD
notes = ['Replaced along the way (test only the final behaviour):',
         '- dd-mm-yyyy labels under the date pickers (FINAL217) -> white pickers with their own date format (FINAL224).',
         '- Contractor pre-filled for -EXT accounts (FINAL221) -> owner pre-filled for every user, contractor empty (FINAL225/227).',
         '- Attachment required when any document is ticked (FINAL221) -> only Case 1 or a ticked framework contract (FINAL226).',
         '- DG matched by word (FINAL222/229) -> DG starting with the department code, else first 3 characters, else blank (FINAL230).',
         '- PDF header text only (FINAL208) -> small brand block centred above it (FINAL233-235).',
         'Not changed: the request number format (26-0006); only the PDF file name starts with the request date.']
for i, line in enumerate(notes, 13):
    s.cell(row=i, column=1, value=line).font = BOLD if i == 13 else BASE
s.column_dimensions['A'].width = 30; s.column_dimensions['B'].width = 12; s.column_dimensions['C'].width = 12

w = wb.create_sheet('Tests')
cols = ['ID', 'Area', 'Version', 'Role', 'Preconditions', 'Steps', 'Expected result', 'Tester', 'Priority', 'Result', 'Date', 'Notes / evidence']
widths = [8, 20, 15, 16, 32, 45, 58, 14, 9, 11, 12, 35]
for i, (h, wd) in enumerate(zip(cols, widths), 1):
    c = w.cell(row=1, column=i, value=h); c.fill = HEAD; c.font = WHITE; c.alignment = Alignment(wrap_text=True, vertical='center'); c.border = BOX
    w.column_dimensions[get_column_letter(i)].width = wd
for r, (area, ver, role, pre, steps, exp, pri) in enumerate(T, 2):
    vals = [f'T{r-1:02d}', area, ver, role, pre, steps, exp, '', pri, 'Not run', None, '']
    for i, v in enumerate(vals, 1):
        c = w.cell(row=r, column=i, value=v); c.font = BASE; c.alignment = WRAP; c.border = BOX
    w.cell(row=r, column=11).number_format = 'dd-mm-yyyy'
dv = DataValidation(type='list', formula1='"Pass,Fail,Blocked,Not run"', allow_blank=True); w.add_data_validation(dv); dv.add(f'J2:J{last}')
dv2 = DataValidation(type='list', formula1='"High,Medium,Low"', allow_blank=True); w.add_data_validation(dv2); dv2.add(f'I2:I{last}')
for val, color in (('Pass', 'D9F2E3'), ('Fail', 'FBD9D9'), ('Blocked', 'FFF2CC')):
    w.conditional_formatting.add(f'J2:J{last}', CellIsRule(operator='equal', formula=[f'"{val}"'], fill=PatternFill('solid', fgColor=color)))
w.freeze_panes = 'C2'; w.auto_filter.ref = f'A1:L{last}'

p = wb.create_sheet('Prerequisites')
rows = [('Where', 'What', 'Settings', 'Needed from', 'Done?'),
        ('Power Automate', 'Flow AVCD_SavePrintPDF 1.0.0.2', 'Import docs/flows/AVCD_SavePrintPDF_solution.zip; folder /AVCDExports; turned on; added in the app', 'FINAL207', ''),
        ('Site', 'Library AV-CD-Exports (URL /AVCDExports)', 'Requestors: Read (lookup and download link); the flow writes the files', 'FINAL207/210', ''),
        ('Studio', 'Data source AV-CD-Exports', 'Already in TEST_22 and later; refresh if the library was recreated', 'FINAL210', ''),
        ('Studio', 'PdfViewer1 on the print sheets', 'Already in TEST_21 and later', 'FINAL202', ''),
        ('Microsoft 365', 'Department of the test accounts', 'e.g. COMM.A.4.007: its code (COMM) must start a DG choice ("COMM - Communication")', 'FINAL230', ''),
        ('SharePoint', 'No new column', 'Nothing to create for FINAL207-237', '-', '')]
for r, row in enumerate(rows, 1):
    for i, v in enumerate(row, 1):
        c = p.cell(row=r, column=i, value=v); c.border = BOX; c.alignment = WRAP
        c.font = WHITE if r == 1 else BASE
        if r == 1: c.fill = HEAD
for i, wd in enumerate([18, 34, 70, 14, 10], 1): p.column_dimensions[get_column_letter(i)].width = wd
wb.save(OUT); print(OUT, N, 'tests')
