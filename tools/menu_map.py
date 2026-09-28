import json, os, re
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
def r(c, p):
    m = [x['InvariantScript'] for x in c['Rules'] if x['Property'] == p]; return m[0] if m else None
ROLES = ('panel', 'requests', 'dashboard', 'review', 'export', 'help')
def role(c):
    n, t = c['Name'], r(c, 'Text') or ''
    if re.search(r'NavPanel_MyRequestScreen', n): return 'panel'
    if 'NavBtnRequests_' in n: return 'requests'
    if 'NavBtnReview_' in n: return 'review'
    if 'NavBtnHelp_' in n: return 'help'
    if 'NavBtnDashboard_' in n:
        return 'export' if 'Export' in t else 'dashboard'
def menu(tp):
    out = {}
    for c in tp['Children']:
        k = role(c)
        if k:
            if k in out: raise SystemExit(f'! {tp["Name"]}: two {k} controls: {out[k]["Name"]}, {c["Name"]}')
            out[k] = c
    return out
