#!/usr/bin/env python3
"""FINAL162 on FINAL161. Why the Legal tab said "Save the media item first to add attachments" although the request was saved:
TEST_14's refreshed data source shows that the SharePoint column PhotographerName was created REQUIRED (schema required =
['Title', 'PhotographerName']) and as rich text (format html). "Add media" creates the media item with Patch(Defaults(...)) without that column,
SharePoint refuses it, IfError(..., 0) swallowed the error, varCurrentChildSPId stayed 0, varAttachRecord stayed blank and the attachments panel
showed the "save first" message.
 * addMediaItem: a failure to create the media item is now reported (with SharePoint's own message) instead of being swallowed.
 * PhotographerName is rich text: every read goes through PlainText (template copy, media list / reopen, print page).
 The SharePoint column must NOT be required (only Photo needs a photographer, and the Validations tab already enforces it)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV23', 'newV24'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

def edit(screen, control, prop, subs):
    t = app.rule(screen, control, prop); u = t
    for pat, new, cnt in subs:
        assert len(re.findall(pat, u, re.S)) == cnt, (screen, control, prop, pat, len(re.findall(pat, u, re.S)))
        u = re.sub(pat, lambda m: new, u, flags=re.S)
    app.set(screen, control, prop, u, expect=t)

# 1. addMediaItem: show why the media item could not be created
edit('RequesDetailScreen', 'addMediaItem', 'OnSelect', [
    (r'(\)\.ID\s*\),)(\s*)0(\s*\)\s*\);\s*Set\(varChildTitle, Blank\(\)\);)',
     '). ID\n        ),\n        Notify("Could not create the media item in SharePoint (the attachments cannot be added until it exists): " & FirstError.Message, NotificationType.Error);\n        0\n    )\n);\nSet(varChildTitle, Blank());', 1)])
t = app.rule('RequesDetailScreen', 'addMediaItem', 'OnSelect'); t2 = t.replace('). ID', ').ID'); app.set('RequesDetailScreen', 'addMediaItem', 'OnSelect', t2, expect=t)

# 2. rich text: PlainText on every read of PhotographerName
for ctl in ('CI_TplRowBg', 'CI_TplConfirmOK'):
    edit('ChildInfoScreen', ctl, 'OnSelect', [
        (r'Coalesce\(varTplCandidate\.PhotographerName, Concat\(',
         'Coalesce(PlainText(Coalesce(varTplCandidate.PhotographerName, "")), Concat(', 1)])
edit('RequesDetailScreen', None, 'OnVisible', [
    (r'Photographer: Coalesce\(PhotographerName, Concat\(',
     'Photographer: Coalesce(PlainText(Coalesce(PhotographerName, "")), Concat(', 1)])
for prop in ('Text', 'Color'):
    edit('PrintPhotoDetailScreen', 'PPD_Val13', prop, [
        (r'Trim\(Coalesce\(ThisItem\.PhotographerName, Concat\(',
         'Trim(Coalesce(PlainText(Coalesce(ThisItem.PhotographerName, "")), Concat(', 1)])
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL162 built')
