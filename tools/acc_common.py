"""Helpers for the accessibility builds: edit a property in Controls/*.json and the matching .pa.yaml, drop a rule, add a rule."""
import os, re, sys
from payaml import find, _block, _span, _fmt

DECOR = ('label', 'rectangle', 'image', 'icon', 'circle')


def ttype(node):
    t = node.get('Template')
    return t.get('Name') if isinstance(t, dict) else t


def lf(t):
    return t.replace('\r\n', '\n')


def walk(n):
    yield n
    for c in n.get('Children', []):
        yield from walk(c)


def _lines(path):
    return open(path, encoding='utf-8', newline='').read().replace('\r\n', '\n').replace('\r', '\n').split('\n')


def _write(path, lines):
    open(path, 'w', encoding='utf-8', newline='').write('\n'.join(lines))


def drop_rule(app, screen, ctl, prop, expect):
    """remove a rule (JSON: rule + property state; YAML: the property line if the YAML lists it)"""
    node = find(app.doc(screen)['TopParent'], ctl)
    hit = [r for r in node['Rules'] if r['Property'] == prop]
    assert len(hit) == 1 and lf(hit[0]['InvariantScript']).strip() == expect, (screen, ctl, prop)
    node['Rules'] = [r for r in node['Rules'] if r['Property'] != prop]
    node['ControlPropertyState'] = [s for s in node['ControlPropertyState'] if s != prop]
    yf = os.path.join(app.path, 'Src', f'{screen}.pa.yaml')
    lines = _lines(yf)
    b = _block(lines, ctl)
    if b is None:
        sys.exit(f'! {screen}: {ctl} not in YAML')
    start, end, pi = b
    key_re = re.compile(r'^' + ' ' * pi + r'([A-Za-z0-9_.]+):')
    sp = _span(lines, start, end, prop, key_re)
    if sp:
        assert lines[sp[0]].strip() in (f'{prop}: =false', f'{prop}: ={expect}'), lines[sp[0]]
        del lines[sp[0]:sp[1]]
        _write(yf, lines)
        return True
    return False


def put_rule(app, screen, ctl, prop, value, category='Design'):
    """set a property to `value` in both representations; the rule is created when the control has none"""
    node = find(app.doc(screen)['TopParent'], ctl)
    hit = [r for r in node['Rules'] if r['Property'] == prop]
    if not hit:
        node['Rules'].append({'Property': prop, 'Category': category, 'InvariantScript': '', 'RuleProviderType': 'Unknown'})
        if prop not in node['ControlPropertyState']:
            node['ControlPropertyState'].append(prop)
        old = ''
    else:
        old = hit[0]['InvariantScript']
    app.set(screen, ctl, prop, value, expect=None)
    return old
