#!/usr/bin/env python3
"""FINAL213 on FINAL212. The loading box also shows while Print saves the PDF: Print only sets locSavePending; a timer then calls
the flow (so the box is drawn first) and clears the flag. Text: "Saving the PDF" / "Preparing the preview"."""
import copy, datetime, os, re, shutil
from payaml import App, find
from hp_common import Builder
SRC, NEW = 'newV74', 'newV75'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)
OLD_BUSY = 'Coalesce(locPdfPending, false)'
BUSY = '(Coalesce(locPdfPending, false) Or Coalesce(locSavePending, false))'
for scr, p in (('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD'), ('PrintPhotoDetailScreen', 'PPD')):
    save = app.rule(scr, f'{p}_PdfDownload', 'OnSelect')
    assert 'AVCD_SavePrintPDF.Run' in save
    body = save.replace('Notify("Saving the PDF...", NotificationType.Information);\n', '')
    setp(scr, f'{p}_PdfDownload', 'OnSelect', '// the loading box is drawn first; the save itself runs in the timer\nUpdateContext({locSavePending: true})')
    setp(scr, f'{p}_PdfDownload', 'DisplayMode', 'If(Coalesce(locSavePending, false), DisplayMode.Disabled, DisplayMode.Edit)')
    for nm in (f'{p}_LoadShade', f'{p}_LoadPanel', f'{p}_LoadText', f'{p}_LoadDot1', f'{p}_LoadDot2', f'{p}_LoadDot3'):
        setp(scr, nm, 'Visible', BUSY)
    setp(scr, f'{p}_LoadText', 'Text', 'If(Coalesce(locSavePending, false), "Saving the PDF", "Preparing the preview")')
    setp(scr, f'{p}_LoadTimer', 'Start', BUSY)
    b = Builder(app, scr)
    b.clone(f'{p}_SaveTimer', 'RequesDetailScreen', 'Timer1', {'AutoStart': 'false', 'Repeat': 'false', 'Duration': '300', 'Visible': 'false',
            'OnTimerEnd': body.strip() + ';\nUpdateContext({locSavePending: false})', 'X': '0', 'Y': '0', 'Width': '10', 'Height': '10'})
    b.save()
    tp = app.doc(scr)['TopParent']; tm = find(tp, f'{p}_SaveTimer')
    r0 = [r for r in tm['Rules'] if r['Property'] == 'Repeat'][0]
    r1 = copy.deepcopy(r0); r1['Property'] = 'Start'; r1['InvariantScript'] = 'Coalesce(locSavePending, false)'; tm['Rules'].append(r1)
    app.save()
    yf = f'{NEW}/Src/{scr}.pa.yaml'; L = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
    i0 = next(i for i, l in enumerate(L) if l == f'      - {p}_SaveTimer:')
    j = next(i for i in range(i0, len(L)) if L[i].startswith('            Repeat:'))
    L.insert(j + 1, '            Start: =Coalesce(locSavePending, false)')
    open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(L))
    t = app.rule(scr, None, 'OnVisible')
    app.set(scr, None, 'OnVisible', t.replace('locDot: 0})', 'locDot: 0, locSavePending: false})'), expect=t)
    assert 'locSavePending: false' in app.rule(scr, None, 'OnVisible')
p_ = f'{NEW}/Properties.json'
raw = open(p_, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
t = re.sub(r'("timer"\s*:\s*)(\d+)', lambda mm: mm.group(1) + str(int(mm.group(2)) + 3), t, count=1)
open(p_, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL213 built')
