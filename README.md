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
