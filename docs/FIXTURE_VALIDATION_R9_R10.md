# LinuxGCB 正向案例驗證（R9/R10，2026-11-01）

依 Commander 核准，對 .61（agent010）施加 GCB 合規 fixture，驗證 P2B3 規則的 PASS 路徑，隨後完整還原。

## 程序
1. 備份：rules.d、auditd.conf、grub、logrotate/rsyslog、sudoers、9 工具 mode → /root/gcb-fixture-backup
2. Fixture：68 行來源 audit 規則（由 controls.json 以檢查同一解析邏輯產生）＋ privileged.rules（真機 setuid/sgid walk 生成）＋ actions.rules＋sudoers logfile＋grub audit 參數＋auditd.conf 32/keep_logs＋工具 750＋aide.conf＋rsyslog FileCreateMode/selector＋journald drop-in＋logrotate GCB stanza＋/var/log/rsyslog 750
3. 本機預驗（w_strtok→argv）：35/38 PASS
4. R9 引擎掃描 → 還原 → R10 引擎掃描

## 結果
- **R9：35 條 FAIL→PASS**（base 63→98，score 56→88）；既有 62 條結果零變動（無 side-effect）
- **R10：與 R8 逐 check 完全相同**（63P/48F）→ 還原完整、雙向（正/負）路徑皆經引擎實證
- 資料：`data/realhost_scan_20261101_r9.json`、`realhost_scan_20261101_r10.json`

## 正向驗證後仍 FAIL 的 3 條 → 規則缺陷（FIX-4）
1. **900176（0176 rsyslog 預設權限）— 假阴性**：RHEL9 預設 `/etc/rsyslog.conf` 的 `module(load="imuxsock" … FileCreateMode="0644")` 是 imuxsock **state file** 參數，非日誌檔案建立模式；規則 overrides 正則把 module 參數誤當日誌模式（0644 & ~0640 ≠ 0）→ 預設 RHEL9 即使已設 `$FileCreateMode 0640` 仍 FAIL。修法：fileCreateMode 只從 `action(type="omfile"…)` 行抽取，排除 `module(` 行。
2. **900143/900144（audit 工具權限/擁有者）— 設計性不可能 PASS**：來源 9 工具含 `audisp-remote`/`audisp-syslog`，RHEL9 audit 3.x 已移除 audisp plugin 系統，該二檔不存在 → `all()` 永遠 FAIL。修法（依 FIX-1 先例，來源解讀待批）：不存在工具跳過，存在工具照檢查，caveat 記錄。

## 操作教訓
- 備份再用 `cp -a src dst` 時若 dst 已存在會巢狀成 dst/src；套 fixture 的 apply 重跑前須先清 dst（本次殘留 /etc/audit/rules.d/rules.d 已清除，R10 確認無影響）。
- privileged.rules 生成必須與檢查的 walk 邏輯一致（xdev、排除 symlink 目錄、pseudo fs 清單），否則 PASS 路徑對不上。

## 狀態
.61 已回原狀（R10 引擎證據＋檔案級抽驗：audit.rules 原內容、max_log_file=8、auditctl 755、grub 無 audit=1）。fixture 與備份暫存檔已清除。

## FIX-4 後續（R11/R12，同日完成）
FIX-4（workspace LinuxGCB-codex-fix4 @693ad43，僅動 900143/144/176，143 條 diff=0，77 測試過）部署後：
- **R11（無 fixture）**：base 64P/47F — 900144 FAIL→PASS 即修正效果（真機工具擁有權本來合規，舊規則因 audisp 缺檔永遠假阴性）；143（755 實缺）與 176（無 FileCreateMode 實缺）正確仍 FAIL。
- **R12（fixture 重套）**：base **101P/10F，score 90** — 38/38 全轉 PASS，引擎實證三條修正生效。剩 10 FAIL 全為歷史真實缺失（900187/188 + cron 權限/allow 8 條）。
- 還原後抽驗：僅 900144 保持 PASS（FIX-4 正確語意），其餘回 FAIL；rules.d 僅剩原 audit.rules。
- 資料：`data/realhost_scan_20261101_r11.json`、`realhost_scan_20261101_r12.json`。
- 待批（來源解讀）：0143/0144「不存在工具跳過」與 0176「fileCreateMode 只認 omfile action」兩項語意，依 FIX-1 先例實施，正式納管前需來源審查確認。
