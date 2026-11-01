# LinuxGCB 真機加固（R13，2026-11-01）

Commander 指示「先處理缺失」。對 .61（agent010）依 GCB v1.2 來源設定方法加固。備份：`/root/gcb-remediation-backup/`（sshd_config、cron modes、wazuh labels、deny 檔）。

## 已修正（R13 引擎實證）
**SSH 12 條**（`/etc/ssh/sshd_config.d/00-gcb-hardening.conf`，00- 前綴勝過 RHEL 預設 01-permitrootlogin 之 first-match）：
- 0258 AllowUsers skycity1010、0263 Ciphers/MACs/KexAlgorithms 精確清單、0265 X11Forwarding no、0266 MaxAuthTries 4、0269 PermitRootLogin no、0272 ClientAliveInterval 600+CountMax 1、0273 LoginGraceTime 60、0275 AllowTcpForwarding no、0276 MaxStartups 10:30:60、0277 MaxSessions 4、0280 IgnoreUserKnownHosts yes（sshd 接受此共享選項，`sshd -t` 驗證有效）、0315 GSSAPIAuthentication no
- **sshd 政策 32/32 PASS，score 100**；`sshd -t` 通過後重啟，新連線實測正常

**cron 8 條**：crontab 600、cron.{hourly,daily,weekly,monthly,d} 700、cron.allow/at.allow 建立（root:root 600）、cron.deny/at.deny 移除
- base 64→72 PASS

## 未以加固解決的 2 條
- **0187 未受限程序**：來源方法為 chcon 至非 unconfined_service_t 域。真機嘗試 `chcon -t bin_t` 無效——SELinux 無 wazuh 政策模組時 systemd 對無轉換規則服務一律給 unconfined_service_t（已 restorecon 復原，agent 正常）。真正修正需自製 SELinux policy（高風險弄壞 agent）。→ **例外立項**（見 EXCEPTIONS.md）。
- **0188 setroubleshoot**：真機早已未安裝，FAIL 為規則缺陷（rpm -qa 全量清單 256 行截斷，FIX-3 同型漏網；R6 誤判為真實缺失）→ FIX-5 修正中。

## R13 摘要
- sshd 32/32（100）、firewalld 3/3（100）、base 72/111（64）
- base 剩 39 FAIL = 37 條日誌/稽核基準設定（audit rules、FileCreateMode、journald、logrotate、GRUB、auditd.conf、工具 750、aide；fixture R9/R12 已證明可修，是否永久套用待 Commander 決定，注意 -e 2 鎖定與 logrotate stanza 替換含預設輪替移除）+ 0187 例外 + 0188 規則缺陷
- 資料：`data/realhost_scan_20261101_r13.json`（待存）
