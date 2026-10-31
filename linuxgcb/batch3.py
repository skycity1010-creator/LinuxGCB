"""P2B3: 49 offline, source-bound read-only candidates.

Python runtime is embedded in -c (RHEL9 python3), never imported on the
endpoint or executed by build. Every command commits exactly one PASS line only
after all reads and predicates finish, avoiding the engine's 256-line boundary.
"""
from functools import lru_cache
import inspect
import json
import re
import shlex
from pathlib import Path
from .argv import quote_argument
from . import p2b3_runtime as runtime

ADDED = set(range(134,141)) | set(range(143,174)) | {176,177,181,182,308,92,93,95,96,99,100}
PACKAGES = {92:'xinetd',96:'net-snmp',99:'vsftpd',100:'ypserv'}
AUDIT = set(range(148,173)) - {158,161}


@lru_cache(maxsize=1)
def sources():
    return {int(r['gcb_id'][-4:]):r for r in json.loads((Path(__file__).resolve().parents[1]/'data/controls.json').read_text()) if int(r['gcb_id'][-4:]) in ADDED}


def audit_lines(n):
    lines = [line.strip() for line in sources()[n]['configuration_method'].splitlines()
             if line.startswith(('-a ', '-w ')) and '(' not in line]
    # Source typo joins two -S flags; preserve intended five syscall semantics.
    return [line.replace('renameat-S', 'renameat -S') for line in lines]


DEPS = {
    'optional_tool_metadata':['metadata'], 'active':[], 'setting':['active'], 'metadata':[], 'read':[], 'files':[],
    'audit_matches':['active','read'], 'uid_min':['active','read'],
    'audit_rules':['uid_min','audit_matches'], 'log_metadata':['setting','read','metadata'],
    'service':[], 'package_state':[], 'optional_service':['package_state','service','active','read'],
    'rsyslog_text':['read','files'], 'rsyslog_mode':['rsyslog_text','active'],
    'rsyslog_rules':['rsyslog_text','active'], 'journal':['files','read','setting'],
    'grub':['active','read'], 'sudo_log':['files','read','active','audit_matches'],
    'privileged':['read','uid_min','audit_matches'], 'immutable':['files','active','read'],
    'logrotate':['active','read','metadata'],
}


def spec(n):
    if n in AUDIT:
        return ['audit_rules'], 'audit_rules('+repr(audit_lines(n))+')'
    if n == 92:
        return [], ''
    if n == 93:
        return ['active','read'], "any(re.fullmatch(r'(server|pool)\\s+[^\\s#()]+(?:\\s+[^#]+)?', line) for line in active(read('/etc/chrony.conf')))"
    if n == 95:
        return ['service'], "service('avahi-daemon.service') and service('avahi-daemon.socket')"
    if n in (96,99,100):
        return ['optional_service'], 'optional_service('+repr(PACKAGES[n])+', '+repr({96:'snmpd',99:'vsftpd',100:'ypserv'}[n]+'.service')+', '+repr(n==96)+')'
    if n in (134,135):
        return ['grub'], 'grub('+repr('audit' if n==134 else 'audit_backlog_limit')+', '+str(1 if n==134 else 8192)+')'
    if n == 136:
        return ['active','read'], "(lambda lines: bool(lines) and re.fullmatch(r'postmaster:\\s*root', lines[-1]) is not None)([line for line in active(read('/etc/aliases')) if re.match(r'postmaster:', line)])"
    if n in (137,138,139,140):
        return ['log_metadata'], 'log_metadata('+{137:'None',138:'0o600',139:'None',140:'0o700'}[n]+', '+repr(n in (139,140))+')'
    if n in (143,144):
        paths=['/sbin/'+name for name in ('auditctl','aureport','ausearch','autrace','auditd','audisp-remote','audisp-syslog','augenrules','rsyslogd')]
        return ['optional_tool_metadata'], 'all(optional_tool_metadata(path, '+('0o750' if n==143 else 'None')+') for path in '+repr(paths)+')'
    if n == 145:
        paths=['/usr/sbin/'+name for name in ('auditctl','auditd','ausearch','aureport','autrace','audisp-remote','audisp-syslog','augenrules')]
        return ['audit_matches'], "audit_matches('/etc/aide.conf', [path + ' p+i+n+u+g+s+b+acl+xattrs+sha512' for path in "+repr(paths)+'])'
    if n in (146,147):
        key='max_log_file' if n==146 else 'max_log_file_action'
        expr="setting(read('/etc/audit/auditd.conf'), "+repr(key)+')'
        return ['setting','read'], ('(lambda v: v is not None and v.isdigit() and int(v) >= 32)('+expr+')' if n==146 else expr+" == 'keep_logs'")
    name={158:'privileged',161:'sudo_log',173:'immutable',176:'rsyslog_mode',177:'rsyslog_rules',308:'logrotate'}.get(n)
    if name:
        return [name], name+'()'
    if n in (181,182):
        return ['journal'], "journal('Compress', 'yes')" if n==181 else "journal('Storage', 'persistent')"
    raise ValueError(n)


@lru_cache(maxsize=None)
def script(n):
    functions, expr = spec(n)
    used=[]
    def add(name):
        for dep in DEPS[name]: add(dep)
        if name not in used: used.append(name)
    for name in functions: add(name)
    return ("import glob, os, re, stat, subprocess\nROOT = ''\n"+
            '\n'.join(inspect.getsource(getattr(runtime,name)) for name in used)+
            '\ntry:\n    ok = '+expr+"\nexcept (OSError, ValueError, IndexError, KeyError):\n    ok = False\nif ok:\n    print('PASS')\n")


@lru_cache(maxsize=1)
def rules():
    result={}
    for n in sorted(ADDED):
        if n == 92:
            body='out=$(rpm -q xinetd 2>/dev/null); rc=$?; case $rc in 0) echo INSTALLED;; 1) echo ABSENT;; *) exit $rc;; esac'
            result[n]=[('c:/bin/sh -c '+quote_argument(body), '^ABSENT$')]
        else:
            command='/usr/bin/python3 -c '+shlex.quote(script(n))
            result[n]=[('c:/bin/sh -c '+quote_argument(command), '^PASS$')]
    return result


def mechanism(n):
    if n in AUDIT: return '持久 audit.rules 全行正則，逐條 all；UID_MIN 取最後有效值'
    return {92:'定向 rpm -q 三態',93:'chrony 有效 server/pool',95:'FIX-1 systemctl service/socket 停用',
            96:'定向 RPM 三態／停用服務／明確 authPriv SNMPv3 子集',99:'定向 RPM 三態＋FIX-1 停用 vsftpd',100:'定向 RPM 三態＋FIX-1 停用 ypserv',
            134:'GRUB audit 開機參數',135:'GRUB backlog 數值下界',136:'aliases postmaster root',
            137:'有效 log_file 檔案 owner',138:'有效 log_file 檔案 mode 位元遮罩',139:'有效 log_file 目錄 owner/type',140:'有效 log_file 目錄 mode/type',
            143:'九個來源工具 mode 位元遮罩',144:'九個來源工具 UID/GID',145:'八個 AIDE 工具完整屬性正則',
            146:'auditd.conf 最後有效值 >=32',147:'auditd.conf 最後有效值 keep_logs',158:'所有實體掛載點 xdev 特權程式逐一對 privileged.rules',
            161:'sudoers logfile 路徑逐一對 actions.rules',173:'持久規則最後有效 -e 2 與 loginuid immutable',
            176:'rsyslog 舊式預設與新式 action fileCreateMode 位元遮罩',177:'rsyslog 三類 selector 與 secure 目的地',
            181:'Journal Compress 最後有效值與排序 drop-in',182:'Journal Storage 最後有效值與排序 drop-in',308:'指定 rsyslog logrotate 完整 stanza 與日誌目錄權限'}[n]


def caveat(n):
    common='P2B3 UNVALIDATED；human_review_pending；execution_review=blocked。唯讀內嵌 Python，需 RHEL9 /usr/bin/python3 標準函式庫；不安裝 helper。完成所有讀取才輸出單行 PASS，錯誤/缺失無成功輸出；w_strtok、PCRE2、timeout 待真機驗證。'
    detail=''
    if n in AUDIT: detail='依來源 audit.rules 的完整 token 順序逐條比對；等價重排或合併 syscall 可能保守失敗；不代表核心已載入。auid 門檻依 login.defs UID_MIN。'
    if n==159: detail+='來源 renameat-S 排版錯誤解讀為 renameat -S，保留五個 syscall，待人工核准。'
    if n in (134,135): detail='僅來源 /etc/default/grub；已產生開機項/執行中核心待真機確認。'
    if n in (137,138,139,140): detail='使用最後有效 log_file，缺失不採範例路徑預設；跟隨 symlink；檔案本體與實際目錄，ACL/輪替檔待審。'
    if n in (143,144): detail='RHEL9 audit 3.x 無 audisp plugin；不存在工具跳過之來源解讀待批。存在工具仍須符合原 mode/owner 標準；僅 FileNotFoundError 跳過，其他 stat 錯誤失敗；stat 跟隨 /sbin symlink；ACL 待審。'
    if n==145: detail='逐工具要求來源完整屬性序列；AIDE macro/Include 與資料庫初始化待審。'
    if n in (95,96,99,100): detail='FIX-1 明確 not-found 且 inactive 視為停用；disabled/masked 且 inactive 合格；systemctl 錯誤不合格。套件 ABSENT 仍須確認服務 inactive，避免移除套件後程序仍存活。多次查詢非原子。'
    if n==96: detail+='來源允許 v3；自動候選限明確 rouser priv，禁 v1/v2 access/include；SHA/AES 金鑰建立與實際協商仍須人工證據，不讀取或輸出私密使用者金鑰。'
    if n in (92,96,99,100): detail+='僅定向 rpm -q，0=INSTALLED、1=ABSENT、其他錯誤無成功輸出；不查 rpm -qa。'
    if n==158: detail='列舉 mountinfo 實體檔案系統（排除 proc/sysfs 等虛擬介面），每掛載點 xdev 查所有 regular setuid/setgid；空集合為全稱真但 privileged.rules 仍須可讀。大型/網路檔案系統成本與競態待審。'
    if n==161: detail='只辨識 /etc/sudoers 與 sudoers.d 的明確 Defaults logfile；不假定 /var/log/sudo.log；條件 Defaults、外部 include 與覆寫完整語意待人工審查。'
    if n==173: detail='來源 -e 2--loginuid-immutable 排版解讀為兩條指令；自然數字排序規則檔，最後 -e 必須為 2 且最後有效行為鎖定指令；核心狀態待審。'
    if n==176: detail='保守要求所有明確 $FileCreateMode 與 action fileCreateMode 均不超過 0640；未設定不假定預設合格；複雜模板/include 待審。'
    if n==177: detail='接受來源逗號與分號 selector，舊式 secure 路徑與新式 omfile action；複雜多行 action/模板/ruleset 待審。'
    if n in (181,182): detail='來源要求新增明確設定；未設定（即使 Compress 套件預設 yes）不判 PASS。解析 [Journal]、最後值與 /usr/lib、/usr/local/lib、/run、/etc drop-in 同名優先/字典順序與 /dev/null mask；執行中狀態待審。'
    if n==308: detail='依來源 /etc/logrotate.d/rsyslog 指定路徑、weekly/rotate 4/compress/missingok/notifempty/postrotate 及目錄 <=0750；不是任意 rsyslog 字樣即合格；複雜多 stanza、實際輪替待審。'
    return detail+common


def expected(row):
    suffix=row.get('gcb_id', '')[-4:]
    if not suffix.isdigit(): return None
    n=int(suffix)
    if n not in ADDED: return None
    if n in AUDIT: return '；'.join(audit_lines(n))
    return {92:'xinetd 未安裝',93:'至少一個有效 server 或 pool',95:'avahi-daemon.service/socket disabled/masked 且 inactive',
            96:'SNMP 停用或僅 SNMPv3（SHA/AES 需人工證據）',99:'vsftpd disabled/masked 或明確 not-found，且 inactive；RPM 三態無錯誤',100:'ypserv disabled/masked 或明確 not-found，且 inactive；RPM 三態無錯誤',
            134:'audit=1',135:'audit_backlog_limit>=8192',136:'postmaster: root',137:'稽核日誌 root:root',138:'稽核日誌 <=0600（位元子集合）',
            139:'稽核日誌目錄 root:root',140:'稽核日誌目錄 <=0700（位元子集合）',143:'九個稽核工具 <=0750（位元子集合）',144:'九個稽核工具 root:root',
            145:'八個稽核工具 p+i+n+u+g+s+b+acl+xattrs+sha512',146:'max_log_file>=32',147:'max_log_file_action=keep_logs',
            158:'每個磁區所有特權程式都有 privileged.rules 執行稽核',161:'sudo 實際 logfile 有 actions.rules wa/actions 稽核',
            173:'-e 2；--loginuid-immutable',176:'$FileCreateMode/action fileCreateMode <=0640（位元子集合）',177:'auth.*、authpriv.*、daemon.* → /var/log/secure',
            181:'[Journal] Compress=yes（明確設定）',182:'[Journal] Storage=persistent',308:'指定 rsyslog logrotate weekly/rotate 4/compress/missingok/notifempty/postrotate；目錄 <=0750'}[n]
