# 離線快照與 Dashboard 資料契約 v1

本版僅匯入檔案並輸出報表；沒有 live API transport、索引 writer 或 Dashboard 匯出。Wazuh Dashboard 是第一目標，先以原生 Configuration Assessment 對帳，再實作跨主機 GCB 面板。`wazuh-alerts-*` 只包含狀態差異，不能以最新 scan alerts 代表完整現況。

## 報表匯入

可執行範例是 `tests/fixtures/snapshot.json`，必須保留 SYNTHETIC 標籤。必要頂層欄位：schema_version=1、source_sha256（XLSX）、policy_hashes（完整檔名→SHA256）、hosts 陣列。synthetic=true 表示測試資料；正式來源不可改標籤冒充測試證據。CLI 先驗證本地政策與來源，來源或政策 hash 不符即拒絕。

每個 host：agent_id（不重複字串）、approved_profiles（base/firewalld/sshd 的已核准角色清單）、scanned_at（含時區 ISO8601，無資料則省略）、checks 陣列。每個 check 為 id（固定整數 SCA-ID）、result（passed/failed/not applicable/error）、reason（原始文字）、可選 execution_error=true。重複 ID、未知 ID、未實作項被當成掃描結果均拒絕；其他狀態正規化為 ERROR。缺少回傳不補 pass。

原始 API 診斷若顯示 timeout、permission denied、缺工具、解析失敗，轉接層必須設定 execution_error=true；不能只因 API result=not applicable 就核准不適用。本版還沒有正式 API schema 轉接器，須完成真機 gate 才能可信自動化判定。source/policy hash 是一致性檢查，不是簽章或可信來源認證；匯入檔案本身與 approved_profiles 的核准來源仍由 Hermes 審查。

`not_applicable`、`exceptions` 均以 GCB-ID 為 key；有效核准物件須包含 approver、reason、ticket、evidence、expires（含時區、未到期）。這些欄位是記錄核准而非本地產生核准；沒有驗證簽章或接工單系統。N/A 可適用於未掃描／原生 N/A／pass，既有 FAIL 或明確 execution_error 不會被覆蓋。例外核准僅加旗標，不改結果。失效／過期核准不生效；錯誤時間格式拒絕匯入。

治理優先順序：EXCLUDED → 明確 ERROR → 原始 FAIL → 不明 raw_result 的 ERROR → 有效核准 N/A → 未核准原生 N/A 的 ERROR → 未決 profile／未實作／局部檢核的 MANUAL_PENDING → raw passed 的 PASS → NOT_SCANNED。全部預期項每主機保留 314 列。未核准角色仍保守列入適用分母，unresolved=true，不自動跳過 SSH 或防火牆失敗。

scanned_at 距產製時間超過 86400 秒或缺少時間即 stale=true；未來時間拒絕。stale 不改 raw_result 或治理狀態，摘要分數是保留的最後結果，不能解讀為新鮮符合性。主機多政策若掃描時間不同，轉接器應保留每政策時間，報表 host.scanned_at 使用最舊時間以保守呈現；本版尚未自動合併 live 多政策快照。

輸出逐列包含來源與政策 hash、raw_result/reason、治理狀態、pending、unresolved、例外與 N/A 核准、stale、scanned_at、synthetic。原始匯入 JSON 副本保留其他欄位（例如 native_score、原始頁面、collector 時間與掃描摘要），不得以 HTML/CSV 的顯示字串取代原始證據。原始 JSON 不做公式前綴處理；CSV 所有文字欄位檢查公式與前導空白，HTML 一律 escaping。匯入前應移除秘密；本版沒有通用敏感資訊自動偵測器，不接受 shadow 內容、私鑰、token 或憑證。

## Collector 抽象

`Collector(transport, page_size=100, max_pages=10000).collect(agent_id, policy_id, policy_hash, now=...)` 是可執行的唯讀分頁抽象。transport 由呼叫端注入，介面為 `get(path, {'offset': n, 'limit': n})`，回傳 Wazuh envelope：`error=0`、data.affected_items、total_affected_items、可選 total_failed_items/failed_items。

路徑使用 `/sca/{agent_id}` 及 `/sca/{agent_id}/checks/{policy_id}`。政策摘要也分頁；每頁總數須一致，不可早停、超量或超出頁數上限。checks 數量須與摘要 total_checks 一致，ID 不得缺少或重複。取得摘要→全部 checks→再取得摘要；目標政策摘要只要任何欄位改變就拒絕快照。讀取失敗、部分 API 失敗、政策缺失、hash 不符都丟出 CollectionError，不回傳完整快照。呼叫端可有限次重試，本版不做隱含無限重試或部分發佈。

為保守起見，本版支援的摘要契約要求 policy_id、hash_file、total_checks、start_scan/end_scan（含時區 ISO8601），拒絕掃描未結束／時間矛盾。實際部署 API 版本可能使用不同欄位或無時區時間；需以部署版本 schema 明確轉接，禁止自行猜時區。沒有 scan_id 時使用已核對的起訖時間、完整摘要及政策 hash。是否有更可靠 scan generation、是否需要 DB 同步穩定等待及 API hash_file 的實際 hash 演算法，仍是阻擋正式上線的 integration gate。

回傳含完整 checks、before/checks/after 原始頁面、collected_at、complete=true、stale 與 snapshot_id。snapshot_id 以 agent/policy/hash/摘要/排序後 checks 計算，不含擷取時間，相同掃描重收冪等。相同掃描標記但內容不同會產生不同 key，未來 writer 必須標示衝突並拒絕靜默覆蓋；本版未提供 writer。before/after 相同仍可能遇到 API DB 非原子更新，須真機確認一致性；不能宣稱跨頁交易快照。

沒有真實網路實作，所以沒有 TLS 關閉選項或憑證讀取。未來 transport 必須啟用 CA 與 hostname 驗證、設定逾時、最小唯讀 RBAC，且不得記錄認證內容。禁止以 insecure flag 或硬編碼帳密繞過。

## 預定索引與面板

`templates/index-mapping.json` 是待審欄位 mapping，不是可直接匯入的完整 index template，也不是報表列可直接送入的格式（dynamic=strict；需要明確轉接）。正式 current/history 索引規劃為 linuxgcb-current-v1、linuxgcb-history-v1；測試資料另用 test-only 名稱，不得混入正式統計。

current 的 document_id 預定為 agent+GCB+profile+政策版本；history 則加 snapshot_id。complete=false 不得覆蓋完整 current；同 scan 不虛增歷史次數。全域率必須加總分子分母，不平均各主機百分比；原生 score 獨立顯示。索引的實際建立、RBAC、衝突處理、保留期限與生命週期均待審，未部署。

| 面板 | 資料與驗收 |
| --- | --- |
| 納管總覽 | 主機／profile／版本、未掃描與 stale、PASS/FAIL/ERROR/待人工，明示完整母體分母 |
| 類別矩陣 | GCB × 主機與類別失敗數；排除、不適用不計 pass |
| 單機明細 | 原始期望、raw_result/reason、治理狀態、政策與來源 hash、核准記錄 |
| 趨勢 | 只採完整快照，按版本分界；重收不產生假新掃描 |
| 品質治理 | 分頁／collector 錯誤、過期、未決適用性、未實作、例外到期 |

所有面板須可依主機、群組、profile、政策版本、類別、GCB-ID、狀態與掃描時間篩選。以同一份完整快照對帳報表與原生 SCA，再由 Hermes 驗收，不提供捏造的「已工作」Dashboard export。

## Q1 報表契約補充

`coverage_manifest.json` 升為 schema_version=2，`reviewed` 包含既有 53 項的全部來源 cells、family、issue_ids、coverage、offline_review、execution_review、source_approval 與 live_validation；舊 `added` 陣列由 `reviewed` 取代，counts.added 仍是歷史新增數 46。

報表列新增 coverage、execution_review、verified_compliance、evidence_status；summary 新增 raw_observed（有 raw_result 的列數，非宣稱完整 scan）、verified_decided。完整率分子只計 verified_compliance=true；通過率與達成率只計已驗證 PASS。候選 raw failed 可保留 state=FAIL，但不自動列入完整判定；blocked／partial raw passed 列 MANUAL_PENDING。

離線 check 可附 evidence_status：missing／absence_unverified／symlink_unresolved 代表適用性或語意未決（有效核准後才 N/A），tool_error／permission_error／timeout 代表 ERROR；未知值拒絕。這是輸入契約，不是端點探測實作，不能以 stdout 自動填寫原因或將缺失默認為合法 absence。原始 raw_result／raw_reason 與 snapshot 永遠保留。
