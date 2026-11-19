#!/usr/bin/env python3
"""FINAL122 on FINAL121 (Message Center):
 1. Title1 (the message text in the MessageCenter gallery) is size 11.
 2. The window scrolls to the newest messages: when it opens, and after every 5 s refresh of the timer (the gallery's Default is the last message and the gallery is reset onto it).
 3. DOA_MessageCenter keeps only the envelope; the number of unread messages is a label of its own (DOA_MessageCenterCount) above the button's top-right corner."""
import datetime, os, re, shutil
from payaml import App, find
from hp_common import Builder
SRC, NEW = 'newQ5', 'newQ6'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
D = 'RequesDetailScreen'
eol = lambda t: '\r\n' if '\r\n' in t else '\n'
def put(ctl, prop, new, old_expect=None):
    t = app.rule(D, ctl, prop)
    app.set(D, ctl, prop, new.replace('\n', eol(t)), expect=old_expect if old_expect is not None else t)

# 1. message text size
put('Title1', 'Size', '11', '13')

# 2. scroll to the newest messages
put('MessageCenter', 'Selectable', 'true', 'false')
t = app.rule(D, 'DOA_MessageCenter', 'OnSelect')
old = 'UpdateContext({ currentIndex: If(currentIndex >= CountRows(MessageCenter.AllItems), 1, currentIndex + 1) });'
assert t.count(old) == 1
new = '''// the window opens on the newest messages
With(
    {notes: Filter('AV-CD-Notes', Title = varCurrentRequest.RequestNumber)},
    UpdateContext({currentIndex: Max(1, CountRows(notes))});
    Reset(MessageCenter)
)'''
put('DOA_MessageCenter', 'OnSelect', t.replace(old, new.replace('\n', eol(t))), t)
put('NT_MessageTimer', 'OnTimerEnd', '''If(
    Coalesce(varCurrentRequest.ID, 0) > 0 And Not(IsBlank(varCurrentRequest.RequestNumber)),
    With(
        {tick: Coalesce(locNoteTick, 0) + 1},
        UpdateContext({locNoteTick: tick});
        // every 5 s while the Message Center is open; every 30 s otherwise, so the unread number above its button stays current
        If(
            locShowNotes Or Mod(tick, 6) = 0,
            Refresh('AV-CD-Notes');
            If(
                locShowNotes,
                // a message that arrives while the window is open is read as it appears
                IfError(
                    ForAll(
                        Filter(MessageCenter.AllItems, IsBlank(ReadOn), AuthorEmail <> User().Email) As n,
                        Patch('AV-CD-Notes', n, {ReadBy: User().FullName, ReadOn: Now()})
                    ),
                    Blank()
                );
                // after the refresh the window shows the newest messages
                With(
                    {notes: Filter('AV-CD-Notes', Title = varCurrentRequest.RequestNumber)},
                    UpdateContext({currentIndex: Max(1, CountRows(notes))});
                    Reset(MessageCenter)
                )
            )
        )
    )
)''')

# 3. the unread number: its own label above the button
UNREAD = "With({notes: Filter('AV-CD-Notes', Title = varCurrentRequest.RequestNumber)}, CountRows(Filter(notes, IsBlank(ReadOn), AuthorEmail <> User().Email)))"
put('DOA_MessageCenter', 'Text', '"✉️"')
app.save()

class NB(Builder):
    def grouped(self, tp): return set()
z = []
walk = lambda n: [n] + [x for c in n.get('Children', []) for x in walk(c)]
for n in walk(app.doc(D)['TopParent']):
    for r in n['Rules']:
        if r['Property'] == 'ZIndex' and r['InvariantScript'].isdigit(): z.append(int(r['InvariantScript']))
lbl = NB(app, D)
lbl.clone('DOA_MessageCenterCount', D, 'DOA_List1CounterText_1', {
    'Text': f'With({{unread: {UNREAD}}}, If(unread > 99, "99+", Text(unread)))',
    # not over the dialogs: the Message Center, the contact picker, the delete confirmation and the production type picker cover the screen
    'Visible': f'Coalesce(varCurrentRequest.ID, 0) > 0 And Not(locShowNotes Or locShowContactPopup Or locShowDelConfirm Or locShowTypePicker) And {UNREAD} > 0',
    'X': '437', 'Y': '62', 'Width': '26', 'Height': '20',
    'Fill': 'RGBA(192, 57, 43, 1)', 'Color': 'RGBA(255, 255, 255, 1)',
    'Align': 'Align.Center', 'VerticalAlign': 'VerticalAlign.Middle',
    'FontWeight': 'FontWeight.Bold', 'Size': '10',
    'PaddingTop': '0', 'PaddingBottom': '0', 'PaddingLeft': '0', 'PaddingRight': '0',
    'BorderColor': 'RGBA(255, 255, 255, 1)', 'BorderThickness': '1',
    'OnSelect': 'Select(DOA_MessageCenter)',
    'Tooltip': '"Unread messages"',
    'ZIndex': str(max(z) + 1)})
lbl.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL122 built')
