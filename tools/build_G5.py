#!/usr/bin/env python3
"""FINAL15 on FINAL14: RS_CRowBadge becomes the media's portal status, in three colours.

 light grey  no Beluga ID yet (also: publishing with an ID, but the file is not approved yet)
 dark grey   "Archiving only, not publication" is ticked on the request and the file has a Beluga ID
 green       publishing, approved and has a Beluga ID: the badge is the link to the AV portal
The Ready / Incomplete status stays in the VALIDATION column (RS_CRowValid).
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG4', 'newG5'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, N = 'RequesDetailScreen', 'RS_CRowBadge'
LIGHT, DARK, GREEN = 'RGBA(236, 238, 242, 1)', 'RGBA(96, 104, 116, 1)', 'RGBA(22, 128, 80, 1)'
LIGHT_T, WHITE = 'RGBA(110, 118, 132, 1)', 'RGBA(255, 255, 255, 1)'


def F(body):
    return f'''With(
    {{
        t: Switch(ThisItem.MediaType, "Podcast", "podcast", "Video", "video", "Photo", "photo", ""),
        pre: Switch(ThisItem.MediaType, "Podcast", "S", "Video", "I", "Photo", "P", ""),
        ref: Upper(Substitute(Trim(Coalesce(ThisItem.BelugaReference, "")), " ", ""))
    }},
    With(
        // the number after the S- / I- / P- of the Beluga reference (the prefix is added when it was typed without)
        {{core: If(StartsWith(ref, pre & "-"), Mid(ref, 3), If(StartsWith(ref, pre), Mid(ref, 2), ref))}},
        With(
            {{
                id: pre & "-" & core,
                // none = no Beluga ID; archive = archiving only; link = publishing + approved; pending = publishing, not approved yet
                mode: If(
                    t = "" Or core = "",
                    "none",
                    If(
                        Coalesce(varRequestArchivedOnly, false),
                        "archive",
                        If(Coalesce(ThisItem.MediaApproved, false) Or Coalesce(varCurrentRequest.Status.Value, "") = "Approved", "link", "pending")
                    )
                ),
                url: "https://audiovisual.ec.europa.eu/en/media/" & t & "/" & pre & "-" & core
            }},
            {body}
        )
    )
)'''


old = {p: app.rule(S, N, p) for p in ('Text', 'DisplayMode', 'OnSelect', 'Fill', 'Color', 'Tooltip', 'HoverFill')}
if 'ok' not in old['DisplayMode'] or 'Launch(url)' not in old['OnSelect']:
    sys.exit('! RS_CRowBadge is not the FINAL14 link badge')
app.set(S, N, 'Text', F('Switch(mode, "none", "No Beluga ID", "archive", "Archive · " & id, "link", "🔗  " & id, "Not approved yet")'), expect=old['Text'])
app.set(S, N, 'Fill', F(f'Switch(mode, "archive", {DARK}, "link", {GREEN}, {LIGHT})'), expect=old['Fill'])
app.set(S, N, 'Color', F(f'Switch(mode, "archive", {WHITE}, "link", {WHITE}, {LIGHT_T})'), expect=old['Color'])
app.set(S, N, 'HoverFill', F(f'If(mode = "link", RGBA(15, 90, 55, 1), Self.Fill)'), expect=old['HoverFill'])
app.set(S, N, 'DisplayMode', F('If(mode = "link", DisplayMode.Edit, DisplayMode.View)'), expect=old['DisplayMode'])
app.set(S, N, 'OnSelect', F('If(mode = "link", Launch(url))'), expect=old['OnSelect'])
app.set(S, N, 'Tooltip', F('Switch(mode, "none", "No Beluga ID yet", "archive", "Archiving only: not published on the portal", "link", "Open " & id & " on the Audiovisual Service portal", "Has a Beluga ID, but the file is not approved yet")'), expect=old['Tooltip'])
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL15 built')
