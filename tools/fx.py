import re
TOK = re.compile(r'\s*(?:(\d+(?:\.\d+)?)|"((?:[^"]|"")*)"|(<>|<=|>=|[-+*/(),=<>&])|([A-Za-z_][A-Za-z0-9_.\']*))')
def tokens(s):
    s = re.sub(r'//[^\n]*', '', s); i = 0; out = []
    while i < len(s):
        if s[i:].strip() == '': break
        m = TOK.match(s, i)
        if not m: raise ValueError('tok ' + s[i:i+20])
        i = m.end()
        if m.group(1): out.append(('n', float(m.group(1))))
        elif m.group(2) is not None: out.append(('s', m.group(2).replace('""', '"')))
        elif m.group(3): out.append(('o', m.group(3)))
        else: out.append(('i', m.group(4)))
    return out
class P:
    def __init__(s, toks, env): s.t, s.p, s.env = toks, 0, env
    def peek(s): return s.t[s.p] if s.p < len(s.t) else (None, None)
    def nxt(s): x = s.peek(); s.p += 1; return x
    def expr(s): return s.orx()
    def orx(s):
        v = s.andx()
        while s.peek() == ('i', 'Or'): s.nxt(); r = s.andx(); v = bool(v) or bool(r)
        return v
    def andx(s):
        v = s.cmp()
        while s.peek() == ('i', 'And'): s.nxt(); r = s.cmp(); v = bool(v) and bool(r)
        return v
    def cmp(s):
        v = s.add()
        while s.peek()[0] == 'o' and s.peek()[1] in ('=', '<>', '<', '>', '<=', '>='):
            op = s.nxt()[1]; r = s.add()
            v = {'=': v == r, '<>': v != r, '<': (v or 0) < (r or 0), '>': (v or 0) > (r or 0), '<=': (v or 0) <= (r or 0), '>=': (v or 0) >= (r or 0)}[op]
        return v
    def add(s):
        v = s.mul()
        while s.peek()[0] == 'o' and s.peek()[1] in ('+', '-', '&'):
            op = s.nxt()[1]; r = s.mul()
            v = (str(v) + str(r)) if op == '&' else ((v or 0) + (r or 0) if op == '+' else (v or 0) - (r or 0))
        return v
    def mul(s):
        v = s.atom()
        while s.peek()[0] == 'o' and s.peek()[1] in ('*', '/'):
            op = s.nxt()[1]; r = s.atom(); v = (v or 0) * (r or 0) if op == '*' else (v or 0) / (r or 1)
        return v
    def atom(s):
        k, v = s.nxt()
        if k in ('n', 's'): return v
        if k == 'o' and v == '(':
            r = s.expr(); s.nxt(); return r
        if k == 'o' and v == '-': return -s.atom()
        if k == 'i':
            if v == 'true': return True
            if v == 'false': return False
            if v == 'Not':
                s.nxt(); r = s.expr(); s.nxt(); return not r
            if s.peek() == ('o', '('):
                s.nxt(); args = []
                # evaluate lazily for If/Switch: parse all args (side-effect free)
                if s.peek() != ('o', ')'):
                    while True:
                        args.append(s.expr())
                        if s.peek() == ('o', ','): s.nxt(); continue
                        break
                s.nxt()
                if v == 'If':
                    i = 0
                    while i + 1 < len(args):
                        if args[i]: return args[i + 1]
                        i += 2
                    return args[i] if i < len(args) else None
                if v == 'Switch':
                    x = args[0]; i = 1
                    while i + 1 < len(args):
                        if args[i] == x: return args[i + 1]
                        i += 2
                    return args[i] if i < len(args) else None
                if v == 'Coalesce':
                    for a in args:
                        if a not in (None, ''): return a
                    return None
                return None
            return s.env.get(v)
        raise ValueError('atom')
def ev(src, env):
    try:
        p = P(tokens(src), env); r = p.expr(); return r
    except Exception as e:
        return ('ERR', str(e)[:30])
