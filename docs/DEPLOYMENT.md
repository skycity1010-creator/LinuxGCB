# 集中部署範本與驗收（本次未部署）

本次不安裝、不變更服務、不發布政策、不重啟 Agent、不建立索引或排程。Hermes 負責部署審查、核准與外部溝通。

一次性端點前置已獲使用者核准：Wazuh Agent 安裝 bootstrap 必須在首次啟動前，於 `/var/ossec/etc/local_internal_options.conf` 冪等設定 `sca.remote_commands=1`，避免重複或衝突值並讀回確認。這是端點本機設定檔寫入，不是 installer CLI 原生參數，也不能由集中 agent.conf 遠端切換。本版沒有 installer 或修改命令。既有端點若需補設或重啟，仍須另納變更範圍；本次不做。

完成 bootstrap 後，政策、掃描參數與後續版本管理集中由 Manager 進行，僅使用原 Wazuh Agent，不新增第二 daemon/agent。本版無 helper 配送，亦不假設 shared 同步可任意安裝檔案到系統路徑。

## 審查中的群組設定

`templates/agent.conf.example` 指向 Agent `etc/shared/` 下三份政策。Manager 端預定置於 `/var/ossec/etc/shared/<核准群組>/`，權限、擁有者、群組合併規則依部署版本與既有政策核對。不可把此 Linux 條件當作 RHEL9 角色審查；requirements 額外限制 RHEL9，並由已核准群組決定 Firewalld／SSH。沒有 SSH 的角色用獨立群組省略 sshd 參照；其不適用證據另記錄，不能看服務 inactive 就跳過失敗。

未設定新掃描頻率。現有設定的合併、預設政策是否重複計分、指令 timeout 與資源限制須在試點確認後，由 Manager 經核准配置；本版不啟用 scheduler。sca.remote_commands 擴大遠端政策信任範圍，Manager 群組政策必須經審查與權限保護。

## 發布與回復的審查順序

1. 保存已核准 group agent.conf 與前一政策完整檔案／SHA256、群組清單、掃描參數及變更工單。新政策 hash 見 `data/policy_hashes.json`；確認數字範圍未撞號。
2. 先在可還原、已核准的乾淨 RHEL9 試點完成一次安裝 bootstrap，再僅由 Manager 下發政策；比對端點檔案 hash、命令日誌、API 摘要與原始結果。不在開發機假冒執行。
3. 驗證同 policy_id 版本更新、hash 改變、完整重掃與 API 收斂；再驗證從 Manager 回復前一版政策及 agent.conf 可恢復舊 hash 與結果。需要緊急停用時，候選做法為 agent.conf 對對應 `etc/shared/...` policy 設 enabled=no；必須先驗證部署版本的 merge/移除語意。
4. 回復不刪歷史證據、不把舊掃描當新通過、不以服務停用調整 profile。只有完整穩定快照可更新 current。既有端點本機 remote_commands 開關變更不在集中 rollback 能力內，須另行變更核准。

以上為文件流程，不包含部署腳本或已執行記錄。

## 阻擋正式上線的 RHEL9 gates

- [ ] Hermes 確認 RHEL minor、核心、OpenSSH、Wazuh Manager/Agent/Dashboard/Indexer 版本及支援矩陣。
- [ ] 314 項逐條語意／適用性審查，307/7 邊界、0180 缺號、數字 ID 範圍與全部既有政策撞號檢查。
- [ ] libyaml 載入 JSON/YAML 子集、pcre2、requirements 與 compliance 欄位在指定版本正確呈現。
- [ ] 乾淨 Agent bootstrap 一次完成 remote_commands；此後只由 Manager 更新／回復政策與掃描參數，沒有第二個端點人工步驟或 daemon。
- [ ] 七項規則各跑 pass/fail/missing/timeout/permission denied/非零 exit 含匹配 stdout；核對 SCA 的 all 與 N/A 聚合、stderr、API reason 和治理 ERROR。錯誤不能成 pass。
- [ ] stat UID/GID、位元子集合、特殊位元、連結與非一般檔案；systemctl absent/failed/masked/disabled/static 狀態；Firewalld nft backend 與獨立 nftables service 差異。
- [ ] 0108 同時驗證 live 與持久覆寫來源、重開機、路由角色與 IPv6 關閉；未完成前 raw pass 仍是人工待辦。
- [ ] SSH Include/Match 在多 user/group/source/host 情境的 `sshd -T -C` 與實際啟動參數核對，未覆蓋前不提升 0269/0270 為完整 PASS。
- [ ] 實際 API 欄位、時區、hash 演算法、分頁上限、RBAC、scan generation/資料庫同步穩定性與一致性驗證；live transport TLS 驗證及 timeout 測試。
- [ ] 完整快照與原生 SCA 對帳；重收冪等、跨掃描重試、離線／stale、不完整資料、政策更新／回復與版本邊界驗證。
- [ ] 報表分母、核准 N/A、到期例外、HTML/CSV 安全、資料去敏、Dashboard 篩選與完整列數驗收。
- [ ] 試點 CPU/I/O/掃描時間/API 負載、正式角色名單、RBAC、報表頻率、保留期限、群組發佈及回復變更核准。

所有核取項目前皆待真機或人工驗收；離線單元測試不能勾選以上項目。
