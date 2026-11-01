# FIX-12 驗收 — Dashboard metadata 層調整（R27/R28）

日期：2026-11-01｜工作區：`~/projects/LinuxGCB-codex-fix12`（branch `codex/linuxgcb-fix12`）
Commits：`322773b`（FIX-12 主體）、`b11893d`（FIX-12b 檔案設定類 fallback）、`fe11ed8`（FIX-12c 報告 command 欄解包）

## Commander 指令
1. 先不動 RHEL 上的設定值 → 本批為 **metadata-only**，未觸碰 `.61` 任何設定。
2. 進行第 3 步驟 → exception 旗標進儀表板；人工複審收尾工具就緒。
3. Description 調整為合規值資訊，移除 PoC 過程註解。
4. Check 欄位與實際檢核程序無關者，改為人工檢核需手動下指令的資訊。

## 實作
### 1. Description（Wazuh Dashboard 檢查清單欄位）
- 舊：`合規值: X ｜ P2B7 執行審查 blocked；coverage=partial；…raw PASS 非已驗證符合。…`
- 新：`合規值: X`（僅合規值；PoC 過程註解全部移除）
- Accepted finding 旗標（第 3 步驟 exception 進儀表板）：
  - `900187`、`900229` description 尾綴
    `｜ 【Accepted finding】Commander 2026-11-01 裁定：維持 FAIL，不矯正系統設定（docs/EXCEPTIONS.md）`
- 治理註記（execution_review/coverage/issues）仍保留於 `data/scope_registry.json`，不再顯示於儀表板。

### 2. Rationale（Wazuh Dashboard 檢查詳情欄位）
Wazuh SCA 的 `rules`（Command/Check）是引擎功能欄位，改動會改變判定，**不可**直接替換。
改以 `rationale` 欄承載人工檢核資訊（檢查詳情可見）：
- 來源有 shell 指令者：`人工檢核指令（來源）：stat -c "%a %n" /sbin/auditctl …`
- 檔案設定類（來源無 shell 指令，39 條）：`人工檢核程序（來源）：編輯/etc/security/pwquality.conf檔案，新增或修改成以下內容： Retry = 3`
- 307/307 全覆蓋，無泛化 fallback。

### 3. 自有 HTML/CSV 報告 command 欄
- 嵌入 Python 規則 → 顯示人工檢核指令。
- `sh -c "out=$(CMD); …LINUXGCB_COMMAND_OK…"` 包裝 → 解包顯示真實內部命令。
- `not c:` 否定規則 → 保留 `not` 前綴（例：`/usr/bin/ps -eZf,not /usr/bin/ps -eZf`）。

## 驗證
- 137 單元測試全過（各批釘選測試改為正規化顯示欄位 `nod()`，rules 仍逐條釘選）。
- 三政策逐 check 比對 fix11：**僅 description/rationale 改變，rules/title/compliance 位元相同**。
- R27（FIX-12a）與 R28（FIX-12b）引擎掃描：307 條結果與 R26 **零翻轉**，`165P/142F`（base 128P/142F、sshd 32/32、firewalld 5/5）。
- API 回讀實證：900108/900143/900187/900229/900032 的 description/rationale 均為新格式。
- 部署 sha256：base `92693c57e4ee…`、sshd `a50984e9f2bc…`、firewalld `f0423da0caeb…`（Manager 與本機對帳一致）。

## 產出
- `data/realhost_scan_20261101_r27.json`、`data/realhost_scan_20261101_r28.json`
- `reports/RHEL9_010_20261101_r28_snapshot.json`、`reports/RHEL9_010_20261101_r28/`（report.html/csv）

## 第 3 步驟狀態
- exception 旗標：已進儀表板（0187/0229）。
- UNVALIDATED 人工複審：工具已備妥 — 審查者可對每條檢查照 rationale 的人工指令手動驗證。
  政策維持 UNVALIDATED 旗標，待 Commander 完成人工複審後才可轉 VERIFIED（本專案不得自行核准）。
