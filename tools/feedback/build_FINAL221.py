#!/usr/bin/env python3
"""FINAL221 on FINAL220.
1. New Request: the Request description box is about 5 lines (53 -> 120 px); the contacts and the media section move down 67 px;
   the media table shows about 2-3 rows (218 -> 150 px) and scrolls for the rest.
2. Contact (Contractor) is optional: no '*', no yellow border, not needed to submit / resubmit.
3. A NEW request proposes the person who opens it as its first contact (editable): an external account ("-EXT)" in the display
   name, or an @ext. mail) in Contact (Contractor), EC staff in Contact (Official DG/Agency).
4. Legal & Docs: an attachment is required only when a document is marked (Case 1, a ticked contract / offer / release form /
   music licence / pre-existing annex / subtitles) and the documents do not travel by FTP. Otherwise "Attachments (optional)".
5. Exported PDF names start with the request date: 26-0006 created on 18-11-2026 -> 20261118-0006_Photo.pdf. The print screens
   still find an older PDF saved under the old name."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV82', 'newV83'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))


def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)


def rep(scr, ctl, prop, old, new, count=1):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    assert t.count(old) == count, (scr, ctl, prop, t.count(old), old[:80])
    app.set(scr, ctl, prop, t.replace(old, new), expect=t)


RS = 'RequesDetailScreen'
D = 67
# ---------------------------------------------------------------- 1. layout
setp(RS, 'RS_Description', 'Height', '120')
for c in ('RS_LblOwner', 'RS_Owner', 'RS_DetailsToggle_contrator_1', 'RS_LblContractor', 'RS_Contractor',
          'RS_DetailsToggle_contrator', 'SaveButton', 'addMediaItem', 'RS_ArchivesSection', 'DOA_List1CounterCircle_1',
          'DOA_List1CounterText_1', 'RS_ChildrenHeader', 'RS_ThStatus_1', 'RS_ThTitle', 'RS_ThPhotos', 'RS_ThStatus',
          'RS_ThApproved', 'RS_ThValidation'):
    y = app.rule(RS, c, 'Y').strip(); assert re.fullmatch(r'\d+', y), (c, y)
    setp(RS, c, 'Y', str(int(y) + D))
setp(RS, 'RS_RequestCard', 'Height', str(293 + D))
setp(RS, 'RS_DetailsDivider', 'Height', str(220 + D))
rep(RS, 'RS_ChildrenCard', 'Y', 'If(locDetailsCollapsed, 150, 448)', 'If(locDetailsCollapsed, 150, 515)')
rep(RS, 'RS_ChildrenCard', 'Height', 'If(locDetailsCollapsed, 550, 266)', 'If(locDetailsCollapsed, 550, 199)')
rep(RS, 'RS_ThTitle_1', 'Y', 'If(locDetailsCollapsed, 150, 460)', 'If(locDetailsCollapsed, 150, 527)')
rep(RS, 'RS_ChildrenGallery', 'Y', 'If(locDetailsCollapsed, 190, 496)', 'If(locDetailsCollapsed, 190, 563)')
setp(RS, 'RS_ChildrenGallery', 'Height', '// about 2-3 rows of 56 px; the scroll bar shows the rest\nIf(locDetailsCollapsed, 218, 150)')
setp(RS, 'RS_ChildrenEmpty', 'Y', '595')
setp(RS, 'RS_BtnAddFirst', 'Y', '635')
setp(RS, 'RS_NewRequestHint', 'Y', '625')

# ---------------------------------------------------------------- 2. Contractor optional
setp(RS, 'RS_LblContractor', 'Text', '"Contact (Contractor)"')
setp(RS, 'RS_Contractor', 'BorderColor', '// optional field: never yellow\nRGBA(0, 18, 107, 1)')
setp(RS, 'RS_Contractor', 'BorderThickness', '2')
for b in ('RS_BtnSubmitRequest', 'RS_BtnResubmitRequest'):
    rep(RS, b, 'DisplayMode', '    And Not(IsEmpty(RS_Contractor.SelectedItems))\n', '')

# ---------------------------------------------------------------- 3. the creator as first contact of a NEW request
anchor = 'Coalesce(IfError(Office365Users.MyProfile().Department, ""), "")'
ov = app.rule(RS, None, 'OnVisible'); i = ov.index(anchor); j = ov.index(');', i) + 2
ins = '''
// a NEW request proposes the person who opens it as its first contact (it stays editable): an external account
// ("-EXT)" in the display name, or an @ext. mail) as Contact (Contractor), EC staff as Contact (Official DG/Agency)
Set(varMeContact, With({me: IfError(Office365Users.MyProfile(), Blank())}, {DisplayName: Coalesce(me.DisplayName, User().FullName), Mail: Coalesce(me.Mail, User().Email)}));
Set(varMeIsExt, "-EXT)" in Upper(Coalesce(varMeContact.DisplayName, "")) Or "@ext." in Lower(Coalesce(varMeContact.Mail, "")));
If(Coalesce(varCurrentRequest.ID, 0) <= 0 And Not(varMeIsExt) And Not(IsBlank(varMeContact.Mail)), Set(varRequestOwnerContact, varMeContact.DisplayName));
'''
app.set(RS, None, 'OnVisible', ov[:j] + '\n' + ins + ov[j:], expect=ov)
for combo, cond in (('RS_Owner', 'Not(varMeIsExt)'), ('RS_Contractor', 'varMeIsExt')):
    old = '''                Not(IsBlank(DisplayName))
            )}
        ),
        rows
    )
)
)'''
    new = '''                Not(IsBlank(DisplayName))
            )},
            // a NEW request: the person who opens it (see OnVisible)
            {rows: Filter(
                Table({DisplayName: varMeContact.DisplayName, Mail: varMeContact.Mail, GivenName: "", Surname: "", MailNickname: ""}),
                Coalesce(varCurrentRequest.ID, 0) <= 0 And %s And Not(IsBlank(Mail))
            )}
        ),
        rows
    )
)
)''' % cond
    rep(RS, combo, 'DefaultSelectedItems', old, new)
# the validations read the owner from varRequestOwnerContact: Save keeps it equal to what is on screen
rep(RS, 'SaveButton', 'OnSelect', 'Set(varRequestDescription, RS_Description.Text);\n',
    'Set(varRequestDescription, RS_Description.Text);\nSet(varRequestOwnerContact, Concat(RS_Owner.SelectedItems, DisplayName, ", "));\n')

# ---------------------------------------------------------------- 4. Legal & Docs: attachment only when a document is marked
DOCS = ('(Left(Coalesce(varChildContractCase, ""), 6) = "Case 1" Or Coalesce(varDocFramework, false) Or Coalesce(varDocSpecific, false)'
        ' Or Coalesce(varDocOffer, false) Or (Coalesce(varChildModelRelease, false) And Coalesce(varChildModelReleaseProvided, false))'
        ' Or ((varChildMediaType = "Video" Or varChildMediaType = "Podcast") And ((Coalesce(varChildMusicUsed, false) And Coalesce(varChildMusicLicenceProvided, false))'
        ' Or (Coalesce(varChildPreexisting, false) And Coalesce(varChildPreexistingProvided, false))))'
        ' Or (varChildMediaType = "Video" And Coalesce(varChildSubtitlesProvided, false)))')
NEED = f'(Not(Coalesce(varDocsViaFTP, false)) And {DOCS})'
OLDP = 'Pass: varDocsViaFTP Or CountRows(CL_DCAttachValue.Attachments) > 0 Or'
NEWP = f'Pass: Not({DOCS}) Or varDocsViaFTP Or CountRows(CL_DCAttachValue.Attachments) > 0 Or'
OLDN = 'Note: "Legal annexes and supporting documents is empty. Attach at least one file on the Legal & Docs tab."'
NEWN = ('Note: "A document is marked on the Legal & Docs tab but nothing is attached. Attach the file(s) on the Legal & Docs tab, '
        'or tick the FTP option if they travel with the media."')
for ctl, prop in ((None, 'OnVisible'), ('CV_BtnRefresh', 'OnSelect')):
    rep('ChildValidScreen', ctl, prop, OLDP, NEWP)
    rep('ChildValidScreen', ctl, prop, OLDN, NEWN)
CL = 'ChildLegalScreen'
setp(CL, 'CL_DCAttachKey', 'Text', f'// required only when a document is marked above and the documents do not travel by FTP\nParent.DisplayName & If({NEED}, " *", " (optional)")')
setp(CL, 'CL_DCAttachValue', 'BorderColor',
     f'// yellow while a marked document has no file; red on a form error\nIf(Not(IsBlank(Parent.Error)), Color.Red, (CountRows(CL_DCAttachValue.Attachments) = 0 And Not(varRequestorLocked) And {NEED}), RGBA(255, 204, 0, 1), Parent.BorderColor)')
setp(CL, 'CL_DCAttachValue', 'BorderThickness',
     f'If((CountRows(CL_DCAttachValue.Attachments) = 0 And Not(varRequestorLocked) And {NEED}), 3, 2)')

# ---------------------------------------------------------------- 5. PDF names start with the request date
PFX = ('With({rn: Coalesce(varPrintRequest.RequestNumber, "%s")}, If(Mid(rn, 3, 1) = "-" And Not(IsBlank(varPrintRequest.Created)), '
       'Text(varPrintRequest.Created, "yyyymmdd") & Mid(rn, 3), rn))')
for scr, tmr, kind in (('PrintPhotoDetailScreen', 'PPD_PdfTimer', 'Photo'), ('PrintVideoDetailScreen', 'PVD_PdfTimer', 'Video'),
                       ('PrintPodcastDetailScreen', 'PPoD_PdfTimer', 'Podcast')):
    rep(scr, tmr, 'OnTimerEnd',
        f'// one file per request: a new export replaces it\n    Set(varPrintPdfName, Coalesce(varPrintRequest.RequestNumber, "request") & "_{kind}.pdf");',
        f'// one file per request: a new export replaces it; the name starts with the request date (26-0006 created on 18-11-2026 -> 20261118-0006_{kind}.pdf)\n'
        f'    Set(varPrintPdfName, {PFX % "request"} & "_{kind}.pdf");')
    rep(scr, None, 'OnVisible',
        '{f: First(Filter(colPrintExports, StartsWith(\'File name with extension\', Coalesce(varPrintRequest.RequestNumber, "§") & "_")))}',
        '{f: First(Filter(colPrintExports, StartsWith(\'File name with extension\', ' + (PFX % "§") + ' & "_") Or StartsWith(\'File name with extension\', Coalesce(varPrintRequest.RequestNumber, "§") & "_")))}')
    rep(scr, None, 'OnVisible', '(the file name cannot be filtered by SharePoint itself); file names start with the request number',
        '(the file name cannot be filtered by SharePoint itself); file names start with the request date and number (older ones with the request number)')

app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL221 built')
