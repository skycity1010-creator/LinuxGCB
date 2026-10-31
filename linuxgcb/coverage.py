"""可重建的逐項來源對照與涵蓋 manifest；不執行候選命令。"""
import json
from collections import Counter
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from .catalog import ROOT, registry, digest
from .batch1 import ADDED, caveat
from .quality import status

def manifest():
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    docx=next(ROOT.glob('*.docx'))
    xml=ET.fromstring(ZipFile(docx).read('word/document.xml'))
    # ID 的 runs 必須在段落內接回，cell 再以換行串接段落。
    tables=[]
    for tr in xml.findall('.//w:tr',ns):
        cells=['\n'.join(''.join(t.text or '' for t in p.findall('.//w:t',ns))
                         for p in cell.findall('.//w:p',ns)) for cell in tr.findall('w:tc',ns)]
        tables.append(cells)
    entries=[]
    for row in registry():
        n=row['sca_id']-900000
        if row['implementation'] != 'candidate': continue
        matches=[c for c in tables if row['gcb_id'] in c]
        if not matches or any(c[-2:] != matches[0][-2:] for c in matches) or row['expected'] not in matches[0]:
            raise ValueError('DOCX ID／期望欄無法唯一核對：'+row['gcb_id'])
        entries.append(dict(gcb_id=row['gcb_id'],sca_id=row['sca_id'],
            source_sheet=row['source_sheet'],source_row=row['source_row'],expected=row['expected'],
            docx_cells=matches[0],docx_occurrences=len(matches),docx_all_cells=matches,docx_sha256=digest(docx),
            mechanism='原生 c: 絕對路徑、正向逐行 PCRE2、all 聚合；無 shell',
            caveats=caveat(n) if n in ADDED else row['pending'],tests=['tests/fixtures/rule_outputs.json#'+str(row['sca_id']), 'tests/test_quality_q1.py'],
            cases=['positive','negative','missing','empty','error','nonzero_matching'],
            review_status='human_review_pending',**status(n)))
    rows=registry();counts=Counter(r['implementation'] for r in rows)
    return dict(schema_version=2,label='離線候選涵蓋；非實機證據',
        counts=dict(source=len(rows),included=sum(r['included'] for r in rows),excluded=counts['excluded'],
                    before=7,added=len(ADDED),implemented=counts['candidate'],remaining=counts['pending'],
                    full=sum(r['coverage']=='full' for r in rows),partial=sum(r['coverage']=='partial' for r in rows),
                    blocked=sum(r['coverage']=='blocked' for r in rows),reviewed=len(entries),execution_blocked=len(entries),live_validated=0),
        reviewed=entries)

def write():
    m=manifest()
    (ROOT/'data/coverage_manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    return m
