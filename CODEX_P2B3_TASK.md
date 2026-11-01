# LinuxGCB P2B3 任務：日誌與稽核 43 條 + 系統服務 6 條（離線開發）

## 背景
- 基準：RHEL9 GCB v1.2；母體 314、scope 307（Nftables 7 排除）。目前 97 候選（base 62 + firewalld 3 + sshd 32），FIX-3 已合併（branch 起點 372a93e）。
- 真機 R7（2026-11-01，agent010/.61）：FIX-3 後 97 條全執行；剩 22 條 FAIL 全部為真機真實缺失（規則正確），不再處理。
- 本批新增 49 條，全部來自 data/controls.json 未實作項，類別與 ID 如下（SCA 數字 ID 沿用 registry 慣例 900000+序號，例 TWGCB-01-012-0134 → 900134；建號前查 registry 防撞號）：
  - 日誌與稽核（43）: 0134, 0135, 0136, 0137, 0138, 0139, 0140, 0143, 0144, 0145, 0146, 0147, 0148, 0149, 0150, 0151, 0152, 0153, 0154, 0155, 0156, 0157, 0158, 0159, 0160, 0161, 0162, 0163, 0164, 0165, 0166, 0167, 0168, 0169, 0170, 0171, 0172, 0173, 0176, 0177, 0181, 0182, 0308
  - 系統服務（6）: 0092, 0093, 0095, 0096, 0099, 0100
- 每條的說明、設定方法、期望值在 data/controls.json 與 coverage_manifest 的 docx_cells；以來源為準，不得自行放寬。

## 設計要求（沿用既有慣例與教訓）
1. **套件不存在類**（0092 xinetd、0096 SNMP、0099 FTP、0100 NIS 等）：沿用 FIX-3 定向 `rpm -q` 三態單行模式（INSTALLED/ABSENT，非零其他退出碼 → 無輸出 → 不合格）。禁止 `rpm -qa` 全量清單。
2. **服務停用類**（0095 avahi-daemon、0100 NIS 服務面）：沿用 FIX-1 systemctl 模式（disabled/masked 且 inactive 為合格；not-found 依來源判定）。
3. **auditd 規則類**（0148–0172、0173）：以持久規則 `/etc/audit/rules.d/*.rules`（含來源指定的檔名）為主體正則檢核；正則必須排除註解行（行首 `#`）與誤匹配（如 `-w /etc/sudoers` 不應匹配 `/etc/sudoers.d` 行——用行錨點/邊界）。0173 不變模式查 `-e 2`。每條依來源指定之 `-w`/`-a` 語意寫規則，不得以「存在任何 audit 規則」代替特定規則存在。
4. **auditd 設定/檔案類**（0134–0147、0161）：查 `/etc/audit/auditd.conf` 有效值（最後一個未註解指定鍵勝過先前值）、`/var/log/audit` 目錄與檔案權限/擁有者（位元遮罩語意，「或更嚴格」）、audit 工具檔權限/擁有者。
5. **rsyslog/journald/logrotate**（0171、0176、0177、0181、0182、0308）：注意 FIX-3 已確立的 rsyslog 新式 `action(type="omfile" file="...")` 與舊式語法並存問題；journald 查 `/etc/systemd/journald.conf`（含 journald.conf.d override），**來源期望值等於 RHEL9 套件預設時，未設定（預設生效）是否合格須依來源文字判定並在 caveats 記錄解讀**，不得自行假設。0308 logrotate 查 /etc/logrotate.d 內 rsyslog 條目存在性依來源文字。
6. **sh -c 包裝**：任何 `c:/bin/sh -c "..."` 必須符合 FIX-2 的 w_strtok 雙引號包裝規則（內部雙引號 `\\\"` 跳脫、不可有裸管線語意誤解）；並通過模擬器的 256 行截斷模型（輸出行數不可依賴 >256 行）。
7. 模擬器/fixture：每條新規則至少 positive、negative、missing、empty、error 五案例；規則類加「規則被註解」案例；套件類加「rpm 其他錯誤退出碼」案例。fixture 標記 test-only。

## 硬性限制
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets、no external writes beyond workspace。
- 不得執行 Excel「設定方法」；來源檔、TWGCB ID、307/7 scope、既有 97 條 rules 不可改（rules diff=0）。
- 政策 name 維持 UNVALIDATED；R2/R3/R6/R7 fixtures 與真機證據檔不可改。
- coverage_manifest 更新為 146 候選；新條目 review_status=human_review_pending、execution_review=blocked、live_validation=UNVALIDATED。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過；`build && validate` 過（146 候選）
- 既有 97 條 rules diff=0；49 條新規則通過上述案例矩陣
- git commit（.git 唯讀則保留工作目錄變更並回報）
- docs/P2B3_REVIEW.md：49 條清單（ID、機轉、caveats）+ 檔案清單 + before/after 摘要
