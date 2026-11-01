# FIX8：900244 不存在服務的停用語意

基準 commit：`7a8a3dbaccffe64ae4c99dc186d28a7de3da316f`。

## 前後對照

| is-enabled 觀察 | is-active 觀察 | 修正前 | 修正後 |
| --- | --- | --- | --- |
| not-found／明確不存在單元診斷 | inactive (rc3) | FAIL | PASS |
| disabled (rc1) | inactive (rc3) | FAIL | PASS |
| masked (rc1) | inactive (rc3) | PASS | PASS |
| enabled | 任意 | FAIL | FAIL |
| 不存在／disabled／masked | active | FAIL | FAIL |
| 無法執行、逾時、權限錯誤或非預期 rc／輸出 | 任意 | FAIL | FAIL |

iptables 與 ip6tables 必須各自符合；任一失敗即無輸出，由既有 ^PASS$ 規則判為 FAIL。缺單元代表不可能啟用，但仍額外要求 is-active 精確回報 inactive/rc3。

以 LC_ALL=C 執行唯讀 systemctl，接受 is-enabled 的 disabled/rc1、masked/rc1；不存在僅接受 rc1 或 rc4，且 stdout 為 not-found、stderr 空白，或 stdout 空白、stderr 精確為 `Failed to get unit file state for <服務>.service: No such file or directory`。其他診斷及異常 rc 不豁免；例外沿用外層捕捉並保持無輸出。

只對 batch10.script(244) 附加 fix8_runtime 覆寫。原共用 runtime 保留，因此 900246（包括 public 判定）及其餘 306 條完整 checks/rules 不變。來源、TWGCB ID、307/7 scope、coverage_manifest 307、UNVALIDATED、既有 fixtures 與證據檔均不變。既有 manifest 的歷史 caveat 依任務限制保留，這份文件記錄本次語意修正。

## R21 證據（2026-11-01）

以下是使用者提供的 .61 真機觀察，非本次離線重新採集：

- `rpm -q iptables-services`：未安裝。
- `systemctl is-enabled iptables`：包含 `No such file or directory`。
- `systemctl is-active iptables`：inactive。

GCB 0244 expected 為「停用」；此缺單元情境應視為已停用。測試以合成 CompletedProcess 重現標準完整診斷及 not-found 輸出，不將合成 rc 或完整診斷冒充 R21 原始紀錄。使用者未提供 ip6tables 的 R21 結果；本次僅以合成回歸驗證同型處理，未宣稱 .61 整條 0244 已經重新驗收。

## 驗證

回歸執行實際產出的內嵌程式，涵蓋兩個服務的不存在、disabled、masked、enabled、active，以及異常 rc、權限、無法執行與逾時。以基準 commit 比較所有 307 條，僅 900244 rules 改變，其餘 306 條完整 checks diff=0，900244 非 rules 欄位不變；受保護檔案 diff=0。

執行 `python3 -m linuxgcb build`、`python3 -m linuxgcb validate`、`python3 -m unittest discover -s tests -v` 與 `git diff --check`。最終結果見下方。

全程離線：無 SSH、生產 API、服務變更、sudo 或 secrets 存取。環境明列 .git 唯讀，依任務例外保留工作目錄變更，不嘗試繞過限制建立 commit。

最終結果：完整 unittest 128 項全過（16.217 秒）；build/validate 均確認 307 候選規則、307/7 範圍維持；git diff --check 通過。獨立逐條比較：307 條中僅 900244 改變，306 條不變。產物僅 firewalld 政策及其 policy_hash 更新，coverage_manifest 與 scope_registry 無差異。
