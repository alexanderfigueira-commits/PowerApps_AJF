#!/usr/bin/env python3
"""FINAL90 on FINAL89: the podcast cover (CI_BtnOpenAttach / 'Podcast visual') is mandatory only for Season 1 AND Episode 1 (before: Season 1).
Label, yellow border, tooltip and both copies of the 'Podcast visual attached (Podcast only)' validation row follow the new rule.
The episode visual on the Metadata tab keeps its own rule (Season 1)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG79', 'newG80'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
CI, CV = 'ChildInfoScreen', 'ChildValidScreen'
FIRST = '(Coalesce(varChildSeasonNumber, 0) = 1 And Coalesce(varChildEpisodeNumber, 0) = 1)'
def edit(s, ctl, prop, fn):
    t = app.rule(s, ctl, prop); n = fn(t); assert n != t, (ctl, prop); app.set(s, ctl, prop, n, expect=t)
sub = lambda t: t.replace('Coalesce(varChildSeasonNumber, 0) = 1', FIRST)
edit(CI, 'CI_LblPodcastVisual', 'Text', sub)
edit(CI, 'CI_BtnOpenAttach', 'BorderColor', sub)
edit(CI, 'CI_BtnOpenAttach', 'BorderThickness', sub)
edit(CI, 'CI_BtnOpenAttach', 'Tooltip', lambda t: sub(t).replace('required when Season nr. is 1', 'required when Season nr. and Episode nr. are both 1'))
def valid(t):
    n = t.replace('Coalesce(varChildSeasonNumber, 0) <> 1 Or CountRows(Filter(CI_PodcastVisual', f'Not{FIRST} Or CountRows(Filter(CI_PodcastVisual')
    return n.replace('Mandatory when Season nr. is 1, optional otherwise.', 'Mandatory when Season nr. and Episode nr. are both 1, optional otherwise.')
edit(CV, None, 'OnVisible', valid)
edit(CV, 'CV_BtnRefresh', 'OnSelect', valid)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL90 built')
