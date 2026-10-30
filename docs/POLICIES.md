# Registry 與候選政策邊界

314 項來源保留原始工作表／列號；270 基本 + 5 Firewalld + 32 SSH = 307 候選，Nftables 工作表恰好 7 項排除。各主機仍須適用性核准。Firewalld 的 0245 屬候選，Firewalld 使用 nftables backend 合法，不能因此啟用獨立 nftables.service。

SCA 數字範圍提案保留 **900000–900999**；固定 mapping 為 `900000 + TWGCB-ID 最後四碼`，不依排序或工作表列號編配。未使用的數字保持空白，0180 不補造。此範圍尚未與實際 Manager 的內建／自訂政策檢查撞號；撞號審查是部署阻擋條件。若有衝突，須正式版本化 migration，不能靜默重編。

每項分類是保守、可重現的提案，並非已核准語意審查：已實作項提案 native_sca；角色相關項先 conditional；集合、權限或載入鏈候選 readonly_helper；其他先 manual_review。分類依據文字記於每列。沒有部署 helper；提案不表示需要第二個 agent 或新套件。全部 314 項保留 human_review_pending。

| TWGCB-01-012 後四碼 | 數字 ID | 政策 | 來源期望與候選行為 | 未決限制 |
| --- | --- | --- | --- | --- |
| 0045 | 900045 | base | /etc/passwd root:root，以 stat 的 UID:GID = 0:0 | 符號連結、權限錯誤與命令路徑真機複查 |
| 0046 | 900046 | base | 644 或更低；列舉 0644 位元子集合，拒絕特殊位元 | 不以八進位大小比較；檔案型態與連結真機複查 |
| 0108 | 900108 | base | sysctl IPv4 ip_forward 與 IPv6 all.forwarding 都為 0 | 僅即時狀態；持久覆寫鏈、路由角色、IPv6 不存在均待審，passed 保留人工待辦 |
| 0243 | 900243 | firewalld | firewalld.service 已載入、active、enabled | 單次 show 屬多次唯讀觀察，非原子快照；政策重跑與人工核對 |
| 0245 | 900245 | firewalld | nftables.service masked 且 inactive | 未安裝／not-found 不自動 pass 或 N/A；須審查缺套件適用性 |
| 0269 | 900269 | sshd | sshd -T 的 permitrootlogin no | 僅預設情境；Match 使用者／群組／來源與 Include 覆寫矩陣待審 |
| 0270 | 900270 | sshd | sshd -T 的 permitemptypasswords no | 同上，raw passed 不提升整項符合 |

候選期望直接取自 XLSX；已離線查閱 DOCX 中 /etc/passwd、IP forwarding、nftables 與 PermitRootLogin 文字以核對，並未宣稱逐條 314 項 DOCX 審查完成。原文設定方法可能包含修改命令，本工具從不執行或轉成 remediation。

其餘 254 候選項全部在 registry 明列 pending，原因為尚未實作、待逐條語意審查。audit/PAM/authselect、模組、mount、演算法、帳號存量、全檔案系統檢查等沒有猜測生成規則。排除的 7 項仍保留來源資料與數字 ID。

政策採 JSON 表示 YAML 子集，檔名 .yml，使用 check 層級 `regex_type: pcre2`、`condition: all` 與 `compliance: twgcb`。是否能被目標 Wazuh/libyaml 版本載入是第一個真機 gate；本版不宣稱引擎驗證完成。requirements 只讀 /etc/os-release，限制 ID=rhel、VERSION_ID=9；群組角色不能靠服務停用自動切換。全部命令使用 RHEL 既有 stat/sysctl/systemctl/sshd 絕對路徑，不使用隱含 shell、管線或新增端點依賴。

正向匹配採錨定逐行輸出，不以命令 exit code 作為 SCA 成敗。已修正原有模擬器將非零 exit 直接視為 ERROR 的錯誤：同一段匹配 stdout 即使 exit=1 仍匹配 PASS，並明列這是引擎執行風險，而不是有錯也安全的保證。模擬器對無可靠輸出（missing observation、error）回 UNRESOLVED，這不是 Wazuh 結果。明確注入 engine_result=NOT_APPLICABLE 才模擬 N/A；all 任何 FAIL 優先於 N/A 或未決。PCRE2 真正執行仍待真機。

官方文件規定 `f:` 內容目標不存在為 Not applicable，空檔無匹配為 Failed；檔案 existence 與內容規則不可互換。how-it-works 官方快照說明：檢查過程被辨識為 error 時會回 Not applicable，並提供 status/reason。哪些權限拒絕、命令不存在、timeout 或 stderr 情況會被辨識為 error，既有快照未逐一界定，不能硬說每次一定 FAIL 或 N/A。命令可執行但檔案不存在，stat 通常不產生匹配 stdout；若引擎仍評估空輸出則 FAIL，若無法執行則依實際引擎可能 N/A，真機 gate 保留。RPM 查無套件通常輸出非匹配診斷，空輸出也不能 PASS；RPM 資料庫錯誤、工具缺失不得視為套件不存在。本批不實作否定式套件移除規則。

全部政策與 checks 明示 pcre2，包含 requirements 的政策層引擎。requirements 不滿足會使整份政策不掃描，報表保留未掃描／待人工。命令不經隱含 shell，無管線、重導向、環境指定前綴或新增 helper。`stat %F` 輸出語系影響需確認，locale 不符可能安全地誤報失敗；不以全域設定修正。本批正向型態規則接受 regular file／regular empty file，拒絕連結；以位元子集合列舉允許權限，含 000 並拒絕 SUID/SGID/sticky，並非 umask 比較。

新增候選與逐項 DOCX、執行機制及風險見 [BATCH1_REVIEW.md](BATCH1_REVIEW.md) 與 `data/coverage_manifest.json`。registry 的 coverage full/partial、implementation candidate/pending/excluded、human_review_pending、execution_review pending、UNVALIDATED 分別表示不同維度。未完成引擎驗收不能宣稱 robust PASS；報表只保留原生 raw_result 與治理判定，不反向證明引擎正確。新增規則沒有觀察時仍為 NOT_SCANNED，不提高完整率。

政策 SHA256 見 `data/policy_hashes.json`。`validate` 核對規則、mapping、hash 與來源；不能驗證 Wazuh engine、RHEL 路徑、權限或 kernel 行為。所有 fixtures 明示 SYNTHETIC；沒有執行端點命令。
