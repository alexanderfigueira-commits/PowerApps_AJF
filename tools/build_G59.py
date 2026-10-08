#!/usr/bin/env python3
"""FINAL69 on FINAL68:
1. Print pages of Video and Podcast hide the menu (panel + five buttons) while printing, like the Photo page (FINAL67).
2. Video: the Language and Type of product dropdowns of ChildInfoScreen show EN / Clip while nothing is stored. The value shown is now the
   value used: CI_ProductType's Default follows varChildProductType (it followed the stale varChildProductType1, so the box could show
   Clip while Teaser was stored), and the Validations screen (OnVisible, refresh, Save Media) first stores what the two dropdowns show
   when nothing is stored, so nothing has to be selected again."""
import datetime, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG58', 'newG59'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
# 1. print pages
for scr, p in (('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD')):
    for n in ('Panel', 'Requests', 'Export', 'Dashboard', 'Help'):
        c = f'{p}_Menu_{n}'; app.set(scr, c, 'Visible', 'Not(locPrinting)', expect='true')
    c = f'{p}_Menu_Review'; app.set(scr, c, 'Visible', 'varUserRole = "ADMINISTRATOR" And Not(locPrinting)', expect='varUserRole = "ADMINISTRATOR"')
# 2. dropdown defaults
CI, CV = 'ChildInfoScreen', 'ChildValidScreen'
app.set(CI, 'CI_ProductType', 'Default', 'Coalesce(varChildProductType, varChildProductType1)', expect='varChildProductType1')
PRE = ('// a Video\'s Language and Type of product dropdowns show EN / Clip while nothing is stored: store what is shown\n'
       'If(\n    varChildMediaType = "Video" And Not(varRequestorLocked),\n'
       '    If(Coalesce(varChildLanguageVersions, "") = "", Set(varChildLanguageVersions, Coalesce(CI_Language.Selected.Value, "EN")));\n'
       '    If(Coalesce(varChildProductType, varChildProductType1, "") = "", Set(varChildProductType, Coalesce(CI_ProductType.Selected.Value, "Clip")))\n'
       ');\n')
for ctl, prop in ((None, 'OnVisible'), ('CV_BtnRefresh', 'OnSelect'), ('CV_BtnSaveArchive', 'OnSelect')):
    o = app.rule(CV, ctl, prop)
    eol = '\r\n' if '\r\n' in o else '\n'
    app.set(CV, ctl, prop, PRE.replace('\n', eol) + o, expect=o)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL69 built')
