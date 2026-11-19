#!/usr/bin/env python3
"""Pack new/ into a .msapp, then prove the result is loadable.

The archive's shape is taken from a known-good .msapp (PACK_REF) and the mapping must be exact in
BOTH directions -- no reference entry absent from the tree, and no file in the tree left out.
A silently dropped Controls file is what made an early package unopenable, so it is an assertion.

Invariants enforced because each has already broken a package once:
  * every control carries "Children" (clones that lost it would not open)
  * the YAML and the JSON name the same controls on every screen
Usage: PACK_REF=<reference.msapp> python3 pack_final.py <out.msapp> <tree dir>
"""
import datetime, io, json, os, sys, zipfile
from paload import load

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
NEW = os.path.join(HERE, sys.argv[2] if len(sys.argv) > 2 else 'new')
REF = os.environ['PACK_REF']

for sub in ('Controls', 'Src', 'References'):
    for f in sorted(os.listdir(os.path.join(NEW, sub))):
        p = os.path.join(NEW, sub, f)
        (load(p) if f.endswith('.pa.yaml') else json.load(open(p, encoding='utf-8')))
for f in ('Header.json', 'Properties.json'):
    json.load(open(os.path.join(NEW, f), encoding='utf-8'))
print(f'parsed OK: {len(os.listdir(os.path.join(NEW, "Controls")))} Controls, '
      f'{len(os.listdir(os.path.join(NEW, "Src")))} Src, References, Properties, Header')

zin = zipfile.ZipFile(REF)
entries = [i for i in zin.infolist() if not i.is_dir()]
names = {i.filename.replace('\\', '/') for i in entries}
on_disk = set()
for root, _, files in os.walk(NEW):
    for f in files:
        on_disk.add(os.path.relpath(os.path.join(root, f), NEW).replace(os.sep, '/'))
absent, extra = sorted(names - on_disk), sorted(on_disk - names)
if absent:
    sys.exit(f'! reference lists files missing from the tree: {absent}')
if extra:
    sys.exit(f'! files in the tree that the reference does not have: {extra}')
print(f'mapping: {len(entries)} reference entries, nothing missing, 0 new file(s) added (0 screen(s))')

# ---- invariants ---------------------------------------------------------------------------------------------------
def walk(n):
    yield n
    for c in n.get('Children', []):
        yield from walk(c)

def yaml_names(node, out):
    for item in node.get('Children') or []:
        for k, v in item.items():
            out.add(k)
            yaml_names(v if isinstance(v, dict) else {}, out)

n_ctl = 0
screens = []
for f in sorted(os.listdir(os.path.join(NEW, 'Controls'))):
    tp = json.load(open(os.path.join(NEW, 'Controls', f), encoding='utf-8'))['TopParent']
    jn = set()
    for c in walk(tp):
        n_ctl += 1
        if 'Children' not in c:
            sys.exit(f'! {c["Name"]} has no "Children"')
        tpl = (c.get('Template') or {}).get('Name') if isinstance(c.get('Template'), dict) else ''
        # groups and gallery templates are implicit in the YAML (a 'Group:' attribute / the gallery itself)
        if c is not tp and not c.get('IsGroupControl') and tpl != 'galleryTemplate':
            jn.add(c['Name'])
    if tp['Name'] == 'App':      # the App object has no controls in YAML (its JSON carries the Host control)
        screens.append('App')
        continue
    y = load(os.path.join(NEW, 'Src', tp['Name'] + '.pa.yaml'))
    yn = set()
    yaml_names((y.get('Screens') or {}).get(tp['Name']) or {}, yn)
    if jn != yn:
        sys.exit(f'! {tp["Name"]}: YAML and JSON name different controls: only JSON {sorted(jn - yn)[:8]}, only YAML {sorted(yn - jn)[:8]}')
    screens.append(tp['Name'])

# ---- write --------------------------------------------------------------------------------------------------------
now = datetime.datetime.utcnow().timetuple()[:6]
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zout:
    for i in entries:
        zi = zipfile.ZipInfo(i.filename, date_time=now)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = i.external_attr
        zi.create_system = i.create_system
        data = open(os.path.join(NEW, i.filename.replace('\\', '/')), 'rb').read()
        zout.writestr(zi, data)
print(f'wrote {os.path.basename(OUT)}  ({os.path.getsize(OUT):,} bytes)')
print(f'  all {n_ctl} controls carry "Children"')
print('  YAML and JSON agree on every screen')
print('  screens: ' + ', '.join(sorted(screens)))
# re-open what was written
z = zipfile.ZipFile(OUT)
assert z.testzip() is None and len(z.infolist()) == len(entries)
print('\nOK')
