#!/usr/bin/env python3
"""FINAL41 on the owner's FINAL (= FINAL40 + a fixed tab link and one removed divider):

1. Dashboard TODO clocks (DOA_List1RowBell, DOR_List1RowBell) follow the PUBLICATION date (PublicationStartDate) instead of the
   shooting / filming / capture date: colour, tooltip and accessible label; text "Publication date" / "No publication date yet".
2. CL_ChkFramework and CL_ChkSpecific start ticked when the request is Processing, Pending, Approved or Rejected (also an old
   "Partially approved"): set when a media item is opened (the media row's open handler, DOA_List1RowBadge_8 in the owner's file) or added (Add_media_icon), so a later manual change survives
   moving between the tabs. A Draft request keeps them unticked.
3. The media item tabs: the text of the selected tab is blue (RGBA(56, 96, 178, 1), the colour of the underline), the others grey.
   (Tab 1 was navy on every screen.)
"""
import datetime, os, re, shutil, sys
from payaml import App, find

SRC, NEW = 'up5', 'newG31'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)


def nl(t):
    return t.replace('\r\n', '\n')


def like(o, t):
    return t.replace('\n', '\r\n') if '\r\n' in o else t


# ---------------------------------------------------------------- 1. bells
for s, c in (('Dashboard-Ope-Requestor', 'DOR_List1RowBell'), ('Dashboard-Ope-Administrator', 'DOA_List1RowBell')):
    for p in ('Color', 'Tooltip', 'AccessibleLabel'):
        t = app.rule(s, c, p)
        n = nl(t)
        n = n.replace('CaptureDate', 'PublicationStartDate')
        n = n.replace('// days left to the media item\'s key date; one column (PublicationStartDate) holds the\n// shooting day (Photo), the filming date (Video) and the capture date (Podcast)',
                      '// days left to the publication date of the request\'s media items (PublicationStartDate)')
        n = n.replace('"No shooting / filming / capture date yet"', '"No publication date yet"')
        n = n.replace('what: Switch(First(m.MediaType).Value, "Photo", "Shooting day", "Video", "Filming date", "Capture date")', 'what: "Publication date"')
        if p == 'Color':
            n = n.replace('// grey: no date. Same date as the tooltip', '// grey: no publication date. Same date as the tooltip')
        if re.search(r'CaptureDate|[Ss]hooting|[Ff]ilming', n):
            sys.exit(f'! {c}.{p}: old wording left')
        app.set(s, c, p, like(t, n), expect=t)
t = app.rule('Dashboard-Ope-Administrator', None, 'OnVisible')
o = '// media items, for the TODO bell (days left to the shooting / filming / capture date)'
if o not in t:
    sys.exit('! admin OnVisible comment not found')
app.set('Dashboard-Ope-Administrator', None, 'OnVisible', t.replace(o, '// media items, for the TODO clock (days left to the publication date)'), expect=t)
t = app.rule('Dashboard-Ope-Requestor', None, 'OnVisible')
if 'shooting' in t or 'capture date' in t:
    app.set('Dashboard-Ope-Requestor', None, 'OnVisible', re.sub(r'\(days left to the shooting / filming / capture date\)', '(days left to the publication date)', t), expect=t)

# ---------------------------------------------------------------- 2. contract checkboxes default true
COND = 'Coalesce(varCurrentRequest.Status.Value, "") in ["Processing", "Pending", "Approved", "Partially approved", "Rejected"]'
OLD = 'Set(varDocFramework, false); Set(varDocSpecific, false); Set(varDocOffer, false);'
NEWC = f'// the framework and specific contracts count as confirmed once the request was submitted\nSet(varDocFramework, {COND}); Set(varDocSpecific, {COND}); Set(varDocOffer, false);'
for s, c in (('RequesDetailScreen', 'DOA_List1RowBadge_8'), ('RequesDetailScreen', 'Add_media_icon')):
    t = app.rule(s, c, 'OnSelect')
    n = nl(t)
    if n.count(OLD) != 1:
        sys.exit(f'! {c}: reset line found {n.count(OLD)} times')
    app.set(s, c, 'OnSelect', like(t, n.replace(OLD, NEWC)), expect=t)

# ---------------------------------------------------------------- 3. selected tab text is blue
BLUE, GREY = 'RGBA(56, 96, 178, 1)', 'RGBA(96, 104, 120, 1)'
TABS = {
    'ChildInfoScreen': (['CI_Tab1', 'CI_Tab2', 'CI_Tab3', 'CI_Tab4'], 0),
    'ChildMetaScreen': (['CI_Tab1_1', 'CI_Tab2_1', 'CI_Tab3_1', 'CI_Tab4_1'], 1),
    'ChildLegalScreen': (['CI_Tab1_2', 'CI_Tab2_2', 'CI_Tab3_2', 'CI_Tab4_2'], 2),
    'ChildValidScreen': (['CI_Tab1_3', 'CI_Tab2_3', 'CI_Tab3_3', 'CI_Tab4_3'], 3),
}
for s, (names, sel) in TABS.items():
    for i, c in enumerate(names):
        old = app.rule(s, c, 'Color')
        if old not in ('RGBA(0, 18, 107, 1)', GREY):
            sys.exit(f'! {s}.{c}.Color unexpected: {old}')
        app.set(s, c, 'Color', BLUE if i == sel else GREY, expect=old)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL41 built')
