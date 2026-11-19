#!/usr/bin/env python3
"""FINAL34 on FINAL33: CL_BtnNext (Legal & Docs -> Validations) recovers the media item's SharePoint ID when the attachments card has none.

The card's ID field (CL_DCIdValue) is empty when varAttachRecord is blank. Save Media needs that id as spId. Before leaving the tab, if the
card has no id, it is recovered: varCurrentChildSPId, else the media list (colArchives), else the request's latest media item with the same
title; then varCurrentChildSPId and varAttachRecord are set so the Validations tab and Save Media see it.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG23', 'newG24'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, N = 'ChildLegalScreen', 'CL_BtnNext'
t = app.rule(S, N, 'OnSelect')
if t != 'Navigate(ChildValidScreen)':
    sys.exit(f'! CL_BtnNext.OnSelect changed: {t!r}')
app.set(S, N, 'OnSelect', '''// The attachments card needs the media item's SharePoint ID (Save Media uses it as spId). If the card has none,
// recover it before leaving this tab: varCurrentChildSPId, else the media list, else the request's latest media item with this title.
If(
    Coalesce(varAttachRecord.ID, 0) = 0,
    With(
        {
            rid: If(
                Coalesce(varCurrentChildSPId, 0) > 0,
                varCurrentChildSPId,
                If(
                    Coalesce(LookUp(colArchives, ArchiveId = varCurrentChildId).SPId, 0) > 0,
                    LookUp(colArchives, ArchiveId = varCurrentChildId).SPId,
                    If(
                        IsBlank(varChildTitle1) Or varChildTitle1 = "",
                        0,
                        Coalesce(
                            First(
                                Sort(
                                    Filter('AV-CD-Mediafiles', ParentRequest = varCurrentRequest.RequestNumber, ProductionTitle = varChildTitle1),
                                    ID,
                                    SortOrder.Descending
                                )
                            ).ID,
                            0
                        )
                    )
                )
            )
        },
        If(
            rid > 0,
            Set(varCurrentChildSPId, rid);
            Set(varAttachRecord, LookUp('AV-CD-Mediafiles', ID = rid))
        )
    )
);
Navigate(ChildValidScreen)''', expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL34 built')
