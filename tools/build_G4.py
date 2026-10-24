#!/usr/bin/env python3
"""FINAL14 on FINAL13: RS_CRowBadge (media row, RequesDetailScreen) becomes a link to the AV portal once the file is approved.

URL = https://audiovisual.ec.europa.eu/en/media/<podcast|video|photo>/<S|I|P>-<number of the BelugaReference>
Shown (as the link) only when the media file is approved (the row's tick, or the whole request Approved) and
the Beluga reference is filled; otherwise the badge stays the Ready / Incomplete status, view-only.
"""
import datetime, os, re, shutil, sys
from payaml import App, find

SRC, NEW = 'newG3', 'newG4'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, N = 'RequesDetailScreen', 'RS_CRowBadge'


def F(body):
    """body may use: ok (link available), url, id."""
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
                ok: t <> "" And core <> "" And (Coalesce(ThisItem.MediaApproved, false) Or Coalesce(varCurrentRequest.Status.Value, "") = "Approved")
            }},
            With(
                {{url: "https://audiovisual.ec.europa.eu/en/media/" & t & "/" & id}},
                {body}
            )
        )
    )
)'''


old = {p: app.rule(S, N, p) for p in ('Text', 'DisplayMode', 'OnSelect', 'Fill', 'Color', 'Tooltip')}
if old['DisplayMode'] != 'DisplayMode.View' or old['OnSelect'] != 'false' or old['Text'].count('"Ready"') != 1:
    sys.exit('! RS_CRowBadge changed')
app.set(S, N, 'Text', F(f'If(ok, "🔗  " & id, {old["Text"]})'), expect=old['Text'])
app.set(S, N, 'DisplayMode', F('If(ok, DisplayMode.Edit, DisplayMode.View)'), expect=old['DisplayMode'])
app.set(S, N, 'OnSelect', F('If(ok, Launch(url))'), expect=old['OnSelect'])
app.set(S, N, 'Fill', F(f'If(ok, RGBA(230, 240, 255, 1), {old["Fill"]})'), expect=old['Fill'])
app.set(S, N, 'Color', F(f'If(ok, RGBA(0, 18, 107, 1), {old["Color"]})'), expect=old['Color'])
app.set(S, N, 'Tooltip', F('If(ok, "Open " & id & " on the Audiovisual Service portal", "")'), expect=old['Tooltip'])
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL14 built')
