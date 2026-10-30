"""以 JSON（YAML 1.2 子集）產生候選 SCA；只模擬輸出匹配，不執行命令。"""
import json
import re
from .catalog import ROOT, registry, digest
from .batch1 import rules as batch_rules


def definitions():
    modes = '|'.join(format(n, 'o') for n in range(0o1000) if n & ~0o644 == 0)
    return {**batch_rules(),
        45: [('c:/usr/bin/stat -c %u:%g /etc/passwd', '^0:0$')],
        46: [('c:/usr/bin/stat -c %a /etc/passwd', '^('+modes+')$')],
        108: [('c:/usr/sbin/sysctl -n net.ipv4.ip_forward', '^0$'),
              ('c:/usr/sbin/sysctl -n net.ipv6.conf.all.forwarding', '^0$')],
        243: [('c:/usr/bin/systemctl show firewalld.service --property=LoadState', '^LoadState=loaded$'),
              ('c:/usr/bin/systemctl show firewalld.service --property=ActiveState', '^ActiveState=active$'),
              ('c:/usr/bin/systemctl show firewalld.service --property=UnitFileState', '^UnitFileState=enabled$')],
        245: [('c:/usr/bin/systemctl show nftables.service --property=LoadState', '^LoadState=masked$'),
              ('c:/usr/bin/systemctl show nftables.service --property=ActiveState', '^ActiveState=inactive$'),
              ('c:/usr/bin/systemctl show nftables.service --property=UnitFileState', '^UnitFileState=masked$')],
        269: [('c:/usr/sbin/sshd -T', '^permitrootlogin no$')],
        270: [('c:/usr/sbin/sshd -T', '^permitemptypasswords no$')],
    }


def build():
    rows = registry()
    for profile in ('base', 'firewalld', 'sshd'):
        filename = 'linuxgcb_'+profile+'.yml'
        checks = []
        for row in rows:
            if row['implementation'] != 'candidate' or row['profile'] != profile:
                continue
            checks.append(dict(id=row['sca_id'], title=row['gcb_id']+' '+row['title'],
                description='UNVALIDATED：'+(row['pending'] or '待 RHEL9/Wazuh 引擎與人工審查'),
                compliance=[{'twgcb': [row['gcb_id']]}], regex_type='pcre2', condition='all',
                rules=[target+' -> r:'+pattern for target, pattern in definitions()[int(row['gcb_id'][-4:])]]))
        policy = dict(policy=dict(id='linuxgcb_rhel9_'+profile+'_v01', file=filename,
                      name='RHEL9 GCB v1.2 '+profile+' v0.1 UNVALIDATED',
                      description='未驗證候選政策；僅供核准 RHEL9 試點，非完整符合性檢核', regex_type='pcre2'),
                      requirements=dict(title='僅 RHEL 9', description='角色由核准群組控制',
                        condition='all', rules=['f:/etc/os-release -> r:^ID="?rhel"?$',
                                               'f:/etc/os-release -> r:^VERSION_ID="?9([.][0-9]+)*"?$']),
                      checks=checks)
        (ROOT/'policies'/filename).write_text(json.dumps(policy, ensure_ascii=False, indent=2)+'\n')
    hashes = {p.name: digest(p) for p in sorted((ROOT/'policies').glob('*.yml'))}
    (ROOT/'data/policy_hashes.json').write_text(json.dumps(hashes, indent=2)+'\n')
    from .coverage import write
    write()
    validate()


def require(condition):
    if not condition:
        raise ValueError('候選政策結構、mapping 或 hash 不符')


def validate():
    rows = {r['sca_id']: r for r in registry()}
    seen = set()
    for path in sorted((ROOT/'policies').glob('*.yml')):
        p = json.loads(path.read_text())
        require(p['policy']['file'] == path.name and p['policy']['regex_type']=='pcre2')
        require(p['requirements'] == dict(title='僅 RHEL 9', description='角色由核准群組控制',
            condition='all', rules=['f:/etc/os-release -> r:^ID="?rhel"?$',
                                   'f:/etc/os-release -> r:^VERSION_ID="?9([.][0-9]+)*"?$']))
        for c in p['checks']:
            require(c['id'] not in seen and rows[c['id']]['included'])
            seen.add(c['id'])
            require(c['regex_type'] == 'pcre2' and c['condition'] == 'all')
            require(c['compliance'] == [{'twgcb': [rows[c['id']]['gcb_id']]}])
            require(rows[c['id']]['policy_id'] == p['policy']['id'])
            require(c['rules'] == [a+' -> r:'+b for a,b in definitions()[c['id']-900000]])
            for rule in c['rules']:
                target, pattern = rule.split(' -> r:')
                require(target.startswith('c:/') and not any(x in target for x in ('|',';', '&&', '$', '`')))
                re.compile(pattern)
    require(seen == {900000+n for n in definitions()})
    hashes = json.loads((ROOT/'data/policy_hashes.json').read_text())
    require(hashes == {p.name:digest(p) for p in (ROOT/'policies').glob('*.yml')})
    from .coverage import manifest
    require(json.loads((ROOT/'data/coverage_manifest.json').read_text()) == manifest())
    require(seen == {r['sca_id'] for r in rows.values() if r['implementation']=='candidate'})
    return len(seen)


def simulate(check, observations):
    """僅輸出匹配模型；執行失敗資訊不足回 UNRESOLVED，不冒充 Wazuh。

    exit_code 不參與 SCA 輸出匹配。明確 engine_result 可表示真機／fixture
    的 Not applicable；error 只表示未取得可靠輸出，不能預測引擎結果。
    """
    if check.get('condition') != 'all':
        raise ValueError('輸出模型只支援目前發出的 all 子集')
    outcomes = []
    for rule in check['rules']:
        target, pattern = rule.split(' -> r:')
        obs = observations.get(target)
        if target.startswith('f:') and obs is not None and obs.get('exists') is False:
            outcomes.append('NOT_APPLICABLE')
            continue
        if obs is None or obs.get('error'):
            outcomes.append('UNRESOLVED')
        elif obs.get('engine_result') == 'NOT_APPLICABLE':
            outcomes.append('NOT_APPLICABLE')
        else:
            outcomes.append('PASS' if any(re.search(pattern, line) for line in obs['stdout'].splitlines()) else 'FAIL')
    # 官方 all：任何 FAIL 優先；未知執行不擅自轉成 N/A。
    if 'FAIL' in outcomes:
        return 'FAIL'
    if 'UNRESOLVED' in outcomes:
        return 'UNRESOLVED'
    return 'NOT_APPLICABLE' if 'NOT_APPLICABLE' in outcomes else 'PASS'
