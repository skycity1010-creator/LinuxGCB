"""以 JSON（YAML 1.2 子集）產生候選 SCA；只模擬輸出匹配，不執行命令。"""
from .batch10 import ADDED as BATCH10, rules as batch10_rules
import json
import re
from functools import lru_cache
from .catalog import ROOT, registry, digest
from .batch1 import rules as batch_rules, disabled_service_rules
from .expected import PREFIX, values, parse_description
from .batch2 import rules as batch2_rules, ADDED as BATCH2
from .batch3 import rules as batch3_rules, ADDED as BATCH3
from .batch6 import rules as batch6_rules, ADDED as BATCH6
from .batch7 import rules as batch7_rules, ADDED as BATCH7
from .batch9 import ADDED as BATCH9, rules as batch9_rules
from .batch8 import rules as batch8_rules, ADDED as BATCH8
from .argv import w_strtok


def definitions():
    modes = '|'.join(format(n, 'o') for n in range(0o1000) if n & ~0o644 == 0)
    return {**batch_rules(), **batch2_rules(), **batch3_rules(), **batch6_rules(), **batch7_rules(), **batch8_rules(), **batch9_rules(), **batch10_rules(),
        45: [('c:/usr/bin/stat -c %u:%g /etc/passwd', '^0:0$')],
        46: [('c:/usr/bin/stat -c %a /etc/passwd', '^('+modes+')$')],
        108: [('c:/usr/sbin/sysctl -n net.ipv4.ip_forward', '^0$'),
              ('c:/usr/sbin/sysctl -n net.ipv6.conf.all.forwarding', '^0$')],
        243: [('c:/usr/bin/systemctl show firewalld.service --property=LoadState', '^LoadState=loaded$'),
              ('c:/usr/bin/systemctl show firewalld.service --property=ActiveState', '^ActiveState=active$'),
              ('c:/usr/bin/systemctl show firewalld.service --property=UnitFileState', '^UnitFileState=enabled$')],
        245: disabled_service_rules('nftables'),
        269: [('c:/usr/sbin/sshd -T', '^permitrootlogin no$')],
        270: [('c:/usr/sbin/sshd -T', '^permitemptypasswords no$')],
    }


ACCEPTED_FINDINGS = {900187, 900229}
FINDING_SUFFIX = ' ｜ 【Accepted finding】Commander 2026-11-01 裁定：維持 FAIL，不矯正系統設定（docs/EXCEPTIONS.md）'


@lru_cache(maxsize=1)
def manual_commands():
    """來源 configuration_method 的人工檢核指令（# 開頭命令，條件詞前）；僅文字，不執行。"""
    out = {}
    for c in json.loads((ROOT/'data/controls.json').read_text()):
        text = str(c.get('configuration_method') or '').replace('<br>', '\n')
        cmds = []
        for line in text.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith('#'):
                cmds.append(s.lstrip('#').strip())
                continue
            m = re.search(r'[：:]\s*#(.+)$', s)
            if m:
                frag = re.split(r'\s+(?:若|如|則|請)', m[1].strip())[0].strip()
                if frag:
                    cmds.append(frag)
            elif cmds and re.search(r'若|如出現|請', s):
                break
        joined = ' ； '.join(cmds)
        if not joined:
            joined = re.sub(r'\s+', ' ', text).strip()
            joined = (joined[:300] + '…') if len(joined) > 300 else joined
            out[c['gcb_id']] = ('【來源設定方法】' + joined) if joined else ''
            continue
        out[c['gcb_id']] = (joined[:500] + '…') if len(joined) > 500 else joined
    return out


def build():
    rows = registry()
    expected = values()
    for profile in ('base', 'firewalld', 'sshd'):
        filename = 'linuxgcb_'+profile+'.yml'
        checks = []
        for row in rows:
            if row['implementation'] != 'candidate' or row['profile'] != profile:
                continue
            manual = manual_commands()[row['gcb_id']]
            rationale = ('人工檢核程序（來源）：'+manual[len('【來源設定方法】'):] if manual.startswith('【來源設定方法】')
                         else ('人工檢核指令（來源）：'+manual) if manual else '人工檢核：見 GCB 來源 configuration_method')
            checks.append(dict(id=row['sca_id'], title=row['gcb_id']+' '+row['title'],
                description=PREFIX+expected[row['gcb_id']]+(FINDING_SUFFIX if row['sca_id'] in ACCEPTED_FINDINGS else ''),
                rationale=rationale,
                compliance=[{'twgcb': [row['gcb_id']]}], regex_type='pcre2', condition='all',
                rules=[emit_rule(target, pattern) for target, pattern in definitions()[int(row['gcb_id'][-4:])]]))
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
            require(parse_description(c.get('description')) == values()[rows[c['id']]['gcb_id']])
            require(c.get('rationale','').startswith('人工檢核'))
            require(c['regex_type'] == 'pcre2' and c['condition'] == 'all')
            require(c['compliance'] == [{'twgcb': [rows[c['id']]['gcb_id']]}])
            require(rows[c['id']]['policy_id'] == p['policy']['id'])
            require(c['rules'] == [emit_rule(a,b) for a,b in definitions()[c['id']-900000]])
            for rule in c['rules']:
                target, _ = rule.split(' -> ', 1)
                require(target.removeprefix('not ').startswith('c:/'))
                if c['id']-900000 not in BATCH2 | BATCH3 | BATCH6 | BATCH7 | BATCH8 | BATCH9 | BATCH10:
                    require(not any(x in target for x in ('|',';', '&&', '$', '`')))
                parse_rule(rule)
    require(seen == {900000+n for n in definitions()})
    hashes = json.loads((ROOT/'data/policy_hashes.json').read_text())
    require(hashes == {p.name:digest(p) for p in (ROOT/'policies').glob('*.yml')})
    from .coverage import manifest
    require(json.loads((ROOT/'data/coverage_manifest.json').read_text()) == manifest())
    require(seen == {r['sca_id'] for r in rows.values() if r['implementation']=='candidate'})
    return len(seen)


@lru_cache(maxsize=1)
def supported_patterns():
    return frozenset(p.lstrip('!') for rules in definitions().values() for _,p in rules) | {
        '^ID="?rhel"?$', '^VERSION_ID="?9([.][0-9]+)*"?$'}


def emit_rule(target, pattern):
    return ('not '+target+' -> r:'+pattern[1:]) if pattern.startswith('!') else target+' -> r:'+pattern


@lru_cache(maxsize=1)
def batch2_emitted():
    return {emit_rule(t,p) for rules in batch2_rules().values() for t,p in rules}


@lru_cache(maxsize=1)
def batch3_emitted():
    return {emit_rule(t,p) for rules in batch3_rules().values() for t,p in rules}


def parse_rule(rule):
    """Legacy bounded grammar plus exact allowlist of BATCH2 emitted rules."""
    if not isinstance(rule, str):
        raise ValueError('不支援的規則語法')
    if rule in {emit_rule(t,p) for rs in [*batch6_rules().values(), *batch7_rules().values(), *batch8_rules().values(), *batch9_rules().values(), *batch10_rules().values()] for t,p in rs}:
        target, expression = rule.split(' -> ', 1)
        argv = w_strtok(target[2:])
        if len(argv) != 3 or argv[:2] != ['/usr/bin/python3', '-c']:
            raise ValueError('Invalid Python argv')
        return target, re.compile(expression.split(':',1)[1], re.ASCII)
    if rule in batch2_emitted() or rule in batch3_emitted():
        target, expression = rule.split(' -> ', 1)
        argv = w_strtok(target.removeprefix('not ')[2:])
        if len(argv) != 3 or argv[:2] != ['/bin/sh', '-c']:
            raise ValueError('Invalid wm_exec shell argv')
        return target.removeprefix('not '), re.compile(expression.split(':',1)[1], re.ASCII)
    if rule.count(' -> r:') != 1:
        raise ValueError('不支援的規則語法')
    target, pattern = rule.split(' -> r:')
    if not re.fullmatch(r'[cf]:/[^\n\r]+', target) or any(x in target for x in (' -> ', ' && ', '|', ';', '`', '$')):
        raise ValueError('不支援的目標')
    if pattern not in supported_patterns() and not re.fullmatch(r'\^[A-Za-z0-9_ =:/-]+\$', pattern):
        raise ValueError('未驗證的 PCRE2 語法')
    try:
        return target, re.compile(pattern, re.ASCII)
    except re.error as exc:
        raise ValueError('無效模式') from exc


def simulate(check, observations):
    """僅輸出匹配模型；執行失敗資訊不足回 UNRESOLVED，不冒充 Wazuh。

    FIX-3 模擬 OS_StrBreak 的前 256 行上限（wm_sca.c:1749）。
    FIX-1 同一 command 的多行輸出仍按逐行存在匹配；alternation 是單一
    正向 regex，規則間維持 all，不以空輸出或 stderr 推論 not-found。
    所有項目 exit_code 不參與輸出匹配（wm_exec 正常結束仍回 0），
    並以 emitted shell guard 確保失敗不發布輸出或成功標記。
    明確 engine_result 可表示真機／fixture
    的 Not applicable；error 只表示未取得可靠輸出，不能預測引擎結果。
    """
    if check.get('regex_type', 'pcre2') != 'pcre2':
        raise ValueError('只支援明確 PCRE2 候選子集')
    if check.get('condition') != 'all':
        raise ValueError('輸出模型只支援目前發出的 all 子集')
    if not isinstance(check.get('rules'), list) or not check['rules']:
        raise ValueError('規則不得為空')
    parsed = [parse_rule(rule) for rule in check['rules']]
    outcomes = []
    for rule, (target, pattern) in zip(check['rules'], parsed):
        obs = observations.get(target)
        if target.startswith('f:') and obs is not None and obs.get('exists') is False:
            outcomes.append('NOT_APPLICABLE')
            continue
        if obs is None or obs.get('error'):
            outcomes.append('UNRESOLVED')
        elif obs.get('engine_result') == 'NOT_APPLICABLE':
            outcomes.append('NOT_APPLICABLE')
        elif not isinstance(obs.get('stdout'), str):
            raise ValueError('觀察必須提供字串 stdout')
        else:
            matched = any(pattern.search(line) for line in obs['stdout'].split('\n')[:256])
            if rule.startswith('not '):
                matched = not matched
            outcomes.append('PASS' if matched else 'FAIL')
    # 官方 all：任何 FAIL 優先；未知執行不擅自轉成 N/A。
    if 'FAIL' in outcomes:
        return 'FAIL'
    if 'UNRESOLVED' in outcomes:
        return 'UNRESOLVED'
    return 'NOT_APPLICABLE' if 'NOT_APPLICABLE' in outcomes else 'PASS'
