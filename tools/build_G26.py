#!/usr/bin/env python3
"""FINAL36 on FINAL35: the "Copy from previous media item" template on ChildInfoScreen works as the form expects.

Defects found by reading the feature end to end:
* the copy wrote the template's media NUMBER into varChildTitle, but the Title box reads varChildTitle1 -> the title was never copied
  (and the breadcrumb showed the template's number). Now varChildTitle1 = the template's production title;
* "you already started filling this form" looked at varChildTitle (never set by typing) -> typed titles were overwritten silently.
  Now it looks at varChildTitle1 and the description;
* credits were taken from the old Photographer/Director/Producer people columns only; the field saved with a media file is CreditContact;
* the copy ignored the Info tab fields Place, Reference links, Tags, FTP path, Type of product (Video) and "No third-party rights";
* the search box showed empty on re-open while the gallery was still filtered by the previous search (varTplSearch was never reset), the
  search hint said "title" but only the media number / ID were searched, and rows showed only the media number;
* the list included the item being edited and untitled draft rows; the subtitle always said "Photo/Reportage"; a locked requestor could use it.
Language / Type of product keep their current value when the template has none (a Video's EN / Clip defaults).
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG25', 'newG26'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'ChildInfoScreen'
X = 'varTplCandidate'

COPY = f'''Set(varChildTitle1, Coalesce({X}.ProductionTitle, ""));
Set(varChildDescription1, Coalesce({X}.Description, ""));
Set(varChildCredits1, Coalesce({X}.CreditContact, First({X}.Photographer).DisplayName, First({X}.Director).DisplayName, First({X}.Producer).DisplayName, ""));
Set(varChildProductionPlace1, Coalesce({X}.ProductionPlace, ""));
Set(varChildLinks1, Coalesce({X}.ReferenceLinks, ""));
Set(varChildTags, Coalesce({X}.Tags, ""));
Set(varChildTags1, Coalesce({X}.Tags, ""));
Set(varChildFTPPath1, Coalesce({X}.FTPPath, ""));
Set(varChildProductType, Coalesce(First({X}.ProductType).Value, varChildProductType));
Set(varChildProductType1, Coalesce(First({X}.ProductType).Value, varChildProductType1));
Set(varChildLanguageVersions, Coalesce(First({X}.LanguageVersions).Value, varChildLanguageVersions));
Set(varChildContractCase, Coalesce(First({X}.ContractCase).Value, ""));
Set(varChildContractCase1Sub, Coalesce(First({X}.ContractCase1Sub).Value, ""));
Set(varChildNoThirdParty, Coalesce({X}.NoThirdPartyRights, false));
Set(varChildModelReleaseProvided, Coalesce({X}.ModelReleaseProvided, false));
Set(varChildModelRelease, Coalesce({X}.ModelReleaseProvided, false));
Set(varChildMusicUsed, Coalesce({X}.MusicUsed, false));
Set(varChildMusicLicenceProvided, Coalesce({X}.MusicLicenseProvided, false));
Set(varChildPreexistingProvided, Coalesce({X}.PreexistingRightsProvided, false));
Set(varChildPreexisting, Coalesce({X}.PreexistingRightsProvided, false));
Set(varChildAIVoiceover, {X}.AIVoiceover = "Yes");'''

# --- the two copies of the copy logic
t = app.rule(S, 'CI_TplConfirmOK', 'OnSelect')
if not t.startswith('Set(varChildTitle, Coalesce(varTplCandidate.CD_MediaNumber, ""));') or not t.rstrip().endswith('Set(varShowTplConfirm, false);\nSet(varShowTemplatePicker, false)'):
    sys.exit('! CI_TplConfirmOK changed')
app.set(S, 'CI_TplConfirmOK', 'OnSelect', COPY + '\nSet(varShowTplConfirm, false);\nSet(varShowTemplatePicker, false)', expect=t)

t = app.rule(S, 'CI_TplRowBg', 'OnSelect')
if not t.startswith('Set(varTplCandidate, ThisItem);\nIf(\n    varChildTitle <> "" Or varChildDescription1 <> "",'):
    sys.exit('! CI_TplRowBg changed')
app.set(S, 'CI_TplRowBg', 'OnSelect', '''Set(varTplCandidate, ThisItem);
If(
    // something is already typed on this form: ask before overwriting
    Coalesce(varChildTitle1, "") <> "" Or Coalesce(varChildDescription1, "") <> "",
    Set(varShowTplConfirm, true),
''' + '\n'.join('    ' + l for l in COPY.split('\n')) + '''
    Set(varShowTemplatePicker, false)
)''', expect=t)

# --- opening the picker: a clean search (variable and box)
t = app.rule(S, 'CI_BtnTemplate', 'OnSelect')
if t != 'Set(varTplSearch1, "");\nSet(varTplCandidate, Blank());\nSet(varShowTplConfirm, false);\nSet(varShowTemplatePicker, true)':
    sys.exit('! CI_BtnTemplate changed')
app.set(S, 'CI_BtnTemplate', 'OnSelect', '''Set(varTplSearch1, "");
Set(varTplSearch, "");
Reset(CI_TplSearch);
Set(varTplCandidate, Blank());
Set(varShowTplConfirm, false);
Set(varShowTemplatePicker, true)''', expect=t)
dm = app.rule(S, 'CI_BtnTemplate', 'DisplayMode')
app.set(S, 'CI_BtnTemplate', 'DisplayMode', 'If(varRequestorLocked, DisplayMode.Disabled, DisplayMode.Edit)', expect=dm)

# --- the list
g = app.rule(S, 'CI_TplGallery', 'Items')
old_items = '''SortByColumns(
    Filter(
        colTplMedia,
        varChildMediaType in MediaType.Value,
        IsBlank(varTplSearch)
            Or varTplSearch in CD_MediaNumber
            Or varTplSearch in Text(ID)
    ),
    "ID", SortOrder.Descending
)'''
app.set(S, 'CI_TplGallery', 'Items', '''SortByColumns(
    Filter(
        colTplMedia,
        varChildMediaType in MediaType.Value,
        // not the item being edited, and not untitled drafts (nothing to copy)
        ID <> Coalesce(varCurrentChildSPId, 0),
        Not(IsBlank(ProductionTitle)),
        IsBlank(varTplSearch)
            Or varTplSearch in CD_MediaNumber
            Or varTplSearch in Text(ID)
            Or varTplSearch in ProductionTitle
    ),
    "ID", SortOrder.Descending
)''', expect=g)
rt = app.rule(S, 'CI_TplRowTitle', 'Text')
app.set(S, 'CI_TplRowTitle', 'Text', 'Coalesce(ThisItem.ProductionTitle, "Untitled media file")', expect=rt)
rm = app.rule(S, 'CI_TplRowMeta', 'Text')
app.set(S, 'CI_TplRowMeta', 'Text', '''Coalesce(ThisItem.CD_MediaNumber, "") & "   |   ID " & Text(ThisItem.ID) & If(IsBlank(First(ThisItem.ContractCase).Value), "", "   |   " & Left(First(ThisItem.ContractCase).Value, 30))''', expect=rm)
st = app.rule(S, 'CI_TplSubtitle', 'Text')
app.set(S, 'CI_TplSubtitle', 'Text', '"Showing only " & If(varChildMediaType = "Photo", "Photo/Reportage", varChildMediaType) & " media files, newest first. Selecting one pre-fills this form and never modifies the original."', expect=st)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL36 built')
