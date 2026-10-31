"""合規值僅作文字；從來源抽取，絕不執行設定方法。"""
import json
import re
from .catalog import ROOT

PREFIX = '合規值: '
UNKNOWN = '待確認（來源未提供單一基準值）'


def source_expected(row):
    value = (row.get('expected') or '').strip()
    method = row.get('configuration_method') or ''
    if value == '安裝':
        match = re.search(r'#dnf install ([a-zA-Z0-9 -]+)', method)
        return match.group(1).strip()+' 已安裝' if match else UNKNOWN
    if value in ('啟用', '停用'):
        match = re.search(r'#systemctl --now (enable|disable|mask) ([a-zA-Z0-9_.-]+)', method)
        if not match:
            return UNKNOWN
        action, service = match.groups()
        return service+' '+{'enable': 'enabled+active', 'disable': 'disabled+inactive',
                              'mask': 'masked+inactive'}[action]
    if row['gcb_id'].endswith('0108'):
        return 'net.ipv4.ip_forward=0；net.ipv6.conf.all.forwarding=0'
    if row['gcb_id'].endswith('0269'):
        return 'PermitRootLogin '+value if value else UNKNOWN
    if row['gcb_id'].endswith('0270'):
        return 'PermitEmptyPasswords '+value if value else UNKNOWN
    return value or UNKNOWN


def values():
    return {r['gcb_id']: source_expected(r) for r in json.loads((ROOT/'data/controls.json').read_text())}


def parse_description(description):
    if not isinstance(description, str) or not description.startswith(PREFIX):
        return ''
    return description[len(PREFIX):].split(' ｜ ', 1)[0].strip()


def report_expected(raw, policy):
    """歷史匯出可用本地政策補充，明示其非掃描時證據。"""
    value = parse_description(raw.get('description'))
    if value:
        return value, 'raw_description'
    value = parse_description(policy.get('description'))
    if value:
        return value, 'policy_description_fallback; raw_prefix_missing'
    return '', 'prefix_missing'
