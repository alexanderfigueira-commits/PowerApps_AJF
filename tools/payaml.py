#!/usr/bin/env python3
"""Set a control property in both Controls/*.json and the matching .pa.yaml.

Writing through one call keeps the two representations in sync by construction:
the same invariant script is written to the JSON rule and formatted into the
YAML block.
"""
import glob, json, os, re, sys
from jio import jwrite

CTL_RE = re.compile(r'^\s*- ([A-Za-z0-9_]+):\s*$')
KEY_RE = re.compile(r'^            ([A-Za-z0-9_.]+):')
SCREEN_KEY_RE = re.compile(r'^      ([A-Za-z0-9_.]+):')


def screens(app):
    """{screen name: Controls/*.json path}"""
    out = {}
    for f in sorted(glob.glob(os.path.join(app, 'Controls', '*.json'))):
        out[json.load(open(f, encoding='utf-8'))['TopParent']['Name']] = f
    return out


def find(node, name):
    if node.get('Name') == name:
        return node
    for k in node.get('Children', []):
        r = find(k, name)
        if r:
            return r


def _fmt(prop, script, indent):
    pad = ' ' * indent
    script = script.replace('\r\n', '\n').replace('\r', '\n')
    if '\n' not in script and ': ' not in script and not script.endswith(':') and ' #' not in script:
        return [f'{pad}{prop}: ={script}']
    return [f'{pad}{prop}: |-'] + [f'{pad}  {ln}' if ln.strip() else '' for ln in ('=' + script).split('\n')]


def _indent(ln):
    return len(ln) - len(ln.lstrip())


def _block(lines, control):
    """(start, props_end, prop_indent) for `control` at any nesting depth.
    start = the '- Name:' line; props_end = where its own properties stop (nested Children excluded)."""
    marker = None
    for i, ln in enumerate(lines):
        m = CTL_RE.match(ln)
        if m and m.group(1) == control:
            if marker is not None:
                sys.exit(f'! {control} appears more than once in the YAML')
            marker = i
    if marker is None:
        return None
    mi = _indent(lines[marker])
    end = len(lines)
    for i in range(marker + 1, len(lines)):
        if lines[i].strip() and _indent(lines[i]) <= mi:
            end = i
            break
    props_end = end
    for i in range(marker + 1, end):
        if lines[i].strip() and _indent(lines[i]) == mi + 4 and lines[i].lstrip().startswith('Children:'):
            props_end = i
            break
    while props_end > marker + 1 and not lines[props_end - 1].strip():
        props_end -= 1
    return marker, props_end, mi + 6


def block_span(lines, control):
    """(start, end) of the whole control block including nested Children."""
    marker = None
    for i, ln in enumerate(lines):
        m = CTL_RE.match(ln)
        if m and m.group(1) == control:
            if marker is not None:
                sys.exit(f'! {control} appears more than once in the YAML')
            marker = i
    if marker is None:
        return None
    mi = _indent(lines[marker])
    end = len(lines)
    for i in range(marker + 1, len(lines)):
        if lines[i].strip() and _indent(lines[i]) <= mi:
            end = i
            break
    while end > marker + 1 and not lines[end - 1].strip():
        end -= 1
    return marker, end


def _span(lines, start, end, prop, key_re):
    """(first, last+1) lines of property `prop` between start and end, or None."""
    for i in range(start, end):
        m = key_re.match(lines[i])
        if m and m.group(1) == prop:
            pi = _indent(lines[i])
            j = i + 1
            while j < end and (not lines[j].strip() or _indent(lines[j]) > pi):
                j += 1
            while j > i + 1 and not lines[j - 1].strip():
                j -= 1
            return i, j
    return None


def _top_prop_span(lines, prop):
    """(span, indent) of a screen-level property (Screens: / Name: / Properties: / key)."""
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith('  ') and not ln.startswith('   ') and ln.strip().endswith(':') and i > 0:
            start = i
            break
    if start is None:
        return None, 6
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith('    Children:'):
            end = i
            break
    indent = 6
    key_re = re.compile(r'^' + ' ' * indent + r'([A-Za-z0-9_.]+):')
    return _span(lines, start, end or len(lines), prop, key_re), indent


class App:
    def __init__(self, path):
        self.path = path
        self.map = screens(path)
        self._json = {}

    def doc(self, screen):
        if screen not in self._json:
            self._json[screen] = json.load(open(self.map[screen], encoding='utf-8'))
        return self._json[screen]

    def rule(self, screen, control, prop):
        tp = self.doc(screen)['TopParent']
        c = tp if control is None else find(tp, control)
        if c is None:
            sys.exit(f'! {screen}: control {control} not found')
        m = [r for r in c['Rules'] if r['Property'] == prop]
        return m[0]['InvariantScript'] if m else None

    def set(self, screen, control, prop, script, expect=None):
        """Write `script` to both representations. `expect` guards the old value."""
        tp = self.doc(screen)['TopParent']
        c = tp if control is None else find(tp, control)
        if c is None:
            sys.exit(f'! {screen}: control {control} not found')
        hit = [r for r in c['Rules'] if r['Property'] == prop]
        if not hit:
            sys.exit(f'! {screen}.{control}.{prop}: no such rule')
        if expect is not None and ' '.join(hit[0]['InvariantScript'].split()) != ' '.join(expect.split()):
            sys.exit(f'! {screen}.{control}.{prop} unexpected:\n  {hit[0]["InvariantScript"][:300]!r}')
        hit[0]['InvariantScript'] = script

        yf = os.path.join(self.path, 'Src', f'{screen}.pa.yaml')
        lines = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').replace('\r', '\n').split('\n')
        if control is None:
            span, indent = _top_prop_span(lines, prop)
            new = _fmt(prop, script, indent)
            if span is None:
                sys.exit(f'! {screen}.{prop} not in YAML top-level properties')
        else:
            b = _block(lines, control)
            if b is None:
                sys.exit(f'! {screen}: {control} not found in YAML')
            start, end, pi = b
            key_re = re.compile(r'^' + ' ' * pi + r'([A-Za-z0-9_.]+):')
            span = _span(lines, start, end, prop, key_re)
            new = _fmt(prop, script, pi)
            if span is None:
                at = end
                for i in range(start, end):
                    m = key_re.match(lines[i])
                    if m and m.group(1).split('.')[0] > prop:
                        at = i
                        break
                span = (at, at)
        lines[span[0]:span[1]] = new
        open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(lines))

    def save(self):
        for screen, doc in self._json.items():
            jwrite(doc, self.map[screen])
