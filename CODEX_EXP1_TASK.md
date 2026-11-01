# LinuxGCB EXP-1 任務：每條 check 增加「合規設定值」（expected）欄位

## 動機（真機實測結論，2026-10-31）
Wazuh Dashboard SCA app 已顯示 command（檢核方式指令），但無合規值欄。
4.14 實測：政策 check 的自訂頂層欄位（如 "expected"）與 compliance 自訂 key 都會被 Agent 剝除；
進 indexer 的 check 文件只有 command/compliance/description/id/result/title。
→ **唯一承載管道是 description 欄**。

## 目標
1. 對 53 項已實作 check，從來源 `data/controls.json`（Excel 原文：設定方法/基準值欄位）逐條抽出「合規設定值」，
   以固定格式前置寫入政策 check 的 description：
   `合規值: <value> ｜ Q1 ...`（既有 Q1 治理文字保留在後面）
   - 無法從來源明確抽出者：`合規值: 待確認（來源未提供單一基準值）`，不得編造。
   - 布林/存在性類（套件已安裝、服務停用）也要寫具體值，例：`firewalld 已安裝`、`nftables disabled+inactive 或未安裝`。
2. 報表管線：snapshot/report 解析 description 前綴，CSV/HTML 新增 `expected` 欄（無前綴者留空+標記）。
3. 模擬器/測試：既有測試同步更新；新增測試斷言 53 條全有 `合規值:` 前綴、R2 fixture 報表 expected 欄非空。
4. docs/EXP1_REVIEW.md：逐條 expected 值清單與來源 cell 對照（TWGCB ID → 來源欄位），無法抽出者列原因。

## 硬性限制
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets、no external writes beyond workspace。
- 不得執行 Excel「設定方法」內容；expected 僅為報告文字。
- rules/command/condition 一字不可改（FIX-1 已真機驗證，不得回歸）。
- 政策 name 仍含 UNVALIDATED；來源 xlsx、TWGCB ID、307/7 scope 不變。
- 合成 fixtures 標 test-only；R2/R3 真實 fixtures 數值不可改。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過；`build && validate` 過
- 用 tests/fixtures/realhost_r3.json 跑 snapshot→report，CSV 有 expected 欄且 53 條 raw 觀察列非空
- git commit（.git 唯讀則保留工作目錄變更並回報）
