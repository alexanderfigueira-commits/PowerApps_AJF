#!/usr/bin/env python3
"""FINAL212 on FINAL211. PDF footer centred with a computed padding (PDF() ignored Align.Center). While the preview PDF is being built (locPdfPending), a loading box sits in the centre of the print sheet:
"Preparing the preview" and three dots that light up one after the other (timer, 350 ms)."""
import copy, datetime, os, re, shutil
from payaml import App, find
from hp_common import Builder
SRC, NEW = 'newV73', 'newV74'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
BUSY = 'Coalesce(locPdfPending, false)'
DOT_ON, DOT_OFF = 'RGBA(0, 18, 107, 1)', 'RGBA(186, 202, 226, 1)'
for scr, p in (('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD'), ('PrintPhotoDetailScreen', 'PPD')):
    b = Builder(app, scr)
    b.clone(f'{p}_LoadShade', 'ChildInfoScreen', 'CI_TplConfirmShade', {'Visible': BUSY, 'Fill': 'RGBA(0, 18, 107, 0.20)'})
    b.clone(f'{p}_LoadPanel', 'ChildInfoScreen', 'CI_TplConfirmPanel', {'Visible': BUSY, 'X': '543', 'Y': '314', 'Width': '280', 'Height': '120'})
    b.clone(f'{p}_LoadText', 'ChildInfoScreen', 'CI_TplConfirmText', {'Visible': BUSY, 'X': '553', 'Y': '330', 'Width': '260', 'Height': '30',
            'Text': '"Preparing the preview"', 'Size': '13', 'Align': 'Align.Center', 'Color': 'RGBA(0, 18, 107, 1)'})
    for k, x in enumerate((650, 674, 698)):
        b.clone(f'{p}_LoadDot{k + 1}', 'ChildInfoScreen', 'CI_TplConfirmText', {
            'Visible': BUSY, 'X': str(x - 3), 'Y': '372', 'Width': '24', 'Height': '40', 'Size': '22', 'Align': 'Align.Center',
            'Text': '"●"', 'Color': f'If(Coalesce(locDot, 0) = {k}, {DOT_ON}, {DOT_OFF})'})
    b.clone(f'{p}_LoadTimer', 'RequesDetailScreen', 'Timer1', {'AutoStart': 'false', 'Repeat': 'true', 'Duration': '350', 'Visible': 'false',
            'OnTimerEnd': 'UpdateContext({locDot: Mod(Coalesce(locDot, 0) + 1, 3)})', 'X': '0', 'Y': '0', 'Width': '10', 'Height': '10'})
    b.save()
    tp = app.doc(scr)['TopParent']; tm = find(tp, f'{p}_LoadTimer')
    r0 = [r for r in tm['Rules'] if r['Property'] == 'Repeat'][0]
    r1 = copy.deepcopy(r0); r1['Property'] = 'Start'; r1['InvariantScript'] = BUSY; tm['Rules'].append(r1)
    yf = f'{NEW}/Src/{scr}.pa.yaml'; L = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
    i0 = next(i for i, l in enumerate(L) if l == f'      - {p}_LoadTimer:')
    j = next(i for i in range(i0, len(L)) if L[i].startswith('            Repeat:'))
    L.insert(j + 1, f'            Start: ={BUSY}')
    open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(L))
    # above everything else on the sheet
    z = lambda n: int(([x['InvariantScript'] for x in n['Rules'] if x['Property'] == 'ZIndex'] or ['0'])[0])
    NEWC = [f'{p}_LoadShade', f'{p}_LoadPanel', f'{p}_LoadText', f'{p}_LoadDot1', f'{p}_LoadDot2', f'{p}_LoadDot3']
    mx = max(z(n) for n in tp['Children'] if n['Name'] not in NEWC)
    for k, nm in enumerate(NEWC): [x for x in find(tp, nm)['Rules'] if x['Property'] == 'ZIndex'][0]['InvariantScript'] = str(mx + 1 + k)
    app.save()
    t = app.rule(scr, None, 'OnVisible')
    app.set(scr, None, 'OnVisible', t.replace('locPdfMode: ""})', 'locPdfMode: "", locDot: 0})'), expect=t)
    assert 'locDot: 0' in app.rule(scr, None, 'OnVisible')
for scr, p in (('PrintVideoDetailScreen', 'PVD'), ('PrintPodcastDetailScreen', 'PPoD'), ('PrintPhotoDetailScreen', 'PPD')):
    for prop, v in (('Align', 'Align.Left'),
                    ('PaddingLeft', '// PDF() drops the label alignment: the text is centred with a left padding (about 8 px per character at 12 pt)\nMax(0, (Self.Width - Len(Self.Text) * 8) / 2)')):
        t = app.rule(scr, f'{p}_PgFooter', prop); assert t is not None, prop
        app.set(scr, f'{p}_PgFooter', prop, v, expect=t)
p_ = f'{NEW}/Properties.json'
raw = open(p_, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
for k, d in (('rectangle', 6), ('label', 12), ('timer', 3)):
    t = re.sub(r'("%s"\s*:\s*)(\d+)' % k, lambda mm: mm.group(1) + str(int(mm.group(2)) + d), t, count=1)
open(p_, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL212 built')
