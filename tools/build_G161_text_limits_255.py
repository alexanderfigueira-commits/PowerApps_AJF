#!/usr/bin/env python3
"""FINAL172 on FINAL171. Same 255-character limit as Script / Shotlist on the other text boxes whose SharePoint column is single-line text (255 at most):
a longer text made the whole Save Media fail. Boxes: media title (Video / Photo and Podcast episode), podcast / series title, place, FTP path, Beluga reference,
reference links, contracting authority, executive producer, contractor / agency, summary of the episode. Each label shows "(n / 255)" from 200 characters on."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newV33', 'newV34'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
I, M = 'ChildInfoScreen', 'ChildMetaScreen'
BOXES = {  # box -> (screen, label, variable)
    'CI_Title': (I, 'CI_LblTitle', 'varChildTitle1'),
    'CI_PodcastTitle': (I, 'CI_LblPodcastTitle', 'varChildSeriesTitle1'),
    'CI_SeriesTitle': (I, 'CI_LblSeriesTitle', 'varChildSeriesTitle1'),
    'CI_Place': (I, 'CI_LblPlace', 'varChildProductionPlace1'),
    'CI_FTPPath': (I, 'CI_LblFTPPath', 'varChildFTPPath1'),
    'CI_BelugaRef': (I, 'CI_LblBeluga', 'varChildBelugaRef'),
    'CI_Links': (I, 'CI_LblLinks', 'varChildLinks1'),
    'CM_Authority': (M, 'CM_LblAuthority', 'varChildContractingAuthority'),
    'CM_EpisodeTitleP': (M, 'CM_LblEpisodeTitleP', 'varChildTitle1'),
    'CM_EpisodeSummary': (M, 'CM_LblEpisodeSummary', 'varChildEpisodeSummary1'),
    'CM_PlacePhoto': (M, 'CM_LblPlacePhoto', 'varChildProductionPlace1'),
    'CM_ExecProducer': (M, 'CM_LblExecProducer', 'varChildExecProducer'),
    'CM_Credits': (M, 'CM_LblCredits', 'varChildCredits1'),
    'CM_LinksPhoto': (M, 'CM_LblLinksPhoto', 'varChildLinks1'),
}
for box, (scr, lbl, var) in BOXES.items():
    t = app.rule(scr, box, 'MaxLength'); assert t == '', (box, t)
    app.set(scr, box, 'MaxLength', '255', expect=t)
    if box == 'CI_SeriesTitle':          # hidden box, no visible label to count in
        continue
    t = app.rule(scr, lbl, 'Text')
    assert '//' not in t and 'MaxLength' not in t, (lbl, t)
    n = f'Len(Coalesce({var}, ""))'
    app.set(scr, lbl, 'Text', f'({t}) & If({n} >= 200, "  (" & {n} & " / 255)", "")', expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL172 built')
