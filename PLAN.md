# LinuxGCB — RHEL 9 / Wazuh SCA 專案規劃

狀態：規劃草案，待確認試點與呈現平台；尚未部署掃描、儀表板或報表服務。

## 1. 來源與範圍

實際專案路徑 `~/projects/LinuxGCB`；使用者原訊息為 `~/project/LinuxGCB`，不另建立重複目錄。

- 規範：專案內 RHEL 9 GCB v1.2 說明 DOCX；條目以使用者指定 Excel 為來源。
- 已程式盤點：314 筆、314 個唯一 TWGCB-ID、無重複 ID，標題／類別／設定值無空白。
- 基本項目 270；Firewalld 5；Nftables 7；SSH 32。
- 文件明示依使用之防火牆與 SSH 部署相應基準。Firewalld 與獨立 nftables service 要求互斥，不可讓同一主機兩套政策一起計分；Firewalld 使用 nftables backend 不等於應啟用獨立 nftables service。
- Excel 不含 TWGCB-01-012-0180；DOCX 刪除列表可確認其已刪除，不補造條目、不重新編號。
- 非 RHEL 9（Ubuntu、Rocky、Alma、容器）不直接宣稱符合本基準；衍生系統另立適用性與差異審查。
- 本期只讀檢核、結果治理、儀表板與報表；不自動執行 Excel「設定方法」，不啟用自動修復。

## 1.1 已確認需求與部署限制

- 使用者環境採 Firewalld；本期不實作 Nftables 工作表 7 項。來源目錄仍保留全部 314 項供追溯，實作候選範圍為 307 項（基本 270 + Firewalld 5 + SSH 32），各主機仍需適用性審查。
- Firewalld 基準內「nftables 服務停用」仍須檢查，不能因排除 Nftables 工作表而刪除；這不要求停用 Firewalld 的 nftables backend。
- 使用者希望端點只安裝 Wazuh Agent，其餘檢核設定由中控下發。
- 官方確認：SCA YAML 與 agent.conf 可由 Manager 群組集中下發；但遠端政策的 command checks 需要端點 `/var/ossec/etc/local_internal_options.conf` 設定 `sca.remote_commands=1`。它是本機安全開關，不能假設由一般集中 agent.conf 啟用。
- **已核准的前置必要條件**：Commander 同意將 `sca.remote_commands=1` 併入一次性 Wazuh Agent 安裝流程。之後要求安裝 Wazuh Agent時，預設包含此本機設定，與 Manager/enrollment/group 設定一併完成；後續政策與掃描參數由中控管理。這是安裝流程中的設定檔寫入，不是套件安裝器的原生 CLI 參數。
- 安裝驗收：在端點 `local_internal_options.conf` 冪等設定 `sca.remote_commands=1`，避免重複或衝突值；Linux 路徑為 `/var/ossec/etc/local_internal_options.conf`，其他平台使用實際 Agent 安裝目錄。於首次啟動前完成；已啟動時依變更範圍重啟 Agent，讀回確認設定，並於政策下發後驗證命令檢查確實執行及結果回傳。
- 本次核准建立未來安裝慣例，未執行安裝，也不代表授權立即批次修改或重啟既有 Agents；既有端點補設另列部署範圍。
- 不以 Active Response 繞過安全開關作為預設設計；不承諾 shared 檔案同步能任意安裝 helper 到系統路徑。優先 SCA + RHEL 既有命令，若 helper 不可避免，須另行驗證集中配送、直譯器呼叫、權限、hash 與更新流程，不能新增未核准的端點人工步驟。
- PoC 驗收增加：從乾淨 RHEL9 執行一次核准安裝後，只操作 Manager 完成政策發布／更新／回復，並確認端點命令檢查與 API 結果；目前是文件可行性確認，尚未完成此真機驗收。

## 2. 建議架構

```text
Excel + DOCX
  → 條目目錄 / 適用性 / 人工審查 / 版本化 mapping
  → 自訂 SCA YAML + 必要的唯讀 helper
  → 試點 RHEL 9 Wazuh Agent
  → Wazuh Manager SCA 現況資料庫
      ├─ 原生 Configuration Assessment：單機原生檢視
      └─ 唯讀 API collector → 完整快照 + 證據索引
                            ├─ GCB current / history 專用索引 → 全域儀表板
                            └─ 報表產生器 → HTML / CSV / XLSX（PDF 後續）
```

選型建議：先使用 Wazuh Dashboard 原生 SCA 驗證；全域 GCB 儀表板以 Wazuh Indexer 專用 `linuxgcb-*` 索引與自訂 Dashboard 為優先方案。Grafana 為替代選項，須驗證 OpenSearch datasource、版本、授權及 SSO；現階段不安裝或變更任何服務。

重要資料原則：官方文件說明 SCA 傳送狀態差異，未變更可僅送摘要。`wazuh-alerts-*` 不是每次掃描完整結果表，不能以最新 scan_id 的 alerts 當作所有條目。完整現況使用 Manager API：
- `GET /sca/{agent_id}`
- `GET /sca/{agent_id}/checks/{policy_id}`

落地前核對實際 Manager/Agent 版本、API schema、分頁上限與 RBAC；本輪未連線驗證現行部署。Collector 須分頁取齊、核對 total_affected_items，掃描摘要前後比對以避免跨掃描混合；異動時重試，失敗不得發布為完整快照。保留原始回應與擷取時間；沒有新 scan 時不虛增掃描次數。Idempotency key 包含 agent、policy、scan 標記、policy hash；若 API 缺 scan 標記，以經驗證的起訖時間及 policy 版本識別。

## 3. SCA 政策與條目設計

本期政策拆為 base、firewalld、sshd，不建立 nftables 政策；政策名稱包含 RHEL9、GCB v1.2 與實作版本。主機先分派經核准 profile，再依 OS requirements 執行；不因「服務剛好未運作」自動切換 profile 來逃避失敗。

每個 GCB 條目保留：
- 原始檔名、sheet、row、來源 SHA256、TWGCB-ID、名稱、類別、說明、原始設定方法、期望值。
- 固定 SCA 數字 ID（另建 registry 檢查撞號）、policy_id、implementation_version、適用條件、檢核方式、證據格式、測試案例。
- mapping 加入 compliance `twgcb`，實際欄位呈現由試點驗證。
- 原則上一個 GCB 對應一個總結果；多個子檢查由 all/any 聚合，不因子檢查數量提高權重。
- 評估類型：native_sca、readonly_helper、manual_review、conditional；314 筆目前皆為 unreviewed，尚未宣稱全部可自動化。

實作重點：
- 靜態檔案匹配不足時，檢查有效設定與持久設定。例如 sysctl live + 設定來源、audit runtime + rules.d、mount live + fstab/systemd。
- SSH 使用有效設定並處理 Include/Match；需多個使用者/來源情境，不能單一 sshd -T 代表所有 Match。
- PAM/authselect/pwquality/faillock 須檢查載入鏈與覆寫順序；密碼期限須區分新帳號預設與既有帳號。
- 檔案「或更低權限」以位元遮罩判斷，不比較八進位數值大小；umask 語意相反，需獨立規則。
- 模組停用須處理已載入、可載入、blacklist/install 與模組不存在；kernel crash dump 與 userspace core dump 不混為同一項。
- 加密演算法、舊版 SSH 選項與 RHEL minor 版本差異須記錄；不可自行把「看似更強」視為已符合法定清單。
- GUI、NFS、可攜式媒體等須由適用性證據決定，無法判斷先列待確認。
- 大型檔案系統掃描限制範圍、timeout、I/O 負載；被排除路徑與未完成範圍入報表，不假報全部通過。
- SCA `c:` 不預設具有 shell 管線語意。複雜解析用固定、root 擁有、不可由一般使用者修改的 helper；禁止遠端傳入任意 shell 指令。
- SCA 命令退出碼不等於檢核結果；helper 輸出明確標記與原因，error 分支必須真機驗證，避免出錯被解讀為 pass。

## 4. 狀態、計分與例外

保留 Wazuh raw_result / reason / 原生 score，另外產出治理狀態：PASS、FAIL、NOT_APPLICABLE、ERROR、MANUAL_PENDING、NOT_SCANNED；stale 為額外時效旗標，不覆寫原始結果。

Wazuh 的 Not applicable 可能來自執行錯誤，不能直接當核准不適用。只有符合適用性規則且有證據者列 NOT_APPLICABLE；權限不足、工具缺失、timeout、解析錯誤列 ERROR。例外核准另存 approver、理由、期限、工單，不將原 FAIL 改 PASS。

建議同時顯示：
- 已判定通過率 = PASS / (PASS + FAIL)。分母為零顯示 N/A。
- 適用項達成率 = PASS / 所有適用項（含 ERROR、待人工、未掃描）。
- 結果完整率 = (PASS + FAIL) / 所有適用項。
- 未核准適用性項目另計 unresolved，不默默從母體消失。
- 全域按 agent × GCB 條目加總，不平均主機百分比；跨 profile/版本比較需標示範圍差異。
- 原生 score 與自訂治理分數分開標示，不宣稱等價。

## 5. 儀表板

1. 管理總覽：納管／在線／未掃描／過期主機，通過率、完整率、錯誤、待人工、到期例外。
2. 類別分析：按 Excel 類別的失敗分布，GCB-ID × 主機矩陣，常見失敗項。
3. 單機詳情：OS、profile、政策版本、掃描時間、TWGCB-ID、期望／實測、判定、原因與改善建議。
4. 趨勢：每日完整快照、新增失敗、恢復通過、持續未改善天數；政策版本變更要有分界。
5. 品質與治理：collector 錯誤、快照不完整、資料延遲、未實作項、適用性未決、例外即將到期。

篩選：主機／群組／profile／政策版本／類別／GCB-ID／狀態／掃描時間。原生 SCA 入口為 Endpoint security → Configuration Assessment；完整全域 GCB 呈現不假設原生即可滿足。

## 6. 報表

- 管理摘要：範圍、基準與政策版本、主機與掃描涵蓋、分數定義、主要缺失、例外與趨勢。
- 主機明細：每個預期條目皆有一列；含未掃描、待人工與 ERROR，不能只列 API 回傳的成功條目。
- 稽核附件：來源檔 hash、policy/helper hash、scan 起訖、collector 時間、原始 API 快照、證據摘要、核准例外。
- 格式：先 HTML + CSV + XLSX；PDF 僅在字型、分頁、長中文及可重現輸出驗證後納入。
- 建議每日收集新掃描、每週摘要與每月稽核報表；頻率與保留期限待核准，不自行排程。
- HTML escaping、CSV/XLSX formula injection 防護；證據遮蔽密碼 hash、私鑰、token 等秘密，不保存完整 shadow 內容。

## 7. 階段與驗收

P0 — 基準整理（本輪完成初步盤點）
- 已產出 importer、完整原文 controls.json、inventory.json 與規劃。
- 待逐條 DOCX 對照、適用性與自動化分類；驗收為 314 項全部有審查處置，無漏列或補造已刪除項。

P1 — 代表性 PoC
- 選擇 RHEL 9 可還原試驗 VM；涵蓋檔案權限、模組、sysctl、服務、audit、PAM、SSH 與防火牆案例。
- 每類驗證 pass、fail、missing、timeout／permission、真正不適用；負向設定只在核准試驗環境進行。
- 先審閱政策與 helper，再部署；確認 agent 文件 hash、SCA 執行日誌、API 結果及人工複查一致。

P2 — 完整政策
- 全部 314 項都須 mapping 與處置，必要時允許明列人工項，不能把未實作項寫成通過。
- 自動規則經獨立程式審查、fixture 與 RHEL 9 真機測試；原生 YAML parse 成功不等於引擎驗收。
- 只驗證 Firewalld profile，Nftables 工作表標記 out_of_scope；涵蓋 headless/GUI、不同檔案系統與 minor 版本差異。

P3 — Collector / 儀表板 / 報表
- 驗收分頁完整、重跑不重複、scan 中途變更不混合、agent 離線不顯示新 pass、原生與治理統計可對帳。
- 相同快照的畫面與報表計數一致；314 項母體可追溯；權限與敏感資料遮蔽測試通過。

P4 — 小批試行與維運
- 群組分批發布、回復前一政策與 helper、備份 agent.conf；核准後才設定排程／索引生命週期。
- 衡量 CPU、I/O、掃描時間與 API 負載後決定頻率；基準升版 diff 與規則回歸納入維運。

## 8. 安全界線與待確認

- 本輪僅在本機專案建立文件與盤點資料；未修改來源 Excel/DOCX，未變更 Wazuh、Indexers 或 Agents。
- Wazuh Manager/Indexer/Dashboard 變更及重啟須 Commander 明確核准。
- 如使用集中下發的 command checks，評估 sca.remote_commands 信任擴大；需逐 agent 明確核准與控制檔案權限，不能全域盲開。
- Collector 使用最小權限唯讀 API 身分與 TLS 憑證驗證；Index writer 與 dashboard reader 分離，不將管理憑證放入專案。
- 開發啟動決策：無阻擋離線開發的未決事項；使用者授權交由 Codex 開始開發，RHEL9 試點稍後提供。第一批為 P0 條目分類／範圍 registry、P1 代表政策及離線測試、collector/report 基礎；不宣稱完成全部真機驗收。
- 開發預設：RHEL9 + Firewalld，SSH 依主機適用性；儀表板以 Wazuh Dashboard 為第一目標，暫不加入 Grafana 整合。報表先本機按需產出 HTML/CSV，XLSX 依依賴與測試進度；不啟用排程、寄送或自動刪除。
- 不阻擋開發、但阻擋正式上線的待決：試點 IP／RHEL minor 版本與 Agent/Manager 版本、真機政策執行驗證、主機角色／適用性與正式納管名單、報表頻率／收件人／保留期限、Index/RBAC 與部署變更核准。
- Codex 使用隔離副本，不接觸實際端點、憑證或外部系統；交付由主代理獨立審查與重跑測試後才合併。

## 9. 官方依據

下列頁面已透過 Firecrawl 擷取，快照位於 docs/references/。current 文件可能變動，實作必須再次對照部署版本。
- https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/how-it-works.html
- https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html
- https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/how-to-configure.html
- https://documentation.wazuh.com/current/user-manual/reference/internal-options.html

更正：先前 sca-custom-policies.html 擷取內容實為網站錯誤頁，不能作為依據；以 how-to-configure.html 的政策分享章節取代。

重跑盤點：`python3 scripts/inventory.py`（只寫 data/ 產物，不修改來源檔）。
