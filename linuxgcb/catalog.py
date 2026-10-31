"""固定來源、候選範圍與保守分類。"""
import hashlib
import json
from pathlib import Path
from scripts.inventory import extract
from .batch1 import ADDED
from .quality import status
from .batch3 import ADDED as BATCH3
from .batch6 import ADDED as BATCH6
from .batch8 import ADDED as BATCH8
from .batch7 import ADDED as BATCH7
from .batch2 import ADDED as BATCH2

ROOT = Path(__file__).resolve().parents[1]
XLSX_HASH = '7d752b639a1e780df08814c6252efadd3ea2711eaa5c9d91c070b84a296c0247'
DOCX_HASH = '986effd9501b1fd97776129c6691cf8fc98246bd04514347322f3337508e0e5b'
IMPLEMENTED = {45: 'base', 46: 'base', 108: 'base', 243: 'firewalld',
               245: 'firewalld', 269: 'sshd', 270: 'sshd'}
IMPLEMENTED.update({n: ('sshd' if n in (256,257) else 'firewalld' if n==242 else 'base') for n in ADDED})
IMPLEMENTED.update({n: ('sshd' if n >= 254 else 'base') for n in BATCH2})
IMPLEMENTED.update({n: 'base' for n in BATCH3})
IMPLEMENTED.update({n: 'base' for n in BATCH6})
IMPLEMENTED.update({n: 'base' for n in BATCH7})
IMPLEMENTED.update({n: 'base' for n in BATCH8})
PARTIAL = {141: '僅來源設定方法明列 audit.rules；其餘 rules.d 規則檔集合尚未覆蓋',
           108: '僅雙協定即時值；持久設定來源、覆寫順序與路由角色待審',
           269: '僅 sshd -T 預設情境；Include/Match 與使用者/來源矩陣待審',
           270: '僅 sshd -T 預設情境；Include/Match 與使用者/來源矩陣待審'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registry():
    source = next(ROOT.glob('*.xlsx'))
    docx = next(ROOT.glob('*.docx'))
    if digest(source) != XLSX_HASH or digest(docx) != DOCX_HASH:
        raise ValueError('來源 hash 改變，停止產生')
    records = extract(source)
    result = []
    for r in records:
        n = int(r['gcb_id'][-4:])
        included = r['sheet'] != 'Nftables防火牆'
        profile = ('firewalld' if r['sheet'] == 'Firewalld防火牆' else
                   'sshd' if r['sheet'] == 'SSH伺服器' else 'base')
        if n in IMPLEMENTED:
            classification, why = 'native_sca', '候選唯讀原生命令；完整語意與引擎驗收待人工審查'
        elif profile != 'base' or any(k in r['title'] for k in ('GUI', '無線', '可攜', 'NFS')):
            classification, why = 'conditional', '須先確認角色、服務與適用性，再選擇實作方式'
        elif any(k in r['title'] for k in ('權限', '所有權', '擁有', '稽核', '密碼', '通行碼')):
            classification, why = 'readonly_helper', '可能涉及集合、位元或載入鏈解析；尚未實作 helper'
        else:
            classification, why = 'manual_review', '尚未逐條語意審查，保守列人工待辦，非不可自動化結論'
        result.append(dict(gcb_id=r['gcb_id'], source_file=r['source_file'],
            source_sheet=r['sheet'], source_row=r['row'], source_sha256=XLSX_HASH,
            category=r['category'], title=r['title'], expected=r['expected'],
            included=included, scope_reason='候選，仍須主機適用性核准' if included else '明確排除 Nftables 工作表',
            sca_id=900000+n, profile=profile, proposed_classification=classification,
            justification=why, review_status='human_review_pending',
            implementation='candidate' if n in IMPLEMENTED else 'pending' if included else 'excluded',
            policy_id='linuxgcb_rhel9_'+IMPLEMENTED[n]+'_v01' if n in IMPLEMENTED else None,
            coverage='partial' if n in PARTIAL else 'full' if n in IMPLEMENTED else 'unimplemented',
            live_validation='UNVALIDATED', execution_review='pending',
            pending=PARTIAL.get(n, '' if n in IMPLEMENTED else '未實作；待逐條 DOCX 語意審查')))
        if n in IMPLEMENTED:
            result[-1].update(status(n))
    if (len(result), sum(r['included'] for r in result), len({r['sca_id'] for r in result}),
        len({r['gcb_id'] for r in result})) != (314, 307, 314, 314):
        raise ValueError('範圍或唯一性不符')
    return result


def write_registry():
    rows = registry()
    (ROOT/'data/scope_registry.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n')
    return rows
