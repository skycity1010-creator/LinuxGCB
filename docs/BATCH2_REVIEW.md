# BATCH2 離線候選審查

本批完成 registry 指定四類的全部未實作項目：**新增 44，53 → 97**，不是預估的 51／104。基線為 `tests/fixtures/batch2_baseline.json`（保存原 53 個 emitted check 完整物件、既有輸出 fixtures 的 canonical hash、來源及 R2/R3 hash）。307 included／7 excluded、所有 TWGCB/sca_id 不變；Nftables配置七項仍 excluded。未擴張其他類別。

| 類別 | registry 總數 | 批前已實作 | 新增 | 批後未實作 |
| --- | ---: | ---: | ---: | ---: |
| SSH設定 | 32 | 4 | 28 | 0 |
| cron設定 | 16 | 12 | 4 | 0 |
| SELinux | 7 | 1 | 6 | 0 |
| 安裝與維護軟體 | 6 | 0 | 6 | 0 |

## 沿用模式與必要差異

- 原有 53 checks（包括 description、rules 與 FIX-1 服務狀態組合）完整物件差異為零；firewalld 政策整檔亦不變。原有 tests 保留行為斷言，僅全域數量改為新增後數量，Q1/EXP-1 專屬斷言仍檢查原 53。新增 crond/sshd 是來源要求 enabled+active 的服務，且 sshd 要求 openssh-server 已安裝；不是停用服務，沒有新增停用服務以重寫 FIX-1。
- 每條 description 仍為 `合規值: <具體基準值> ｜ <治理備註>`，新增治理標籤為 BATCH2。0258 的組織授權清單無單一基準值，明示 `待確認（來源未提供單一基準值）`，不使用來源示例 smith/jones 冒充正式清單。
- SSH 以 `sshd -T` 預設情境有效值為主，沿用 Include/Match、使用者/來源矩陣限制。0255 以成功標記加規則層級否定排除非 Protocol 2，接受現代版本不輸出已移除的 Protocol 欄。0279 接受 no/delayed，以及 RHEL9 OpenSSH 8.0+ 的 yes（僅認證後壓縮）；此預設/等價依據寫在 description，仍須 RHEL9 引擎驗證。
- **Q1-01 差異不能隱瞞**：原專案不存在已實作的 exit-code 保護；既有測試明確要求非零且 stdout 匹配仍 raw PASS。因此不能同時「保留原 53 diff=0」又聲稱已修復它們。只為新增命令加入 `out=$(command); rc=$?` 緩衝保護；exit 0 才發布完整 stdout 與 `LINUXGCB_COMMAND_OK`，非零不發布 stdout、保留退出狀態。每個命令另有正向成功標記必要條件。只讀 shell 命令全部固定明列；不執行來源 F 欄的 remediation。引擎 argv/quoting、stderr 合併、輸出截斷與 timeout 均未真機驗證，execution_review 仍 blocked。
- 模擬器只對精確白名單的新增 emitted rules 支援 `not c:` 全規則否定，並將明確非零執行回 UNRESOLVED；原 53 的輸出模型保留。實際 guard 非零會提供空 stdout、無成功標記，因而至少一條必要規則 FAIL，不能 PASS。UNRESOLVED 是離線證據分類，不能宣稱 Wazuh 必然產生同名結果。
- 不使用 `!r:` 表達「整份輸出不存在」。隨附 [Wazuh 文件](references/creating-custom-policies.md) 的 content-negation 段落指出 `!r:` 是逐行判斷，任一無關行可能導致通過；本批使用 `not c:... -> r:禁止內容`，再以 all 加上成功標記，失敗或空輸出不能藉否定而假通過。
- 套件移除先成功列舉整個 RPM DB，再否定指定套件名稱，避免把 rpm 查詢錯誤解釋成未安裝。主機鑰匙依來源 find 集合檢查，必須至少有一把且不得有任何不符 metadata 的成員。不存在檔案以成功 find + 規則否定檢查，權限錯誤不得通過。
- DOCX 0272 同時包含修訂歷史 CountMax=0 與現行 CountMax=1；採用 XLSX F/G 與 DOCX 現行/修改後值 1，coverage manifest 另存 `docx_historical_cells`，不刪歷史或放寬成 0。

## 測試與保留限制

`python3 -m linuxgcb build`、`python3 -m linuxgcb validate`、`python3 -m unittest discover -s tests -v` 為驗收命令。測試結果保存於 `docs/BATCH2_TEST_OUTPUT.txt`。97 個候選皆 UNVALIDATED；coverage full=0 / partial=92 / blocked=5，execution_review 97 blocked。離線成功不等於 RHEL9／Wazuh 實機通過。

`python3 -m scripts.batch2_fixtures` 由已發出的 check/rule targets 加上獨立作者提供的正反輸出樣本重建新增 fixtures；`python3 -m scripts.batch2_review` 重建本文件。所有命令都只建置／測試本地資料，不掃描開發機冒充 RHEL9。唯一子程序 guard 測試先從 emitted shell 取出腳本，完整替換其中的 inventory 命令為合成 printf/exit，再執行；不會執行任何政策命令或設定方法。

每條至少 positive、negative、missing、empty、error、nonzero_matching；另外逐條 source predicate 反例，逐 target 缺失、權限失敗與非零匹配。範圍/基線測試核對原 53 checks 全物件、原 fixtures hash、原 controls/XLSX/R2/R3 hash；既有 FIX-1、報表與真實快照測試仍保留。邊界包括 1–4、1–600、1–60、所有權限位元及特殊位元、cipher/MAC/KEX 三者獨立變壞、好/壞鑰匙混合、Protocol 缺省與錯誤版本。

已知 partial 範圍：0107/0185/0186/0205/0284 的文字設定不是完整載入順序解析；0184 僅 /etc/default/grub，未宣稱已產生 grub.cfg/實際開機參數符合；0185 接受 targeted 或來源允許更嚴格的 mls；0258 授權清單仍須人工核准；0260 來源敘述文字提 600，但 F 命令與 G 期望為 640，依 F/G 實作並保留差異。0259–0262 只涵蓋來源 type f 集合，未解決 ACL、symlink 與額外 HostKey 路徑。0282/0283 的全檔案系統 find 有 timeout／掛載邊界限制。所有治理備註逐條保留於 description。

## 逐條規則與來源 cells

下表 F/G 為原始 XLSX 的設定方法／期望欄，等同 `controls.json.configuration_method`／`expected`；不修改原始資料。每行的 fixture 路徑均為 `tests/fixtures/rule_outputs.json#<sca_id>`。正反樣本依子規則列示，實際 fixture 合併同命令的輸出並補成功標記；「空集合」只有在命令成功與成功標記存在時才可能符合不存在條件。規則摘要前綴 `not` 表示整個輸出不得存在匹配行。位元子集合以簡寫呈現，完整 emitted regex 保存在政策中。

| sca_id / TWGCB ID | 規則摘要 | 正案例輸出（依子規則） | 反案例輸出（依子規則） | 合規值 | 來源 cell 與原 G 值 |
| --- | --- | --- | --- | --- | --- |
| 900102 / TWGCB-01-012-0102 NIS用戶端套件 | /usr/bin/rpm -qa --queryformat '%{NAME}\n' → not ^ypbind$ | bash<br>coreutils | ypbind | ypbind 未安裝 | 基本項目!F106 / G106；G=移除 |
| 900103 / TWGCB-01-012-0103 telnet用戶端套件 | /usr/bin/rpm -qa --queryformat '%{NAME}\n' → not ^telnet$ | bash<br>coreutils | telnet | telnet 未安裝 | 基本項目!F107 / G107；G=移除 |
| 900104 / TWGCB-01-012-0104 telnet伺服器套件 | /usr/bin/rpm -qa --queryformat '%{NAME}\n' → not ^telnet-server$ | bash<br>coreutils | telnet-server | telnet-server 未安裝 | 基本項目!F108 / G108；G=移除 |
| 900105 / TWGCB-01-012-0105 rsh伺服器套件 | /usr/bin/rpm -qa --queryformat '%{NAME}\n' → not ^rsh-server$ | bash<br>coreutils | rsh-server | rsh-server 未安裝 | 基本項目!F109 / G109；G=移除 |
| 900106 / TWGCB-01-012-0106 tftp伺服器套件 | /usr/bin/rpm -qa --queryformat '%{NAME}\n' → not ^tftp-server$ | bash<br>coreutils | tftp-server | tftp-server 未安裝 | 基本項目!F110 / G110；G=移除 |
| 900107 / TWGCB-01-012-0107 更新套件後移除舊版本元件 | /usr/bin/cat /etc/yum.conf → ^[ \t]*clean_requirements_on_remove[ \t]*=[ \t]*[Tt]rue[ \t]*$<br>/usr/bin/cat /etc/dnf/dnf.conf → ^[ \t]*clean_requirements_on_remove[ \t]*=[ \t]*[Tt]rue[ \t]*$ | [main]<br>clean_requirements_on_remove=True<br>[main]<br>clean_requirements_on_remove=True | [main]<br>clean_requirements_on_remove=False<br>[main]<br>clean_requirements_on_remove=False | clean_requirements_on_remove=True（/etc/yum.conf 與 /etc/dnf/dnf.conf） | 基本項目!F111 / G111；G=True |
| 900184 / TWGCB-01-012-0184 開機載入程式啟用SELinux | /usr/bin/cat /etc/default/grub → not ^[ \t]*GRUB_CMDLINE_LINUX[^=]*=.*(selinux=0&#124;enforcing=0) | GRUB_CMDLINE_LINUX="quiet" | GRUB_CMDLINE_LINUX="selinux=0" | 所有 GRUB_CMDLINE_LINUX* 不含 selinux=0 或 enforcing=0 | 基本項目!F187 / G187；G=啟用 |
| 900185 / TWGCB-01-012-0185 SELinux政策 | /usr/bin/cat /etc/selinux/config → ^[ \t]*SELINUXTYPE=(targeted&#124;mls)[ \t]*$ | SELINUXTYPE=targeted | SELINUXTYPE=minimum | SELINUXTYPE=targeted（或來源允許之更嚴格 mls） | 基本項目!F188 / G188；G=targeted或更嚴格之政策 |
| 900186 / TWGCB-01-012-0186 SELinux啟用狀態 | /usr/bin/cat /etc/selinux/config → ^[ \t]*SELINUX=enforcing[ \t]*$<br>/usr/sbin/getenforce → ^Enforcing$ | SELINUX=enforcing<br>Enforcing | SELINUX=permissive<br>Permissive | SELINUX=enforcing；即時 enforcing | 基本項目!F189 / G189；G=enforcing |
| 900187 / TWGCB-01-012-0187 未受限程序 | /usr/bin/ps -eZf → not unconfined_service_t | system_u:system_r:init_t:s0 root 1 | system_u:system_r:unconfined_service_t:s0 root 2 | 無 unconfined_service_t 程序 | 基本項目!F190 / G190；G=無未受限程序 |
| 900188 / TWGCB-01-012-0188 setroubleshoot套件 | /usr/bin/rpm -qa --queryformat '%{NAME}\n' → not ^setroubleshoot$ | bash<br>coreutils | setroubleshoot | setroubleshoot 未安裝 | 基本項目!F191 / G191；G=移除 |
| 900189 / TWGCB-01-012-0189 mcstrans套件 | /usr/bin/rpm -qa --queryformat '%{NAME}\n' → not ^mcstrans$ | bash<br>coreutils | mcstrans | mcstrans 未安裝 | 基本項目!F192 / G192；G=移除 |
| 900190 / TWGCB-01-012-0190 cron守護程序 | /usr/bin/systemctl show crond.service --property=LoadState → ^LoadState=loaded$<br>/usr/bin/systemctl show crond.service --property=ActiveState → ^ActiveState=active$<br>/usr/bin/systemctl show crond.service --property=UnitFileState → ^UnitFileState=enabled$ | LoadState=loaded<br>ActiveState=active<br>UnitFileState=enabled | LoadState=wrong<br>ActiveState=wrong<br>UnitFileState=wrong | crond enabled+active | 基本項目!F193 / G193；G=啟用 |
| 900203 / TWGCB-01-012-0203 at.allow與cron.allow檔案所有權 | /usr/bin/stat -c %U:%G /etc/at.allow → ^root:root$<br>/usr/bin/stat -c %U:%G /etc/cron.allow → ^root:root$<br>/usr/bin/find /etc -maxdepth 1 -name '*.deny' → not ^/etc/(at&#124;cron)[.]deny$ | root:root<br>root:root<br>空集合 | nobody:root<br>nobody:root<br>/etc/cron.deny | root:root；/etc/at.deny 與 /etc/cron.deny 不存在 | 基本項目!F206 / G206；G=root:root |
| 900204 / TWGCB-01-012-0204 at.allow與cron.allow檔案權限 | /usr/bin/stat -c %a /etc/at.allow → ^(0&#124;200&#124;400&#124;600)$<br>/usr/bin/stat -c %a /etc/cron.allow → ^(0&#124;200&#124;400&#124;600)$<br>/usr/bin/find /etc -maxdepth 1 -name '*.deny' → not ^/etc/(at&#124;cron)[.]deny$ | 600<br>600<br>空集合 | 666<br>666<br>/etc/cron.deny | 600 或更低權限；/etc/at.deny 與 /etc/cron.deny 不存在 | 基本項目!F207 / G207；G=600或更低權限 |
| 900205 / TWGCB-01-012-0205 cron日誌記錄功能 | /usr/bin/cat /etc/rsyslog.conf && /usr/bin/find /etc/rsyslog.d -maxdepth 1 -type f -name '*.conf' -exec /usr/bin/cat {} + → ^[ \t]*cron[.][*][ \t]+/var/log/cron[ \t]*$ | cron.* /var/log/cron | cron.none /var/log/cron | cron.* /var/log/cron | 基本項目!F208 / G208；G=啟用 |
| 900254 / TWGCB-01-012-0254 sshd守護程序 | /usr/bin/systemctl show sshd.service --property=LoadState → ^LoadState=loaded$<br>/usr/bin/systemctl show sshd.service --property=ActiveState → ^ActiveState=active$<br>/usr/bin/systemctl show sshd.service --property=UnitFileState → ^UnitFileState=enabled$<br>/usr/bin/rpm -q --queryformat '%{NAME}:installed' openssh-server → ^openssh-server:installed$ | LoadState=loaded<br>ActiveState=active<br>UnitFileState=enabled<br>openssh-server:installed | LoadState=wrong<br>ActiveState=wrong<br>UnitFileState=wrong<br>package openssh-server is not installed | openssh-server 已安裝；sshd enabled+active | SSH伺服器!F5 / G5；G=啟用 |
| 900255 / TWGCB-01-012-0255 SSH協定版本 | /usr/sbin/sshd -T → not ^protocol (?!2$).+ | port 22 | protocol 1 | Protocol 2 | SSH伺服器!F6 / G6；G=Protocol 2 |
| 900258 / TWGCB-01-012-0258 限制存取SSH | /usr/sbin/sshd -T → ^(allowusers&#124;allowgroups&#124;denyusers&#124;denygroups) .+ | allowusers approved_user | port 22 | 待確認（來源未提供單一基準值） | SSH伺服器!F9 / G9；G=啟用 |
| 900259 / TWGCB-01-012-0259 SSH主機私鑰檔案所有權 | /usr/bin/find /etc/ssh -xdev -type f -name 'ssh_host_*_key' -exec /usr/bin/stat -c %U:%G {} + → ^root:ssh_keys$<br>/usr/bin/find /etc/ssh -xdev -type f -name 'ssh_host_*_key' -exec /usr/bin/stat -c %U:%G {} + → not ^(?!root:ssh_keys$&#124;LINUXGCB_COMMAND_OK$).+ | root:ssh_keys<br>root:ssh_keys | root:root<br>root:root | root:ssh_keys | SSH伺服器!F10 / G10；G=root:ssh_keys |
| 900260 / TWGCB-01-012-0260 SSH主機私鑰檔案權限 | /usr/bin/find /etc/ssh -xdev -type f -name 'ssh_host_*_key' -exec /usr/bin/stat -c %a {} + → ^(0&#124;40&#124;200&#124;240&#124;400&#124;440&#124;600&#124;640)$<br>/usr/bin/find /etc/ssh -xdev -type f -name 'ssh_host_*_key' -exec /usr/bin/stat -c %a {} + → not ^(?!(0&#124;40&#124;200&#124;240&#124;400&#124;440&#124;600&#124;640)$&#124;LINUXGCB_COMMAND_OK$).+ | 640<br>640 | 666<br>666 | 640 或更低權限 | SSH伺服器!F11 / G11；G=640或更低權限 |
| 900261 / TWGCB-01-012-0261 SSH主機公鑰檔案所有權 | /usr/bin/find /etc/ssh -xdev -type f -name 'ssh_host_*_key.pub' -exec /usr/bin/stat -c %U:%G {} + → ^root:root$<br>/usr/bin/find /etc/ssh -xdev -type f -name 'ssh_host_*_key.pub' -exec /usr/bin/stat -c %U:%G {} + → not ^(?!root:root$&#124;LINUXGCB_COMMAND_OK$).+ | root:root<br>root:root | nobody:root<br>nobody:root | root:root | SSH伺服器!F12 / G12；G=root:root |
| 900262 / TWGCB-01-012-0262 SSH主機公鑰檔案權限 | /usr/bin/find /etc/ssh -xdev -type f -name 'ssh_host_*_key.pub' -exec /usr/bin/stat -c %a {} + → ^(0&#124;4&#124;40&#124;44&#124;200&#124;204&#124;240&#124;244&#124;400&#124;404&#124;440&#124;444&#124;600&#124;604&#124;640&#124;644)$<br>/usr/bin/find /etc/ssh -xdev -type f -name 'ssh_host_*_key.pub' -exec /usr/bin/stat -c %a {} + → not ^(?!(0&#124;4&#124;40&#124;44&#124;200&#124;204&#124;240&#124;244&#124;400&#124;404&#124;440&#124;444&#124;600&#124;604&#124;640&#124;644)$&#124;LINUXGCB_COMMAND_OK$).+ | 644<br>644 | 666<br>666 | 644 或更低權限 | SSH伺服器!F13 / G13；G=644或更低權限 |
| 900263 / TWGCB-01-012-0263 SSH加密演算法 | /usr/sbin/sshd -T → ^ciphers aes128-ctr,aes192-ctr,aes256-ctr$<br>/usr/sbin/sshd -T → ^macs hmac-sha2-512,hmac-sha2-256$<br>/usr/sbin/sshd -T → ^kexalgorithms ecdh-sha2-nistp256,ecdh-sha2-nistp384,ecdh-sha2-nistp521,diffie-hellman-group-exchange-sha256,diffie-hellman-group14-sha256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512$ | ciphers aes128-ctr,aes192-ctr,aes256-ctr<br>macs hmac-sha2-512,hmac-sha2-256<br>kexalgorithms ecdh-sha2-nistp256,ecdh-sha2-nistp384,ecdh-sha2-nistp521,diffie-hellman-group-exchange-sha256,diffie-hellman-group14-sha256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512 | ciphers aes128-cbc<br>macs hmac-md5<br>kexalgorithms diffie-hellman-group1-sha1 | Ciphers aes128-ctr,aes192-ctr,aes256-ctr；MACS=hmac-sha2-512,hmac-sha2-256；KexAlgorithms=ecdh-sha2-nistp256,ecdh-sha2-nistp384,ecdh-sha2-nistp521,diffie-hellman-group-exchange-sha256,diffie-hellman-group14-sha256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512 | SSH伺服器!F14 / G14；G=aes128-ctr,aes192-ctr,aes256-ctr |
| 900264 / TWGCB-01-012-0264 SSH日誌記錄等級 | /usr/sbin/sshd -T → ^loglevel (VERBOSE&#124;INFO)$ | loglevel VERBOSE | loglevel DEBUG | LogLevel VERBOSE 或 INFO | SSH伺服器!F15 / G15；G=VERBOSE或INFO |
| 900265 / TWGCB-01-012-0265 SSH X11Forwarding功能 | /usr/sbin/sshd -T → ^x11forwarding no$ | x11forwarding no | x11forwarding yes | X11Forwarding no | SSH伺服器!F16 / G16；G=no |
| 900266 / TWGCB-01-012-0266 SSH MaxAuthTries參數 | /usr/sbin/sshd -T → ^maxauthtries [1-4]$ | maxauthtries 4 | maxauthtries 0 | MaxAuthTries 4（來源允許 1–4） | SSH伺服器!F17 / G17；G=4以下，但須大於0 |
| 900267 / TWGCB-01-012-0267 SSH IgnoreRhosts參數 | /usr/sbin/sshd -T → ^ignorerhosts yes$ | ignorerhosts yes | ignorerhosts no | IgnoreRhosts yes | SSH伺服器!F18 / G18；G=yes |
| 900268 / TWGCB-01-012-0268 SSH HostbasedAuthentication參數 | /usr/sbin/sshd -T → ^hostbasedauthentication no$ | hostbasedauthentication no | hostbasedauthentication yes | HostbasedAuthentication no | SSH伺服器!F19 / G19；G=no |
| 900271 / TWGCB-01-012-0271 SSH PermitUserEnvironment參數 | /usr/sbin/sshd -T → ^permituserenvironment no$ | permituserenvironment no | permituserenvironment yes | PermitUserEnvironment no | SSH伺服器!F22 / G22；G=no |
| 900272 / TWGCB-01-012-0272 SSH逾時時間 | /usr/sbin/sshd -T → ^clientaliveinterval ([1-9]&#124;[1-9][0-9]&#124;[1-5][0-9]{2}&#124;600)$<br>/usr/sbin/sshd -T → ^clientalivecountmax 1$ | clientaliveinterval 600<br>clientalivecountmax 1 | clientaliveinterval 0<br>clientalivecountmax 0 | ClientAliveInterval 600（來源允許 1–600）；ClientAliveCountMax 1 | SSH伺服器!F23 / G23；G=ClientAliveInterval設為600以下，但須大於0，且ClientAliveCountMax設為1 |
| 900273 / TWGCB-01-012-0273 SSH LoginGraceTime參數 | /usr/sbin/sshd -T → ^logingracetime ([1-9]&#124;[1-5][0-9]&#124;60)$ | logingracetime 60 | logingracetime 0 | LoginGraceTime 60（來源允許 1–60） | SSH伺服器!F24 / G24；G=60以下，但須大於0 |
| 900274 / TWGCB-01-012-0274 SSH UsePAM參數 | /usr/sbin/sshd -T → ^usepam yes$ | usepam yes | usepam no | UsePAM yes | SSH伺服器!F25 / G25；G=yes |
| 900275 / TWGCB-01-012-0275 SSH AllowTcpForwarding參數 | /usr/sbin/sshd -T → ^allowtcpforwarding no$ | allowtcpforwarding no | allowtcpforwarding yes | AllowTcpForwarding no | SSH伺服器!F26 / G26；G=no |
| 900276 / TWGCB-01-012-0276 SSH MaxStartups參數 | /usr/sbin/sshd -T → ^maxstartups 10:30:60$ | maxstartups 10:30:60 | maxstartups 10:30:100 | MaxStartups 10:30:60 | SSH伺服器!F27 / G27；G=10:30:60 |
| 900277 / TWGCB-01-012-0277 SSH MaxSessions參數 | /usr/sbin/sshd -T → ^maxsessions [1-4]$ | maxsessions 4 | maxsessions 0 | MaxSessions 4（來源允許 1–4） | SSH伺服器!F28 / G28；G=4以下，但須大於0 |
| 900278 / TWGCB-01-012-0278 SSH StrictModes參數 | /usr/sbin/sshd -T → ^strictmodes yes$ | strictmodes yes | strictmodes no | StrictModes yes | SSH伺服器!F29 / G29；G=yes |
| 900279 / TWGCB-01-012-0279 SSH Compression參數 | /usr/sbin/sshd -T → ^compression (delayed&#124;no&#124;yes)$ | compression no | compression invalid | Compression delayed 或 no | SSH伺服器!F30 / G30；G=delayed或no |
| 900280 / TWGCB-01-012-0280 SSH IgnoreUserKnownHosts參數 | /usr/sbin/sshd -T → ^ignoreuserknownhosts yes$ | ignoreuserknownhosts yes | ignoreuserknownhosts no | IgnoreUserKnownHosts yes | SSH伺服器!F31 / G31；G=yes |
| 900281 / TWGCB-01-012-0281 SSH PrintLastLog參數 | /usr/sbin/sshd -T → ^printlastlog yes$ | printlastlog yes | printlastlog no | PrintLastLog yes | SSH伺服器!F32 / G32；G=yes |
| 900282 / TWGCB-01-012-0282 shosts.equiv檔案 | /usr/bin/find / -name shosts.equiv → not ^/ | 空集合 | /home/example/shosts.equiv | 移除所有 shosts.equiv | SSH伺服器!F33 / G33；G=移除 |
| 900283 / TWGCB-01-012-0283 .shosts檔案 | /usr/bin/find / -name '*.shosts' → not ^/ | 空集合 | /home/example/.shosts | 移除所有 *.shosts | SSH伺服器!F34 / G34；G=移除 |
| 900284 / TWGCB-01-012-0284 覆寫全系統加密原則 | /usr/bin/cat /etc/sysconfig/sshd → not ^[ \t]*CRYPTO_POLICY[ \t]*= | # CRYPTO_POLICY= | CRYPTO_POLICY= | 不存在未註解的 CRYPTO_POLICY 設定 | SSH伺服器!F35 / G35；G=停用 |
| 900315 / TWGCB-01-012-0315 停用GSSAPI驗證 | /usr/sbin/sshd -T → ^gssapiauthentication no$ | gssapiauthentication no | gssapiauthentication yes | GSSAPIAuthentication no | SSH伺服器!F36 / G36；G=停用 |
