#!/usr/bin/env python3
"""Read XLSX with stdlib; preserve source cells and inventory GCB IDs."""
import collections
import hashlib
import json
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def extract(path):
    records = []
    with zipfile.ZipFile(path) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        rels = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        for sheet in wb.findall('s:sheets/s:sheet', NS):
            rid = sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            target = rels[rid]
            target = target.lstrip('/') if target.startswith('/') else 'xl/' + target
            for row in ET.fromstring(z.read(target)).findall('s:sheetData/s:row', NS):
                cells = {}
                for c in row.findall('s:c', NS):
                    match = re.match(r'[A-Z]+', c.attrib['r'])
                    if match is None:
                        raise ValueError('Invalid XLSX cell reference')
                    col = match.group()
                    v = c.find('s:v', NS)
                    value = (v.text or '') if v is not None else ''
                    if c.attrib.get('t') == 's':
                        value = strings[int(value)]
                    elif c.attrib.get('t') == 'inlineStr':
                        value = ''.join(t.text or '' for t in c.findall('.//s:t', NS))
                    cells[col] = value
                if re.fullmatch(r'TWGCB-\d{2}-\d{3}-\d{4}', cells.get('B', '')):
                    records.append(dict(source_file=path.name, sheet=sheet.attrib['name'], row=int(row.attrib['r']),
                        ordinal=cells.get('A'), gcb_id=cells['B'], category=cells.get('C'), title=cells.get('D'),
                        description=cells.get('E'), configuration_method=cells.get('F'), expected=cells.get('G'),
                        implementation_status='unreviewed'))
    return records

def main():
    sources = sorted(ROOT.glob('*.xlsx'))
    records = [r for p in sources for r in extract(p)]
    counts = collections.Counter(r['gcb_id'] for r in records)
    summary = dict(total=len(records), unique_ids=len(counts), duplicate_ids=[k for k,v in counts.items() if v>1],
        categories=dict(collections.Counter(r['category'] for r in records)),
        sheets=dict(collections.Counter(r['sheet'] for r in records)),
        missing_required=[r['gcb_id'] for r in records if not all(r.get(k) for k in ('title','category','expected'))],
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    out = ROOT/'data'
    out.mkdir(exist_ok=True)
    (out/'controls.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    (out/'inventory.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    assert records and not summary['duplicate_ids'] and not summary['missing_required']

if __name__ == '__main__':
    main()
