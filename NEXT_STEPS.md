# Q1 後續驗收（不擴充控制）

只處理既有 53 項。coverage full 0／partial 48／blocked 5；execution_review blocked 53，尚無真機或來源核准。307／7 母體與所有數字 ID 不變；歷史 handoff 不改寫。

1. Hermes 獨立審閱 [QUALITY_REVIEW_Q1](docs/QUALITY_REVIEW_Q1.md)、逐項 manifest 與未提交 diff，重跑 README 的 build、validate、38 個 unittest、合成報表與 git diff --check，核對來源 hash 與 ID 集合。
2. 在另行核准的可還原 RHEL9 試驗機固定 minor、coreutils/systemd/RPM/OpenSSH、Wazuh Agent/Manager 版本。先驗證每族正常、空輸出、工具缺失、權限錯誤、timeout、stderr、非零但匹配 stdout，保留命令／引擎／API 對帳證據，不執行 Excel remediation。
3. 來源審查確認檔案型態、symlink 解參照、root/shadow 的 NSS 身分、ACL 與特殊位元、缺少備份或選用檔案之適用性；目錄 %f 在多語系與各型態重跑。不讀取或保存 shadow／gshadow 內容。
4. 為 autofs、rsyncd、squid、smb、nftables 核准「未安裝而無啟動路徑」與 disable／mask 的來源解讀；測 active/inactive/failed、static/alias、socket activation、enabled-runtime、masked-runtime、D-Bus 錯誤與查詢競態。0245 只核對原 nftables.service 身分與 Firewalld 適用條件，不新增 Nftables 政策。
5. 0108 持久設定、0141 規則集合、0269／0270 SSH Match 矩陣仍待既有 ID 的核准設計。若執行狀態保護需要唯讀 helper 或 bootstrap 架構改變，先提出集中配送、權限、hash、更新／回復與信任提案，等待明確授權；本次未實作。
6. 核准試點才驗證既有 sca.remote_commands=1 安裝慣例、Manager 下發／更新／回復與 API 完整快照。依證據逐項解除 execution_review 阻擋，來源核准與真機驗證分開記錄，不能由離線測試自動解除。

本輪不開發下一批、全量政策、Dashboard、live transport、daemon、排程或新端點人工步驟。未獲獨立接受前不得把 raw PASS 宣稱為完整符合。
