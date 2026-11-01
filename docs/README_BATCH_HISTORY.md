# LinuxGCB P2B3：日誌與稽核／系統服務（離線）

新增 **49 項（97→146）**：日誌與稽核 43、系統服務 6。既有 97 個完整 checks 不變；來源 314、scope 307／排除 7 不變。所有新增候選均為 human_review_pending、execution_review=blocked、UNVALIDATED。

逐條機轉與限制見 [P2B3 審查](docs/P2B3_REVIEW.md)，驗證見 [測試輸出](docs/P2B3_TEST_OUTPUT.txt)。新增解析命令需要端點 `/usr/bin/python3`，不安裝 helper；仍待 RHEL9／Wazuh 真機驗證。

```bash
python3 -m scripts.p2b3_fixtures
python3 -m scripts.p2b3_review
python3 -m linuxgcb build
python3 -m linuxgcb validate
mkdir -p out/p2b3-tmp
TMPDIR="$PWD/out/p2b3-tmp" python3 -m unittest discover -s tests -v
```

以下為歷史批次說明。

# LinuxGCB P2-BATCH2：四類剩餘候選擴充

本批依 registry 實際剩餘數新增 **44 項（53→97）**：SSH 28、cron 4、SELinux 6、安裝與維護軟體 6。原 53 個 emitted checks 完整內容不變，307/7 scope、來源及 R2/R3 保留。政策仍為 UNVALIDATED；詳見 [逐條審查與來源 cells](docs/BATCH2_REVIEW.md) 及 [離線測試結果](docs/BATCH2_TEST_OUTPUT.txt)。

新增規則使用成功輸出保護與全規則否定；原 Q1 模擬行為保留。重建及檢查：

```bash
python3 -m linuxgcb build
python3 -m scripts.batch2_fixtures
python3 -m linuxgcb validate
python3 -m unittest discover -s tests -v
```

以下為原 Q1／REPORT-1 歷史說明，其 53 項數字與語法限制不代表 BATCH2 當前總量。

# LinuxGCB Q1：既有 53 項候選品質整併

僅離線開發，分支 `codex/linuxgcb-quality1`。來源 314 項 = 307 候選 + 7 排除；固定數字 ID 不變，僅審查既有 53 項，沒有擴充控制或 Dashboard。完整結論見 [Q1 審查](docs/QUALITY_REVIEW_Q1.md)。歷史交接保留原樣，過去 full 數量不代表本次核准。

目前 coverage **full 0／partial 48／blocked 5**；53 項 execution_review 均 blocked，真機驗證 0、來源核准 0。離線審查已完成並記錄問題，不表示 review pass。非零退出且 stdout 符合仍可能 raw PASS；原生命令沒有已驗證的執行狀態保護。未新增 helper 或端點人工步驟。

Python 3.10+ 標準函式庫，無安裝與網路需求：

```bash
python3 -m linuxgcb build
python3 -m linuxgcb validate
python3 -m unittest discover -s tests -v
python3 -m linuxgcb report tests/fixtures/snapshot.json --out out/q1-synthetic --now 2026-10-30T00:00:00Z
```

CLI 不執行政策命令。build 核對 XLSX/DOCX hash，重建 registry、三份候選政策、policy hashes 與 schema v2 coverage manifest。`reviewed` 包含全部 53 項來源 DOCX cells、問題代碼與處置；validate 重算對帳，並非 Wazuh YAML／PCRE2 驗收。原始 XLSX、DOCX、controls.json、inventory.json 不修改。

報表保存 raw_result、raw_reason、evidence_status、coverage、execution_review、verified_compliance。raw passed 在 blocked／partial 時為 MANUAL_PENDING；raw failed 保留候選 FAIL 觀察，但不列完整符合判定。完整率只計 verified_compliance；目前為 0%。有效核准不適用需 approver、reason、ticket、evidence、expires；錯誤不能藉核准 N/A 隱藏。缺少備份檔或服務不自動 PASS／FAIL／核准 N/A；輸入明確 missing／absence_unverified 時列待審，tool_error／permission_error／timeout 為 ERROR。無法分類的原始結果仍保留，不能藉缺失原因推測適用性。

合成 fixture 僅有 6 筆原始觀察，53 項候選的 authored 數量不算 scanned。`out/` 的 HTML、CSV、summary.json 與原始 snapshot.json 為忽略產物；同名輸出會覆寫。測試固定時間不能用於正式資料。

模擬器只支援實際發出的 all、c:/f: 正向單一 r:，模式限現有規則與 ASCII literal；拒絕 any／none、其他運算子與未驗證語法。逐 LF 行搜尋，退出碼與 stderr 不提供保護；Python regex 並非 PCRE2。CRLF、Unicode、Wazuh 的緩衝／stderr／timeout／argv 與錯誤辨識都須真機驗證。

有效 Wazuh 依據為 docs/references 內 creating-custom-policies、how-it-works、how-to-configure、internal-options 快照；sca-custom-policies 是 soft404，不作依據。本次無外網查詢、SSH、生產 API、秘密、sudo、安裝、服務變更或 Excel remediation。`sca.remote_commands=1` 沿用已核准的一次性 Agent 安裝 bootstrap，並非集中 agent.conf 開關。

Hermes 負責獨立驗收、整合與溝通。本次留下未提交 diff，不主張父代理接受；後續限 [NEXT_STEPS](NEXT_STEPS.md) 的 Q1 驗收。

## REPORT-1：Manager DB 真實快照（離線）

`tests/fixtures/realhost_r2.json` 為 **REAL EVIDENCE agent010**，逐位元複製 R2 原始匯出，非合成資料。53 筆觀察為 46 passed／7 failed；label 由 snapshot 加入，不改寫 fixture。其他合成 fixture 僅供 test-only。

```bash
python3 -m linuxgcb snapshot tests/fixtures/realhost_r2.json --out out/report1-r2/snapshot.json
python3 -m linuxgcb report out/report1-r2/snapshot.json --out out/report1-r2/report
```

輸入為 `{policy_id: {scan_id, checks: [...]}}`。若另有同次離線 `sca_scan_info`，使用 `--scan-info path.json`，格式為 `{policy_id: {"end_scan": "2026-10-31T04:03:00Z"}}`（此為格式範例，不能冒作本次實測時間），也接受 UTC epoch 秒。時間僅按 policy_id 對應；不得將 sca_scan_info.hash join sca_check.scan_id。匯出應使用各政策最新 scan：`select scan_id from sca_check where policy_id=? group by scan_id order by max(rowid) desc limit 1`。Manager 4.14 不使用已移除的 `/sca/{agent}/checks`。

目前 R2 原始檔沒有 sca_scan_info，故 scanned_at=null、stale=true 並顯示警示；必須提供離線時間證據才能補齊。現有 policies/*.yml 沒有 remediation，原始匯出同欄為 null；報表保留空值並明示「政策未提供 remediation」，不產生修復指令。本批未修改政策。7 FAIL 仍逐項顯示 TWGCB ID、title、command 與 remediation 欄；UNVALIDATED 的 raw passed 不算已驗證符合。詳見 [REPORT-1 審查](docs/REPORT1_REVIEW.md)。
