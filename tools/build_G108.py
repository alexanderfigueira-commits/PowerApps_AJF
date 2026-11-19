#!/usr/bin/env python3
"""FINAL118 on FINAL117:
 1. ReviewScreen: the decision buttons are in the order Approve (Approved) - Need info (Pending) - Reject (Rejected).
 2. Podcast, Info tab: "Title of the podcast" and "Description of the podcast" are no longer the request title / description (they shared varRequestTitle / varRequestDescription, so
    they were copied from the request and overwrote it). They are now the podcast's own fields, saved on the media item (SeriesTitle and Description), like the title and description of
    a photo or a video. Photo and video never copied the request text. The mandatory checks and the podcast print page read the same columns."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newQ1', 'newQ2'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
walk = lambda n: [n] + [x for c in n.get('Children', []) for x in walk(c)]

# ------------------------------------------------------------ 1. ReviewScreen order: Approve | Need info | Reject
R = 'ReviewScreen'
assert app.rule(R, 'RV_BtnApprove', 'X') == '460' and app.rule(R, 'RV_BtnReject', 'X') == '676' and app.rule(R, 'RV_BtnNeedInfo', 'X') == '852'
assert app.rule(R, 'RV_BtnReject', 'Width') == '160' and app.rule(R, 'RV_BtnNeedInfo', 'Width') == '200'
app.set(R, 'RV_BtnNeedInfo', 'X', '676', expect='852')
app.set(R, 'RV_BtnReject', 'X', '892', expect='676')

# ------------------------------------------------------------ 2. podcast title / description are their own fields
C = 'ChildInfoScreen'
desc_default = app.rule(C, 'CI_Description', 'Default')            # rich-text column: text only
t_old = app.rule(C, 'CI_PodcastTitle', 'Default'); assert t_old == 'Coalesce(varRequestTitle, varRequestTitle1)'
app.set(C, 'CI_PodcastTitle', 'Default', 'varChildSeriesTitle1', expect=t_old)
o = app.rule(C, 'CI_PodcastTitle', 'OnChange'); assert o == 'Set(varRequestTitle, Self.Text); Set(varRequestTitle1, Self.Text)'
app.set(C, 'CI_PodcastTitle', 'OnChange', 'Set(varChildSeriesTitle1, Self.Text)', expect=o)
d_old = app.rule(C, 'CI_PodcastDesc', 'Default'); assert d_old == 'Coalesce(varRequestDescription, varRequestDescription1)'
app.set(C, 'CI_PodcastDesc', 'Default', desc_default, expect=d_old)
o = app.rule(C, 'CI_PodcastDesc', 'OnChange'); assert o == 'Set(varRequestDescription, Self.Text); Set(varRequestDescription1, Self.Text)'
app.set(C, 'CI_PodcastDesc', 'OnChange', 'Set(varChildDescription1, Self.Text)', expect=o)

# mandatory checks (screen opened, and Refresh)
V = 'ChildValidScreen'
for ctl, prop in ((None, 'OnVisible'), ('CV_BtnRefresh', 'OnSelect')):
    t = app.rule(V, ctl, prop)
    assert t.count('varRequestTitle') == 2 and t.count('varRequestDescription') == 2
    n = t.replace('varRequestTitle', 'varChildSeriesTitle1').replace('varRequestDescription', 'varChildDescription1')
    app.set(V, ctl, prop, n, expect=t)

# podcast print page: the podcast's own title, and the episode title that is typed on the Metadata tab
P = 'PrintPodcastDetailScreen'
FP = 'First(colPrintReqMedia)'
for prop, old, new in (
    ('Color',   f'If(IsBlank({FP}.ProductionTitle), RGBA(150, 155, 165, 1), RGBA(30, 34, 44, 1))',
                f'If(IsBlank({FP}.SeriesTitle), RGBA(150, 155, 165, 1), RGBA(30, 34, 44, 1))'),
    ('Text',    f'If(IsBlank({FP}.ProductionTitle), "Not provided", {FP}.ProductionTitle)',
                f'If(IsBlank({FP}.SeriesTitle), "Not provided", {FP}.SeriesTitle)'),
    ('Visible', f'Not(IsBlank({FP}.ProductionTitle))', f'Not(IsBlank({FP}.SeriesTitle))')):
    app.set(P, 'PPoD_PodVal0', prop, new, expect=old)
EP = 'Coalesce(ThisItem.EpisodeTitle, ThisItem.ProductionTitle)'
for prop, old, new in (
    ('Color', 'If(IsBlank(ThisItem.EpisodeTitle), RGBA(150, 155, 165, 1), RGBA(30, 34, 44, 1))',
              f'If(IsBlank({EP}), RGBA(150, 155, 165, 1), RGBA(30, 34, 44, 1))'),
    ('Text',  'If(IsBlank(ThisItem.EpisodeTitle), "Not provided", ThisItem.EpisodeTitle)',
              f'If(IsBlank({EP}), "Not provided", {EP})')):
    app.set(P, 'PPoD_Val1', prop, new, expect=old)
old = '"■  " & Coalesce(ThisItem.CD_MediaNumber, "Media file") & If(IsBlank(ThisItem.EpisodeTitle), "", "  —  " & ThisItem.EpisodeTitle)'
app.set(P, 'PPoD_RowCaption', 'Text', f'"■  " & Coalesce(ThisItem.CD_MediaNumber, "Media file") & If(IsBlank({EP}), "", "  —  " & {EP})', expect=old)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL118 built')
