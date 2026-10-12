#!/usr/bin/env python3
"""FINAL94 on FINAL93: SaveButton (the draft save icon) sits next to addMediaItem instead of behind it (X 1196, addMediaItem stays at 1240) and stays
visible while the request is a Draft you can edit - before and after the first save - so the draft can be saved again with the media list open.
Yellow border until the first click, blue after, as before."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG83', 'newG84'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
app.set(S, 'SaveButton', 'X', '1196')
app.set(S, 'SaveButton', 'Width', '40')
VIS = 'Not(varViewOnly) And Not(varRequestorLocked) And (IsBlank(varCurrentRequest) Or Coalesce(varCurrentRequest.ID, 0) <= 0 Or Coalesce(varCurrentRequest.Status.Value, "Draft") = "Draft")'
app.set(S, 'SaveButton', 'Visible', VIS)
app.set(S, 'SaveButton', 'Tooltip', '"Save draft"')
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL94 built')
