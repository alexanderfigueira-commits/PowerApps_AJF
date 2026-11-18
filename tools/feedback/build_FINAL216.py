#!/usr/bin/env python3
"""FINAL216 on TEST_23 (= FINAL215 + a modern date picker DatePicker1 inserted in Studio + small moves of the media buttons).
Every classic date picker of the app (12) is replaced by a modern one (ModernDatePicker 1.0.2) with the SAME name, place and parent,
so every formula that reads .SelectedDate or calls Reset() keeps working. Carried over: DefaultDate, OnChange, Visible, DisplayMode,
AccessibleLabel, the amber "mandatory and empty" border (BorderColor / BorderThickness), Fill, font, size, padding, StartOfWeek,
DateTimeZone, IsEditable, X/Y/Width/Height, ZIndex; StartYear/EndYear become StartDate/EndDate.
Not available on the modern control: the custom text format "dd-mm-yyyy" (DatePickerFormat.Short is used: the user's locale), the
Tooltip and the classic calendar colours. The loose DatePicker1 is removed."""
import copy, datetime, json, glob, os, re, shutil
from payaml import App, find, block_span, _fmt
SRC, NEW = 'newT23', 'newV78'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
DONOR_SCR, DONOR = 'RequestManagementScreen', 'DatePicker1'
dtp = app.doc(DONOR_SCR)['TopParent']; donor = find(dtp, DONOR)
CARRY_DATA = ['DefaultDate', 'DateTimeZone', 'StartOfWeek', 'AccessibleLabel', 'IsEditable']
CARRY_DESIGN = ['X', 'Y', 'Width', 'Height', 'Visible', 'DisplayMode', 'BorderColor', 'BorderThickness', 'Fill', 'Color', 'Font', 'Size',
                'FontWeight', 'PaddingLeft', 'PaddingRight', 'PaddingTop', 'PaddingBottom', 'ZIndex']
ORDER = ['DefaultDate', 'StartDate', 'EndDate', 'Placeholder', 'DateTimeZone', 'Format', 'StartOfWeek', 'IsEditable', 'AccessibleLabel',
         'ValidationState', 'Appearance', 'Italic', 'Underline', 'Strikethrough', 'BorderColor', 'BorderStyle', 'BorderThickness', 'Fill', 'Color',
         'Font', 'Size', 'FontWeight', 'PaddingLeft', 'PaddingRight', 'PaddingTop', 'PaddingBottom', 'X', 'Y', 'Width', 'Height', 'Visible',
         'DisplayMode', 'ZIndex', 'OnChange']
def rule(prop, script, cat):
    return {'Property': prop, 'Category': cat, 'InvariantScript': script, 'RuleProviderType': 'Unknown'}
done = []
for f in sorted(glob.glob(f'{NEW}/Controls/*.json')):
    scr = json.load(open(f, encoding='utf-8-sig'))['TopParent']['Name']
    tp = app.doc(scr)['TopParent']
    targets = []
    def walk(n, host):
        for i, c in enumerate(n.get('Children', [])):
            if c['Template']['Name'] == 'datepicker': targets.append((n, i, c))
            walk(c, n)
    walk(tp, None)
    for host, i, old in targets:
        r = {x['Property']: x['InvariantScript'] for x in old['Rules']}
        sy = r.get('StartYear', '1900'); ey = r.get('EndYear', None)
        rules = {
            'StartDate': rule('StartDate', f'Date({sy.strip()}, 1, 1)', 'Data'),
            'EndDate': rule('EndDate', f'Date({ey.strip()}, 12, 31)' if ey else 'Date(Year(Today())+100, 12, 31)', 'Data'),
            'Placeholder': rule('Placeholder', '"Select a date"', 'Data'),
            'Format': rule('Format', 'DatePickerFormat.Short', 'Data'),
            'ValidationState': rule('ValidationState', 'ValidationState.None', 'Data'),
            'Appearance': rule('Appearance', 'Appearance.Outline', 'Design'),
            'BorderStyle': rule('BorderStyle', 'BorderStyle.Solid', 'Design'),
            'Italic': rule('Italic', 'false', 'Design'), 'Underline': rule('Underline', 'false', 'Design'), 'Strikethrough': rule('Strikethrough', 'false', 'Design'),
        }
        for p in CARRY_DATA:
            if p in r and r[p].strip(): rules[p] = rule(p, r[p], 'Data')
        for p in CARRY_DESIGN:
            if p in r and r[p].strip(): rules[p] = rule(p, r[p], 'Design')
        if 'OnChange' in r and r['OnChange'].strip(): rules['OnChange'] = rule('OnChange', r['OnChange'], 'Behavior')
        new = copy.deepcopy(donor)
        for k in ('Name', 'ControlUniqueId', 'PublishOrderIndex', 'Index', 'Parent', 'IsLocked'):
            if k in old: new[k] = old[k]
        new['Children'] = []
        new['Rules'] = [rules[p] for p in ORDER if p in rules]
        cps = [e for e in donor['ControlPropertyState'] if isinstance(e, dict)]
        new['ControlPropertyState'] = [p for p in ORDER if p in rules and p != 'Format'] + cps
        host['Children'][i] = new
        done.append((scr, old['Name']))
        # YAML block
        yf = f'{NEW}/Src/{scr}.pa.yaml'
        L = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
        s, e = block_span(L, old['Name'])
        mi = len(L[s]) - len(L[s].lstrip())
        group = [ln for ln in L[s:e] if ln.strip().startswith('Group:') and len(ln) - len(ln.lstrip()) == mi + 4]
        out = [' ' * mi + f'- {old["Name"]}:', ' ' * (mi + 4) + 'Control: ModernDatePicker@1.0.2'] + group + [' ' * (mi + 4) + 'Properties:']
        for p in sorted(rules):
            if p == 'ZIndex': continue
            out += _fmt(p, rules[p]['InvariantScript'], mi + 6)
        out.append(' ' * (mi + 4) + 'Children: []')
        L[s:e] = out
        open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(L))
    app.save()
# remove the loose donor
dtp = app.doc(DONOR_SCR)['TopParent']
n0 = len(dtp['Children']); dtp['Children'] = [c for c in dtp['Children'] if c['Name'] != DONOR]; assert len(dtp['Children']) == n0 - 1
app.save()
yf = f'{NEW}/Src/{DONOR_SCR}.pa.yaml'; L = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
s, e = block_span(L, DONOR); del L[s:e]; open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(L))
# control counts
p_ = f'{NEW}/Properties.json'
raw = open(p_, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
t, k = re.subn(r'"datepicker"(\s*):(\s*)\d+', lambda m: '"modernDatePicker"' + m.group(1) + ':' + m.group(2) + str(len(done)), t, count=1)
assert k == 1
open(p_, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('replaced', len(done), done)
print('FINAL216 built')
