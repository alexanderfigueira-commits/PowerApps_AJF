#!/usr/bin/env python3
"""FINAL181 on FINAL180 - accessibility, part 3 of 3: accessible labels (what a screen reader says) on the 101 controls that had none:
text boxes, date pickers, drop-downs and combo boxes take the text of their visible label (so it follows the label, e.g. 'Photo/Reportage Title' / 'Video Title'; the ' *'
required mark is dropped); attachments, galleries, icons, pop-up shades and search boxes get a short description."""
import datetime, os, re, shutil, sys
sys.path.insert(0, 'ana')
from payaml import App
from acc_common import *
SRC, NEW = 'newV42', 'newV43'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)

def L(lbl):                        # the text of the visible label, without the required-field mark
    return f'Substitute({lbl}.Text, " *", "")'
def S(txt):
    return '"' + txt.replace('"', '""') + '"'

I, M, G, V, R, H, RM, RV = 'ChildInfoScreen', 'ChildMetaScreen', 'ChildLegalScreen', 'ChildValidScreen', 'RequesDetailScreen', 'HomePrintScreen', 'RequestManagementScreen', 'ReviewScreen'
DA, DR, DB = 'Dashboard-Ope-Administrator', 'Dashboard-Ope-Requestor', 'DashboardScreen'
PHOTO, PODCAST, VIDEO = 'PrintPhotoDetailScreen', 'PrintPodcastDetailScreen', 'PrintVideoDetailScreen'
MAP = {
 # ---- Info
 (I, 'CI_AttachShade'): S('Close the podcast visual window'), (I, 'CI_VisualShade'): S('Close the podcast visual preview'),
 (I, 'CI_BelugaRef'): L('CI_LblBeluga'), (I, 'CI_CaptureDate'): L('CI_LblCaptureDate'), (I, 'CI_Description'): L('CI_LblDescription'),
 (I, 'CI_FTPPath'): L('CI_LblFTPPath'), (I, 'CI_Gallery'): S('Media file: Info tab'), (I, 'CI_Language'): L('CI_LblLanguage'),
 (I, 'CI_Links'): L('CI_LblLinks'), (I, 'CI_Notes'): L('CI_LblNotes'), (I, 'CI_Place'): L('CI_LblPlace'),
 (I, 'CI_PodcastDesc'): L('CI_LblPodcastDesc'), (I, 'CI_PodcastTitle'): L('CI_LblPodcastTitle'), (I, 'CI_PodcastVisual'): L('CI_LblPodcastVisual'),
 (I, 'CI_ProductType'): L('CI_LblProductType'), (I, 'CI_ProductionEndDate'): L('CI_LblProductionEndDate'), (I, 'CI_PubEndDate'): L('CI_LblPubEndDate'),
 (I, 'CI_PubStartDate'): L('CI_LblPubStartDate'), (I, 'CI_SeriesTitle'): L('CI_LblSeriesTitle'), (I, 'CI_Tags'): L('CI_LblTags'), (I, 'CI_Title'): L('CI_LblTitle'),
 (I, 'CI_TplGallery'): S('Previous media files that can be used as a template'), (I, 'CI_TplOverlay'): S('Close the template list'),
 (I, 'CI_TplRowBg'): S('Use this media file as a template'), (I, 'CI_TplSearch'): S('Search previous media files by title, media ID or Beluga ID'),
 # ---- Legal
 (G, 'CL_Case'): L('CL_LblCase'), (G, 'CL_DCAttachValue'): S('Legal annexes and supporting documents'), (G, 'CL_Gallery'): S('Media file: Legal and documents tab'),
 # ---- Metadata
 (M, 'CM_AttachShade'): S('Close the audio files window'), (M, 'CM_EVAttachShade'): S('Close the episode visual window'), (M, 'CM_EpVisualShade'): S('Close the episode visual preview'),
 (M, 'CM_AudioFiles'): S('Audio files'), (M, 'CM_Authority'): L('CM_LblAuthority'), (M, 'CM_Caption'): L('CM_LblCaptions'), (M, 'CM_Credits'): L('CM_LblCredits'),
 (M, 'CM_Desc'): L('CM_LblDesc'), (M, 'CM_EpisodeNumber'): L('CM_LblEpisodeNumber'), (M, 'CM_EpisodeSummary'): L('CM_LblEpisodeSummary'),
 (M, 'CM_EpisodeTitleP'): L('CM_LblEpisodeTitleP'), (M, 'CM_EpisodeVisual'): L('CM_LblEpisodeVisual'), (M, 'CM_ExecProducer'): L('CM_LblExecProducer'),
 (M, 'CM_Gallery'): S('Media file: Metadata tab'), (M, 'CM_Language'): L('CM_LblLanguage'), (M, 'CM_LinksPhoto'): L('CM_LblLinksPhoto'),
 (M, 'CM_PhotographerName'): L('CM_LblPhotographer'), (M, 'CM_PlacePhoto'): L('CM_LblPlacePhoto'), (M, 'CM_ProdEnd'): L('CM_LblProdEnd'),
 (M, 'CM_Producer'): L('CM_LblProducer'), (M, 'CM_PubEndV'): L('CM_LblPubEndV'), (M, 'CM_PubStartV'): L('CM_LblPubStartV'), (M, 'CM_Script'): L('CM_LblScript'),
 (M, 'CM_SeasonNumber'): L('CM_LblSeasonNumber'), (M, 'CM_ShootDate'): L('CM_LblShootDate'), (M, 'CM_TagsPhoto'): L('CM_LblTagsPhoto'),
 # ---- Validations
 (V, 'CV_ChecklistGallery'): S('Validation checklist of the media file'),
 # ---- dashboards
 **{(DA, f'DOA_List{i}Gallery'): f'DOA_List{i}Title.Text' for i in (1, 2, 3)},
 **{(DR, f'DOR_List{i}Gallery'): f'DOR_List{i}Title.Text' for i in (1, 2, 3)},
 (DB, 'DB_TrendOverlay'): S('Close the trend chart'),
 # ---- export / print
 (H, 'HP_DateEnd'): S('Submitted until (date)'), (H, 'HP_DateStart'): S('Submitted from (date)'), (H, 'HP_Gallery'): S('Requests to print'),
 (H, 'HP_TxtRequestID'): S('Search by request ID'), (H, 'HP_TxtTitle'): S('Search by request title'),
 (PHOTO, 'PPD_Gallery'): S('Photo media files to print'), (PODCAST, 'PPoD_Gallery'): S('Podcast media files to print'), (VIDEO, 'PVD_Gallery'): S('Video media files to print'),
 # ---- request
 (R, 'BackButton_ReviewScreen'): S('Back to the review queue'), (R, 'HomeFilterDG'): L('RS_LblDG') if False else S('DG / Agency'),
 (R, 'MessageCenter'): S('Messages of this request'), (R, 'NT_Backdrop'): S('Close the messages window'), (R, 'NT_Input'): S('Write a message'),
 (R, 'RS_ChildrenGallery'): S('Media files of this request'), (R, 'RS_Contractor'): L('RS_LblContractor'), (R, 'RS_Description'): L('RS_LblDescription'),
 (R, 'RS_Owner'): L('RS_LblOwner'), (R, 'RS_Title'): L('RS_LblTitle'), (R, 'RS_TypePickerOverlay'): S('Production type required: select one to continue'),
 (R, 'RS_drpContactType'): S('Contact type'), (R, 'RS_txtEmailContact'): S('Contact e-mail address'), (R, 'SaveButton'): S('Save draft'), (R, 'addMediaItem'): S('Add a media file'),
 # ---- Requests list
 (RM, 'HomeFilterBeluga'): S('Search by Beluga reference'), (RM, 'HomeFilterEnd'): S('Date range: to'), (RM, 'HomeFilterRequestID'): S('Search by request ID'),
 (RM, 'HomeFilterRequestName'): S('Search by request title'), (RM, 'HomeFilterStart'): S('Date range: from'), (RM, 'HomeGallery'): S('Requests'),
 (RM, 'HomeRowSelect'): S('Open this request'), (RM, 'cmbFilterAssignee_1'): S('Filter by assignee'), (RM, 'cmbFilterRequestor'): S('Filter by requestor'),
 # ---- Review
 (RV, 'Icon1'): S('Open this request to review it'), (RV, 'RV_Assignee'): S('Assignee'), (RV, 'RV_CRowNotes'): S('Internal notes for this media file'),
 (RV, 'RV_ChildrenGallery'): S('Media files of the request under review'), (RV, 'RV_Comment'): L('RV_LblComment'), (RV, 'RV_QRowBg'): S('Select this request for review'),
 (RV, 'RV_QueueGallery'): S('Review queue'),
}
from acc_predict import predict
need, ctls = predict(SRC)
need = need['Missing accessible label']
assert set(MAP) == need, (sorted(need - set(MAP)), sorted(set(MAP) - need))
# every label a text refers to must exist on that screen
for (scr, ctl), v in MAP.items():
    for ref in re.findall(r'([A-Za-z_0-9]+)\.Text', v):
        assert (scr, ref) in ctls and ctls[(scr, ref)]['type'] == 'label', (scr, ctl, ref)
cat = None
for scr in app.map:
    for n in walk(app.doc(scr)['TopParent']):
        for r in n['Rules']:
            if r['Property'] == 'AccessibleLabel': cat = r['Category']; break
        if cat: break
    if cat: break
print('AccessibleLabel rule category in this app:', cat)
for (scr, ctl), v in sorted(MAP.items()):
    put_rule(app, scr, ctl, 'AccessibleLabel', v, category=cat or 'Design')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL181 built:', len(MAP), 'accessible labels')
