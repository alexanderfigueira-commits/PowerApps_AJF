#!/usr/bin/env python3
"""FINAL165 on TEST_15 (= FINAL164 + the user's dashboard layout edits, all kept).
Deep check of "save a media file -> back on the request -> open it again". The data plumbing (Save Patch -> loader -> row-open -> controls) was audited
field by field: every saved column is read back by the loader and every loaded field is put in a variable by the row-open. What was wrong:
 1. ChildLegalScreen: seven "Rights & declarations" checkboxes had Default = false, so a saved media file always re-opened with them unticked
    (model release, music used, pre-existing rights, subtitles and their "provided" sub-boxes) - or kept the previous media file's ticks.
    They now follow their variables like the other fields of the screen.
 2. Opening a media file did not reset varChildTitle (read by the Podcast's "Title of the episode" box through Coalesce(varChildTitle, varChildTitle1)),
    so it showed the title of the media file opened before; varChildEpisodeTitle (saved as EpisodeTitle) was never loaded. Both are loaded now.
 3. RS_CRowValid (the "Ready / Incomplete" label of each media row) tested Title, which since the media number became the list title is never empty;
    it now tests the production title, the production type, the contract case and the AI voice-over, and its tooltip names what is missing.
 4. Save Media now reads the item back from SharePoint and warns when the production title, the production type or the contract case were not kept."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newT15', 'newV27'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

# ---- 1. ChildLegalScreen checkboxes ------------------------------------------------------------------------------
L = 'ChildLegalScreen'
for ctl, var in (('CL_ChkModel', 'varChildModelRelease'), ('CL_ChkModelProvided', 'varChildModelReleaseProvided'),
                 ('CL_ChkMusic', 'varChildMusicUsed'), ('CL_ChkMusicProvided', 'varChildMusicLicenceProvided'),
                 ('CL_ChkPreexisting', 'varChildPreexisting'), ('CL_ChkPreexistingProvided', 'varChildPreexistingProvided'),
                 ('CL_ChkSubtitles', 'varChildSubtitlesProvided')):
    t = app.rule(L, ctl, 'Default'); assert t == 'false', (ctl, t)
    app.set(L, ctl, 'Default', f'Coalesce({var}, false)', expect=t)

# ---- 2. row-open: the two variables it did not load -----------------------------------------------------------------
R = 'RequesDetailScreen'
t = app.rule(R, 'DOA_List1RowBadge_8', 'OnSelect')
anchor = 'Set(varChildTitle1, Coalesce(ThisItem.ProductionTitle, ""));'
assert t.count(anchor) == 1 and 'Set(varChildTitle,' not in t
u = t.replace(anchor, anchor + '\nSet(varChildTitle, Coalesce(ThisItem.ProductionTitle, ""));\nSet(varChildEpisodeTitle, Coalesce(ThisItem.EpisodeTitle, ""));')
app.set(R, 'DOA_List1RowBadge_8', 'OnSelect', u, expect=t)

# ---- 3. RS_CRowValid ---------------------------------------------------------------------------------------------------
MISSING = ('Concat(Filter(Table(\n'
           '    {n: "production title", bad: IsBlank(Trim(Coalesce(ThisItem.ProductionTitle, "")))},\n'
           '    {n: "production type", bad: IsBlank(ThisItem.MediaType) Or ThisItem.MediaType = ""},\n'
           '    {n: "contract case", bad: IsBlank(ThisItem.ContractCase) Or ThisItem.ContractCase = ""},\n'
           '    {n: "AI voice-over (not accepted)", bad: Coalesce(ThisItem.AIVoiceover, false)}\n'
           '), bad), n, ", ")')
OK = 'Not(IsBlank(Trim(Coalesce(ThisItem.ProductionTitle, "")))) And Not(IsBlank(ThisItem.MediaType)) And ThisItem.MediaType <> "" And Not(IsBlank(ThisItem.ContractCase)) And ThisItem.ContractCase <> "" And Not(Coalesce(ThisItem.AIVoiceover, false))'
for prop, new in (('Text', f'If(\n    {OK},\n    "✓  Ready",\n    "⚠  Incomplete"\n)'),
                  ('Color', f'If(\n    {OK},\n    RGBA(22, 128, 80, 1),\n    RGBA(193, 40, 40, 1)\n)'),
                  ('Tooltip', f'If(\n    {OK},\n    "",\n    "Missing: " & {MISSING}\n)')):
    t = app.rule(R, 'RS_CRowValid', prop)
    app.set(R, 'RS_CRowValid', prop, new, expect=t)

# ---- 4. Save Media: read the item back ---------------------------------------------------------------------------------
V = 'ChildValidScreen'
t = app.rule(V, 'CV_BtnSaveArchive', 'OnSelect')
anchor = 'Set(varCurrentChildSPId, savedMedia.ID);'
assert t.count(anchor) == 1
VERIFY = '''
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
app.set(V, 'CV_BtnSaveArchive', 'OnSelect', t.replace(anchor, anchor + VERIFY), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL165 built')
