"""有界批次：明列來源路徑，不以標題啟發式生成控制。"""
# (路徑, owner 或 mode, 允許值)；mode 是位元子集合，非 umask。
FILES = {
 47:('/etc/shadow','owner','root:(root|shadow)'),48:('/etc/shadow','mode',0),
 49:('/etc/group','owner','root:root'),50:('/etc/group','mode',0o644),
 51:('/etc/gshadow','owner','root:(root|shadow)'),52:('/etc/gshadow','mode',0),
 53:('/etc/passwd-','owner','root:root'),54:('/etc/passwd-','mode',0o644),
 55:('/etc/shadow-','owner','root:(root|shadow)'),56:('/etc/shadow-','mode',0),
 57:('/etc/group-','owner','root:root'),58:('/etc/group-','mode',0o644),
 59:('/etc/gshadow-','owner','root:(root|shadow)'),60:('/etc/gshadow-','mode',0),
 141:('/etc/audit/rules.d/audit.rules','mode',0o600),142:('/etc/audit/auditd.conf','mode',0o640),
 178:('/var/log/messages','owner','root:root'),179:('/var/log','owner','root:root'),
 191:('/etc/crontab','owner','root:root'),192:('/etc/crontab','mode',0o600),
 193:('/etc/cron.hourly','owner','root:root'),194:('/etc/cron.hourly','mode',0o700),
 195:('/etc/cron.daily','owner','root:root'),196:('/etc/cron.daily','mode',0o700),
 197:('/etc/cron.weekly','owner','root:root'),198:('/etc/cron.weekly','mode',0o700),
 199:('/etc/cron.monthly','owner','root:root'),200:('/etc/cron.monthly','mode',0o700),
 201:('/etc/cron.d','owner','root:root'),202:('/etc/cron.d','mode',0o700),
 256:('/etc/ssh/sshd_config','owner','root:root'),257:('/etc/ssh/sshd_config','mode',0o600),
 301:('/etc/shells','owner','root:root'),302:('/etc/shells','mode',0o644),
}
PACKAGES = {33:['sudo'],132:['audit','audit-libs'],174:['rsyslog'],183:['libselinux'],242:['firewalld']}
# 0036 AIDE 初始化另有要求，0231 架構需審查，本批不以套件存在充當完整實作。
SERVICES = {30:('autofs','disabled'),94:('rsyncd','masked'),97:('squid','masked'),
            98:('smb','masked'),101:('kdump','enabled'),133:('auditd','enabled'),
            175:('rsyslog','enabled')}
ADDED = set(FILES) | set(PACKAGES) | set(SERVICES)

def mode_pattern(mask):
    return '^('+'|'.join(format(n,'o') for n in range(0o10000) if n & ~mask == 0)+')$'

def rules():
    result = {}
    for n,(path,kind,value) in FILES.items():
        result[n] = [('c:/usr/bin/stat -c '+('%U:%G' if kind=='owner' else '%a')+' '+path,
                      '^'+value+'$' if kind=='owner' else mode_pattern(value)),
                     ('c:/usr/bin/stat -c %F '+path, '^directory$' if n in (179,193,194,195,196,197,198,199,200,201,202) else '^regular (empty )?file$')]
    for n,packages in PACKAGES.items():
        # RPM 的成功輸出必須含正向標記；不依賴退出碼或空輸出。
        result[n] = [('c:/usr/bin/rpm -q --queryformat %{NAME}:installed '+p,'^'+p+':installed$') for p in packages]
    for n,(unit,state) in SERVICES.items():
        props = [('LoadState','loaded' if state!='masked' else 'masked'),
                 ('ActiveState','active' if state=='enabled' else 'inactive'),('UnitFileState',state)]
        result[n] = [('c:/usr/bin/systemctl show '+unit+'.service --property='+k,'^'+k+'='+v+'$') for k,v in props]
    return result

def caveat(n):
    common='命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。'
    if n in FILES:
        path,kind,_=FILES[n]
        text='固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。'
        if path.endswith('-'): text+='備份檔缺失不自動視為不適用，需核准適用性。'
        if n==141: text+='僅來源明列 audit.rules，其他 rules.d 檔案覆蓋待審。'
        if n in (256,257): text+='僅 sshd_config metadata，不代表 Include 或 SSH 內容符合。'
        return text+common
    if n in PACKAGES: return '僅 RPM 資料庫套件存在；不代表服務或內容規則通過。RPM 資料庫錯誤不得以未安裝推論。'+common
    return '分開確認開機狀態與即時狀態；不接受 not-found、static、alias、enabled-runtime；不存在不自動通過；多次查詢非原子。'+common
