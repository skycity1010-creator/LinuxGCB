"""離線正規化與完整母體報表；不把原生 N/A 當成核准不適用。"""
import csv
import html
import json
from collections import Counter
from pathlib import Path
from .catalog import registry, ROOT, XLSX_HASH
from .collector import timestamp

STATES = {'PASS', 'FAIL', 'ERROR', 'NOT_APPLICABLE', 'MANUAL_PENDING', 'NOT_SCANNED', 'EXCLUDED'}


def approval(value, now):
    return (isinstance(value, dict) and all(value.get(k) for k in ('approver','reason','ticket','evidence','expires'))
            and timestamp(value['expires']) > now)


def normalize(snapshot, now):
    """只接受明確離線契約；全部 314 項逐主機保留，未核准 profile 不消失。"""
    if snapshot.get('schema_version') != 1 or not isinstance(snapshot.get('hosts'), list):
        raise ValueError('不支援的離線快照 schema')
    if snapshot.get('source_sha256') != XLSX_HASH:
        raise ValueError('來源 hash 不符')
    if snapshot.get('policy_hashes') != json.loads((ROOT/'data/policy_hashes.json').read_text()):
        raise ValueError('政策 hash 不符')
    policy_checks = {}
    for path in (ROOT/'policies').glob('*.yml'):
        policy_checks.update({c['id']: c for c in json.loads(path.read_text())['checks']})
    all_rows, host_ids = [], set()
    for host in snapshot['hosts']:
        agent = host['agent_id']
        if not isinstance(agent, str) or not agent or agent in host_ids:
            raise ValueError('主機 ID 空白或重複')
        host_ids.add(agent)
        profiles = host.get('approved_profiles', [])
        if not isinstance(profiles, list) or not set(profiles) <= {'base','firewalld','sshd'}:
            raise ValueError('未知 profile')
        raw = {}
        known = {r['sca_id']:r for r in registry()}
        for check in host.get('checks', []):
            sid = check['id']
            if not isinstance(sid, int) or sid not in known or sid in raw:
                raise ValueError('未知或重複 SCA-ID')
            if known[sid]['implementation'] != 'candidate':
                raise ValueError('回傳未實作控制項；拒絕冒用政策結果')
            raw[sid] = check
        scanned_at = host.get('scanned_at')
        stale = scanned_at is None or (now-timestamp(scanned_at)).total_seconds() > 86400
        if scanned_at and timestamp(scanned_at) > now:
            raise ValueError('掃描時間在未來')
        for control in known.values():
            c = raw.get(control['sca_id'], {})
            raw_result, reason = c.get('result'), c.get('reason', '')
            evidence_status = c.get('evidence_status')
            if evidence_status not in (None, 'missing', 'absence_unverified', 'symlink_unresolved', 'tool_error', 'permission_error', 'timeout'):
                raise ValueError('未知 evidence_status')
            unresolved = control['included'] and control['profile'] not in profiles
            na = host.get('not_applicable', {}).get(control['gcb_id'])
            exception = host.get('exceptions', {}).get(control['gcb_id'])
            approved_na = approval(na, now)
            if not control['included']:
                state = 'EXCLUDED'
            elif c.get('execution_error') or raw_result == 'error' or evidence_status in ('tool_error','permission_error','timeout'):
                state = 'ERROR'
            elif evidence_status in ('missing','absence_unverified','symlink_unresolved'):
                state = 'NOT_APPLICABLE' if approved_na else 'MANUAL_PENDING'
            elif raw_result == 'failed':
                state = 'FAIL'
            elif raw_result not in (None, 'passed', 'not applicable', 'not_applicable'):
                state = 'ERROR'
            elif approved_na:
                state = 'NOT_APPLICABLE'
            elif raw_result in ('not applicable', 'not_applicable'):
                state = 'ERROR'
            elif raw_result == 'passed' and (control['execution_review'] != 'passed' or control['coverage'] != 'full'):
                state = 'MANUAL_PENDING'
            elif unresolved or control['implementation'] == 'pending' or control['pending']:
                state = 'MANUAL_PENDING'
            elif raw_result == 'passed':
                state = 'PASS'
            elif raw_result is not None:
                state = 'ERROR'
            else:
                state = 'NOT_SCANNED'
            all_rows.append(dict(agent_id=agent, gcb_id=control['gcb_id'], sca_id=control['sca_id'],
                command=c.get('command', ','.join(r.split(' -> r:')[0][2:] for r in policy_checks.get(control['sca_id'], {}).get('rules', []))),
                remediation=policy_checks.get(control['sca_id'], {}).get('remediation'),
                raw_remediation=c.get('remediation'),
                remediation_status='provided' if policy_checks.get(control['sca_id'], {}).get('remediation') else '政策未提供 remediation',
                category=control['category'], title=control['title'], expected=control['expected'],
                policy_id=control['policy_id'], policy_hash=snapshot['policy_hashes'].get('linuxgcb_'+control['profile']+'.yml'),
                source_sha256=control['source_sha256'],
                state=state, raw_result=raw_result, raw_reason=reason, evidence_status=evidence_status,
                coverage=control['coverage'], execution_review=control['execution_review'],
                verified_compliance=state in ('PASS','FAIL') and control['coverage']=='full' and control['execution_review']=='passed',
                pending=control['pending'], unresolved=unresolved and not approved_na,
                exception_approved=approval(exception, now), exception=exception, na_approval=na,
                stale=stale, scanned_at=scanned_at, synthetic=snapshot.get('synthetic', False)))
    return all_rows


def metrics(rows):
    counts = Counter(r['state'] for r in rows)
    applicable = sum(v for k,v in counts.items() if k not in ('EXCLUDED','NOT_APPLICABLE'))
    decided = sum(r['verified_compliance'] for r in rows)
    verified_pass = sum(r['verified_compliance'] and r['state']=='PASS' for r in rows)
    def pct(n,d):
        return round(100*n/d, 2) if d else None
    return dict(counts=dict(counts), expected=len(rows), applicable=applicable,
                unresolved=sum(r['unresolved'] for r in rows),
                raw_observed=sum(r['raw_result'] is not None for r in rows), verified_decided=decided,
                pass_rate=pct(verified_pass, decided),
                attainment=pct(verified_pass, applicable), completeness=pct(decided, applicable))


def safe_cell(value):
    text = '' if value is None else str(value)
    # Excel 可忽略前導空白/控制字元；CSV 所有文字欄位都經此處理。
    probe = text
    while probe and (probe[0].isspace() or ord(probe[0]) < 32 or probe[0] == '\ufeff'):
        probe = probe[1:]
    if probe.startswith(('=', '+', '-', '@')) or (text and ord(text[0]) < 32):
        return "'"+text
    return text


def render(snapshot, output, now):
    rows = normalize(snapshot, now)
    summary = metrics(rows)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ['agent_id','gcb_id','state']
    with (out/'report.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for r in rows:
            writer.writerow([safe_cell(json.dumps(r[k], ensure_ascii=False) if isinstance(r[k], dict) else r[k]) for k in fields])
    esc = lambda x: html.escape('' if x is None else str(x), quote=True)
    page = '<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>LinuxGCB 離線報表</title>'
    page += '<h1>LinuxGCB 離線候選結果</h1><p>'+('SYNTHETIC／僅供測試，非真實掃描證據' if snapshot.get('synthetic') else '未完成 RHEL9 真機驗收；請核對原始快照與政策版本')+'</p>'
    page += '<p>'+esc(snapshot.get('label', ''))+'</p>'
    page += '<p>'+esc('; '.join(snapshot.get('warnings', [])))+'</p>'
    page += '<p>raw_result 是原始輸出；FAIL 可為候選失敗觀察。完整率只計 verified_compliance，部分／阻擋控制不計完整判定。None 表示 N/A；核准例外不改寫 FAIL。UNVALIDATED 政策結果不代表完整符合性。</p>'
    page += '<pre>'+esc(json.dumps(summary, ensure_ascii=False, indent=2))+'</pre><table><thead><tr>'
    page += ''.join('<th>'+esc(k)+'</th>' for k in fields)+'</tr></thead><tbody>'
    for r in rows:
        page += '<tr>'+''.join('<td>'+esc(r[k])+'</td>' for k in fields)+'</tr>'
    page += '</tbody></table></html>'
    (out/'report.html').write_text(page, encoding='utf-8')
    (out/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    # 原始值不經公式處理；保留匯入內容以利稽核，勿以試算表開啟此 JSON。
    (out/'snapshot.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2)+'\n')
    return summary
