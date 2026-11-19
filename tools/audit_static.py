import json,glob,re,collections,sys
D=sys.argv[1] if len(sys.argv)>1 else 'newG21'
scr={}
for f in glob.glob(D+'/Controls/*.json'):
    j=json.load(open(f,encoding='utf-8-sig')); scr[j['TopParent']['Name']]=j['TopParent']
def walk(c,par=None,path=()):
    yield c,par,path
    for k in c.get('Children',[]): yield from walk(k,c,path+(c['Name'],))
allc=[]  # (screen, ctl, parent, rules)
for s,t in scr.items():
    for c,p,pa in walk(t): allc.append((s,c,p))
def rules(c): return {r['Property']:r['InvariantScript'] for r in c['Rules']}
def strip(t):
    t=re.sub(r'(?m)^\s*//[^\n]*','',t); t=re.sub(r'//[^\n"]*$','',t,flags=re.M)
    return re.sub(r'"(?:[^"]|"")*"','""',t)
# ---- 1 variables
setv=collections.Counter(); readv=collections.defaultdict(set)
ctxset=set()
for s,c,p in allc:
    for prop,v in rules(c).items():
        sv=strip(v)
        for m in re.finditer(r'\bSet\(\s*([A-Za-z_]\w*)',sv): setv[m.group(1)]+=1
        for m in re.finditer(r'UpdateContext\(\s*\{(.*?)\}\s*\)',sv,flags=re.S):
            for mm in re.finditer(r'([A-Za-z_]\w*)\s*:',m.group(1)): ctxset.add((s,mm.group(1)))
        for m in re.finditer(r'\b(var[A-Z]\w*|loc[A-Z]\w*|col[A-Z]\w*)\b',sv): readv[m.group(1)].add((s,c['Name'],prop))
        # Navigate context records
        for m in re.finditer(r'Navigate\([^,]+,[^,]+,\s*\{(.*?)\}\s*\)',sv,flags=re.S):
            for mm in re.finditer(r'([A-Za-z_]\w*)\s*:',m.group(1)): ctxset.add(('*',mm.group(1)))
collset=set()
for s,c,p in allc:
    for prop,v in rules(c).items():
        for m in re.finditer(r'\b(?:Clear)?Collect\(\s*(col\w+)',v): collset.add(m.group(1))
ctxnames={n for _,n in ctxset}
print('== variables read but never Set (var*):')
for v in sorted(readv):
    if v.startswith('var') and setv[v]==0: print('  ',v,sorted(readv[v])[:3])
print('== loc* read but never defined via UpdateContext/Navigate:')
for v in sorted(readv):
    if v.startswith('loc') and v not in ctxnames: print('  ',v,sorted(readv[v])[:3])
print('== col* read but never collected:')
for v in sorted(readv):
    if v.startswith('col') and v not in collset: print('  ',v,sorted(readv[v])[:3])
print('== var Set but never read (info):')
print('  ',sorted(v for v in setv if v not in readv or all(1 for x in readv[v] if False)) [:0])
unread=[v for v in setv if not any(not re.search(r'\bSet\(\s*'+v+r'\b',strip(rules(c).get(prop,''))) or re.search(r'\b'+v+r'\b(?<!Set\()',strip(rules(c).get(prop,''))) and len(re.findall(r'\b'+v+r'\b',strip(rules(c).get(prop,''))))>len(re.findall(r'\bSet\(\s*'+v+r'\b',strip(rules(c).get(prop,'')))) for s,c,p in allc for prop in rules(c))]
print('   set-only variables:',sorted(unread))
# ---- 2 control name refs
names=collections.defaultdict(list)
for s,c,p in allc: names[c['Name']].append(s)
print('== duplicate control names:',{n:v for n,v in names.items() if len(v)>1})
prefs=set(re.match(r'([A-Za-z]+)_',n).group(1) for n in names if re.match(r'([A-Za-z]+)_',n))
allnames=set(names)|set(scr)
print('== references to control-like names that do not exist:')
seen=set()
for s,c,p in allc:
    for prop,v in rules(c).items():
        sv=strip(v)
        for m in re.finditer(r'\b([A-Z][A-Za-z0-9]*_[A-Za-z0-9_]+)\.(?:[A-Z]\w+)',sv):
            n=m.group(1)
            if n not in allnames and (s,c['Name'],n) not in seen:
                seen.add((s,c['Name'],n)); print('  ',s,c['Name'],prop,'->',n)
# ---- 3 text with +
print('== "+" used next to text:')
for s,c,p in allc:
    for prop,v in rules(c).items():
        t=re.sub(r'(?m)^\s*//[^\n]*','',v)
        if re.search(r'"\s*\+|\+\s*"',t): print('  ',s,c['Name'],prop)
# ---- 4 Patch keys vs schema
ds=json.load(open(D+'/References/DataSources.json',encoding='utf-8'))
cols={}
for x in ds['DataSources']:
    if x.get('DataEntityMetadataJson'):
        m=json.loads(list(x['DataEntityMetadataJson'].values())[0])
        mp=x.get('ConnectedDataSourceInfoNameMapping',{}); cols[x['Name']]=set(m['schema']['items']['properties'])|set(mp)|set(mp.values())
def balanced_record(t,i):
    d=0
    for j in range(i,len(t)):
        if t[j] in '({[': d+=1
        elif t[j] in ')}]': 
            d-=1
            if d==0: return j
    return None
def topkeys(rec):
    keys=[];d=0;i=0;s=strip(rec)
    # tokenise at depth 1
    body=s[1:-1]; d=0; cur=''
    out=[];
    for ch in body:
        if ch in '({[': d+=1
        if ch in ')}]': d-=1
        if ch==',' and d==0: out.append(cur);cur=''
        else: cur+=ch
    out.append(cur)
    for o in out:
        m=re.match(r"\s*([A-Za-z_'][\w' ]*?)\s*:",o)
        if m: keys.append(m.group(1).strip("'"))
    return keys
print('== Patch/Collect record fields not in the SharePoint schema:')
for s,c,p in allc:
    for prop,v in rules(c).items():
        t=re.sub(r'(?m)^\s*//[^\n]*','',v)
        for m in re.finditer(r"Patch\(\s*'(AV-CD-[A-Za-z]+|SuspensionDates)'",t):
            # find the third arg: the first '{' at depth 1 after the second top-level comma
            start=m.start(); end=balanced_record(t,t.index('(',start))
            seg=t[t.index('(',start)+1:end]; d=0;args=[];cur=''
            ss=re.sub(r'"(?:[^"]|"")*"',lambda mm:'"'+'x'*(len(mm.group(0))-2)+'"',seg)
            last=0
            for i,ch in enumerate(ss):
                if ch in '({[': d+=1
                elif ch in ')}]': d-=1
                elif ch==',' and d==0: args.append(seg[last:i]);last=i+1
            args.append(seg[last:])
            if len(args)>=3 and args[-1].strip().startswith('{'):
                for k in topkeys(args[-1].strip()):
                    if k not in cols.get(m.group(1),set()): print('  ',s,c['Name'],prop,m.group(1),'field',k)
