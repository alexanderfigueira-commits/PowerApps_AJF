#!/usr/bin/env python3
"""FINAL120 on FINAL119: fixes the formula errors of CL_DCAttach.Update that Studio reported ("Name isn't valid. 'saved' / 'here' isn't recognized"):
the names of a With record cannot refer to each other, so `saved` and `here` are declared in an outer With and the lists that use them in an inner one. Nothing else changes."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newQ3', 'newQ4'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
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
            // this panel's files, minus the podcast files removed on Info / Metadata
            kept: Filter(
                CL_DCAttachValue.Attachments,
                varChildMediaType <> "Podcast"
                    Or Not(Name in saved)
                    Or (Not(EndsWith(Lower(Name), ".jpg") Or EndsWith(Lower(Name), ".jpeg") Or EndsWith(Lower(Name), ".png")) Or Name in CI_PodcastVisual.Attachments.Name Or Name in CM_EpisodeVisual.Attachments.Name)
                        And (Not(EndsWith(Lower(Name), ".mp3") Or EndsWith(Lower(Name), ".wav") Or EndsWith(Lower(Name), ".m4a") Or EndsWith(Lower(Name), ".aac")) Or Name in CM_AudioFiles.Attachments.Name)
            ),
            // new files added on Info / Metadata
            newVisual: Filter(CI_PodcastVisual.Attachments, Not(Name in saved) And Not(Name in here)),
            newAudio: Filter(CM_AudioFiles.Attachments, Not(Name in saved) And Not(Name in here)),
            newEpisode: Filter(
                CM_EpisodeVisual.Attachments,
                Not(Name in saved) And Not(("EpisodeVisual_" & Name) in saved) And Not(("EpisodeVisual_" & Name) in here)
            )
        },
        If(
            // photos, videos, and podcasts with nothing changed on the other tabs: the control's own table (the standard save)
            varChildMediaType <> "Podcast"
                Or (CountRows(kept) = CountRows(CL_DCAttachValue.Attachments) And IsEmpty(newVisual) And IsEmpty(newAudio) And IsEmpty(newEpisode)),
            CL_DCAttachValue.Attachments,
            // shaped as SharePoint attachment records: the saved attachment's Id, or the file name for a new file
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
                    Id: Coalesce(LookUp(varAttachRecord.Attachments, DisplayName = f.pre & f.Name).Id, f.pre & f.Name),
                    Value: f.Value
                }
            )
        )
    )
)'''
t = app.rule(L, 'CL_DCAttach', 'Update'); assert 'newVisual' in t
app.set(L, 'CL_DCAttach', 'Update', UPD.replace('\n', '\r\n') if '\r\n' in t else UPD, expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL120 built')
