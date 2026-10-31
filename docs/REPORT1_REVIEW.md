# REPORT-1 離線審查

## 檔案清單

- linuxgcb/snapshot.py：Manager DB JSON → snapshot schema v1，保留原始 check 全欄。
- linuxgcb/__main__.py：snapshot 子命令與 --scan-info。
- linuxgcb/report.py：command、政策 remediation、raw_remediation、缺漏狀態及證據 label／警示。
- tests/fixtures/realhost_r2.json：REAL EVIDENCE agent010；原始檔逐位元複製，未改數值。
- tests/test_snapshot.py：真實證據轉換與 HTML／CSV、錯誤結果及時間契約測試；記憶體變異皆 test-only。
- README.md、docs/REPORT1_REVIEW.md：操作與限制。

## 欄位對應

| snapshot 欄位 | 來源／規則 |
| --- | --- |
| schema_version | 1 |
| synthetic / label | false / REAL EVIDENCE agent010／真實掃描證據（agent 010 / RHEL9 192.168.1.61） |
| source_sha256 | 實際 XLSX bytes SHA256（report 再與固定來源 hash 對帳） |
| policy_hashes | 當前 policies/*.yml bytes SHA256；不代表 DB 提供了掃描當時政策 hash |
| manager_dump_sha256 | 原始 JSON bytes SHA256 |
| hosts.agent_id / approved_profiles | 010 / base、firewalld、sshd |
| hosts.scan_ids | 每個 policy_id 的原始 scan_id |
| hosts.policy_scanned_at | 同次 sca_scan_info.end_scan，按 policy_id 對應，UTC ISO8601 |
| hosts.scanned_at | 全部政策有時間才取最早 end_scan，以保守判斷時效；缺漏為 null |
| hosts.checks | 原始欄位完整保留，另加 policy_id；result 不過濾、reason 不改寫 |
| warnings | 逐政策時間缺漏警示 |
| report.command | 原始 DB command；缺欄才取政策 rules 的 command |
| report.remediation | 政策 remediation；不存在保留 null 並標示缺漏 |
| report.raw_remediation | DB 原始 remediation，與政策值分開保留 |

## 實際樣本與驗證

- snapshot：`out/report1-r2/snapshot.json`
- HTML：`out/report1-r2/report/report.html`
- CSV：`out/report1-r2/report/report.csv`
- 稽核副本與摘要：同目錄 `snapshot.json`、`summary.json`。
- `python3 -m unittest discover -s tests -v`：45 tests OK。
- `python3 -m linuxgcb build` 與 `python3 -m linuxgcb validate`：通過，53 項，UNVALIDATED。
- raw 46 passed／7 failed；FAIL：TWGCB-01-012-0192、0194、0196、0198、0200、0202、0269。
- 314 列母體、307 適用、7 排除；治理狀態 300 MANUAL_PENDING／7 FAIL／7 EXCLUDED。verified_decided=0，pass_rate=null，completeness=0%。

## 尚缺來源證據

R2 原始 JSON 僅含 scan_id/checks，沒有 sca_scan_info；無法如實填入實測 scanned_at。目前 null 且 stale=true，不以檔案時間或交接描述代替。需提供同次離線 sca_scan_info 才能完成此驗收項。

現有政策沒有 remediation 欄，DB 匯出為 null。政策本批禁止修改，因此無法提供非空的「政策內 remediation」；7 FAIL 均明示缺漏。這是來源限制，並未完成非空修復內容驗收。未執行 Excel／DOCX 修復、政策命令、開發機掃描、SSH、API、sudo 或服務操作。build 重建後政策與來源均無 diff。
