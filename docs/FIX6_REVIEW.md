# FIX6 離線審查

## 範圍與規格釐清

本次按明列 ID 修正 900079–900085、900303、900304，共 **9 條**；236 條候選中其餘 **227 條** rules 完全不變。任務文字的「8／228」與列出的 ID 數量不符。保留 ≤0644 位元子集語意：0644 PASS、0664 FAIL；「644→FAIL」與該標準矛盾，未自行收緊至 0600。

0032、0038、0073、0074、0091 未修改。來源檔、TWGCB ID、307/7 scope、coverage_manifest 236、UNVALIDATED 政策名稱、既有 fixtures 及證據均保留。只更新指定政策 rules 與必要的 policy_hashes。

## 前後對照

| 項目 | 修正前 | 修正後 |
| --- | --- | --- |
| 900079–900085 帳號排除 | 精確排除 /sbin/nologin、/bin/false | shell 以 /nologin 或 /false 結尾即排除，涵蓋 usrmerge 路徑 |
| 900079 權限 | 0700 位元子集 | 不變；/root 0550 仍 FAIL |
| 900303 所有權 | opasswd 與 .old 都必須存在且 root:root | 只對存在的檔案要求 root:root；兩檔均不存在 PASS |
| 900304 權限 | 兩檔都必須存在且 ≤0644 | 略過不存在檔案；存在者仍需符合 0644 位元子集，拒絕 0664、0755、特殊位元 |
| 讀取錯誤 | 不產生 PASS | 只略過 FileNotFoundError；PermissionError 等仍不產生 PASS |

P2B7 將整份 runtime 內嵌至每條命令。batch7.script 對非 FIX6 規則還原兩段原始文字，以確保其 rules 逐字不變；FIX6 指定規則使用修正後 runtime。既有 P2B7_REVIEW 與 registry 審查文字保留為歷史證據，本文件記錄本次語意修正，不重寫舊證據。

## R16 證據及重現界線

以下為任務提供的 R16 真機觀察，並非本次連線取得：

- RHEL9 服務帳號 tss、clevis、libstoragemgmt、setroubleshoot、sshd 使用 /usr/sbin/nologin。
- check(80) debug 顯示 `USER clevis home /var/cache/clevis isdir False`、`USER tss home / want_uid 59 stat_uid 0`，服務帳號進入家目錄檢查，造成 080–085 假陰性。
- /root 為 0550，0079 為真實缺失，修正後仍應 FAIL。
- .61 僅有 root:root 0600 的 opasswd；opasswd.old 尚未因 pwhistory 輪替生成。

新增 tests/test_fix6.py 以暫存合成樹重現 tss 的 / 與 clevis 的不存在家目錄，驗證四種 nologin/false 路徑、互動帳號缺家目錄仍失敗、0550 仍失敗、單檔與雙檔缺失、錯誤 UID/GID、權限邊界與存取錯誤。測試執行生成腳本，驗證 PASS 輸出。既有 test_p2b7.py 僅更新缺檔預期。

未執行 SSH、production API、服務操作、sudo 或任何工作區外的外部寫入。

## 驗收結果

- `python3 -m unittest discover -s tests -v`：104 tests，全部 OK。
- `python3 -m linuxgcb validate`：通過，236 項候選規則。
- `git diff --check`：通過。
- 新增範圍回歸逐條比對 bc2cfbb：恰好上述 9 條 rules 改變，其餘 227 條及所有 check metadata 完全相同；coverage_manifest、scope_registry 位元組相同。
- 舊證據保護測試原先將 P2B7 新增的 TEST_OUTPUT 與 P2B6 提交 6788fdc 比較，造成既有失敗；僅將證據比對基準改為 FIX6 前的 bc2cfbb，證據本身未修改。
- `.git` 在本環境唯讀（`test -w .git` 為 false，環境亦明列 read-only），未建立 commit；變更保留工作目錄。既有未追蹤 codex_fix6.log 未納入修改。
