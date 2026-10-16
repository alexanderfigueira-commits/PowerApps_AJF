#!/usr/bin/env python3
"""FINAL40 on the owner's FINAL_1 (= FINAL37 + the owner's own layout edits), after FINAL38 (end-of-day date) and FINAL39 (All Status order)
were re-applied by build_G30a / build_G30b:

"Partially approved" is no longer a status.
* ReviewScreen RV_BtnApprove always writes Status = Approved (it wrote "Partially approved" when only some media files were ticked);
* the six dashboard status badges (DOA_/DOR_ List1-3 RowBadge) show "Approved" (also for old requests still stored as "Partially approved"),
  no longer use the dark-gold colour, and their tooltip says "Partially Approved Request." when the request is Approved but only some of its
  media files carry the RS_CRowApproved tick (some, not all; or an old "Partially approved" record); otherwise the tooltip stays "Status".
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG30b', 'newG30'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)


def nl(t):
    return t.replace('\r\n', '\n')


def like(o, t):
    return t.replace('\n', '\r\n') if '\r\n' in o else t


# ---- ReviewScreen: always Approved
S, C = 'ReviewScreen', 'RV_BtnApprove'
t = app.rule(S, C, 'OnSelect')
n = nl(t)
old = '''            // some but not all media files ticked "Approved" on the request screen -> Partially approved
            Status: {Value: If(
            With(
                {n: CountRows(RV_ChildrenGallery.AllItems), ok: CountRows(Filter(RV_ChildrenGallery.AllItems, MediaApproved = true))},
                ok > 0 And ok < n
            ),
            "Partially approved",
            "Approved"
        )},'''
if n.count(old) != 1:
    sys.exit('! approve status block not found')
n = n.replace(old, '''            // always "Approved": a request with only some media files ticked is shown as "Partially Approved Request." on the dashboards (tooltip)
            Status: {Value: "Approved"},''')
m = '"Request partially approved: only the ticked media files are approved."'
if n.count(m) != 1:
    sys.exit('! approve notification not found')
n = n.replace(m, '"Partially Approved Request: only the ticked media files are approved."')
app.set(S, C, 'OnSelect', like(t, n), expect=t)

# ---- dashboards: the six badges
BADGES = [('Dashboard-Ope-Administrator', f'DOA_List{i}RowBadge') for i in (1, 2, 3)] + [('Dashboard-Ope-Requestor', f'DOR_List{i}RowBadge') for i in (1, 2, 3)]
for s, c in BADGES:
    tx = app.rule(s, c, 'Text')
    if tx != 'If(IsBlank(ThisItem.Status.Value), "Draft", Text(ThisItem.Status.Value))':
        sys.exit(f'! {c}.Text changed: {tx}')
    app.set(s, c, 'Text', 'If(IsBlank(ThisItem.Status.Value), "Draft", If(ThisItem.Status.Value = "Partially approved", "Approved", Text(ThisItem.Status.Value)))', expect=tx)
    tt = app.rule(s, c, 'Tooltip')
    if tt != '"Status"':
        sys.exit(f'! {c}.Tooltip changed: {tt}')
    app.set(s, c, 'Tooltip', '''// "Partially approved" is not a status: an Approved request whose media files are only partly ticked (RS_CRowApproved) says so here
With(
    {
        n: CountRows(Filter(colOpeMedia, ParentRequest = ThisItem.RequestNumber)),
        ok: CountRows(Filter(colOpeMedia, ParentRequest = ThisItem.RequestNumber, MediaApproved = true))
    },
    If(
        ThisItem.Status.Value = "Partially approved" Or (ThisItem.Status.Value = "Approved" And ok > 0 And ok < n),
        "Partially Approved Request.",
        "Status"
    )
)''', expect=tt)
    f = app.rule(s, c, 'Fill')
    nf = re.sub(r'\n? *"Partially approved" in ThisItem\.Status\.Value, Color\.DarkGoldenRod,', '', nl(f), count=1)
    if nf == nl(f):
        sys.exit(f'! {c}.Fill: partial branch not found')
    app.set(s, c, 'Fill', like(f, nf), expect=f)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL40 built')
