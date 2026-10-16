"""Proof of the reading technique: the same XPath 1.0 expressions would run in Power Automate (xpath(xml(...), ...)).
1) fill a copy of each template the way a person would (text in the value cell, tick Word checkboxes)  2) read it back with XPath only."""
import zipfile, shutil, sys, re, json
from lxml import etree  # pip install lxml
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main', 'w14': 'http://schemas.microsoft.com/office/word/2010/wordml'}
W = '{%s}' % NS['w']
def row_xp(label, exact): 
    cond = f"normalize-space(*[local-name()='tc'][1])='{label}'" if exact else f"starts-with(normalize-space(*[local-name()='tc'][1]),'{label}')"
    return f"//*[local-name()='tr'][{cond}]"
def value(doc, label, exact=True):
    return doc.xpath(f"normalize-space(string({row_xp(label, exact)}/*[local-name()='tc'][2]))")
def ticks(doc, label, exact=False):
    return doc.xpath(f"{row_xp(label, exact)}/*[local-name()='tc'][2]//*[local-name()='checked']/@*[local-name()='val']")
# ---------- fill (simulates the person)
def fill(src, dst, texts, tick):
    z = zipfile.ZipFile(src); root = etree.fromstring(z.read('word/document.xml'))
    for tr in root.iter(W + 'tr'):
        tcs = tr.findall(W + 't' + 'c')
        if len(tcs) < 2: continue
        label = ''.join(t.text or '' for t in tcs[0].iter(W + 't')).strip()
        for k, v in texts.items():
            if label == k or (len(k) > 12 and label.startswith(k)):
                p = tcs[1].find(W + 'p'); r = etree.SubElement(p, W + 'r'); t = etree.SubElement(r, W + 't'); t.text = v
        for k, idxs in tick.items():
            if label.startswith(k):
                boxes = list(tcs[1].iter('{%s}checked' % NS['w14']))
                for i in idxs: boxes[i].set('{%s}val' % NS['w14'], '1')
    zo = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)
    for i in z.infolist(): zo.writestr(i, etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True) if i.filename == 'word/document.xml' else z.read(i))
    zo.close()
fill('templates/video.docx', 'video_filled.docx', {'Title': 'Opening ceremony 2026', 'Description/Summary': 'Short clip of the opening.', 'Production place': 'Brussels', 'Filming': '2026-03-02',
     'Producer (contracting authority)': 'DG COMM', 'Pertinent tags': 'ceremony; opening'}, {'Case 1': [0, 1], 'Model release forms': [0]})
fill('templates/podcast.docx', 'podcast_filled.docx', {'Title of the podcast': 'Voices of Europe', 'Season and/or Episode number': 'S1 / E1', 'Title of the Episode': 'Pilot', 'Recording': '2026-02-10'}, {'Case 2': [0], 'Podcast visual': [0]})
# ---------- read back with XPath only (what the flow does)
def read(path):
    doc = etree.fromstring(zipfile.ZipFile(path).read('word/document.xml'))
    heading = doc.xpath("normalize-space(string(//*[local-name()='p'][contains(.,'Mandatory Metadata')]))")
    kind = 'Photo' if 'for Photos' in heading else 'Podcast' if 'for Podcast' in heading else 'Video'
    out = {'type': kind}
    labels = {'Photo': ['Title of reportage', 'Description of the reportage', 'Shooting date', 'Place where the photo has been taken', 'Name of the photographer', 'Pertinent tags'],
              'Podcast': ['Title of the podcast', 'Season and/or Episode number', 'Title of the Episode', 'Recording', 'Pertinent tags'],
              'Video': ['Title', 'Description/Summary', 'Filming', 'Production place', 'Producer (contracting authority)', 'Pertinent tags']}[kind]
    for l in labels: out[l] = value(doc, l)
    out['cases'] = {c: ticks(doc, c) for c in ('Case 1', 'Case 2', 'Model release forms')}
    return out
for f in ('video_filled.docx', 'podcast_filled.docx', 'templates/photo.docx'): print(f, json.dumps(read(f), ensure_ascii=False))
