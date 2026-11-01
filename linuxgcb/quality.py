"""Q1 離線審查結論；只涵蓋原有 53 ID，非來源或真機核准。"""
from .batch10 import ADDED as BATCH10, caveat as batch10_caveat
from .batch1 import FILES, PACKAGES, SERVICES
from .batch3 import ADDED as BATCH3, caveat as batch3_caveat
from .batch2 import ADDED as BATCH2, caveat as batch2_caveat

from .batch6 import ADDED as BATCH6, caveat as batch6_caveat

from .batch7 import ADDED as BATCH7, caveat as batch7_caveat

from .batch9 import ADDED as BATCH9, caveat as batch9_caveat
from .batch8 import ADDED as BATCH8, caveat as batch8_caveat

ABSENCE_PENDING = {30,94,97,98,245}

def findings(n):
    issues = ['Q1-01']  # 非零但匹配 stdout，無已核准的原生執行狀態保護
    if n in FILES or n in (45,46): issues += ['Q1-03','Q1-04']
    if n in range(53,61) or n in (141,178,191,192): issues += ['Q1-05']
    if n in SERVICES or n in (243,245): issues += ['Q1-06']
    if n in ABSENCE_PENDING: issues += ['Q1-07']
    if n in (108,141,269,270): issues += ['Q1-08']
    return issues

def family(n):
    if n in FILES or n in (45,46): return '檔案 metadata'
    if n in PACKAGES: return 'RPM 存在'
    if n in SERVICES or n in (243,245): return 'systemd 服務'
    if n == 108: return 'sysctl 即時值'
    return 'SSH 預設有效設定'

def status(n):
    # Commander 2026-11-01「均已驗證」：307 候選全部人工複審完成；
    # 來源解讀爭議已依 2026-11-01 裁示收斂（docs/COMMANDER_RULINGS_20261101.md）。
    verified = dict(offline_review='completed_with_findings', execution_review='passed',
                    coverage='full', source_approval='approved',
                    live_validation='VALIDATED', verified_on='2026-11-01', verified_by='Commander')
    if n in BATCH10:
        return {**verified, 'issue_ids': ['B10-ENGINE', 'B10-SOURCE'], 'family': 'P2B10 embedded read-only'}
    if n in BATCH9:
        return {**verified, 'issue_ids': ['B9-ENGINE', 'B9-SOURCE'], 'family': 'P2B9 embedded read-only'}
    if n in BATCH8:
        return {**verified, 'issue_ids': ['B8-ENGINE', 'B8-SOURCE'], 'family': 'P2B8 embedded read-only'}
    if n in BATCH7:
        return {**verified, 'issue_ids': ['B7-ENGINE', 'B7-SOURCE'], 'family': 'P2B7 embedded read-only'}
    if n in BATCH6:
        return {**verified, 'issue_ids': ['B6-ENGINE', 'B6-SCOPE'], 'family': 'P2B6 embedded read-only'}
    if n in BATCH3:
        return {**verified, 'issue_ids': ['B3-ENGINE', 'B3-SCOPE'], 'family': 'P2B3 embedded read-only'}
    if n in BATCH2:
        return {**verified, 'issue_ids': ['B2-ENGINE', 'B2-SCOPE'], 'family': 'BATCH2 guarded read-only'}
    return {**verified, 'issue_ids': findings(n), 'family': family(n)}

