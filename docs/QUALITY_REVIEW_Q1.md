# Q1 既有 53 項候選品質審查

日期：2026-10-30。工作目錄 `/home/skycity1010/projects/LinuxGCB-codex-quality1`，分支 `codex/linuxgcb-quality1`。基線為 HEAD 的未驗證候選，並非已接受產品。僅離線程式／來源審查；未執行政策、連線或變更端點，未新增 ID、helper、daemon、套件或人工端點步驟。Hermes 保有獨立接受、整合與溝通責任。

本次 53/53 已完成程式與來源對照並列出發現，**不是 review pass**。offline-test pass 僅表示合成案例符合本程式契約；真正 Wazuh 驗證、來源解讀核准與父代理接受均未完成。母體仍 314 = 307 候選 + 7 排除，實作 ID 仍 53，其餘 254 未實作。coverage full 0／partial 48／blocked 5；execution_review blocked 53；live validated 0。

## 依據與審查方式

讀取 PLAN、原始 controls.json、全部 53 項 DOCX cells、BATCH1_REVIEW、三份 emitted policies、batch1/policy/catalog/coverage/report 與相關測試程式；不是沿用歷史摘要。manifest schema v2 的 `reviewed` 保存全部 53 項 source sheet/row、DOCX 每次出現的 cells 與 hash、逐項問題與狀態。0301／0302 修訂表重複出現的來源保留。0141 不擴充為所有規則集合的完成宣告。

Wazuh 依據限既有有效快照：creating-custom-policies 的 rule syntax／condition／regex_type／缺失內容目標，how-it-works 的錯誤 N/A 與差異傳送，how-to-configure／internal-options 的集中下發、安全開關與 timeout。sca-custom-policies 是 soft404，未引用。沒有為此次離線工作瀏覽外網；部署版本差異仍是 gate。

數值 stat 依據為本機 GNU coreutils `stat(1)` 手冊：`%f` raw mode in hex、`%a` 八進位 mode、`%u/%g` 數字身分、`%U/%G` 名稱、`-L` follow links；已讀取 `/usr/share/man/man1/stat.1.gz`，未執行 generated commands。以 Python stat 常數生成明示 SYNTHETIC 型態案例，不把本機文件或常數當成目標 RHEL9 真機證據。

## 發現與處置

共 9 類：高 6、中 3、重大 0。嚴重度按可能錯誤符合宣告與適用性影響，非 53 項的相加項數。規則 ID 可直接定位 policies；函式定位可用 `rg -n`，避免重建後行號漂移。

| 問題 | 程度／位置與影響 | 可重現 SYNTHETIC 案例 | 處置與殘餘風險 |
| --- | --- | --- | --- |
| Q1-01 | 高；policy.definitions／batch1.rules，全部 53 ID | 每個 rule 的正向 stdout 配 exit_code=1/127、stderr=error，仍匹配 PASS | 不假造退出碼保護。現有正向匹配無法證明命令完整成功；53 項 execution_review blocked、描述逐項列問題，報表阻止 raw PASS 成為 verified compliance。需目標引擎錯誤辨識證據；若要可靠狀態標記須另提核准架構。 |
| Q1-02 | 高；report.normalize／metrics | 全部 53 回 passed，舊版把 full 候選計為 PASS／完整率 | 已修正：raw_result 保留，blocked／partial passed 為 MANUAL_PENDING；候選 FAIL 保留，但完整率不計未驗證判定。新增 verified_compliance／raw_observed／verified_decided。未著作虛構掃描。 |
| Q1-03 | 中；batch1.rules，FILES 全部 | 中文／德文型態不是英文 regular file；舊版 false FAIL。舊版額外拒絕非 regular | 已移除所有 %F。來源明列目錄的 0179、0193–0202 以 `%f` 的 `^4[0-9a-f]{3}$` 核對型態；不附加來源未明定的 regular 限制。多語系為具名合成情境，非已安裝 locale 真測。 |
| Q1-04 | 高；0045/0046 與 FILES metadata | root 擁有的 symlink 可有 root:root；NSS 名稱 root 不必證明 uid=0；ACL 可能有額外或 default entries | 來源明列 chown/chmod，未明定 regular-only 或 symlink 的符合性；不猜解參照、不固定 shadow GID、不把 %U:%G 名稱當完整身分保證。0045 數字 0:0 與其他名稱規則差異保留待來源核准。mode mask 窮舉 0000–7777，拒絕額外 special bits；ACL mask 對 effective 權限與 default ACL、特殊位元是否額外要求均待審，不宣稱已檢查 ACL。 |
| Q1-05 | 高；0053–0060、0141、0178、0191/0192，report.normalize | 備份／角色相關檔案缺失，stat 空輸出、N/A、權限錯誤不可混同 | 不創建或讀取秘密檔內容。新 evidence_status missing 為 MANUAL_PENDING，tool_error／permission_error／timeout 為 ERROR，raw 原樣保存；缺失需明確證據與適用性核准才 N/A。無分類的 raw failed 仍是候選 FAIL 觀察，非已驗證不符合或自動核准 N/A。 |
| Q1-06 | 高；0030/0094/0097/0098/0101/0133/0175/0243/0245 systemctl show | 各 property 分次讀取可混合狀態；service inactive 不能證明無 socket／alias 啟動路徑；錯誤 stdout 也可匹配 | 保留實際 unit 身分與嚴格 raw predicate，不把 disabled/masked、active/inactive/failed 混為一談。沒有已驗證的無相依原生命令組合解決原子性、啟動閉包與錯誤區分；execution blocked。enabled-runtime、masked-runtime、static、alias、indirect 不自動批准。 |
| Q1-07 | 中；0030/0094/0097/0098/0245 | 不必要服務不存在、LoadState=not-found，舊規則 raw FAIL；D-Bus failure 也可能無輸出 | 來源意圖可能已滿足，不能只因不存在宣告不符合。這 5 項 coverage blocked，新增 absence_unverified 治理待審；不以空輸出或文字錯誤自動 PASS。0030 原方法 disable；0094/0097/0098/0245 原方法 mask，來源核准須分別決定不存在與已安裝遮蔽的處置。 |
| Q1-08 | 高；0108/0141/0269/0270 | live sysctl=0 但持久=1；其他 rules.d 弱權限；sshd 預設 no、Match 情境 yes | 保留 partial、raw passed 待審。未擴充掃描、未改變來源設定方法；須核准解析／情境設計及 RHEL9 證據。 |
| Q1-09 | 中；policy.parse_rule／simulate | p:、複合 regex、lookahead、空 rules 舊版可默默近似；splitlines 將內嵌 CR 拆行成 PASS | 已限制現有 c:/f: 單一正向 r:、all、固定 emitted patterns 與簡單 ASCII literal；其他語法先拒絕。以 LF 分行，內嵌 CR 不自行拆出符合行。仍不是 PCRE2／Wazuh 引擎驗收。 |

## 各實作族結論

檔案 metadata 共 36 項（原有 0045/0046 + FILES 34 項）：權限採位元子集合，000 要求精確零，不作八進位大小比較。來源的「目錄」支持 directory predicate；來源的「檔案」不必然限定 regular，移除額外限制後必須把 symlink／FIFO／socket／device 的來源解讀交回核准，不稱它們符合。目錄型態檢查不替代 mode 檢查，owner 控制不偷偷加入 mode 限制。備份檔不存在和查詢失敗無法由空輸出區分；僅保留 metadata，不存 shadow/gshadow 內容。cron.d 未聲稱檢查內部檔案。

RPM 存在共 5 項：0033 sudo、0132 audit + audit-libs（兩者都必要）、0174 rsyslog、0183 libselinux、0242 firewalld。queryformat 正向標記避免「否定空輸出＝未安裝」問題，仍不能保證 RPM DB 失敗而部分 stdout 不會 false PASS；不代表 AIDE 初始化或其他來源要求，未擴充 ID。

systemd 共 9 項：0030 autofs disabled；0094 rsyncd／0097 squid／0098 smb masked；0101 kdump／0133 auditd／0175 rsyslog／0243 firewalld enabled 且 active；0245 nftables masked 且 inactive。失敗、暫態、runtime、static、alias 都保留原始差異；沒有把 failed 當 inactive。停用組的不存在可能滿足降低攻擊面的意圖，但 mask 設定方法與合法 absence 要分別核准；D-Bus、權限與工具錯誤不能偽裝 absence。socket activation、alias canonical unit、masked-runtime 持久性與狀態競態尚未完整實作；不能自行增設 helper。

0245 以 Firewalld profile 核准適用；nftables backend 不等於 nftables.service。來源寫明 Firewalld 相依套件與停用並遮蔽的目的，不將 Nftables 工作表納入，也不建立完整 Nftables 政策。

sysctl 1 項與 SSH 2 項維持原部分候選，分別欠缺持久設定／路由角色與 Match／使用者／來源矩陣，不能用單次 stdout 宣告完整要求。

## 模擬與報表的明確邊界

模擬器不執行命令；exit_code 與 stderr 不影響 stdout regex。error 是呼叫端「無可靠觀察」診斷，只回 UNRESOLVED，並非假設 Wazuh 有相同錯誤辨識。engine_result=NOT_APPLICABLE 是明確 fixture／引擎結果；f: 內容目標 exists=False 按文件 N/A，空內容為 FAIL。all 有 FAIL 優先；未定觀察次之，再 N/A。any／none 未被發出，測試確保拒絕，不宣稱模擬它們。

Python re.ASCII 僅替代現有有限模式的逐 LF 行 search。PCRE2 Unicode/UCP、case folding、lookaround、backreference、possessive quantifier、CRLF/newline convention、NUL、截斷、輸出編碼及 Wazuh regex flags 未驗證；未知語法拒絕。Wazuh argv／命令啟動、stdout/stderr 合併、timeout、權限、檔案競態與 N/A 真實轉換都不由模型保證。%f 的格式與 locale 無關係是離線設計依據，仍須目標 coreutils 版本實測。

報表 `state=FAIL` 可保留候選負向觀察，只有 `verified_compliance=true` 才計完整判定。full 與 execution_review=passed 同時具備才可計分，目前無項目具備；不能靠來源命名或附上 UNVALIDATED 字樣繼續計為完整。缺失與工具錯誤 evidence_status 是明確離線輸入契約，不是新增端點探測器。未提供原因時不能自行推論 missing，也沒有由 stdout 發明原因。

## 逐 ID 對帳

以下 suffix 均指 TWGCB-01-012-，數字 SCA ID 為 900000 + suffix。每項 execution_review=blocked、source_approval=pending、live_validation=UNVALIDATED；問題代碼對應上表的案例、處置與殘餘風險。完整來源逐格證據見 manifest.reviewed。

| ID | SCA ID | 實作族／實際對象 | 來源期望 | coverage | 發現 |
| --- | --- | --- | --- | --- | --- |
| 0030 | 900030 | systemd 服務 / autofs.service | 停用 | blocked | Q1-01, Q1-06, Q1-07 |
| 0033 | 900033 | RPM 存在 / sudo | 安裝 | partial | Q1-01 |
| 0045 | 900045 | 檔案 metadata / /etc/passwd owner | root:root | partial | Q1-01, Q1-03, Q1-04 |
| 0046 | 900046 | 檔案 metadata / /etc/passwd mode | 644或更低權限 | partial | Q1-01, Q1-03, Q1-04 |
| 0047 | 900047 | 檔案 metadata / /etc/shadow | root:root或root:shadow | partial | Q1-01, Q1-03, Q1-04 |
| 0048 | 900048 | 檔案 metadata / /etc/shadow | 000 | partial | Q1-01, Q1-03, Q1-04 |
| 0049 | 900049 | 檔案 metadata / /etc/group | root:root | partial | Q1-01, Q1-03, Q1-04 |
| 0050 | 900050 | 檔案 metadata / /etc/group | 644或更低權限 | partial | Q1-01, Q1-03, Q1-04 |
| 0051 | 900051 | 檔案 metadata / /etc/gshadow | root:root或root:shadow | partial | Q1-01, Q1-03, Q1-04 |
| 0052 | 900052 | 檔案 metadata / /etc/gshadow | 000 | partial | Q1-01, Q1-03, Q1-04 |
| 0053 | 900053 | 檔案 metadata / /etc/passwd- | root:root | partial | Q1-01, Q1-03, Q1-04, Q1-05 |
| 0054 | 900054 | 檔案 metadata / /etc/passwd- | 644或更低權限 | partial | Q1-01, Q1-03, Q1-04, Q1-05 |
| 0055 | 900055 | 檔案 metadata / /etc/shadow- | root:root或root:shadow | partial | Q1-01, Q1-03, Q1-04, Q1-05 |
| 0056 | 900056 | 檔案 metadata / /etc/shadow- | 000 | partial | Q1-01, Q1-03, Q1-04, Q1-05 |
| 0057 | 900057 | 檔案 metadata / /etc/group- | root:root | partial | Q1-01, Q1-03, Q1-04, Q1-05 |
| 0058 | 900058 | 檔案 metadata / /etc/group- | 644或更低權限 | partial | Q1-01, Q1-03, Q1-04, Q1-05 |
| 0059 | 900059 | 檔案 metadata / /etc/gshadow- | root:root或root:shadow | partial | Q1-01, Q1-03, Q1-04, Q1-05 |
| 0060 | 900060 | 檔案 metadata / /etc/gshadow- | 000 | partial | Q1-01, Q1-03, Q1-04, Q1-05 |
| 0094 | 900094 | systemd 服務 / rsyncd.service | 停用 | blocked | Q1-01, Q1-06, Q1-07 |
| 0097 | 900097 | systemd 服務 / squid.service | 停用 | blocked | Q1-01, Q1-06, Q1-07 |
| 0098 | 900098 | systemd 服務 / smb.service | 停用 | blocked | Q1-01, Q1-06, Q1-07 |
| 0101 | 900101 | systemd 服務 / kdump.service | 啟用 | partial | Q1-01, Q1-06 |
| 0108 | 900108 | sysctl 即時值 / IPv4/IPv6 forwarding | 0 | partial | Q1-01, Q1-08 |
| 0132 | 900132 | RPM 存在 / audit, audit-libs | 安裝 | partial | Q1-01 |
| 0133 | 900133 | systemd 服務 / auditd.service | 啟用 | partial | Q1-01, Q1-06 |
| 0141 | 900141 | 檔案 metadata / /etc/audit/rules.d/audit.rules | 600或更低權限 | partial | Q1-01, Q1-03, Q1-04, Q1-05, Q1-08 |
| 0142 | 900142 | 檔案 metadata / /etc/audit/auditd.conf | 640或更低權限 | partial | Q1-01, Q1-03, Q1-04 |
| 0174 | 900174 | RPM 存在 / rsyslog | 安裝 | partial | Q1-01 |
| 0175 | 900175 | systemd 服務 / rsyslog.service | 啟用 | partial | Q1-01, Q1-06 |
| 0178 | 900178 | 檔案 metadata / /var/log/messages | root:root | partial | Q1-01, Q1-03, Q1-04, Q1-05 |
| 0179 | 900179 | 檔案 metadata / /var/log | root:root | partial | Q1-01, Q1-03, Q1-04 |
| 0183 | 900183 | RPM 存在 / libselinux | 安裝 | partial | Q1-01 |
| 0191 | 900191 | 檔案 metadata / /etc/crontab | root:root | partial | Q1-01, Q1-03, Q1-04, Q1-05 |
| 0192 | 900192 | 檔案 metadata / /etc/crontab | 600或更低權限 | partial | Q1-01, Q1-03, Q1-04, Q1-05 |
| 0193 | 900193 | 檔案 metadata / /etc/cron.hourly | root:root | partial | Q1-01, Q1-03, Q1-04 |
| 0194 | 900194 | 檔案 metadata / /etc/cron.hourly | 700或更低權限 | partial | Q1-01, Q1-03, Q1-04 |
| 0195 | 900195 | 檔案 metadata / /etc/cron.daily | root:root | partial | Q1-01, Q1-03, Q1-04 |
| 0196 | 900196 | 檔案 metadata / /etc/cron.daily | 700或更低權限 | partial | Q1-01, Q1-03, Q1-04 |
| 0197 | 900197 | 檔案 metadata / /etc/cron.weekly | root:root | partial | Q1-01, Q1-03, Q1-04 |
| 0198 | 900198 | 檔案 metadata / /etc/cron.weekly | 700或更低權限 | partial | Q1-01, Q1-03, Q1-04 |
| 0199 | 900199 | 檔案 metadata / /etc/cron.monthly | root:root | partial | Q1-01, Q1-03, Q1-04 |
| 0200 | 900200 | 檔案 metadata / /etc/cron.monthly | 700或更低權限 | partial | Q1-01, Q1-03, Q1-04 |
| 0201 | 900201 | 檔案 metadata / /etc/cron.d | root:root | partial | Q1-01, Q1-03, Q1-04 |
| 0202 | 900202 | 檔案 metadata / /etc/cron.d | 700或更低權限 | partial | Q1-01, Q1-03, Q1-04 |
| 0301 | 900301 | 檔案 metadata / /etc/shells | root:root | partial | Q1-01, Q1-03, Q1-04 |
| 0302 | 900302 | 檔案 metadata / /etc/shells | 644或更低權限 | partial | Q1-01, Q1-03, Q1-04 |
| 0242 | 900242 | RPM 存在 / firewalld | 安裝 | partial | Q1-01 |
| 0243 | 900243 | systemd 服務 / firewalld.service | 啟用 | partial | Q1-01, Q1-06 |
| 0245 | 900245 | systemd 服務 / nftables.service | 停用 | blocked | Q1-01, Q1-06, Q1-07 |
| 0256 | 900256 | 檔案 metadata / /etc/ssh/sshd_config | root:root | partial | Q1-01, Q1-03, Q1-04 |
| 0257 | 900257 | 檔案 metadata / /etc/ssh/sshd_config | 600或更低權限 | partial | Q1-01, Q1-03, Q1-04 |
| 0269 | 900269 | SSH 預設有效設定 / PermitRootLogin | no | partial | Q1-01, Q1-08 |
| 0270 | 900270 | SSH 預設有效設定 / PermitEmptyPasswords | no | partial | Q1-01, Q1-08 |

## 實際執行證據與重跑方式

基線 HEAD：`ca76af50b6a2805bc8de29d6f06315639fb9daa2`。將 HEAD 已追蹤內容複製到 `/tmp` 的暫存目錄，只加入目前 `tests/test_quality_q1.py`，執行 `python3 -m unittest discover -s tests -p test_quality_q1.py -v`：11 methods，exit 1，**96 failures（包含 subtests）、1 error**。error 為基線缺少新增報表契約欄位；失敗包含既有 raw PASS 計分、missing 治理、%F、未知語法與 CR 拆行。這不是 97 個獨立測試方法。完整輸出保留於忽略產物 `out/q1-baseline-regression.txt`；未執行其中任何政策命令。

目前版本實際重跑全部 exit 0：

```bash
python3 -m linuxgcb build
python3 -m linuxgcb validate
python3 -m unittest discover -s tests -v
python3 -m linuxgcb report tests/fixtures/snapshot.json --out out/q1-synthetic --now 2026-10-30T00:00:00Z
git diff --check
```

**38 tests 全數 OK**，包含 11 個新增 Q1 methods；mode 子案例窮舉 0000–7777、來源逐格對照、53 項 positive/negative/missing/empty/error/nonzero matching、全部 9 服務的 property 狀態矩陣、7 種型態與 3 個具名合成語系、unsupported syntax、all 聚合、報表端到端。語系資料是合成，沒有實際變更 locale 或掃描開發機。

SYNTHETIC 報表：314 列，適用 307，MANUAL_PENDING 260、NOT_SCANNED 45、候選 FAIL 1、ERROR 1、EXCLUDED 7、PASS 0；raw_observed 6、verified_decided 0、pass_rate null、attainment 0%、completeness 0%。歷史交接所寫「七筆觀察」不精確：目前及 HEAD snapshot 實際均只有 6 個 checks；沒有補造第七筆。重建僅更新 fixture policy hashes。

來源逐位元對照 HEAD 未變：

| 來源 | SHA256 |
| --- | --- |
| XLSX | `7d752b639a1e780df08814c6252efadd3ea2711eaa5c9d91c070b84a296c0247` |
| DOCX | `986effd9501b1fd97776129c6691cf8fc98246bd04514347322f3337508e0e5b` |
| controls.json | `a95f8358b18f57600c97c0023bb48f98a867adf09c2535f86d9be25e28643be4` |
| inventory.json | `b7351760043d1732aef3ebe3df38fde2d6065f63ac87dc17cd037bc1ca6d769e` |

全部 314 數字 ID 序列與既有 53 候選 ID 集合均等於 HEAD；政策 manifest 重算對帳 53。歷史 BATCH1_REVIEW、HANDOFF、CODEX_HANDOFF、CODEX_BATCH1_HANDOFF 與來源均未重寫。

## RHEL9 接受 gates 與架構待核准點

依 NEXT_STEPS 固定目標版本，在核准可還原試驗環境測三份 YAML 載入與逐族正常／負向／錯誤、非零但匹配輸出、stdout/stderr／timeout／argv 與 PCRE2 的真實結果，對照 Agent log、Manager API、人工唯讀證據。先做失敗注入再談解除 blocked；不得以本機 38 tests 代替。

來源核准另確認 metadata 的 symlink／ACL／NSS／special bits、備份缺失及 optional file、停用與 mask 的合法 absence；核對 socket、alias、static、runtime 狀態與 Firewalld 適用條件。保留真正 source identities，不推導完整 nftables 政策。

若原生固定命令無法可靠封裝退出狀態，候選提案為「固定唯讀、失敗分支不輸出 PASS 標記的受控執行器」，需另審命令白名單、執行上限、stdout 格式、競態、集中配送／hash／權限與更新回復，並沿用已核准 bootstrap 慣例。**本次沒有實作此架構，也沒有新增端點安裝或人工步驟；此變更停止於提案，等待明確授權。** 即使引擎能辨識部分錯誤，仍需逐族證據才能解除相應阻擋。

修改範圍：linuxgcb 的 batch1/catalog/coverage/policy/report，新增 quality；三份候選 policies；scope_registry/coverage_manifest/policy_hashes；測試與合成 fixtures；README/NEXT_STEPS/POLICIES 與本文件。保留 inspectable 未提交 diff，不 merge、不宣稱 Hermes 接受。精確檔案與增刪量以 `git status --short`、`git diff --stat` 與新檔 diff 查閱。
