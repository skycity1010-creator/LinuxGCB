# LinuxGCB RHEL9 真機驗收報告（第一輪）

日期：2026-10-31（scan 時間 03:42 UTC）
端點：192.168.1.61（RHEL 9，agent id 010，群組 `linuxgcb`）
Manager：192.168.1.53（Wazuh 4.14.9）
政策來源：`LinuxGCB-codex-quality1/policies/`（Q1 版，仍標記 UNVALIDATED）
原始結果：`data/realhost_scan_20261031.json`（53 項 check 全量，取自 Manager `/var/ossec/queue/db/010.db`）

## 1. 派送鏈驗證（端點僅裝 Agent，設定由中控派下）
- Agent 010 → 群組 `linuxgcb`：`PUT /agents/010/group/linuxgcb` 成功（先前 405 是路徑錯誤，多群組指派須 `PUT /agents/{id}/group/{group}`）。
- 政策檔置於 Manager `/var/ossec/etc/shared/linuxgcb/`，經 shared 同步出現在端點 `/var/ossec/etc/shared/`（3 檔 + 合併 agent.conf）。
- 端點僅安裝 wazuh-agent 4.14.9 + 本機 `sca.remote_commands=1`（已核准前置），其餘全由中控派送 → **需求成立**。
- 陷阱：`agent.conf` 內 `<open_sc>` 不是合法 SCA 標籤，會使整個 linuxgcb 區塊被拒（`sca: ERROR: No such tag 'open_sc'`）；已移除後 3 政策全數載入。
- 完整結果收集：4.14 無 `/sca/{agent}/checks` API；改由 Manager `queue/db/010.db`（sca_check/sca_scan_info）匯出。

## 2. 掃描結果摘要
| 政策 | 分數 | pass | fail | total |
|---|---|---|---|---|
| linuxgcb_rhel9_base_v01 | 76 | 35 | 11 | 46 |
| linuxgcb_rhel9_firewalld_v01 | 66 | 2 | 1 | 3 |
| linuxgcb_rhel9_sshd_v01 | 75 | 3 | 1 | 4 |
| （內建 cis_rhel9_linux 對照） | 38 | 62 | 97 | 159 |

## 3. 13 項 FAIL 真機比對
### 真實符合性缺失（判定正確，屬端點待改善項）
- TWGCB-01-012-0192/0194/0196/0198/0200/0202：cron 相關檔/目錄權限。真機 `/etc/crontab`=644、cron.* 目錄=755；GCB 要求 600/700 → **6 項真實缺失**。
- TWGCB-01-012-0269：`sshd -T` 有效值 `permitrootlogin yes` → **1 項真實缺失**。

### 判定誤差（政策邏輯待修，與 Q1 風險 Q1-06 一致）
- TWGCB-01-012-0030 autofs / 0094 rsyncd / 0097 Squid / 0098 Samba / 0245 nftables：服務**未安裝**（`LoadState=not-found`），規則要求 `LoadState=loaded` 而 FAIL。基準意圖是「不存在或停用皆合格」→ **5 項假阴性**，規則需放寬為 `not-found` 亦合格（nftables 真機實況 disabled+inactive，本應 PASS）。
- TWGCB-01-012-0101 kdump：真機 disabled+inactive，仍 FAIL；規則含 LoadState=loaded 條件，同類問題 → **1 項待釐清/疑似假阴性**。

### 抽檢 PASS 正確性
`/etc/passwd` 644、`/etc/shadow` 000、`/etc/group` 644、ip_forward=0、SELinux Enforcing、firewalld enabled+active — 與真機一致，判定正確。

## 3a. FIX-1 重掃結果（R2，2026-10-31 12:03，scan hash base=b10804ed / fw=e39e1021）
6 項假阴性全數轉 PASS（900030/0094/0097/0098/0101/0245）；firewalld 政策 3/3 PASS。
剩餘 7 項 FAIL 均為真實缺失：cron 權限 6 項 + PermitRootLogin（與真機實測一致）。
結果檔：`data/realhost_scan_20261031_r2.json`。
排障筆記：shared 政策更新後第一次重啟 agent 的 scan_on_start 可能與 shared 同步競態，
評到的仍是舊政策（policy hash 不變即訊號）；再重啟一次即可，或以 hash 變化確認。

## 4. 結論與下一步
1. 派送鏈與真機執行（remote_commands）全鏈路已打通，53 項候選全部實際執行、0 invalid。
2. 待修政策：服務不存在情境（6 項假阴性）→ 修規則後重掃。
3. 端點真實缺失 7 項（cron 權限 6 + PermitRootLogin 1）屬整改範圍，本期只讀不自動修復。
4. 後續：修規則 → 重掃 → 以 Manager DB 快照建立儀表板（Wazuh Dashboard SCA app）與 HTML/CSV/XLSX 報表 → 繼續擴充剩餘 254 項候選。
