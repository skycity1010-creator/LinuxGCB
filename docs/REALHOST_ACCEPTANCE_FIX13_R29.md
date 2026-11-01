# FIX-13 驗收：治理狀態轉 VERIFIED（2026-11-01）

## 依據
Commander 於 2026-11-01 回覆「均已驗證」（Discord #專案 / Wazuh SCA LinuxGCB thread），
確認 307 條候選全部完成人工複審。

## 變更內容（commit c55b0d8 / 88328d9，branch codex/linuxgcb-fix12）
1. `linuxgcb/quality.py`：全部批次治理欄位轉為
   - `offline_review = completed_with_findings`
   - `execution_review = passed`
   - `source_approval = approved`
   - `live_validation = VALIDATED`、`verified_on = 2026-11-01`、`verified_by = Commander`
2. `linuxgcb/catalog.py`：coverage partial 僅保留 4 條範圍保留項：
   - `108`：僅雙協定即時值；持久設定來源、覆寫順序與路由角色未涵蓋
   - `141`：僅來源設定方法明列 audit.rules；其餘 rules.d 規則檔集合未涵蓋
   - `269`/`270`：僅 sshd -T 預設情境；Include/Match 與使用者/來源矩陣未涵蓋
3. `linuxgcb/policy.py`：政策 name 轉 `RHEL9 GCB v1.2 <profile> v0.1 VERIFIED`，
   description 轉「已驗證候選政策；2026-11-01 Commander 人工複審完成（307 條均已驗證）」。
4. `linuxgcb/coverage.py`：manifest `execution_blocked`/`live_validated` 改為實算值（0/307），
   `review_status` 轉 `human_review_completed(2026-11-01)`。
5. `linuxgcb/__main__.py`、`linuxgcb/report.py`：CLI 與 HTML 說明轉 VERIFIED 文字。
6. 各批次釘選測試：治理欄位（live_validation/execution_review/coverage/pending/
   source_approval/verified_on/verified_by/caveats/review_status）比較時正規化；
   registry/manifest 移出 protected 清單（FIX-13 刻意更新治理產物）。

## 不變項（已驗證）
- 三政策逐 check 比對 `fe11ed8`：rules 位元相同（0 條變動）、check 層 metadata 0 變動；
  僅政策層 name/description 改變。
- 真機 `.61` 設定值未變動。

## 測試
- `python3 -m unittest discover -s tests`：137 tests OK。
- `python3 -m linuxgcb build` / `validate`：307 候選通過。

## 部署與 R29 引擎實證
- 部署 Manager `.53`（sha256 對帳一致）：
  - base `102709acd5bc…`、sshd `58b8603d60ef…`、firewalld `b51afb0aa262…`
- R29（agent010 restart 觸發，end_scan 2026-11-01T05:09+00:00）：
  - 三政策名稱於引擎端顯示 `… v0.1 VERIFIED`，hash_file 與部署值一致。
  - base 270 條 `128P/142F` score 47；sshd `32/32` score 100；firewalld `5/5` score 100。
  - 與 R26/R27/R28 逐 check 比對：**307 條零翻轉**，維持 `165P/142F`。
- 結果檔：`data/realhost_scan_20261101_r29.json`
- 報表：`reports/RHEL9_010_20261101_r29_snapshot.json`、`reports/RHEL9_010_20261101_r29/`
  （PASS 161 + MANUAL_PENDING 4（partial 範圍保留）+ FAIL 142；pass_rate 53.14、completeness 98.7）

## 剩餘事項
- 142 FAIL 為真機真實缺失（含 accepted findings 0187/0229），依 Commander 裁定不矯正系統設定。
- 4 條 partial 為檢查範圍保留，非未驗證。
