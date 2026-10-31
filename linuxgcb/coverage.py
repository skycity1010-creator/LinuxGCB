"""可重建的逐項來源對照與涵蓋 manifest；不執行候選命令。"""
import json
from collections import Counter
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from .catalog import ROOT, registry, digest
from .batch1 import ADDED, caveat
from .quality import status
from .batch3 import ADDED as BATCH3, caveat as batch3_caveat, mechanism as batch3_mechanism, sources as batch3_sources
from .batch2 import ADDED as BATCH2, caveat as batch2_caveat

from .batch6 import ADDED as BATCH6, caveat as batch6_caveat, sources as batch6_sources

from .batch7 import ADDED as BATCH7, caveat as batch7_caveat, sources as batch7_sources

from .batch8 import ADDED as BATCH8, caveat as batch8_caveat, sources as batch8_sources

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
        historical=[]
        if n in BATCH8:
            method=batch8_sources()[n]['configuration_method']
            historical=[c for c in matches if c[-2] != method or c[-1] != row['expected']]
            matches=[c for c in matches if c[-2] == method and c[-1] == row['expected']]
        elif n in BATCH7:
            method=batch7_sources()[n]['configuration_method']
            historical=[c for c in matches if c[-2] != method or c[-1] != row['expected']]
            matches=[c for c in matches if c[-2] == method and c[-1] == row['expected']]
        elif n in BATCH6:
            method=batch6_sources()[n]['configuration_method']
            historical=[c for c in matches if c[-2] != method or c[-1] != row['expected']]
            matches=[c for c in matches if c[-2] == method and c[-1] == row['expected']]
        elif n in BATCH3:
            method=batch3_sources()[n]['configuration_method']
            historical=[c for c in matches if c[-2] != method or c[-1] != row['expected']]
            matches=[c for c in matches if c[-2] == method and c[-1] == row['expected']]
        elif n in BATCH2:
            historical=[c for c in matches if c[-1] != row['expected']]
            matches=[c for c in matches if c[-1] == row['expected']]
        if not matches or any(c[-2:] != matches[0][-2:] for c in matches) or row['expected'] not in matches[0]:
            raise ValueError('DOCX ID／期望欄無法唯一核對：'+row['gcb_id'])
        entries.append(dict(gcb_id=row['gcb_id'],sca_id=row['sca_id'],
            source_sheet=row['source_sheet'],source_row=row['source_row'],expected=row['expected'],
            docx_historical_cells=historical,docx_cells=matches[0],docx_occurrences=len(matches),docx_all_cells=matches,docx_sha256=digest(docx),
            mechanism=('P2B8 direct Python argv source predicates' if n in BATCH8 else 'P2B7 direct Python argv source predicates' if n in BATCH7 else 'P2B6 direct Python argv source predicates' if n in BATCH6 else batch3_mechanism(n) if n in BATCH3 else 'BATCH2 c: shell 成功輸出保護、正向/否定逐行 PCRE2、all 聚合' if n in BATCH2 else '原生 c: 絕對路徑、正向逐行 PCRE2、all 聚合；無 shell'),
            caveats=batch8_caveat(n) if n in BATCH8 else batch7_caveat(n) if n in BATCH7 else batch6_caveat(n) if n in BATCH6 else batch3_caveat(n) if n in BATCH3 else batch2_caveat(n) if n in BATCH2 else caveat(n) if n in ADDED else row['pending'],tests=[('tests/test_p2b8.py#' if n in BATCH8 else 'tests/test_p2b7.py#' if n in BATCH7 else 'tests/test_p2b6.py#' if n in BATCH6 else 'tests/fixtures/p2b3/cases.json#' if n in BATCH3 else 'tests/fixtures/rule_outputs.json#')+str(row['sca_id']), 'tests/test_p2b8.py' if n in BATCH8 else 'tests/test_p2b7.py' if n in BATCH7 else 'tests/test_p2b6.py' if n in BATCH6 else 'tests/test_p2b3.py' if n in BATCH3 else 'tests/test_batch2.py' if n in BATCH2 else 'tests/test_quality_q1.py'],
            cases=(['isolated_positive','isolated_negative','missing_no_commit','argv_roundtrip'] if n in BATCH6 | BATCH7 | BATCH8 else ['positive','negative','missing','empty','error','nonzero_matching'])+(['commented'] if n in BATCH3 and (148 <= n <= 173 or n==145) else [])+(['rpm_other_error'] if n in (92,96,99,100) else []),
            review_status='human_review_pending',**status(n)))
        if n in BATCH8 and 20 <= n <= 28:
            entries[-1]['cases'] += ['absence_review', 'conditional_negative']
    rows=registry();counts=Counter(r['implementation'] for r in rows)
    return dict(schema_version=2,label='離線候選涵蓋；非實機證據',
        counts=dict(source=len(rows),included=sum(r['included'] for r in rows),excluded=counts['excluded'],
                    before=7,batch8_before=236,batch8_added=46,batch8_after=282,added=len(BATCH8)+len(ADDED)+len(BATCH2)+len(BATCH3)+len(BATCH6)+len(BATCH7),batch7_before=188,batch7_added=48,batch7_after=236,batch6_before=146,batch6_added=42,batch6_after=188,batch3_added=len(BATCH3),batch3_before=97,batch3_after=97+len(BATCH3),batch2_added=len(BATCH2),implemented=counts['candidate'],remaining=counts['pending'],
                    full=sum(r['coverage']=='full' for r in rows),partial=sum(r['coverage']=='partial' for r in rows),
                    blocked=sum(r['coverage']=='blocked' for r in rows),reviewed=len(entries),execution_blocked=len(entries),live_validated=0),
        reviewed=entries)

def write():
    m=manifest()
    (ROOT/'data/coverage_manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    return m
