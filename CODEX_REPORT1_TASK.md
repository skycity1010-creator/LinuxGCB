# LinuxGCB REPORT-1 任務：真機快照匯入 + 報表管線（離線開發）

## 背景
FIX-1 已真機驗證（R2 掃描 2026-10-31 12:03）：53 項 check、46 pass / 7 fail（全部為真實缺失：cron 權限 6 項 + PermitRootLogin）。
Manager 4.14 已無 `/sca/{agent}/checks` API；完整結果由 Manager 本機 SQLite `/var/ossec/queue/db/{agent_id}.db` 匯出（tables sca_check / sca_scan_info / sca_check_rules；latest scan per policy: `select scan_id from sca_check where policy_id=? group by scan_id order by max(rowid) desc limit 1`；sca_scan_info.hash 與 sca_check.scan_id 不可 join）。
真機原始匯出範例（真實證據，非合成）：`/home/skycity1010/projects/LinuxGCB/data/realhost_scan_20261031_r2.json`（結構：{policy_id: {scan_id, checks:[{id,title,description,rationale,remediation,command,result,reason}]}}）。

## 目標
1. 新增 `linuxgcb/snapshot.py`（或擴充 collector）：把上述 Manager DB 匯出 JSON 轉成既有 report 模組的 snapshot schema v1：
   - `synthetic: false`、label 標明「真實掃描證據（agent 010 / RHEL9 192.168.1.61）」
   - `source_sha256`、`policy_hashes` 如實計算自 policies/*.yml
   - host: agent_id=010、approved_profiles=[base,firewalld,sshd]、scanned_at 取自 sca_scan_info（UTC ISO8601）
   - checks 逐項 id/result；保留 raw reason
   - 任何 result 非 passed/failed（invalid/error）必須如實帶入，不得吞掉
2. `python3 -m linuxgcb report` 輸入該 snapshot 輸出 HTML/CSV：
   - 7 項 FAIL 逐項含 TWGCB ID、title、command、remediation（政策內 remediation 欄）
   - 分數與 coverage 標記沿用既有治理語意（UNVALIDATED 候選不得計為已驗證符合）
3. 新增測試：以 R2 真實匯出（複製為 tests/fixtures/realhost_r2.json，label 標 REAL EVIDENCE agent010）驅動 snapshot 轉換與報表，斷言 46 pass/7 fail、7 個 FAIL id 正確。
4. CLI：`python3 -m linuxgcb snapshot <manager_dump.json> --out <snapshot.json>` 之類子命令（名稱自定但需寫入 README）。

## 硬性限制
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets、no external writes beyond this workspace。
- 不得執行任何 Excel/DOCX 修復指令；不得掃描開發機冒充 RHEL9。
- 合成 fixtures 標 test-only；R2 匯出標真實證據且不可被改寫數值。
- 政策檔本批不得修改（UNVALIDATED 狀態不變）；來源 xlsx、TWGCB ID、307/7 scope 不變。
- 不做排程、寄送、Grafana 整合。

## 驗收
- `python3 -m unittest discover -s tests -v` 全數通過
- `python3 -m linuxgcb build && python3 -m linuxgcb validate` 通過
- 用 R2 fixture 實際跑 snapshot→report，輸出目錄內 HTML/CSV 存在且內容含 7 FAIL 明細
- git commit 於 branch codex/linuxgcb-report1（若 .git 唯讀則保留工作目錄變更並回報）
- docs/REPORT1_REVIEW.md：檔案清單、snapshot 欄位對應表、報表樣本路徑
