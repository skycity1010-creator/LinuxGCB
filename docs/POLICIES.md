# Q1 候選政策限制

以 [QUALITY_REVIEW_Q1.md](QUALITY_REVIEW_Q1.md) 為本次審查依據；歷史 handoff 不是來源核准或產品接受。只保留既有 53 ID、三份政策與 307／7 母體，無全量 Nftables 政策。

所有命令為絕對路徑，不假設 c: 支援 shell 管線。非零退出而 stdout 匹配仍可能 raw PASS，沒有已驗證的原生命令執行狀態保護，故 execution_review 全部 blocked。coverage full 0、partial 48、blocked 5；政策 description 列出逐項問題碼。報表不能將 raw passed 轉為已驗證符合。

metadata 不再使用受語系影響的 %F。僅來源明列目錄者用 stat %f 十六進位型態；其餘檔案不附加 regular-only 條件。stat 不加 -L，symlink 解參照、NSS 名稱與 uid/gid、ACL/default ACL 及來源特殊位元解讀仍待核准。位元遮罩已離線窮舉，但不是所有檔案型態與有效存取權的真機驗證。缺少備份與選用檔案不得自動 PASS 或核准 N/A；不讀取秘密內容。

服務保留原始單位與來源方法：autofs disable，rsyncd/squid/smb/nftables mask，kdump/auditd/rsyslog/firewalld enable 且 active。不存在可能滿足停用意圖，但需要適用性證據；D-Bus 錯誤不是 absence。socket/alias、runtime 持久性、多次查詢競態未解。0245 僅在核准 Firewalld profile 檢查 nftables.service，不限制 Firewalld 的 nftables backend。

模擬器僅支援 all + c:/f: 單一正向 r:、固定 emitted regex 與簡單 ASCII literal，其他語法拒絕。all 有 FAIL 優先；未知觀察為 UNRESOLVED，不冒充引擎 N/A。any/none 未使用並明確拒絕。Python regex、LF 分行及注入 stdout 不能證明 PCRE2/Wazuh runtime 行為。

正式發布仍須來源核准、固定 RHEL9/Wazuh 版本、負向／錯誤矩陣、政策數字 ID 撞號、已核准 Agent bootstrap、集中下發／更新／回復與 API 對帳。任何 helper 或新端點步驟先另提案，未授權前不實作。
