import sys,re
sys.path.insert(0,'ana')
from acc_model import *
def predict(tree):
    ctls=load(tree)
    tab=lambda c:(lambda v: v is None or not re.match(r'^\d+$',v.strip()))(c['rs'].get('TabIndex'))
    foc=lambda c:c['rs'].get('FocusedBorderThickness') is not None and c['rs'].get('FocusedBorderThickness').strip()=='0'
    lab=lambda c:(c['rs'].get('AccessibleLabel') in (None,'','""'))
    EXCL_TAB={'galleryTemplate','timer','checkbox'}
    res={}
    res['Missing tab stop']={k for k,c in ctls.items() if c['type'] not in EXCL_TAB and model(c,True) and tab(c) and not (c['type'] in ('attachments','datepicker','button','text','combobox','dropdown') and c['rs'].get('TabIndex') is None)}
    res['Focus not showing']={k for k,c in ctls.items() if model(c,True) and foc(c)}
    res['Missing accessible label']={k for k,c in ctls.items() if c['type'] not in ('label','button','timer','checkbox','galleryTemplate') and model(c,True) and lab(c)}
    return res,ctls
if __name__=='__main__':
    for t in sys.argv[1:]:
        r,c=predict(t); print(t.ljust(8),{k:len(v) for k,v in r.items()},'total',sum(len(v) for v in r.values()))
