#!/usr/bin/env python3
"""Shared helpers for control work: cloning / swapping controls and mirroring the YAML.

Every new control is cloned from a real donor on an existing screen so it inherits
that screen's exact palette, font and radius rather than a fresh guess. The donor
also guarantees the control carries every key the package expects, including
"Children" -- a clone that lost it made an earlier package unopenable.
"""
import copy, json, os, re, sys
from jio import jwrite
from payaml import App, find, CTL_RE, _indent, block_span, _fmt

NEW = 'new'


def next_ids(path=NEW):
    """(ControlUniqueId, PublishOrderIndex) beyond anything in the package."""
    uids, pois = [], []
    for f in sorted(os.listdir(os.path.join(path, 'Controls'))):
        st = [json.load(open(os.path.join(path, 'Controls', f), encoding='utf-8'))['TopParent']]
        while st:
            c = st.pop()
            uids.append(int(c['ControlUniqueId']))
            pois.append(int(c['PublishOrderIndex']))
            st.extend(c.get('Children', []))
    return max(uids) + 1, max(pois) + 1


def _read_lines(path):
    return open(path, encoding='utf-8', newline='').read().replace('\r\n', '\n').replace('\r', '\n').split('\n')


def _donor_props(dlines, dname):
    """Donor YAML block -> (control_type_line_value, group_line, {prop: [lines at donor indent]}, donor marker indent)."""
    s, e = block_span(dlines, dname)
    mi = _indent(dlines[s])
    pi = mi + 6
    props, order, ctype, group = {}, [], None, None
    i = s + 1
    in_props = False
    while i < e:
        ln = dlines[i]
        ind = _indent(ln) if ln.strip() else 99
        if ln.strip() and ind == mi + 4:
            k = ln.strip()
            if k.startswith('Control:'): ctype = k
            elif k.startswith('Group:'): group = k
            elif k.startswith('Properties:'): in_props = True
            elif k.startswith('Children:'):
                break
            i += 1
            continue
        if in_props and ln.strip() and ind == pi:
            m = re.match(r'^\s*([A-Za-z0-9_.]+):', ln)
            key = m.group(1)
            j = i + 1
            while j < e and (not dlines[j].strip() or _indent(dlines[j]) > pi):
                j += 1
            while j > i + 1 and not dlines[j - 1].strip():
                j -= 1
            props[key] = dlines[i:j]
            order.append(key)
            i = j
            continue
        i += 1
    return ctype, group, props, order, mi


class Builder:
    """Clone / swap controls on a target screen, keeping JSON and YAML in step."""

    def __init__(self, app, screen):
        self.app, self.screen = app, screen
        self.doc = app.doc(screen)
        self.tp = self.doc['TopParent']
        self.uid, self.poi = next_ids(app.path)
        self.built = []

    def grouped(self, tp):
        g = set()
        for c in tp['Children']:
            if c.get('IsGroupControl'):
                g |= set(c.get('GroupedControlsKey') or [])
        return g

    # -- JSON ---------------------------------------------------------------------------------------------
    def _make(self, name, donor_screen, donor_name, overrides):
        dtp = self.app.doc(donor_screen)['TopParent']
        donor = find(dtp, donor_name)
        if donor is None:
            sys.exit(f'! donor {donor_screen}.{donor_name} not found')
        if donor_name in self.grouped(dtp):
            sys.exit(f'! donor {donor_name} is inside a group')
        c = copy.deepcopy(donor)
        missing = set(overrides) - {r['Property'] for r in c['Rules']}
        if missing:
            sys.exit(f'! {name}: donor {donor_name} lacks {sorted(missing)}')
        c['Name'] = name
        c['Children'] = []
        for p, v in overrides.items():
            [r for r in c['Rules'] if r['Property'] == p][0]['InvariantScript'] = v
        for e in c.get('ControlPropertyState', []):
            if isinstance(e, dict) and e.get('AutoRuleBindingString'):
                m = [r for r in c['Rules'] if r['Property'] == e['InvariantPropertyName']]
                if m:
                    e['AutoRuleBindingString'] = m[0]['InvariantScript']
        return donor, c

    def clone(self, name, donor_screen, donor_name, overrides, parent=None):
        """New direct child of the screen (parent=None) cloned from a donor."""
        if find(self.tp, name):
            sys.exit(f'! {name} already exists on {self.screen}')
        if parent is not None:
            sys.exit('! nested clone not supported here')
        donor, c = self._make(name, donor_screen, donor_name, overrides)
        c['ControlUniqueId'] = str(self.uid); self.uid += 1
        c['PublishOrderIndex'] = self.poi; self.poi += 1
        c['Index'] = 0
        c['Parent'] = self.screen
        self.tp['Children'].append(c)
        self.built.append(('clone', name, donor_screen, donor_name, overrides))
        return c

    def swap(self, name, donor_screen, donor_name, overrides, new_name=None):
        """Replace the control `name` in place (same parent and position) by a copy of a donor of another control type.
        Without new_name the control keeps its name and ids; with new_name the old control is deleted and a new one
        (new name, new ControlUniqueId) takes exactly its place."""
        old = find(self.tp, name)
        if old is None:
            sys.exit(f'! {name} not found on {self.screen}')
        if old.get('Children'):
            sys.exit(f'! {name} has children')
        if new_name and find(self.tp, new_name):
            sys.exit(f'! {new_name} already exists on {self.screen}')
        donor, c = self._make(new_name or name, donor_screen, donor_name, overrides)
        for k in ('PublishOrderIndex', 'Index', 'Parent'):
            c[k] = old[k]
        if new_name:
            c['ControlUniqueId'] = str(self.uid); self.uid += 1
        else:
            c['ControlUniqueId'] = old['ControlUniqueId']
        oz = [r['InvariantScript'] for r in old['Rules'] if r['Property'] == 'ZIndex']
        for r in c['Rules']:
            if r['Property'] == 'ZIndex' and oz:
                r['InvariantScript'] = oz[0]
        host = find(self.tp, old['Parent']) if old['Parent'] != self.screen else self.tp
        host['Children'] = [c if k['Name'] == name else k for k in host['Children']]
        self._new_name = getattr(self, '_new_name', {}); self._new_name[name] = new_name or name
        for g in self.tp['Children']:     # a group list keeps the name, nothing to change
            pass
        self.built.append(('swap', name, donor_screen, donor_name, overrides))
        return c

    # -- YAML ---------------------------------------------------------------------------------------------
    def save(self):
        self.app.save()
        yf = os.path.join(self.app.path, 'Src', f'{self.screen}.pa.yaml')
        for kind, name, dscreen, dname, overrides in self.built:
            lines = _read_lines(yf)
            dlines = lines if dscreen == self.screen else _read_lines(os.path.join(self.app.path, 'Src', f'{dscreen}.pa.yaml'))
            ctype, group, props, order, dmi = _donor_props(dlines, dname)
            out_name = getattr(self, '_new_name', {}).get(name, name) if kind == 'swap' else name
            if kind == 'swap':
                s, e = block_span(lines, name)
                mi = _indent(lines[s])
            else:
                mi = 6
                s = e = None
            pi = mi + 6
            for p, v in overrides.items():
                props[p] = _fmt(p, v, pi)
            out = [' ' * mi + f'- {out_name}:', ' ' * (mi + 4) + ctype]
            if group and kind == 'swap':
                pass  # a swapped control keeps no group line unless the old one had it (checked below)
            old_group = None
            if kind == 'swap':
                for ln in lines[s:e]:
                    if _indent(ln) == mi + 4 and ln.strip().startswith('Group:'):
                        old_group = ln.strip()
                        break
            if old_group:
                out.append(' ' * (mi + 4) + old_group)
            out.append(' ' * (mi + 4) + 'Properties:')
            for p in sorted(props):
                body = props[p]
                if p in overrides:
                    out.extend(body)
                else:
                    shift = pi - (dmi + 6)
                    out.extend((' ' * shift + ln if shift >= 0 else ln[-shift:]) if ln.strip() else ln for ln in body)
            out.append(' ' * (mi + 4) + 'Children: []')
            if kind == 'swap':
                lines[s:e] = out
            else:
                end = len(lines)
                while end and not lines[end - 1].strip():
                    end -= 1
                lines[end:end] = out
            open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
        self.built = []
