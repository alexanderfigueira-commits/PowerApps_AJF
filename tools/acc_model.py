import json,re,glob,sys
from collections import Counter,defaultdict
def load(tree):
    ctls={}
    for f in glob.glob(tree+'/Controls/*.json'):
        dd=json.load(open(f,encoding='utf-8')); scr=dd['TopParent']['Name']
        def walk(n,anc=()):
            tpl=n.get('Template'); tn=tpl.get('Name') if isinstance(tpl,dict) else tpl
            rs={r['Property']:r['InvariantScript'] for r in n['Rules']}
            ctls[(scr,n['Name'])]=dict(type=tn,rs=rs,anc=anc,node=n)
            for c in n.get('Children',[]): walk(c,anc+((n['Name'],tn),))
        walk(dd['TopParent'])
    return ctls
def flagged(sarif):
    d=json.load(open(sarif,encoding='utf-8')); run=d['runs'][0]
    fl=defaultdict(set)
    for r in run['results']:
        if not r['ruleId'].startswith('acc-'): continue
        fq=r['locations'][0]['logicalLocations'][0]['fullyQualifiedName']
        parts=[p.strip("'") for p in re.findall(r"'[^']+'|[^.]+",fq)]
        fl[r['ruleId']].add((parts[0],parts[-2]))
    return fl
INPUT_TYPES={'button','text','combobox','dropdown','datepicker','attachments','checkbox','toggle','slider','radio','listbox','timer','htmlviewer'}
def onsel(c):
    s=c['rs'].get('OnSelect')
    return None if s is None else s.strip()
def interactive(c):
    t=c['type']
    if t in INPUT_TYPES: return True
    s=onsel(c)
    return bool(s) and s!='false' and s!='Select(Parent)' or (s=='false' and False)
def model(c, variant):
    """variant: how OnSelect=false counts"""
    t=c['type']; rs=c['rs']; s=onsel(c)
    if t in INPUT_TYPES or t=='gallery': inter=True
    elif s is None or s=='' : inter=False
    elif s=='Select(Parent)': inter=False
    elif s=='false': inter=variant
    else: inter=True
    return inter
if __name__=='__main__':
    tree,sarif=sys.argv[1],sys.argv[2]
    ctls=load(tree); fl=flagged(sarif)
    for variant in (True,):
        for rid,fn in (('acc-TabIndexShouldBeDefinedForInteractiveControl',lambda c:(lambda v: v is None or not re.match(r'^\d+$',v.strip()))(c['rs'].get('TabIndex'))),
                       ('acc-FocusBorderShouldBeVisible',lambda c:c['rs'].get('FocusedBorderThickness') is not None and c['rs'].get('FocusedBorderThickness').strip()=='0'),
                       ('acc-AccessibleLabelNeeded',lambda c:(c['rs'].get('AccessibleLabel') in (None,'','""')))):
            pred={k for k,c in ctls.items() if model(c,variant) and fn(c)}
            act=fl[rid]
            tp=len(pred&act); print(rid.split('-')[1][:28],'variant OnSelect=false interactive:',variant,'| predicted',len(pred),'actual',len(act),'both',tp,'| only predicted',len(pred-act),'only actual',len(act-pred))
            if len(pred-act)<15: print('   only predicted:',sorted((k[1],ctls[k]['type']) for k in pred-act)[:15])
            miss=sorted((k[1],ctls[k]['type'],ctls[k]['rs'].get('TabIndex'),(onsel(ctls[k]) or '')[:20]) for k in act-pred)
            print('   only actual sample:',miss[:12])
