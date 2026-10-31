"""BATCH2 fixed, source-reviewed read-only candidates. Never execute at build time.

Only new commands use a stdout commit guard: buffer output, publish it and an
explicit success marker only after exit 0. This is new: Q1 had no such guard.
Wazuh argv/quoting and RHEL9 runtime remain UNVALIDATED.
"""
import shlex
from .batch1 import mode_pattern

CATEGORIES = {'SSH設定', 'cron設定', 'SELinux', '安裝與維護軟體'}
ADDED = set(range(102,108)) | set(range(184,190)) | {190,203,204,205,254,255,258,259,260,261,262,263,264,265,266,267,268,271,272,273,274,275,276,277,278,279,280,281,282,283,284,315}
MARKER = 'LINUXGCB_COMMAND_OK'


def guarded(command):
    script = ('out=$('+command+'); rc=$?; if [ "$rc" -eq 0 ]; then '
              'printf "%s\\n" "$out" "'+MARKER+'"; else exit "$rc"; fi')
    return 'c:/bin/sh -c '+shlex.quote(script)


# command, predicate, compliant stdout, noncompliant stdout. These are authored
# semantic examples, independent of the fixture generator / regex matcher.
def specs():
    result = {}
    for n,package in {102:'ypbind',103:'telnet',104:'telnet-server',105:'rsh-server',106:'tftp-server',188:'setroubleshoot',189:'mcstrans'}.items():
        result[n] = [('/usr/bin/rpm -qa --queryformat '+shlex.quote('%{NAME}\\n'),
                      '!^'+package+'$', 'bash\ncoreutils', package)]
    result[107] = [('/usr/bin/cat '+p, '^[ \\t]*clean_requirements_on_remove[ \\t]*=[ \\t]*[Tt]rue[ \\t]*$',
                    '[main]\nclean_requirements_on_remove=True', '[main]\nclean_requirements_on_remove=False')
                   for p in ('/etc/yum.conf','/etc/dnf/dnf.conf')]
    result[184] = [('/usr/bin/cat /etc/default/grub',
                    '!^[ \\t]*GRUB_CMDLINE_LINUX[^=]*=.*(selinux=0|enforcing=0)',
                    'GRUB_CMDLINE_LINUX="quiet"', 'GRUB_CMDLINE_LINUX="selinux=0"')]
    result[185] = [('/usr/bin/cat /etc/selinux/config', '^[ \\t]*SELINUXTYPE=(targeted|mls)[ \\t]*$',
                    'SELINUXTYPE=targeted', 'SELINUXTYPE=minimum')]
    result[186] = [('/usr/bin/cat /etc/selinux/config', '^[ \\t]*SELINUX=enforcing[ \\t]*$',
                    'SELINUX=enforcing', 'SELINUX=permissive'),
                   ('/usr/sbin/getenforce', '^Enforcing$', 'Enforcing', 'Permissive')]
    result[187] = [('/usr/bin/ps -eZf', '!unconfined_service_t',
                    'system_u:system_r:init_t:s0 root 1', 'system_u:system_r:unconfined_service_t:s0 root 2')]
    for n,unit in ((190,'crond'),(254,'sshd')):
        result[n] = [('/usr/bin/systemctl show '+unit+'.service --property='+prop,
                      '^'+prop+'='+state+'$', prop+'='+state, prop+'=wrong')
                     for prop,state in (('LoadState','loaded'),('ActiveState','active'),('UnitFileState','enabled'))]
    # Source 0254 also explicitly installs openssh-server.
    result[254].append(('/usr/bin/rpm -q --queryformat '+shlex.quote('%{NAME}:installed')+' openssh-server',
                        '^openssh-server:installed$', 'openssh-server:installed', 'package openssh-server is not installed'))
    for n,fmt,pattern,good,bad in ((203,'%U:%G','^root:root$','root:root','nobody:root'),
                                  (204,'%a',mode_pattern(0o600),'600','666')):
        result[n] = [('/usr/bin/stat -c '+fmt+' '+p,pattern,good,bad)
                     for p in ('/etc/at.allow','/etc/cron.allow')]
        result[n].append(('/usr/bin/find /etc -maxdepth 1 -name '+shlex.quote('*.deny'),
                          '!^/etc/(at|cron)[.]deny$', '', '/etc/cron.deny'))
    # Read every source configuration successfully; empty optional .conf set is
    # allowed, but an unreadable directory or any cat/find failure is not.
    result[205] = [('/usr/bin/cat /etc/rsyslog.conf && /usr/bin/find /etc/rsyslog.d -maxdepth 1 -type f -name '+shlex.quote('*.conf')+' -exec /usr/bin/cat {} +',
                    '^[ \\t]*cron[.][*][ \\t]+/var/log/cron[ \\t]*$', 'cron.* /var/log/cron', 'cron.none /var/log/cron')]
    ssh = '/usr/sbin/sshd -T'
    settings = {
        255:('!^protocol (?!2$).+', 'port 22', 'protocol 1'),
        258:('^(allowusers|allowgroups|denyusers|denygroups) .+', 'allowusers approved_user', 'port 22'),
        263:('^ciphers aes128-ctr,aes192-ctr,aes256-ctr$', 'ciphers aes128-ctr,aes192-ctr,aes256-ctr', 'ciphers aes128-cbc'),
        264:('^loglevel (VERBOSE|INFO)$','loglevel VERBOSE','loglevel DEBUG'),
        265:('^x11forwarding no$','x11forwarding no','x11forwarding yes'),
        266:('^maxauthtries [1-4]$','maxauthtries 4','maxauthtries 0'),
        267:('^ignorerhosts yes$','ignorerhosts yes','ignorerhosts no'),
        268:('^hostbasedauthentication no$','hostbasedauthentication no','hostbasedauthentication yes'),
        271:('^permituserenvironment no$','permituserenvironment no','permituserenvironment yes'),
        272:('^clientaliveinterval ([1-9]|[1-9][0-9]|[1-5][0-9]{2}|600)$','clientaliveinterval 600','clientaliveinterval 0'),
        273:('^logingracetime ([1-9]|[1-5][0-9]|60)$','logingracetime 60','logingracetime 0'),
        274:('^usepam yes$','usepam yes','usepam no'),
        275:('^allowtcpforwarding no$','allowtcpforwarding no','allowtcpforwarding yes'),
        276:('^maxstartups 10:30:60$','maxstartups 10:30:60','maxstartups 10:30:100'),
        277:('^maxsessions [1-4]$','maxsessions 4','maxsessions 0'),
        278:('^strictmodes yes$','strictmodes yes','strictmodes no'),
        279:('^compression (delayed|no|yes)$','compression no','compression invalid'),
        280:('^ignoreuserknownhosts yes$','ignoreuserknownhosts yes','ignoreuserknownhosts no'),
        281:('^printlastlog yes$','printlastlog yes','printlastlog no'),
        315:('^gssapiauthentication no$','gssapiauthentication no','gssapiauthentication yes'),
    }
    for n,(pattern,good,bad) in settings.items():
        result[n] = [(ssh,pattern,good,bad)]
    result[272].append((ssh,'^clientalivecountmax 1$','clientalivecountmax 1','clientalivecountmax 0'))
    result[263] += [(ssh,'^macs hmac-sha2-512,hmac-sha2-256$', 'macs hmac-sha2-512,hmac-sha2-256','macs hmac-md5'),
                    (ssh,'^kexalgorithms ecdh-sha2-nistp256,ecdh-sha2-nistp384,ecdh-sha2-nistp521,diffie-hellman-group-exchange-sha256,diffie-hellman-group14-sha256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512$',
                     'kexalgorithms ecdh-sha2-nistp256,ecdh-sha2-nistp384,ecdh-sha2-nistp521,diffie-hellman-group-exchange-sha256,diffie-hellman-group14-sha256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512','kexalgorithms diffie-hellman-group1-sha1')]
    for n,glob,fmt,pattern,good,bad in (
        (259,'ssh_host_*_key','%U:%G','root:ssh_keys','root:ssh_keys','root:root'),
        (260,'ssh_host_*_key','%a',mode_pattern(0o640)[1:-1],'640','666'),
        (261,'ssh_host_*_key.pub','%U:%G','root:root','root:root','nobody:root'),
        (262,'ssh_host_*_key.pub','%a',mode_pattern(0o644)[1:-1],'644','666')):
        cmd='/usr/bin/find /etc/ssh -xdev -type f -name '+shlex.quote(glob)+' -exec /usr/bin/stat -c '+fmt+' {} +'
        # Existence plus absence of any bad member: never just "some key good".
        result[n]=[(cmd,'^'+pattern+'$',good,bad),
                   (cmd,'!^(?!'+pattern+'$|'+MARKER+'$).+',good,bad)]
    for n,name in ((282,'shosts.equiv'),(283,'*.shosts')):
        result[n]=[('/usr/bin/find / -name '+shlex.quote(name), '!^/', '', '/home/example/'+name.replace('*',''))]
    result[284]=[('/usr/bin/cat /etc/sysconfig/sshd','!^[ \\t]*CRYPTO_POLICY[ \\t]*=',
                  '# CRYPTO_POLICY=', 'CRYPTO_POLICY=')]
    assert set(result)==ADDED
    return result


def rules():
    result={}
    for n,items in specs().items():
        predicates=[(guarded(cmd),pattern) for cmd,pattern,_,_ in items]
        # Explicit success prerequisite even for negated predicates and empty sets.
        result[n]=list(dict.fromkeys(predicates+[(guarded(cmd),'^'+MARKER+'$') for cmd,_,_,_ in items]))
    return result


def caveat(n):
    common='BATCH2 輸出先緩衝，exit 0 才發布成功標記；shell argv/quoting、stderr、timeout 與 RHEL9 引擎待真機驗證；UNVALIDATED。'
    if n >= 254:
        common+='sshd -T 僅預設情境；Include/Match 與使用者/來源矩陣沿用 Q1 限制；服務啟動參數與 crypto-policy 注入尚待核對。'
    if n==255:
        common+='RHEL9 OpenSSH 8.0+ 僅支援 SSH2；sshd -T 不輸出 Protocol 時接受預設，輸出 protocol 1 則拒絕。'
    if n==279:
        common+='RHEL9 OpenSSH 8.0+ 的 compression yes 僅認證後壓縮（等同歷史 delayed）；no 亦符合。'
    if n==258:
        common+='來源清單依組織授權，沒有單一基準值；只檢查至少一個有效限制清單，授權正確性待人工審查。'
    if n in (259,260,261,262):
        common+='僅來源 find -xdev -type f 集合；至少一把鑰匙且全部 metadata 符合；ACL、連結與有效 HostKey 路徑待審。'
    if n==260:
        common+='來源文字提 600 但設定命令與 expected 為 640，依 F/G 欄實作 640 位元子集合，差異待核准。'
    if n==184: common+='僅 /etc/default/grub 設定；實際開機項與已產生 grub.cfg 尚待驗證。'
    if n in (107,185,186,205,284): common+='僅來源指定文字設定；重複指令、載入順序與執行中狀態待審。'
    if n in (282,283): common+='全檔案系統唯讀 find 可能昂貴；權限錯誤不通過，掛載集合與 timeout 待審。'
    return common


def expected(row):
    """Concrete values from F cells; no site-specific users or invented defaults."""
    suffix=row.get('gcb_id','')[-4:]
    if not suffix.isdigit(): return None
    n=int(suffix)
    if n not in ADDED: return None
    method=row.get('configuration_method','')
    if not method: return '待確認（來源未提供單一基準值）'
    if n==258: return '待確認（來源未提供單一基準值）'
    if n in (102,103,104,105,106,188,189):
        return method.split('#dnf remove ',1)[1].splitlines()[0]+' 未安裝'
    if n==263:
        return 'Ciphers aes128-ctr,aes192-ctr,aes256-ctr；MACS=hmac-sha2-512,hmac-sha2-256；KexAlgorithms='+method.split('-oKexAlgorithms=',1)[1].splitlines()[0]
    return {
        107:'clean_requirements_on_remove=True（/etc/yum.conf 與 /etc/dnf/dnf.conf）',
        184:'所有 GRUB_CMDLINE_LINUX* 不含 selinux=0 或 enforcing=0',
        185:'SELINUXTYPE=targeted（或來源允許之更嚴格 mls）',
        186:'SELINUX=enforcing；即時 enforcing',187:'無 unconfined_service_t 程序',
        190:'crond enabled+active',203:'root:root；/etc/at.deny 與 /etc/cron.deny 不存在',
        204:'600 或更低權限；/etc/at.deny 與 /etc/cron.deny 不存在',
        205:'cron.* /var/log/cron',254:'openssh-server 已安裝；sshd enabled+active',
        255:'Protocol 2',259:'root:ssh_keys',260:'640 或更低權限',261:'root:root',262:'644 或更低權限',
        264:'LogLevel VERBOSE 或 INFO',265:'X11Forwarding no',266:'MaxAuthTries 4（來源允許 1–4）',
        267:'IgnoreRhosts yes',268:'HostbasedAuthentication no',271:'PermitUserEnvironment no',
        272:'ClientAliveInterval 600（來源允許 1–600）；ClientAliveCountMax 1',
        273:'LoginGraceTime 60（來源允許 1–60）',274:'UsePAM yes',275:'AllowTcpForwarding no',
        276:'MaxStartups 10:30:60',277:'MaxSessions 4（來源允許 1–4）',278:'StrictModes yes',
        279:'Compression delayed 或 no',280:'IgnoreUserKnownHosts yes',281:'PrintLastLog yes',
        282:'移除所有 shosts.equiv',283:'移除所有 *.shosts',284:'不存在未註解的 CRYPTO_POLICY 設定',
        315:'GSSAPIAuthentication no',
    }[n]
