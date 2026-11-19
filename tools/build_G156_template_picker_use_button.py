#!/usr/bin/env python3
"""FINAL167 on TEST_16 (= FINAL166 + the user's edit of CL_BtnPrev.Text, kept).
The "Copy from previous media item" picker (ChildInfoScreen):
 1. "Use" was a label whose OnSelect is Select(Parent), and the gallery has no OnSelect: clicking the word "Use" or the title did nothing, only the thin
    uncovered strips of the row background worked. "Use" is now a real button (blue, white bold text, hover colour) and every part of the row
    (background, title, meta line) presses it.
 2. The picker opens only when the production type is known (button disabled with a tooltip otherwise) and the gallery lists nothing without it;
    only media files of that production type are listed, each row names its type, and a file of another type is refused again when pressed.
 3. Every field of the chosen media file is read, as the media file itself is read when opened, attachments excepted (they are never touched) and the
    Beluga reference excepted (it identifies one file): the episode title (the variable Save Media writes) and the title variable the breadcrumbs read were
    missed, Notes and Photo caption (rich-text columns) came in as HTML. A confirmation message says what was copied."""
import datetime, os, re, shutil
from payaml import App
from hp_common import Builder
SRC, NEW = 'newT16', 'newV29'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))   # scripts mix CRLF and LF: edit on LF
I = 'ChildInfoScreen'
b = Builder(app, I)

# ---- the copy itself: from the existing "Overwrite and pre-fill" formula, with the gaps closed --------------------------------
t_ok = app.rule(I, 'CI_TplConfirmOK', 'OnSelect')


def sub(t, old, new):
    assert t.count(old) == 1, old
    return t.replace(old, new)


apply_ = t_ok
apply_ = sub(apply_, 'Set(varChildTitle1, Coalesce(varTplCandidate.ProductionTitle, ""));',
             'Set(varChildTitle1, Coalesce(varTplCandidate.ProductionTitle, ""));\nSet(varChildTitle, Coalesce(varTplCandidate.ProductionTitle, ""));')
apply_ = sub(apply_, 'Set(varChildNotes, Coalesce(varTplCandidate.Notes, ""));', 'Set(varChildNotes, PlainText(Coalesce(varTplCandidate.Notes, "")));')
apply_ = sub(apply_, 'Set(varChildPhotoCaption, Coalesce(varTplCandidate.PhotoCaption, ""));', 'Set(varChildPhotoCaption, PlainText(Coalesce(varTplCandidate.PhotoCaption, "")));')
apply_ = sub(apply_, 'Set(varChildEpisodeTitle1, Coalesce(varTplCandidate.EpisodeTitle, ""));',
             'Set(varChildEpisodeTitle1, Coalesce(varTplCandidate.EpisodeTitle, ""));\nSet(varChildEpisodeTitle, Coalesce(varTplCandidate.EpisodeTitle, ""));')
assert apply_.rstrip().endswith('Set(varShowTemplatePicker, false)')
apply_ = apply_.rstrip() + ';\nNotify("Pre-filled from " & Char(34) & Coalesce(varTplCandidate.ProductionTitle, varTplCandidate.CD_MediaNumber) & Char(34) & " (" & varTplCandidate.CD_MediaNumber & "). Attachments and the Beluga reference are not copied: add the files on the Legal & Docs tab.", NotificationType.Information)'
app.set(I, 'CI_TplConfirmOK', 'OnSelect', apply_, expect=t_ok)

# ---- "Use": a real button that holds the selection logic; every part of the row presses it ----------------------------------------
USE = ('Set(varTplCandidate, ThisItem);\n'
       'If(\n'
       '    // the picker lists only media files of this production type; a file of another type is never applied\n'
       '    ThisItem.tplType <> varChildMediaType,\n'
       '    Notify("Only " & varChildMediaType & " media files can be used as a template here.", NotificationType.Warning),\n'
       '    // something is already typed on this form: ask before overwriting\n'
       '    Coalesce(varChildTitle1, "") <> "" Or Coalesce(varChildDescription1, "") <> "",\n'
       '    Set(varShowTplConfirm, true),\n'
       + apply_.replace('\n', '\n    ').join(['    ', '']) + '\n)')
b.swap('CI_TplRowUse', I, 'CI_TplConfirmOK', {
    'Text': '"Use  ➤"',
    'Tooltip': '"Pre-fill this form from " & Char(34) & Coalesce(ThisItem.ProductionTitle, "this media file") & Char(34)',
    'X': '588', 'Y': '10', 'Width': '112', 'Height': '36',
    'Visible': 'true',
    'DisplayMode': 'If(varRequestorLocked Or IsBlank(varChildMediaType) Or varChildMediaType = "", DisplayMode.Disabled, DisplayMode.Edit)',
    'OnSelect': USE,
})
for ctl in ('CI_TplRowBg', 'CI_TplRowTitle', 'CI_TplRowMeta'):
    t = app.rule(I, ctl, 'OnSelect')
    app.set(I, ctl, 'OnSelect', 'Select(CI_TplRowUse)', expect=t)

# ---- the production type gates the picker ------------------------------------------------------------------------------------
NOTYPE = 'IsBlank(varChildMediaType) Or varChildMediaType = ""'
t = app.rule(I, 'CI_BtnTemplate', 'Text'); assert t == '"Copy from previous media item"', t
app.set(I, 'CI_BtnTemplate', 'Text', f'If({NOTYPE}, "Copy from previous media item", "Copy from previous " & If(varChildMediaType = "Photo", "Photo/Reportage", varChildMediaType))', expect=t)
t = app.rule(I, 'CI_BtnTemplate', 'Tooltip')
app.set(I, 'CI_BtnTemplate', 'Tooltip', f'If({NOTYPE}, "Select the production type first: the templates are the media files of that type.", "")', expect=t)
t = app.rule(I, 'CI_BtnTemplate', 'DisplayMode'); assert t == 'If(varRequestorLocked, DisplayMode.Disabled, DisplayMode.Edit)', t
app.set(I, 'CI_BtnTemplate', 'DisplayMode', f'If(varRequestorLocked Or {NOTYPE}, DisplayMode.Disabled, DisplayMode.Edit)', expect=t)
t = app.rule(I, 'CI_BtnTemplate', 'OnSelect')
app.set(I, 'CI_BtnTemplate', 'OnSelect',
        f'If(\n    {NOTYPE},\n    Notify("Select the production type first.", NotificationType.Warning),\n    ' + t.replace('\n', '\n    ') + '\n)', expect=t)

# ---- only the selected production type is listed, and each row says which ---------------------------------------------------------
t = app.rule(I, 'CI_TplGallery', 'Items')
old = 'tplType = varChildMediaType,'
assert t.count(old) == 1
app.set(I, 'CI_TplGallery', 'Items', t.replace(old, 'Not(IsBlank(varChildMediaType)) And varChildMediaType <> "" And tplType = varChildMediaType,'), expect=t)
t = app.rule(I, 'CI_TplRowMeta', 'Text')
old = 'Coalesce(ThisItem.CD_MediaNumber, "") & "   |   ID "'
assert t.count(old) == 1
app.set(I, 'CI_TplRowMeta', 'Text', t.replace(old, 'ThisItem.tplType & "   |   " & Coalesce(ThisItem.CD_MediaNumber, "") & "   |   ID "'), expect=t)
t = app.rule(I, 'CI_TplSubtitle', 'Text')
app.set(I, 'CI_TplSubtitle', 'Text',
        '"Showing only " & If(varChildMediaType = "Photo", "Photo/Reportage", varChildMediaType) & " media files, newest first. Press Use to pre-fill every field of this form except the attachments and the Beluga ID; the original is never modified."', expect=t)
t = app.rule(I, 'CI_TplEmpty', 'Text')
app.set(I, 'CI_TplEmpty', 'Text',
        'If(IsBlank(varTplSearch), "No previous " & If(varChildMediaType="Photo", "Photo/Reportage", varChildMediaType) & " media files yet.", "No " & If(varChildMediaType="Photo", "Photo/Reportage", varChildMediaType) & " media file matches " & Char(34) & varTplSearch & Char(34) & ".")', expect=t)

b.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL167 built')
