#!/usr/bin/env python3
"""FINAL131 on TEST_7 (the user's re-saved FINAL130): podcast Save Media - "Field 'Id' is required".
 * CL_DCAttach.Update: the merged list (podcasts with files on the Info / Metadata tabs) never carries a nameless record (a record without a file name could only get an empty Id, which
   is what the form refuses) and the result is cleaned of them; the Id of a new file is written in one of two ways (varAttachMode 0: the file name, 1: left empty for SharePoint to assign).
 * CL_FormAttach.OnFailure: for a podcast, if the form refuses the first way, the second is tried once before reporting; the report says how many files were sent and their names.
 * CV_BtnSaveArchive starts every Save Media on mode 0; CL_FormAttach.OnSuccess puts it back.
 * RequesDetailScreen.addMediaItem.BorderThickness had been typed as "2If(locSaveClicked, 2, 3)" in Studio (a formula error): back to If(locSaveClicked, 2, 3)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newR1', 'newR2'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
eol = lambda t: '\r\n' if '\r\n' in t else '\n'
L = 'ChildLegalScreen'
UPD = '''// CL_FormAttach is the only form that is submitted (Save Media). For podcasts the
// podcast visual (Info tab, CI_PodcastVisual), the episode visual (Metadata tab,
// CM_EpisodeVisual) and the audio files (Metadata tab, CM_AudioFiles) are edited in
// their own forms; a change made there is merged here so one SubmitForm saves every file
// and no form removes another form's files.
With(
    {
        saved: varAttachRecord.Attachments.DisplayName,
        here: CL_DCAttachValue.Attachments.Name
    },
    With(
        {
            // this panel's files, minus the podcast files removed on Info / Metadata (a record without a file name is never carried)
            kept: Filter(
                CL_DCAttachValue.Attachments,
                Not(IsBlank(Name))
                    And (
                        varChildMediaType <> "Podcast"
                            Or Not(Name in saved)
                            Or (
                                (Not(EndsWith(Lower(Name), ".jpg") Or EndsWith(Lower(Name), ".jpeg") Or EndsWith(Lower(Name), ".png")) Or Name in CI_PodcastVisual.Attachments.Name Or Name in CM_EpisodeVisual.Attachments.Name)
                                And (Not(EndsWith(Lower(Name), ".mp3") Or EndsWith(Lower(Name), ".wav") Or EndsWith(Lower(Name), ".m4a") Or EndsWith(Lower(Name), ".aac")) Or Name in CM_AudioFiles.Attachments.Name)
                            )
                    )
            ),
            // new files added on Info / Metadata
            newVisual: Filter(CI_PodcastVisual.Attachments, Not(IsBlank(Name)) And Not(Name in saved) And Not(Name in here)),
            newAudio: Filter(CM_AudioFiles.Attachments, Not(IsBlank(Name)) And Not(Name in saved) And Not(Name in here)),
            newEpisode: Filter(
                CM_EpisodeVisual.Attachments,
                Not(IsBlank(Name)) And Not(Name in saved) And Not(("EpisodeVisual_" & Name) in saved) And Not(("EpisodeVisual_" & Name) in here)
            )
        },
        If(
            // photos, videos, and podcasts with nothing changed on the other tabs: the control's own table (the standard save)
            varChildMediaType <> "Podcast"
                Or (CountRows(kept) = CountRows(CL_DCAttachValue.Attachments) And IsEmpty(newVisual) And IsEmpty(newAudio) And IsEmpty(newEpisode)),
            CL_DCAttachValue.Attachments,
            // shaped as SharePoint attachment records. Id: the saved attachment's Id; for a new file, the file name (varAttachMode 0) or empty (varAttachMode 1, the retry in OnFailure)
            Filter(
                ForAll(
                    Ungroup(
                        Table(
                            {pre: "", files: kept},
                            {pre: "", files: newVisual},
                            {pre: "", files: newAudio},
                            // a new episode visual is saved as "EpisodeVisual_<name>", which keeps it apart from the podcast visual
                            {pre: "EpisodeVisual_", files: newEpisode}
                        ),
                        files
                    ) As f,
                    {
                        Name: f.pre & f.Name,
                        DisplayName: f.pre & f.Name,
                        Id: Switch(
                            Coalesce(varAttachMode, 0),
                            0, Coalesce(LookUp(varAttachRecord.Attachments, DisplayName = f.pre & f.Name).Id, f.pre & f.Name),
                            LookUp(varAttachRecord.Attachments, DisplayName = f.pre & f.Name).Id
                        ),
                        Value: f.Value
                    }
                ),
                Not(IsBlank(Name))
            )
        )
    )
)'''
t = app.rule(L, 'CL_DCAttach', 'Update'); assert 'newVisual' in t and 'varAttachMode' not in t
app.set(L, 'CL_DCAttach', 'Update', UPD.replace('\n', eol(t)), expect=t)

FAIL = '''// Stop: stay on the Validations tab. The other fields were already Patched
// and the staged files are still in the form, so Save Media can be retried.
With(
    {sent: CL_DCAttach.Update},
    If(
        // a podcast's list merges the files of three panels: if the form refuses it, the second way of writing a new file's Id is tried once before reporting
        varChildMediaType = "Podcast" And Coalesce(varAttachMode, 0) = 0,
        Set(varAttachMode, 1);
        SubmitForm(CL_FormAttach),
        Notify(
            "The media details were saved, but the attachments were not: " & CL_FormAttach.Error & " (" & CountRows(sent) & " file(s) sent: " & Concat(sent, Name, ", ") & ")  Press Save Media to try again.",
            NotificationType.Error
        )
    )
)'''
t = app.rule(L, 'CL_FormAttach', 'OnFailure'); assert 'sent' not in t
app.set(L, 'CL_FormAttach', 'OnFailure', FAIL.replace('\n', eol(t)), expect=t)
t = app.rule(L, 'CL_FormAttach', 'OnSuccess'); assert t.startswith('Notify("Media and attachments saved')
app.set(L, 'CL_FormAttach', 'OnSuccess', ('Set(varAttachMode, 0);\n' + t.replace('\r\n', '\n')).replace('\n', eol(t)), expect=t)

V = 'ChildValidScreen'
t = app.rule(V, 'CV_BtnSaveArchive', 'OnSelect'); old = 'SubmitForm(CL_FormAttach),'
assert t.count(old) == 1
app.set(V, 'CV_BtnSaveArchive', 'OnSelect', t.replace(old, 'Set(varAttachMode, 0); SubmitForm(CL_FormAttach),'), expect=t)

t = app.rule('RequesDetailScreen', 'addMediaItem', 'BorderThickness'); assert t == '2If(locSaveClicked, 2, 3)'
app.set('RequesDetailScreen', 'addMediaItem', 'BorderThickness', 'If(locSaveClicked, 2, 3)', expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL131 built')
