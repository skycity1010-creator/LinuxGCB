"""Q1 離線審查結論；只涵蓋原有 53 ID，非來源或真機核准。"""
from .batch1 import FILES, PACKAGES, SERVICES
from .batch3 import ADDED as BATCH3, caveat as batch3_caveat
from .batch2 import ADDED as BATCH2, caveat as batch2_caveat

from .batch6 import ADDED as BATCH6, caveat as batch6_caveat

from .batch7 import ADDED as BATCH7, caveat as batch7_caveat

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
    if n in BATCH7:
        return dict(offline_review='completed_with_findings', execution_review='blocked',
                    coverage='partial', issue_ids=['B7-ENGINE', 'B7-SOURCE'],
                    family='P2B7 embedded read-only', source_approval='pending',
                    live_validation='UNVALIDATED', pending=batch7_caveat(n))
    if n in BATCH6:
        return dict(offline_review="completed_with_findings", execution_review="blocked",
                    coverage="partial", issue_ids=["B6-ENGINE", "B6-SCOPE"],
                    family="P2B6 embedded read-only", source_approval="pending",
                    live_validation="UNVALIDATED", pending=batch6_caveat(n))
    if n in BATCH3:
        return dict(offline_review='completed_with_findings', execution_review='blocked',
                    coverage='partial', issue_ids=['B3-ENGINE', 'B3-SCOPE'],
                    family='P2B3 embedded read-only', source_approval='pending',
                    live_validation='UNVALIDATED', pending=batch3_caveat(n))
    if n in BATCH2:
        return dict(offline_review='completed_with_findings', execution_review='blocked',
                    coverage='partial', issue_ids=['B2-ENGINE', 'B2-SCOPE'],
                    family='BATCH2 guarded read-only', source_approval='pending',
                    live_validation='UNVALIDATED', pending=batch2_caveat(n))
    return dict(offline_review='completed_with_findings',
                execution_review='blocked',
                coverage='blocked' if n in ABSENCE_PENDING else 'partial',
                issue_ids=findings(n), family=family(n),
                source_approval='pending', live_validation='UNVALIDATED')
