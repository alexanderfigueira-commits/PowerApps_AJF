#!/usr/bin/env python3
"""FINAL121 on FINAL120:
 1. ReviewScreen: the queue lists only the requests in Processing (a request returned as Pending, or already decided, is no longer offered; a request kept selected from a row also has to be Processing).
 2. Info tab: the FTP delivery path appears for every production type (Photo, Video, Podcast) and is optional: no asterisk, no yellow border, and the Validations tab no longer asks for it.
    For Video and Podcast it sits where Photo has it, above Notes: Notes, Beluga reference and the podcast-visual block move down by 90 for those two types.
 3. Copy from previous media item (CI_TplGallery): only media files of the production type of this media file; an administrator sees everyone's, a requestor only their own (loaded that way
    from SharePoint, so a long list never cuts them off). The type is a plain column read once when the list is loaded."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newQ4', 'newQ5'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
eol = lambda t: '\r\n' if '\r\n' in t else '\n'
def put(screen, ctl, prop, new, old_expect=None):
    t = app.rule(screen, ctl, prop)
    app.set(screen, ctl, prop, new.replace('\n', eol(t)), expect=old_expect if old_expect is not None else t)

# ------------------------------------------------------------ 1. ReviewScreen: Processing only
R = 'ReviewScreen'
put(R, 'RV_QueueGallery', 'Items', '''Sort(
    Filter(colRevReqs,
        // only what waits for a decision: Processing. (Pending is waiting for the requestor; Approved / Rejected are decided.)
        // ReviewScreen is only reachable by administrators; anyone else would see only their own.
        Status.Value = "Processing" And (varUserRole = "ADMINISTRATOR" Or Lower('Created By'.Email) = Lower(User().Email)),
        Not(varReviewQueueMine) Or Not(IsEmpty(Filter(DG_Agency_Contact, Lower(Email) = Lower(User().Email))))
    ),
    Modified, SortOrder.Descending
)''')
t = app.rule(R, None, 'OnVisible')
old = 'Coalesce(varReviewFromRow, false) And Not(IsBlank(varReviewProject)),'
assert t.count(old) == 1
put(R, None, 'OnVisible', t.replace(old, 'Coalesce(varReviewFromRow, false) And Not(IsBlank(varReviewProject)) And LookUp(colRevReqs, ID = varReviewProject.ID).Status.Value = "Processing",'), t)

# ------------------------------------------------------------ 2. FTP delivery path: every type, optional
C = 'ChildInfoScreen'
put(C, 'CI_LblFTPPath', 'Text', '"FTP delivery path (optional)"', '"FTP delivery path *"')
put(C, 'CI_LblFTPPath', 'Visible', 'true', 'varChildMediaType = "Photo"')
put(C, 'CI_LblFTPPath', 'Y', 'If(varChildMediaType = "Photo", 265, 356)', '265')
put(C, 'CI_FTPPath', 'Visible', 'true', 'varChildMediaType = "Photo"')
put(C, 'CI_FTPPath', 'Y', 'If(varChildMediaType = "Photo", 290, 381)', '290')
t = app.rule(C, 'CI_FTPPath', 'BorderColor')
put(C, 'CI_FTPPath', 'BorderColor', 'RGBA(0, 18, 107, 1)', t)
t = app.rule(C, 'CI_FTPPath', 'BorderThickness')
put(C, 'CI_FTPPath', 'BorderThickness', '2', t)
# below the FTP path (Video / Podcast): Notes, Beluga reference, the podcast-visual block
for ctl, y in (('CI_LblNotes', 356), ('CI_Notes', 381), ('CI_LblBeluga', 458), ('CI_BelugaRef', 480)):
    put(C, ctl, 'Y', f'{y} + If(varChildMediaType = "Photo", 0, 90)', str(y))
for ctl, y in (('CI_LblPodcastVisual', 544), ('CI_HintPodcastVisual', 565), ('CI_BtnOpenAttach', 587), ('CI_BtnViewVisual', 588)):
    put(C, ctl, 'Y', str(y + 90), str(y))
put(C, 'CI_Gallery', 'TemplateSize', 'If(varChildMediaType = "Photo", 540, If(varChildMediaType = "Video", 680, If(varChildMediaType = "Podcast", 750, 916)))',
    'If(varChildMediaType = "Photo", 540, If(varChildMediaType = "Video", 590, If(varChildMediaType = "Podcast", 660, 916)))')

# Validations tab
V = 'ChildValidScreen'
OLD = re.compile(r'\{Check: "FTP delivery path set on this media file \(Photo only\)",\s*Pass:[^\n]*\n?\s*Note:[^\n]*?\}', re.S)
NEWROW = '{Check: "FTP delivery path (optional)", Pass: true, Note: "Optional: enter the FTP path on the Info tab if the files are delivered by FTP."}'
for ctl, prop in ((None, 'OnVisible'), ('CV_BtnRefresh', 'OnSelect')):
    t = app.rule(V, ctl, prop)
    n, k = OLD.subn(NEWROW, t); assert k == 1, (ctl, k)
    app.set(V, ctl, prop, n, expect=t)

# ------------------------------------------------------------ 3. template picker: same production type; administrator all, requestor own
t = app.rule(C, None, 'OnVisible')
old = "ClearCollect(colTplMedia, 'AV-CD-Mediafiles');"
assert t.count(old) == 1
new = '''// the media files that can be copied: an administrator's list is everyone's, a requestor's only the ones they created; tplType is the production type as plain text
ClearCollect(
    colTplMedia,
    AddColumns(
        If(varUserRole = "ADMINISTRATOR", 'AV-CD-Mediafiles', Filter('AV-CD-Mediafiles', 'Created By'.Email = User().Email)),
        tplType, Coalesce(First(MediaType).Value, "")
    )
);'''
put(C, None, 'OnVisible', t.replace(old, new.replace('\n', eol(t))), t)
put(C, 'CI_TplGallery', 'Items', '''SortByColumns(
    Filter(
        colTplMedia,
        // only the production type of this media file (Photo, Video or Podcast), never another
        tplType = varChildMediaType,
        // a requestor sees only the media files they created; an administrator sees all of that type
        varUserRole = "ADMINISTRATOR" Or Lower('Created By'.Email) = Lower(User().Email),
        // not the item being edited, and not untitled drafts (nothing to copy)
        ID <> Coalesce(varCurrentChildSPId, 0),
        Not(IsBlank(ProductionTitle)),
        IsBlank(varTplSearch)
            Or varTplSearch in CD_MediaNumber
            Or varTplSearch in Text(ID)
            Or varTplSearch in ProductionTitle
            Or varTplSearch in BelugaReference
    ),
    "ID", SortOrder.Descending
)''')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL121 built')
