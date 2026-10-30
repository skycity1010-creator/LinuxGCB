# P2 batch 1 候選控制審查交接

本分支僅離線開發，未執行政策命令、未掃描開發機、未連線端點或生產 API。Hermes 負責獨立審查、重跑測試、合併與溝通；沒有 commit。原始 XLSX、DOCX、controls.json、inventory.json 與歷史 P0P1 handoff 均保留。

## 涵蓋對帳

程式計算：原有 7 項，本批新增 46 項，合計 53 項；其中 49 full 候選、4 partial 候選，尚餘 254 項未實作。母體 314 = 307 候選 + 7 排除。真機驗證 0 項。

full 僅指候選已表達該來源要求，不表示語意審查核准、引擎驗收或符合性證據。全部 human_review_pending、execution_review pending、live UNVALIDATED。部分候選為 0108（持久 sysctl）、0141（僅 audit.rules）、0269／0270（SSH 情境矩陣）。0141 的 raw passed 保留 MANUAL_PENDING。其他未完成困難類別仍為未實作，啟發式分類只是提案。

`data/coverage_manifest.json` 由 build 重建，包含每項原始期望、sheet/row、DOCX 逐格文字及 hash、執行方式、測試位置、限制與狀態。validate 重算 manifest 並對帳 registry 與政策全部數字 ID。固定數字 ID 保持 900000 + 原始末四碼，0180 不補造，Nftables 工作表 7 項不生成政策，0245 仍保留。

## 語意修正與測試邊界

依據限既有有效官方快照：creating-custom-policies 的 condition／rules／regex_type，how-it-works 的 error→N/A 與政策 hash 同步，how-to-configure 及 internal-options 的遠端命令與 timeout。sca-custom-policies.md 是 soft404，未使用。未連外查詢 current 文件；部署版本對照仍是 gate。

原模擬器非零退出碼直接 ERROR、ERROR 優先 all FAIL、以 fullmatch 代表逐行 regex 都已修正。現模型逐行 search，exit_code 不參與匹配，all 的 FAIL 優先於 N/A。缺觀察或 error 診斷表示無可靠輸出，回 UNRESOLVED，不冒充引擎保證。若非零退出碼卻有匹配輸出，模型如政策仍匹配 PASS；這是明示未解風險，沒有暗中後處理改為 ERROR 來假裝政策安全。

政策及 checks 均設 PCRE2，包含 requirements 的政策層預設；Python regex 只是所用有限模式的離線替身，並非 PCRE2 驗收。f: 內容目標缺失按官方為 N/A、空檔無匹配 FAIL；existence 不代表內容。引擎辨識出的執行錯誤為 N/A，但工具缺失、權限拒絕、timeout、stderr、命令非零有 stdout 的實際辨識仍須真機。報表保留原生結果；未核准 N/A 為 ERROR，partial raw passed 為人工待辦，這是治理規則而非修正引擎。新增 authored 規則沒有虛構掃描結果。

命令均為絕對路徑，c: 不隱含 shell，無管線、shell 前綴、安裝、remediation、新 helper 或新端點人工步驟。sca.remote_commands=1 沿用已核准一次性安裝 bootstrap，不是 agent.conf 或安裝器 CLI 選項。

## 每項新增候選

全部新增都有固定 SYNTHETIC positive、negative、missing observation、empty stdout、command-error、nonzero-matching fixtures，測試直接使用發出的 rules。另逐子規則反轉、加入無關行驗證逐行存在語意。下表的測試欄代碼：F＝檔案型態／連結／空檔；O＝精確 owner/group 替代（shadow 只允許來源指定項）；M＝全部 0000–7777 位元組合（拒絕特殊位元，非 umask）；P＝套件缺失診斷與多套件每項必要；S＝enabled-runtime/static/alias/not-found 拒絕及三狀態分離。

| ID（TWGCB-01-012-） | 原始期望 | 執行機制 | 候選 | 額外測試 | 限制與待補 |
| --- | --- | --- | --- | --- | --- |
| 0030 | 停用 | `systemctl show autofs.service`：LoadState / ActiveState / UnitFileState | full | S | 分開確認開機狀態與即時狀態；不接受 not-found、static、alias、enabled-runtime；不存在不自動通過；多次查詢非原子。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0033 | 安裝 | `rpm -q --queryformat %{NAME}:installed`：sudo | full | P | 僅 RPM 資料庫套件存在；不代表服務或內容規則通過。RPM 資料庫錯誤不得以未安裝推論。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0047 | root:root或root:shadow | `stat %U:%G /etc/shadow` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0048 | 000 | `stat %a /etc/shadow` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0049 | root:root | `stat %U:%G /etc/group` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0050 | 644或更低權限 | `stat %a /etc/group` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0051 | root:root或root:shadow | `stat %U:%G /etc/gshadow` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0052 | 000 | `stat %a /etc/gshadow` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0053 | root:root | `stat %U:%G /etc/passwd-` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。備份檔缺失不自動視為不適用，需核准適用性。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0054 | 644或更低權限 | `stat %a /etc/passwd-` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。備份檔缺失不自動視為不適用，需核准適用性。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0055 | root:root或root:shadow | `stat %U:%G /etc/shadow-` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。備份檔缺失不自動視為不適用，需核准適用性。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0056 | 000 | `stat %a /etc/shadow-` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。備份檔缺失不自動視為不適用，需核准適用性。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0057 | root:root | `stat %U:%G /etc/group-` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。備份檔缺失不自動視為不適用，需核准適用性。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0058 | 644或更低權限 | `stat %a /etc/group-` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。備份檔缺失不自動視為不適用，需核准適用性。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0059 | root:root或root:shadow | `stat %U:%G /etc/gshadow-` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。備份檔缺失不自動視為不適用，需核准適用性。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0060 | 000 | `stat %a /etc/gshadow-` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。備份檔缺失不自動視為不適用，需核准適用性。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0094 | 停用 | `systemctl show rsyncd.service`：LoadState / ActiveState / UnitFileState | full | S | 分開確認開機狀態與即時狀態；不接受 not-found、static、alias、enabled-runtime；不存在不自動通過；多次查詢非原子。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0097 | 停用 | `systemctl show squid.service`：LoadState / ActiveState / UnitFileState | full | S | 分開確認開機狀態與即時狀態；不接受 not-found、static、alias、enabled-runtime；不存在不自動通過；多次查詢非原子。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0098 | 停用 | `systemctl show smb.service`：LoadState / ActiveState / UnitFileState | full | S | 分開確認開機狀態與即時狀態；不接受 not-found、static、alias、enabled-runtime；不存在不自動通過；多次查詢非原子。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0101 | 啟用 | `systemctl show kdump.service`：LoadState / ActiveState / UnitFileState | full | S | 分開確認開機狀態與即時狀態；不接受 not-found、static、alias、enabled-runtime；不存在不自動通過；多次查詢非原子。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0132 | 安裝 | `rpm -q --queryformat %{NAME}:installed`：audit, audit-libs | full | P | 僅 RPM 資料庫套件存在；不代表服務或內容規則通過。RPM 資料庫錯誤不得以未安裝推論。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0133 | 啟用 | `systemctl show auditd.service`：LoadState / ActiveState / UnitFileState | full | S | 分開確認開機狀態與即時狀態；不接受 not-found、static、alias、enabled-runtime；不存在不自動通過；多次查詢非原子。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0141 | 600或更低權限 | `stat %a /etc/audit/rules.d/audit.rules` 位元子集合 + `%F` | partial | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。僅來源明列 audit.rules，其他 rules.d 檔案覆蓋待審。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0142 | 640或更低權限 | `stat %a /etc/audit/auditd.conf` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0174 | 安裝 | `rpm -q --queryformat %{NAME}:installed`：rsyslog | full | P | 僅 RPM 資料庫套件存在；不代表服務或內容規則通過。RPM 資料庫錯誤不得以未安裝推論。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0175 | 啟用 | `systemctl show rsyslog.service`：LoadState / ActiveState / UnitFileState | full | S | 分開確認開機狀態與即時狀態；不接受 not-found、static、alias、enabled-runtime；不存在不自動通過；多次查詢非原子。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0178 | root:root | `stat %U:%G /var/log/messages` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0179 | root:root | `stat %U:%G /var/log` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0183 | 安裝 | `rpm -q --queryformat %{NAME}:installed`：libselinux | full | P | 僅 RPM 資料庫套件存在；不代表服務或內容規則通過。RPM 資料庫錯誤不得以未安裝推論。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0191 | root:root | `stat %U:%G /etc/crontab` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0192 | 600或更低權限 | `stat %a /etc/crontab` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0193 | root:root | `stat %U:%G /etc/cron.hourly` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0194 | 700或更低權限 | `stat %a /etc/cron.hourly` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0195 | root:root | `stat %U:%G /etc/cron.daily` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0196 | 700或更低權限 | `stat %a /etc/cron.daily` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0197 | root:root | `stat %U:%G /etc/cron.weekly` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0198 | 700或更低權限 | `stat %a /etc/cron.weekly` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0199 | root:root | `stat %U:%G /etc/cron.monthly` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0200 | 700或更低權限 | `stat %a /etc/cron.monthly` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0201 | root:root | `stat %U:%G /etc/cron.d` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0202 | 700或更低權限 | `stat %a /etc/cron.d` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0301 | root:root | `stat %U:%G /etc/shells` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0302 | 644或更低權限 | `stat %a /etc/shells` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0242 | 安裝 | `rpm -q --queryformat %{NAME}:installed`：firewalld | full | P | 僅 RPM 資料庫套件存在；不代表服務或內容規則通過。RPM 資料庫錯誤不得以未安裝推論。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0256 | root:root | `stat %U:%G /etc/ssh/sshd_config` + `%F` | full | F/O | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。僅 sshd_config metadata，不代表 Include 或 SSH 內容符合。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |
| 0257 | 600或更低權限 | `stat %a /etc/ssh/sshd_config` 位元子集合 + `%F` | full | F/M | 固定路徑 lstat 並檢查檔案／目錄型態；連結不解參照且不通過；stat 英文型態受 locale 影響，非英文可能誤報 FAIL，待實機確認；不檢查 ACL。僅 sshd_config metadata，不代表 Include 或 SSH 內容符合。命令啟動／stderr／權限錯誤與非零但匹配輸出之行為待真機驗證；不依賴退出碼。 |

## 尚未實作與刻意界線

本批只選正向套件 presence。移除 xinetd、ypbind、telnet、rsh、tftp、setroubleshoot、mcstrans 等仍 pending，須正向、可區分 RPM／命令錯誤的 absence 機制，禁止否定空輸出。0036 AIDE 初始化不以僅安裝包充數，0231 架構需求待審。0096 SNMPv3 替代方案不強制停用。

0038/0039 BIOS/UEFI、GUI 依賴、wildcards／SSH host keys、0203/0204 allow/deny 多檔集合、0303/0304 選用 opasswd.old、動態 audit log_file、全檔案系統／合法帳號、audit/PAM/authselect 載入鏈、mount、模組、演算法與持久 sysctl 均需另批。備份檔 0053–0060 缺失不自動通過或自動核准 N/A。cron.d 只檢查目錄 metadata，不宣稱檢查目錄內檔案內容。服務不存在不視為已 disabled，來源 mask 與 disable 分開，enabled 需 active，查詢非原子。stat 型態文字語系、NSS 名稱解析、ACL 與競態均須目標版本驗證。

## 驗證與來源

最終命令及結果記於本文件末段；所有測試資料明示 SYNTHETIC，沒有真實主機證據。snapshot 只更新政策 hash，保留原有七筆測試觀察，沒有新增假 PASS。報表完整率仍 3/307 = 0.98%，PASS=2、FAIL=1，新增 46 項為 NOT_SCANNED（0141 partial 為人工待辦）。

來源 SHA256（build/validate/測試核對，controls 與 XLSX 重抽逐筆相同）：

- XLSX：`7d752b639a1e780df08814c6252efadd3ea2711eaa5c9d91c070b84a296c0247`
- DOCX：`986effd9501b1fd97776129c6691cf8fc98246bd04514347322f3337508e0e5b`

DOCX 先接回段落內 XML runs，再接 cell 段落，以完整 ID 對照。0301/0302 同時出現在主表與修訂表，期望／設定方法相同；保留所有出現的 cells，沒有誤當成重複控制。此為本批逐項候選對照，不是 314 項已完成人工核准。

## 最終重跑結果

2026-10-30 離線重跑，以下全部 exit 0：

```bash
python3 -m linuxgcb build
python3 -m linuxgcb validate
python3 -m unittest discover -s tests -v
python3 -m linuxgcb report tests/fixtures/snapshot.json --out out/batch1-synthetic --now 2026-10-30T00:00:00Z
git diff --check
```

build／validate 對帳 53 控制；unittest 27 tests 全數 OK。報表 314 列：PASS 2、FAIL 1、ERROR 1、MANUAL_PENDING 258、NOT_SCANNED 45、EXCLUDED 7；適用 307、完整率 0.98%。輸出位於 out/batch1-synthetic，受 gitignore 排除。新增候選沒有提高完整率。

原始 XLSX／DOCX SHA256 均等於上述固定值；`git diff --exit-code -- data/controls.json data/inventory.json '*.xlsx' '*.docx' docs/HANDOFF.md CODEX_HANDOFF.md` 通過，原始資料與歷史交接未變動。

本次變更檔案：

- 新增 `linuxgcb/batch1.py`、`linuxgcb/coverage.py`、`data/coverage_manifest.json`、`docs/BATCH1_REVIEW.md`。
- 修改 `linuxgcb/catalog.py`、`linuxgcb/policy.py`、`linuxgcb/__main__.py`：候選定義、分維度狀態、模型修正、產物對帳。
- 重建 `data/scope_registry.json`、`data/policy_hashes.json`、三份 `policies/linuxgcb_{base,firewalld,sshd}.yml`。
- 修改 `tests/test_catalog_policy.py`、`tests/test_report.py`、`tests/fixtures/rule_outputs.json`、`tests/fixtures/snapshot.json`。
- 更新 `README.md`、`NEXT_STEPS.md`、`docs/POLICIES.md`。

Hermes 獨立重跑與人工審查後才考慮合併；正式發布仍受 RHEL9/Wazuh 版本、PCRE2、命令錯誤、locale、政策數字 ID 撞號、bootstrap 與集中下發／更新／回復 gates 約束。
