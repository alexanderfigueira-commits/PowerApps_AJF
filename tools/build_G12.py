#!/usr/bin/env python3
"""FINAL22 on FINAL21: Add_media_icon (RequesDetailScreen) is disabled until the draft is saved, with a tooltip that says what to do.

* DisplayMode: Edit only when the request has been saved (varCurrentRequest.ID > 0), Disabled before that.
* Tooltip: "Add a media file to this request" when enabled; when disabled it lists what is still missing
  (title, DG / Agency, production type) and then points to "Draft Save".
* DisabledColor: the disabled icon stays visible (it was almost white).
* RS_NewRequestHint under the media list says the same.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG11', 'newG12'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S, N = 'RequesDetailScreen', 'Add_media_icon'

app.set(S, N, 'DisplayMode', '''// the media list needs a saved request: enabled once "Draft Save" has been done
If(Coalesce(varCurrentRequest.ID, 0) > 0, DisplayMode.Edit, DisplayMode.Disabled)''', expect='DisplayMode.Edit')
app.set(S, N, 'Tooltip', '''If(
    Coalesce(varCurrentRequest.ID, 0) > 0,
    "Add a media file to this request",
    With(
        {
            // what is still missing before the draft can be saved and media added
            need: Concat(
                Filter(
                    Table(
                        {s: "enter the request title", m: IsBlank(Trim(RS_Title.Text))},
                        {s: "select the DG / Agency", m: IsBlank(HomeFilterDG.Selected.Value)},
                        {s: "choose the production type", m: IsBlank(varRequestMediaType) Or varRequestMediaType = ""}
                    ),
                    m
                ),
                s,
                ", "
            )
        },
        "Add media is available once the draft is saved. "
            & If(
                need = "",
                "Click “Draft Save ➤” (bottom right).",
                "First " & need & ", then click “Draft Save ➤” (bottom right)."
            )
    )
)''', expect='"Add Media"')
app.set(S, N, 'DisabledColor', 'RGBA(166, 172, 184, 1)', expect='RGBA(244, 244, 244, 1)')
app.set(S, 'RS_NewRequestHint', 'Text', '"Save the draft first (Draft Save ➤) to start adding media."', expect='"Save the request first to start adding archives."')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL22 built')
