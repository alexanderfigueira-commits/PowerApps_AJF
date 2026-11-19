#!/usr/bin/env python3
"""Reads the unpacked canvas app (Controls/*.json) and turns each screen into a flat list of draw operations for a given scenario
(role, production type, ...). A small Power Fx evaluator resolves X/Y/Width/Height/Visible/Text/Fill/... with the scenario variables;
anything it cannot resolve is UNK and gets a safe default (visible, first branch, sample text)."""
import json, re, sys, os, glob

APP = sys.argv[1] if len(sys.argv) > 1 else '../newV46'

UNK = object()


# ---------------------------------------------------------------- tokenizer / parser
TOK = re.compile(r"""
 (?P<ws>\s+)
|(?P<lc>//[^\n]*)
|(?P<bc>/\*.*?\*/)
|(?P<str>"(?:[^"]|"")*")
|(?P<num>\d+(?:\.\d+)?)
|(?P<qid>'(?:[^']|'')*')
|(?P<op><>|<=|>=|&&|\|\||[=<>+\-*/&!(),;\[\]])
|(?P<id>[A-Za-z_][A-Za-z0-9_]*)
|(?P<dot>\.)
""", re.X | re.S)


def tokenize(s):
    out = []
    pos = 0
    while pos < len(s):
        m = TOK.match(s, pos)
        if not m:
            raise ValueError('tok ' + s[pos:pos + 20])
        pos = m.end()
        k = m.lastgroup
        if k in ('ws', 'lc', 'bc'):
            continue
        out.append((k, m.group()))
    return out


class P:
    def __init__(self, toks):
        self.t = toks
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def eat(self, v=None):
        k, x = self.peek()
        if v is not None and x != v:
            raise ValueError('expected ' + v + ' got ' + str(x))
        self.i += 1
        return k, x

    def parse(self):
        e = self.chain()
        return e

    def chain(self):
        # a ; b ; c  -> last value
        es = [self.expr()]
        while self.peek()[1] == ';':
            self.eat()
            if self.peek()[0] is None:
                break
            es.append(self.expr())
        return es[-1] if len(es) == 1 else ('seq', es)

    def expr(self):
        return self.or_()

    def or_(self):
        a = self.and_()
        while self.peek()[1] in ('||',) or (self.peek()[0] == 'id' and self.peek()[1] == 'Or'):
            self.eat()
            b = self.and_()
            a = ('or', [a, b])
        return a

    def and_(self):
        a = self.cmp()
        while self.peek()[1] in ('&&',) or (self.peek()[0] == 'id' and self.peek()[1] == 'And'):
            self.eat()
            b = self.cmp()
            a = ('and', [a, b])
        return a

    def cmp(self):
        a = self.cat()
        while self.peek()[1] in ('=', '<>', '<', '>', '<=', '>=') or (self.peek()[0] == 'id' and self.peek()[1] == 'in'):
            _, op = self.eat()
            b = self.cat()
            a = ('cmp', op, a, b)
        return a

    def cat(self):
        a = self.add()
        while self.peek()[1] == '&':
            self.eat()
            b = self.add()
            a = ('cat', a, b)
        return a

    def add(self):
        a = self.mul()
        while self.peek()[1] in ('+', '-'):
            _, op = self.eat()
            b = self.mul()
            a = ('bin', op, a, b)
        return a

    def mul(self):
        a = self.unary()
        while self.peek()[1] in ('*', '/'):
            _, op = self.eat()
            b = self.unary()
            a = ('bin', op, a, b)
        return a

    def unary(self):
        k, x = self.peek()
        if x == '!':
            self.eat()
            return ('not', self.unary())
        if x == '-':
            self.eat()
            return ('neg', self.unary())
        if k == 'id' and x == 'Not':
            self.eat()
            return ('not', self.unary())
        return self.atom()

    def atom(self):
        k, x = self.eat()
        if k == 'num':
            return ('lit', float(x))
        if k == 'str':
            return ('lit', x[1:-1].replace('""', '"'))
        if x == '(':
            e = self.chain()
            self.eat(')')
            return e
        if x == '[':
            items = []
            if self.peek()[1] != ']':
                items.append(self.expr())
                while self.peek()[1] == ',':
                    self.eat()
                    items.append(self.expr())
            self.eat(']')
            return ('list', items)
        if k in ('id', 'qid'):
            name = x[1:-1].replace("''", "'") if k == 'qid' else x
            # dotted path
            while self.peek()[1] == '.':
                self.eat()
                k2, y = self.eat()
                name += '.' + (y[1:-1] if k2 == 'qid' else y)
            if self.peek()[1] == '(':
                self.eat('(')
                args = []
                if self.peek()[1] != ')':
                    args.append(self.chain())
                    while self.peek()[1] == ',':
                        self.eat()
                        args.append(self.chain())
                self.eat(')')
                node = ('call', name, args)
                # field access on call result: User().FullName
                while self.peek()[1] == '.':
                    self.eat()
                    self.eat()
                    node = ('unk',)
                return node
            return ('ref', name)
        raise ValueError('atom ' + str(x))


# ---------------------------------------------------------------- evaluator
COLORS = {
    'White': (255, 255, 255, 1), 'Black': (0, 0, 0, 1), 'Red': (255, 0, 0, 1), 'LightGray': (211, 211, 211, 1), 'Gray': (128, 128, 128, 1),
    'DarkGreen': (0, 100, 0, 1), 'DarkKhaki': (189, 183, 107, 1), 'SlateBlue': (106, 90, 205, 1), 'DarkGoldenRod': (184, 134, 11, 1),
    'Transparent': (0, 0, 0, 0), 'Blue': (0, 0, 255, 1), 'Green': (0, 128, 0, 1), 'Orange': (255, 165, 0, 1), 'Yellow': (255, 255, 0, 1),
    'Silver': (192, 192, 192, 1), 'WhiteSmoke': (245, 245, 245, 1), 'DarkGray': (169, 169, 169, 1), 'Gold': (255, 215, 0, 1),
    'LightGreen': (144, 238, 144, 1), 'LightCoral': (240, 128, 128, 1), 'DarkRed': (139, 0, 0, 1), 'Crimson': (220, 20, 60, 1),
    'LightYellow': (255, 255, 224, 1), 'Khaki': (240, 230, 140, 1), 'DimGray': (105, 105, 105, 1),
}


class Ev:
    def __init__(self, env, geo):
        self.env = env      # scenario variables
        self.geo = geo      # callable(ctlname, prop) -> number or UNK
        self.stack = []

    def ev(self, n):
        t = n[0]
        if t == 'lit':
            return n[1]
        if t == 'unk':
            return UNK
        if t == 'list':
            return [self.ev(i) for i in n[1]]
        if t == 'seq':
            r = UNK
            for e in n[1]:
                r = self.ev(e)
            return r
        if t == 'ref':
            return self.ref(n[1])
        if t == 'not':
            v = self.ev(n[1])
            return UNK if v is UNK else (not self.truth(v))
        if t == 'neg':
            v = self.ev(n[1])
            return UNK if v is UNK or not isinstance(v, (int, float)) else -v
        if t == 'and':
            a, b = self.ev(n[1][0]), self.ev(n[1][1])
            if a is False or b is False:
                return False
            if a is UNK or b is UNK:
                return UNK
            return self.truth(a) and self.truth(b)
        if t == 'or':
            a, b = self.ev(n[1][0]), self.ev(n[1][1])
            if a is True or b is True:
                return True
            if a is UNK or b is UNK:
                return UNK
            return self.truth(a) or self.truth(b)
        if t == 'cmp':
            op = n[1]
            a, b = self.ev(n[2]), self.ev(n[3])
            if a is UNK or b is UNK:
                return UNK
            if op == 'in':
                if isinstance(b, list):
                    return a in b
                return str(a) in str(b)
            try:
                if op == '=':
                    return a == b
                if op == '<>':
                    return a != b
                if op == '<':
                    return a < b
                if op == '>':
                    return a > b
                if op == '<=':
                    return a <= b
                if op == '>=':
                    return a >= b
            except TypeError:
                return UNK
        if t == 'cat':
            a, b = self.ev(n[1]), self.ev(n[2])
            return self.s(a) + self.s(b)
        if t == 'bin':
            a, b = self.ev(n[2]), self.ev(n[3])
            if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) or isinstance(a, bool) or isinstance(b, bool):
                return UNK
            op = n[1]
            return a + b if op == '+' else a - b if op == '-' else a * b if op == '*' else (a / b if b else UNK)
        if t == 'call':
            return self.call(n[1], n[2])
        return UNK

    @staticmethod
    def truth(v):
        return bool(v)

    @staticmethod
    def s(v):
        if v is UNK or v is None or isinstance(v, bool):
            return ''
        if isinstance(v, float) and v == int(v):
            return str(int(v))
        return str(v)

    def ref(self, name):
        if name == 'true':
            return True
        if name == 'false':
            return False
        if name in self.env:
            return self.env[name]
        if name == 'Connection.Connected':
            return True
        if name in ('App.Width',):
            return 1366
        if name in ('App.Height',):
            return 768
        if name in ('App.MinScreenWidth', 'App.MinScreenHeight'):
            return 0
        if name.startswith('Color.'):
            return COLORS.get(name[6:], UNK)
        if name.startswith('FontWeight.') or name.startswith('Align.') or name.startswith('VerticalAlign.') or name.startswith('DisplayMode.') or name.startswith('Icon.') or name.startswith('Layout.'):
            return name
        if name == 'App.ActiveScreen':
            return self.env.get('__screen', UNK)
        if name in self.env.get('__screens', ()):
            return name
        m = re.match(r'^([A-Za-z0-9_]+)\.(X|Y|Width|Height)$', name)
        if m:
            return self.geo(m.group(1), m.group(2))
        if name.endswith('.AllItemsCount'):
            return 3
        if re.match(r'^(var|loc)[A-Za-z0-9_]+$', name):
            return False      # unknown flag: overlays and pop-ups stay closed
        return UNK

    def call(self, fn, args):
        f = fn
        if f == 'If':
            i = 0
            while i + 1 < len(args):
                c = self.ev(args[i])
                if c is UNK:
                    return self.ev(args[i + 1])   # unknown condition: first branch
                if c:
                    return self.ev(args[i + 1])
                i += 2
            return self.ev(args[i]) if i < len(args) else UNK
        if f in ('Coalesce',):
            for a in args:
                v = self.ev(a)
                if v is not UNK and v not in ('', None):
                    return v
            return UNK
        if f == 'IsBlank':
            v = self.ev(args[0])
            return UNK if v is UNK else v in ('', None)
        if f in ('IsEmpty',):
            return UNK
        if f in ('And', 'Or'):
            vs = [self.ev(a) for a in args]
            if f == 'And':
                if any(v is False for v in vs):
                    return False
                return UNK if any(v is UNK for v in vs) else True
            if any(v is True for v in vs):
                return True
            return UNK if any(v is UNK for v in vs) else False
        if f == 'Not':
            v = self.ev(args[0])
            return UNK if v is UNK else not v
        if f in ('Max', 'Min'):
            vs = [self.ev(a) for a in args]
            if any(not isinstance(v, (int, float)) for v in vs):
                return UNK
            return max(vs) if f == 'Max' else min(vs)
        if f in ('CountRows', 'CountIf', 'Sum', 'Count'):
            return 3
        if f == 'Text':
            v = self.ev(args[0])
            if v is UNK:
                return ''
            if len(args) > 1:
                fmt = self.ev(args[1])
                if isinstance(fmt, str) and ('yy' in fmt.lower() or 'mm' in fmt.lower() or 'hh' in fmt.lower()):
                    return '12/10/2026' if 'hh' not in fmt.lower() else '12/10/2026 09:30'
            return self.s(v)
        if f == 'Char':
            v = self.ev(args[0])
            return '\n' if v == 10 else '"' if v == 34 else ''
        if f in ('Left', 'Mid', 'Right', 'Trim', 'Lower', 'Upper', 'Concatenate', 'Substitute', 'Switch', 'LookUp', 'First', 'Filter', 'Concat', 'With'):
            if f == 'Switch':
                # Switch(expr, v1, r1, v2, r2, default): evaluate when decidable, else first result
                x = self.ev(args[0])
                i = 1
                while i + 1 < len(args):
                    v = self.ev(args[i])
                    if x is not UNK and v is not UNK and x == v:
                        return self.ev(args[i + 1])
                    i += 2
                if i < len(args):
                    return self.ev(args[i])
                return self.ev(args[2]) if len(args) > 2 else UNK
            if f == 'Lower':
                v = self.ev(args[0])
                return v.lower() if isinstance(v, str) else UNK
            if f == 'Trim':
                v = self.ev(args[0])
                return v.strip() if isinstance(v, str) else UNK
            return UNK
        if f == 'RGBA':
            v = [self.ev(a) for a in args]
            if len(v) == 4 and all(isinstance(x, (int, float)) for x in v):
                return (int(v[0]), int(v[1]), int(v[2]), v[3])
            return UNK
        if f == 'RGB':
            v = [self.ev(a) for a in args]
            if len(v) == 3 and all(isinstance(x, (int, float)) for x in v):
                return (int(v[0]), int(v[1]), int(v[2]), 1)
            return UNK
        if f == 'ColorValue':
            v = self.ev(args[0])
            if isinstance(v, str) and re.match(r'^#[0-9A-Fa-f]{6}$', v):
                return (int(v[1:3], 16), int(v[3:5], 16), int(v[5:7], 16), 1)
            return UNK
        if f in ('ColorFade',):
            c = self.ev(args[0])
            a = self.ev(args[1]) if len(args) > 1 else 0
            if isinstance(c, tuple) and isinstance(a, (int, float)):
                if a >= 0:
                    return tuple(int(c[i] + (255 - c[i]) * a) for i in range(3)) + (c[3],)
                return tuple(int(c[i] * (1 + a)) for i in range(3)) + (c[3],)
            return UNK
        if f in ('Today', 'Now'):
            return UNK
        if f in ('Len',):
            return UNK
        return UNK


# ---------------------------------------------------------------- tree
def load_screens():
    out = {}
    for fpath in sorted(glob.glob(os.path.join(APP, 'Controls', '*.json'))):
        j = json.load(open(fpath, encoding='utf-8-sig'))
        tp = j['TopParent']
        if tp['Name'] in ('App',):
            continue
        out[tp['Name']] = tp
    return out


def rules(n):
    return {r['Property']: r['InvariantScript'].replace('\r\n', '\n') for r in n.get('Rules', [])}


def ttype(n):
    t = n.get('Template')
    return t.get('Name') if isinstance(t, dict) else t


_cache = {}


def parse(src):
    if src in _cache:
        return _cache[src]
    try:
        r = P(tokenize(src)).parse()
    except Exception:
        r = ('unk',)
    _cache[src] = r
    return r


class Screen:
    def __init__(self, tp, env, all_screens):
        self.tp = tp
        self.env = dict(env)
        self.env['__screen'] = tp['Name']
        self.env['__screens'] = set(all_screens)
        self.byname = {}
        self.parent = {}

        def idx(n, p):
            self.byname[n['Name']] = n
            self.parent[n['Name']] = p
            for c in n.get('Children', []):
                idx(c, n)
        idx(tp, None)
        self._busy = set()
        self._geo = {}
        self.ev = Ev(self.env, self.geo)

    def prop(self, name, p):
        n = self.byname.get(name)
        if not n:
            return None
        r = rules(n).get(p)
        return r

    def geo(self, name, p):
        key = (name, p)
        if key in self._geo:
            return self._geo[key]
        if key in self._busy:
            return UNK
        self._busy.add(key)
        n = self.byname.get(name)
        v = UNK
        if n is not None:
            if ttype(n) == 'screen':
                v = 1366 if p == 'Width' else 768 if p == 'Height' else 0
            else:
                src = rules(n).get(p)
                if src is not None:
                    v = self.ev.ev(parse(src))
        self._busy.discard(key)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            v = UNK
        self._geo[key] = v
        return v

    def val(self, n, p):
        src = rules(n).get(p)
        if src is None:
            return None
        # resolve Self./Parent. against this control
        src = src.replace('Self.', n['Name'] + '.')
        return self.ev.ev(parse(src))


ROWSTAT = ['Draft', 'Processing', 'Pending', 'Approved', 'Rejected']

SAMPLE = [
    (r'List1RowBadge', '26-0144'),
    (r'RequestNumber|RowRequest|RequestID|MediaNumber|RowID|ReqNo', '26-0144'),
    (r'Title|Name|ProductionTitle', 'Sample production title'),
    (r'DG', 'COMM'),
    (r'Assignee|Contact|Author|Requestor|Owner|User', 'A. Surname'),
    (r'Status|Badge', 'Processing'),
    (r'Date|Submitted|Updated|Created|Modified|Time', '12/10/2026'),
    (r'Desc|Summary|Note|Message|Text|Body', 'Sample text'),
]


def sample_text(name, tpl):
    for pat, s in SAMPLE:
        if re.search(pat, name):
            return s
    return tpl


def num(v, d=0):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d


def color(v):
    if isinstance(v, tuple):
        return [v[0], v[1], v[2], round(float(v[3]), 3)]
    return None


def build(screen_name, tp, env, all_screens, variant_name):
    S = Screen(tp, env, all_screens)
    ops = []

    def emit(n, ox, oy, depth, row_i, in_gallery):
        t = ttype(n)
        r = rules(n)
        if t in ('timer', 'appinfo', 'hostControl', 'galleryTemplate', 'group', 'screen'):
            for c in sorted(n.get('Children', []), key=zkey):
                if t == 'screen' or t == 'group':
                    emit(c, ox, oy, depth, row_i, in_gallery)
            return
        vis = S.val(n, 'Visible') if 'Visible' in r else True
        if vis is False or vis == 0 and vis is not UNK and not isinstance(vis, str):
            return
        x, y = S.geo(n['Name'], 'X'), S.geo(n['Name'], 'Y')
        w, h = S.geo(n['Name'], 'Width'), S.geo(n['Name'], 'Height')
        if x is UNK or y is UNK:
            return
        if w is UNK:
            w = 100
        if h is UNK:
            h = 30
        ax, ay = ox + x, oy + y
        if t == 'gallery':
            tpl = S.val(n, 'TemplateSize')
            tpl = num(tpl, 60)
            pad = num(S.val(n, 'TemplatePadding'), 0)
            ops.append(['gal', round(ax), round(ay), round(w), round(h), n['Name']])
            nrows = max(1, min(4, int((h + pad) // (tpl + pad)) + (1 if (h + pad) % (tpl + pad) > 0 else 0)))
            kids = sorted(n.get('Children', []), key=zkey)
            sc = S.env.get('__scroll', {}).get(n['Name'], 0)
            if n['Name'] in ('CI_Gallery', 'CM_Gallery', 'CL_Gallery'):
                nrows = 1
            for i in range(nrows):
                S.env['ThisItem.Status.Value'] = ROWSTAT[i % len(ROWSTAT)]
                for c in kids:
                    emit(c, ax, ay + i * (tpl + pad) - sc, depth + 1, i, True)
            S.env.pop('ThisItem.Status.Value', None)
            return
        if t in ('form', 'typedDataCard'):
            for c in sorted(n.get('Children', []), key=zkey):
                emit(c, ax, ay, depth + 1, row_i, in_gallery)
            return
        fill = color(S.val(n, 'Fill')) if 'Fill' in r else None
        col = color(S.val(n, 'Color')) if 'Color' in r else None
        bcol = color(S.val(n, 'BorderColor')) if 'BorderColor' in r else None
        bth = num(S.val(n, 'BorderThickness'), 0) if 'BorderThickness' in r else 0
        rad = num(S.val(n, 'RadiusTopLeft'), 0) if 'RadiusTopLeft' in r else 0
        size = num(S.val(n, 'Size'), 11) if 'Size' in r else 11
        wt = S.val(n, 'FontWeight') if 'FontWeight' in r else None
        wtn = 'B' if wt == 'FontWeight.Bold' else 'S' if wt == 'FontWeight.Semibold' else 'R'
        al = S.val(n, 'Align') if 'Align' in r else None
        aln = 'C' if al == 'Align.Center' else 'R' if al == 'Align.Right' else 'L'
        va = S.val(n, 'VerticalAlign') if 'VerticalAlign' in r else None
        van = 'T' if va == 'VerticalAlign.Top' else 'B' if va == 'VerticalAlign.Bottom' else 'M'
        text = None
        if t in ('label', 'button', 'checkbox'):
            src = r.get('Text')
            if src is not None:
                tv = S.val(n, 'Text')
                text = tv if isinstance(tv, str) else ''
                lit = re.findall(r'"((?:[^"]|"")*)"', src)
                if (text == '' or text is None) and src.strip() not in ('""',):
                    text = sample_text(n['Name'], lit[0] if lit else '')
        if t in ('text', 'combobox', 'dropdown', 'datepicker'):
            hint = S.val(n, 'HintText') if 'HintText' in r else None
            dflt = S.val(n, 'Default') if 'Default' in r else None
            text = hint if isinstance(hint, str) and hint else (dflt if isinstance(dflt, str) else '')
        if text:
            text = re.sub(r'[\U0001F000-\U0001FFFF☀-➿️‍⬀-⯿■-◿]', '', text)
            text = text.replace('\r', '').strip()
            if len(text) > 160:
                text = text[:157] + '...'
        icon = S.val(n, 'Icon') if t == 'icon' else None
        ops.append([t, round(ax), round(ay), round(w), round(h), fill, col, bcol, bth, rad, text, size, wtn, aln, van, n['Name'], icon, row_i if in_gallery else -1])
        for c in sorted(n.get('Children', []), key=zkey):
            emit(c, ax, ay, depth + 1, row_i, in_gallery)

    def zkey(n):
        z = rules(n).get('ZIndex')
        try:
            return int(float(z))
        except Exception:
            return n.get('PublishOrderIndex', 0)

    emit(tp, 0, 0, 0, 0, False)
    # screen background
    sf = color(S.val(tp, 'Fill')) if 'Fill' in rules(tp) else None
    return {'screen': screen_name, 'variant': variant_name, 'fill': sf, 'ops': ops}


if __name__ == '__main__':
    screens = load_screens()
    print(sorted(screens))
