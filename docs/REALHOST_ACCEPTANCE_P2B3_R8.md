# LinuxGCB 真機驗收 — P2B3（R8，2026-11-01）

端點：192.168.1.61（RHEL 9，agent 010，群組 linuxgcb）；Manager 192.168.1.53。
政策：base a623de08…（P2B3，111 checks）、firewalld 08e97373…、sshd 34b2d3b4…（未變）。
原始結果：`data/realhost_scan_20261101_r8.json`（Manager API 分頁收齊）。
部署前備份：Manager `/var/ossec/etc/shared/linuxgcb.bak.p2b3.202610311433`。

## 1. 掃描摘要
| 政策 | pass | fail | total | score |
|---|---|---|---|---|
| linuxgcb_rhel9_base_v01 | 63 | 48 | 111 | 56 |
| linuxgcb_rhel9_firewalld_v01 | 3 | 0 | 3 | 100 |
| linuxgcb_rhel9_sshd_v01 | 20 | 12 | 32 | 62 |

新增 49 條全執行：**11 PASS / 38 FAIL**。

## 2. 引擎層驗證（本批主要目的）
- **多行內嵌 Python `c:` 命令在真引擎完整執行**：900136–140（同模式）PASS 證明 w_strtok 雙引號包裝 + 換行 + 巢狀單引號往返正確；無截斷、無引號破損。
- 38 條 FAIL 以 w_strtok→argv 直接（忠於引擎、非多一層 shell）在真機 root 重跑：全部 rc=0、無 stderr、無 PASS 輸出 → 與引擎結果一致，**無假阴性**。
- 教訓：外層多包一層 `sh -c` 驗證會把腳本內 `$FileCreateMode` 當 shell 變數展開造成 re.error 假崩潰；對帳必須用 argv 直接。

## 3. 38 FAIL 真機實值對帳（全部真實缺失）
- 0134/0135：GRUB_CMDLINE_LINUX 無 `audit=1`/`audit_backlog_limit=8192`。
- 0143/0144：audit 工具實測 755（基準 750）。
- 0145：aide 未安裝。
- 0146/0147：`max_log_file=8`（要求 ≥32）、`max_log_file_action=ROTATE`（要求 keep_logs）。
- 0148–0172：`/etc/audit/rules.d/` 僅預設 audit.rules（-D/-b/-f），無任何基準 `-w`/`-a` 規則（含 0171 faillock `-w /var/log/faillock -p wa -k logins`）。
- 0173：無 `-e 2`。
- 0176：rsyslog 全境無 `$FileCreateMode`/`fileCreateMode`。
- 0177：預設 selector 不符基準三類 selector→secure 要求。
- 0181：journald 未明確 `Compress=yes`（來源設定方法為明確新增；預設 yes 不视为已設定，解讀見 P2B3 caveats）。
- 0182：未明確 `Storage=persistent` 且 `/var/log/journal` 不存在（volatile）。
- 0308：`/etc/logrotate.d/rsyslog` 為 RHEL 預設 stanza，非基準要求的 `/var/log/rsyslog/*.log` weekly/rotate 4/compress 結構；`/var/log/rsyslog` 目錄不存在。

## 4. 11 PASS 抽驗
0092/0096/0099/0100（xinetd、net-snmp、vsftpd、ypserv 未安裝）、0093 chrony active+server 來源、0095 avahi 停用、0136 postmaster: root、0137–0140 `/var/log/audit` 目錄 700/檔 600 root（RHEL9 預設即符合）。

## 5. 治理狀態
146 條 raw 結果皆 `execution_review=blocked` → 報表 MANUAL_PENDING 247 / FAIL 60 / EXCLUDED 7；verified_decided=0。raw PASS 不宣稱已驗證符合。
待辦：正向案例（compliant fixture）驗證需對 .61 施加基準設定（rules.d 規則、FileCreateMode、journald、logrotate、GRUB），屬主機變更，**待 Commander 核准**後以備份/回復流程執行。

## 6. 報表
`reports/RHEL9_010_20261101_r8/`（HTML/CSV）＋ `RHEL9_010_20261101_r8_snapshot.json`。
