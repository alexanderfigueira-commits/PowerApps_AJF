#!/usr/bin/env python3
"""FINAL93 on FINAL92: removes the two delegation warnings of DOA_List1RowBadge_7. The unread notes are now taken from MessageCenter.AllItems (the
gallery already filtered by request number on the server) instead of filtering AV-CD-Notes with IsBlank / <> on the data source."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG82', 'newG83'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
o = app.rule(S, 'DOA_List1RowBadge_7', 'OnSelect'); eol = '\r\n' if '\r\n' in o else '\n'; n = o.replace('\r\n', '\n')
old = "Filter('AV-CD-Notes', Title = varCurrentRequest.RequestNumber, IsBlank(ReadOn), AuthorEmail <> User().Email) As n,"
assert n.count(old) == 1
new = ("// MessageCenter.AllItems is already limited to this request on the server, so the other tests run on that short list (no delegation)\n"
       "        Filter(MessageCenter.AllItems, IsBlank(ReadOn), AuthorEmail <> User().Email) As n,")
app.set(S, 'DOA_List1RowBadge_7', 'OnSelect', n.replace(old, new).replace('\n', eol), expect=o)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL93 built')
