import zipfile, json, re, sys
from lxml import etree
z=zipfile.ZipFile('/home/user/PowerApps_AJF/flows/CentralDepositFlows_1_1_0_13.zip'); n=[x for x in z.namelist() if x.startswith('Workflows/')][0]
flow=json.loads(z.read(n)); main=flow['properties']['definition']['actions']['Scope_-_Main']['actions']
acts=main['If_phase']['actions']['If_docx_found']['actions']; lay=acts['If_layout_ok']['actions']
comps={k:v['inputs'] for k,v in {**acts, **lay}.items() if k.startswith('Compose') and isinstance(v.get('inputs'),str)}
def run(path):
    doc=etree.fromstring(zipfile.ZipFile(path).read('word/document.xml')); out={}
    for k,e in comps.items():
        m=re.match(r"@xpath\(outputs\('Compose_document'\), '(.*)'\)$",e)
        if m: out[k[8:]]=doc.xpath(m.group(1)); continue
        m=re.match(r"@greater\(xpath\(outputs\('Compose_document'\), '(.*)'\), 0\)$",e)
        if m: out[k[8:]]=doc.xpath(m.group(1))>0
    # layout check pieces
    return out
for f in sys.argv[1:]:
    o=run(f); print('=====',f)
    print({k:v for k,v in o.items() if v not in ('',False,0.0)})
