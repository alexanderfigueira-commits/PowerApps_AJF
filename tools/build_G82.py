#!/usr/bin/env python3
"""FINAL92 on FINAL91: Message Center read receipts with the AV-CD-Notes columns ReadBy (text) and ReadOn (date, already in the data source).
 - opening the Message Center (DOA_List1RowBadge_7) stamps every note of this request written by someone else and not read yet:
   ReadBy = the reader's name, ReadOn = Now()
 - each message shows 'Read by <name> on <date time>' (author's own messages show 'Not read yet' until the other side opens them)"""
import datetime, os, re, shutil
from payaml import App
from hp_common import Builder
SRC, NEW = 'newG81', 'newG82'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
o = app.rule(S, 'DOA_List1RowBadge_7', 'OnSelect'); eol = '\r\n' if '\r\n' in o else '\n'
mark = ('// the notes of this request written by someone else are now read: who and when\n'
        'IfError(\n    ForAll(\n        Filter(\'AV-CD-Notes\', Title = varCurrentRequest.RequestNumber, IsBlank(ReadOn), AuthorEmail <> User().Email) As n,\n'
        '        Patch(\'AV-CD-Notes\', n, {ReadBy: User().FullName, ReadOn: Now()})\n    ),\n    Blank()\n);\n')
app.set(S, 'DOA_List1RowBadge_7', 'OnSelect', o.replace('\r\n', '\n').replace('UpdateContext({locShowNotes: true});\n', 'UpdateContext({locShowNotes: true});\n' + mark, 1).replace('\n', eol), expect=o)
b = Builder(app, S)
TXT = ('If(\n    IsBlank(ThisItem.ReadOn),\n    "Not read yet",\n    "✓ Read by " & Coalesce(ThisItem.ReadBy, "—") & " on " & Text(ThisItem.ReadOn, "dd-mm-yyyy hh:mm")\n)')
VIS = 'Not(IsBlank(ThisItem.ReadOn)) Or Lower(Coalesce(ThisItem.AuthorEmail, "")) = Lower(User().Email)'
b.clone('NT_ReadReceipt', S, 'Body1_1', {'Text': TXT, 'Y': '92', 'Size': '9', 'Visible': VIS,
                                      'Color': 'If(IsBlank(ThisItem.ReadOn), RGBA(150, 155, 165, 1), RGBA(22, 128, 80, 1))'}, parent='MessageCenter')
b.save()
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL92 built')
