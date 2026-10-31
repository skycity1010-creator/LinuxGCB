"""離線 Manager SQLite 匯出轉換；不推測掃描時間或補造證據。"""
import copy
import json
from datetime import datetime, timezone
from .catalog import ROOT, digest
from .collector import timestamp
from .expected import report_expected

LABEL = 'REAL EVIDENCE agent010／真實掃描證據（agent 010 / RHEL9 192.168.1.61）'


def scan_time(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.fromtimestamp(value, timezone.utc).isoformat()
    return timestamp(value).isoformat()


def convert(path, scan_info=None):
    """scan_info: {policy_id: {end_scan: UTC epoch 或含時區 ISO8601}}。

    scan_info 必須來自同次離線 DB 匯出，按 policy_id 對應，絕不以 hash join scan_id。
    """
    from pathlib import Path
    path = Path(path)
    dump = json.loads(path.read_text())
    policies = {}
    for p in sorted((ROOT/'policies').glob('*.yml')):
        policy = json.loads(p.read_text())
        policies[policy['policy']['id']] = {c['id']: c for c in policy['checks']}
    if not isinstance(dump, dict) or not dump or not set(dump) <= set(policies):
        raise ValueError('未知或空白 policy 匯出')
    checks, scans, times, warnings, seen = [], {}, [], [], set()
    for pid, data in dump.items():
        scans[pid] = data['scan_id']
        info = (scan_info or {}).get(pid, data.get('sca_scan_info', {}))
        end = info.get('end_scan')
        if end is None:
            warnings.append(pid+': 缺少 sca_scan_info.end_scan；scanned_at 不推造')
        else:
            times.append(scan_time(end))
        for c in data['checks']:
            sid = c['id']
            if not isinstance(sid, int) or isinstance(sid, bool) or sid not in policies[pid] or sid in seen:
                raise ValueError('未知、重複或錯誤 policy 的 check ID')
            if 'result' not in c:
                raise ValueError('check 缺少 result')
            seen.add(sid)
            check = copy.deepcopy(c)
            check['policy_id'] = pid
            check['expected'], check['expected_status'] = report_expected(c, policies[pid][sid])
            checks.append(check)
    return dict(schema_version=1, synthetic=False, label=LABEL,
        source_sha256=digest(next(ROOT.glob('*.xlsx'))),
        policy_hashes={p.name: digest(p) for p in sorted((ROOT/'policies').glob('*.yml'))},
        manager_dump_sha256=digest(path), scan_info=copy.deepcopy(scan_info), warnings=warnings,
        hosts=[dict(agent_id='010', approved_profiles=['base','firewalld','sshd'],
                    scanned_at=min(times) if len(times)==len(dump) else None,
                    policy_scanned_at={pid: scan_time((scan_info or {}).get(pid, dump[pid].get('sca_scan_info', {}))['end_scan'])
                                       for pid in dump if (scan_info or {}).get(pid, dump[pid].get('sca_scan_info', {})).get('end_scan') is not None},
                    scan_ids=scans, checks=checks)])
