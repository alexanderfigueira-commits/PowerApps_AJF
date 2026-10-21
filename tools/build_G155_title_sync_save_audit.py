#!/usr/bin/env python3
"""FINAL166 on FINAL165 (= TEST_15 + fixes; the user's dashboard layout edits are all kept).
Save Media reported "SharePoint did not keep: production title". Static reading of the whole app shows only Save Media writes ProductionTitle
(from varChildTitle1, which the Validations tab also tests), so the app cannot be proven to send an empty title; the build therefore
 1. makes the title box (CI_Title / CM_EpisodeTitleP) win over the variable when its OnChange did not reach it, before the Validations are
    built (ChildValidScreen.OnVisible, CV_BtnRefresh) and before Save Media; Save Media also re-checks title / type / contract case on the
    live values (the Validations list is a snapshot);
 2. unifies the two title variables: CI_Title.OnChange and the Validations sync write varChildTitle too, the Podcast episode box and the
    three breadcrumbs read varChildTitle1 (the one Save Media uses);
 3. replaces the read-back (3 values) by an audit of every value Save Media sends: anything the app sent that SharePoint returns empty is
    named; the production title is written once more on its own when SharePoint did not keep it, and the title sent is quoted in the warning;
 4. CL_FormAttach.OnSuccess checks the title once more after the attachments were saved (and writes it again if it was blanked)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV27', 'newV28'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))   # scripts mix CRLF and LF: edit on LF
V, I, M, L = 'ChildValidScreen', 'ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen'

SYNC = '''// the title box is what the user sees: if its OnChange did not reach varChildTitle1 (typing, then a quick click on Next) the box wins
If(
    varChildMediaType = "Podcast",
    If(Not(IsBlank(Trim(CM_EpisodeTitleP.Text))), Set(varChildTitle1, Trim(CM_EpisodeTitleP.Text))),
    If(Not(IsBlank(Trim(CI_Title.Text))), Set(varChildTitle1, Trim(CI_Title.Text)))
);
Set(varChildTitle, varChildTitle1);
'''

# ---- 1a. Validations tab opens ---------------------------------------------------------------------------------------
t = app.rule(V, None, 'OnVisible')
a = 'Set(varNavArm, "");\n'
assert t.count(a) == 1
u = t.replace(a, a + SYNC)
app.set(V, None, 'OnVisible', u, expect=t)

# ---- 1b. Validations refresh -----------------------------------------------------------------------------------------
t = app.rule(V, 'CV_BtnRefresh', 'OnSelect')
a = '// a Video\'s Language and Type of product dropdowns show EN / Clip while nothing is stored: store what is shown\n'
assert t.startswith(a) and t.count(a) == 1
app.set(V, 'CV_BtnRefresh', 'OnSelect', SYNC + t, expect=t)

# ---- 2. one title variable: CI_Title writes both, the Podcast box and the breadcrumbs read varChildTitle1 -----------------
t = app.rule(I, 'CI_Title', 'OnChange'); assert t == 'Set(varChildTitle1, Self.Text)', t
app.set(I, 'CI_Title', 'OnChange', 'Set(varChildTitle1, Self.Text); Set(varChildTitle, Self.Text)', expect=t)
t = app.rule(M, 'CM_EpisodeTitleP', 'Default'); assert t == 'Coalesce(varChildTitle, varChildTitle1)', t
app.set(M, 'CM_EpisodeTitleP', 'Default', 'varChildTitle1', expect=t)
for scr, ctl in ((I, 'CI_Breadcrumb'), (M, 'CM_Breadcrumb'), (L, 'CL_Breadcrumb')):
    t = app.rule(scr, ctl, 'Text')
    assert t.count('varChildTitle') == 3 and 'varChildTitle1' not in t, (ctl, t)
    app.set(scr, ctl, 'Text', t.replace('varChildTitle', 'varChildTitle1'), expect=t)

# ---- 3. Save Media ---------------------------------------------------------------------------------------------------
t0 = app.rule(V, 'CV_BtnSaveArchive', 'OnSelect')
t = SYNC + t0

# 3a. the Validations list is a snapshot: what a media file cannot be saved without is checked again on the live values
a = '''First(Filter(colValidations, Not(Pass))).Note, NotificationType.Warning),
    With(
        {existingRec: LookUp(colArchives, ArchiveId = varCurrentChildId)},'''
assert t.count(a) == 1
GUARD = '''First(Filter(colValidations, Not(Pass))).Note, NotificationType.Warning),
    // the Validations list is a snapshot taken when this tab opened: what a media file cannot be saved without is checked again on the live values
    IsBlank(Trim(Coalesce(varChildTitle1, ""))) Or IsBlank(varChildMediaType) Or varChildMediaType = "" Or IsBlank(varChildContractCase) Or varChildContractCase = "",
    Notify("The media file cannot be saved yet: " & If(IsBlank(Trim(Coalesce(varChildTitle1, ""))), "the title is empty (Info tab).", If(IsBlank(varChildMediaType) Or varChildMediaType = "", "the production type is not selected (Info tab).", "no contract case is selected (Legal & Docs tab).")), NotificationType.Warning),
    With(
        {existingRec: LookUp(colArchives, ArchiveId = varCurrentChildId)},'''
t = t.replace(a, GUARD)

# 3b. the read-back becomes an audit of everything Save Media sends
OLD = '''
                    // what SharePoint really kept: the item is read back and anything empty that must not be is named
                    Refresh('AV-CD-Mediafiles');
                    With(
                        {chk: LookUp('AV-CD-Mediafiles', ID = savedMedia.ID)},
                        With(
                            {lost: Concat(Filter(Table(
                                {n: "production title", bad: IsBlank(Trim(Coalesce(chk.ProductionTitle, "")))},
                                {n: "production type", bad: IsEmpty(chk.MediaType)},
                                {n: "contract case", bad: IsEmpty(chk.ContractCase)}
                            ), bad), n, ", ")},
                            If(lost <> "", Notify("Saved, but SharePoint did not keep: " & lost & ". Open the media file and save it again.", NotificationType.Warning))
                        )
                    );'''
assert t.count(OLD) == 1


def txt(n, var, col):
    return f'{{n: "{n}", bad: Not(IsBlank(Trim(Coalesce({var}, "")))) And IsBlank(Trim(Coalesce(chk.{col}, "")))}}'


def html(n, var, col):      # rich-text columns come back wrapped in HTML
    return f'{{n: "{n}", bad: Not(IsBlank(Trim(Coalesce({var}, "")))) And IsBlank(Trim(PlainText(Coalesce(chk.{col}, ""))))}}'


def choice(n, var, col):
    return f'{{n: "{n}", bad: Not(IsBlank({var})) And {var} <> "" And IsEmpty(chk.{col})}}'


def date(n, var, col):
    return f'{{n: "{n}", bad: Not(IsBlank({var})) And IsBlank(chk.{col})}}'


def num(n, var, col):
    return f'{{n: "{n}", bad: Coalesce({var}, 0) > 0 And Coalesce(chk.{col}, 0) = 0}}'


def tick(n, var, col):
    return f'{{n: "{n}", bad: Coalesce({var}, false) And Not(Coalesce(chk.{col}, false))}}'


ROWS = [
    '{n: "production title", bad: IsBlank(Trim(Coalesce(chk.ProductionTitle, "")))}',
    '{n: "production type", bad: IsEmpty(chk.MediaType)}',
    '{n: "contract case", bad: IsEmpty(chk.ContractCase)}',
    html('description', 'varChildDescription1', 'Description'),
    date('capture date', 'varChildCaptureDate', 'CaptureDate'),
    txt('place', 'varChildProductionPlace1', 'ProductionPlace'),
    choice('type of product', 'varChildProductType', 'ProductType'),
    choice('language', 'varChildLanguageVersions', 'LanguageVersions'),
    txt('contractor / agency', 'varChildCredits1', 'CreditContact'),
    txt('contracting authority', 'varChildContractingAuthority', 'ContractingAuthority'),
    txt('executive producer', 'varChildExecProducer', 'ExecProducerName'),
    '{n: "producer", bad: Not(IsEmpty(varChildProducerSel)) And IsEmpty(chk.Producer)}',
    html('photographer', 'varChildPhotographer', 'PhotographerName'),
    html('photo caption', 'varChildPhotoCaption', 'PhotoCaption'),
    txt('series title', 'varChildSeriesTitle1', 'SeriesTitle'),
    txt('episode title', 'varChildEpisodeTitle', 'EpisodeTitle'),
    txt('episode summary', 'varChildEpisodeSummary1', 'EpisodeSummary'),
    num('season number', 'varChildSeasonNumber', 'SeasonNumber'),
    num('episode number', 'varChildEpisodeNumber', 'EpisodeNumber'),
    date('production end date', 'varChildProductionEndDate', 'ProductionEndDate'),
    date('publication start', 'varChildPublicationStartDate', 'PublicationStartDate'),
    date('publication end', 'varChildPublicationEndDate', 'PublicationEndDate'),
    txt('reference links', 'varChildLinks1', 'ReferenceLinks'),
    txt('tags', 'varChildTags', 'Tags'),
    txt('FTP path', 'varChildFTPPath1', 'FTPPath'),
    txt('Beluga reference', 'varChildBelugaRef', 'BelugaReference'),
    txt('script / shotlist', 'varChildScript', 'ScriptShotlist'),
    html('notes', 'varChildNotes', 'Notes'),
    choice('contract sub-case', 'varChildContractCase1Sub', 'ContractCase1Sub'),
    tick('model release', 'varChildModelRelease', 'ModelRelease'),
    tick('model release provided', 'varChildModelReleaseProvided', 'ModelReleaseProvided'),
    tick('music used', 'varChildMusicUsed', 'MusicUsed'),
    tick('music licence provided', 'varChildMusicLicenceProvided', 'MusicLicenseProvided'),
    tick('pre-existing rights', 'varChildPreexisting', 'PreexistingRights'),
    tick('pre-existing rights provided', 'varChildPreexistingProvided', 'PreexistingRightsProvided'),
    tick('subtitles provided', 'varChildSubtitlesProvided', 'SubtitlesProvided'),
    tick('no third-party rights', 'varChildNoThirdParty', 'NoThirdPartyRights'),
    tick('framework contract', 'varDocFramework', 'FrameworkContractSigned'),
    tick('specific contract', 'varDocSpecific', 'SpecificContractSigned'),
    tick('offer provided', 'varDocOffer', 'OfferProvided'),
]
TABLE = ',\n                                '.join(ROWS)
NEWV = f'''
                    // what SharePoint really kept. The production title is what the whole app is keyed on: if it is empty after the
                    // Patch it is written once more on its own (the Patch above already put it in the same request).
                    Refresh('AV-CD-Mediafiles');
                    If(
                        IsBlank(Trim(Coalesce(LookUp('AV-CD-Mediafiles', ID = savedMedia.ID).ProductionTitle, ""))),
                        IfError(
                            Patch('AV-CD-Mediafiles', LookUp('AV-CD-Mediafiles', ID = savedMedia.ID), {{ProductionTitle: Trim(Coalesce(varChildTitle1, ""))}}); true,
                            Notify("The production title could not be written to SharePoint: " & FirstError.Message, NotificationType.Error)
                        );
                        Refresh('AV-CD-Mediafiles')
                    );
                    // then every value the app sent that SharePoint returns empty is named
                    With(
                        {{chk: LookUp('AV-CD-Mediafiles', ID = savedMedia.ID)}},
                        With(
                            {{lost: Concat(Filter(Table(
                                {TABLE}
                            ), bad), n, ", ")}},
                            If(lost <> "", Notify("Saved, but SharePoint did not keep: " & lost & "." & If("production title" in lost, " The title sent was """ & Trim(Coalesce(varChildTitle1, "")) & """.", "") & " Open the media file and save it again.", NotificationType.Warning))
                        )
                    );'''
t = t.replace(OLD, NEWV)
app.set(V, 'CV_BtnSaveArchive', 'OnSelect', t, expect=t0)

# ---- 4. after the attachments were saved --------------------------------------------------------------------------------
t = app.rule(L, 'CL_FormAttach', 'OnSuccess')
a = "Set(varAttachRecord, LookUp('AV-CD-Mediafiles', ID = Coalesce(varCurrentChildSPId, 0)));\n"
assert t.count(a) == 1
CHECK = '''// the attachments save must not take the title away: checked once more, and written again if it was blanked
With(
    {k: LookUp('AV-CD-Mediafiles', ID = Coalesce(varCurrentChildSPId, 0))},
    If(
        Not(IsBlank(Trim(Coalesce(varChildTitle1, "")))) And IsBlank(Trim(Coalesce(k.ProductionTitle, ""))),
        IfError(
            Patch('AV-CD-Mediafiles', k, {ProductionTitle: Trim(varChildTitle1)});
            Notify("The production title was empty in SharePoint after the attachments were saved: it was written again.", NotificationType.Warning),
            Notify("The production title could not be written to SharePoint: " & FirstError.Message, NotificationType.Error)
        )
    )
);
'''
app.set(L, 'CL_FormAttach', 'OnSuccess', t.replace(a, a + CHECK), expect=t)

app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL166 built')
