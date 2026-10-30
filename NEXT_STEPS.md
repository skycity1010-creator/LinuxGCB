# 後續工作與交接

本批狀態：314 項可追溯 registry、307 候選／7 排除、53 項未驗證候選 SCA（49 full／4 partial）、離線報表、可注入 transport collector 與測試。其餘 254 候選項未實作；全部 314 項語意審查仍待人工核准。

優先工作：

1. Hermes 在本分支獨立重跑 README 命令並審查 diff，核對來源 hash、固定數字 ID 與 307/7 母體。
2. 取得核准的 RHEL9 試點與部署版本，完成 [部署 gates](docs/DEPLOYMENT.md)；先驗證錯誤、非零但匹配輸出、語系與 N/A 的真實行為；不阻擋下一批離線開發。
3. 為 0108 補持久來源覆寫解析，為 0269/0270 建立 SSH 情境矩陣。決定核准的唯讀實作方式；需要 helper 時先驗證集中配送與信任，不增加未核准端點人工步驟。
4. 逐條 DOCX 對照 registry 分類與適用性；新規則須有來源、負向案例、錯誤案例與真機證據，不批次猜測產出完整 307 規則。
5. 驗證 Manager API schema 後實作 TLS 唯讀 transport 與多政策快照→報表轉接器。確認摘要變更／資料庫同步、hash 演算法、時區、重試上限與衝突資料處置。
6. 以原生 Wazuh Configuration Assessment 為對帳基礎，落實專用 current/history 索引與面板；先審查 RBAC、正式角色名單、時效門檻、頻率與保留期限，再另行核准部署。

未決：實際版本／minor、適用性核准權責與證據格式、正式 SCA 數字範圍撞號、API hash/時間欄位、試點負載與掃描頻率、例外簽核來源、索引權限與保留期限。這些不阻擋離線原型，皆阻擋正式上線。

本版沒有 live transport、多政策自動轉接、憑證處理、寫入索引、Dashboard 匯出、XLSX/PDF、排程、寄送、刪除、修復或端點 helper。所有 generated report 放 out/ 不進 git，僅固定 registry/hash/政策與具名小型 SYNTHETIC fixtures 留作審查。沒有 commit；由 Hermes 決定整合。

P2 batch 1 已完成有界擴充 46 項，詳見 [逐項審查](docs/BATCH1_REVIEW.md)。下一批優先：套件移除的正向 absence 證據（須先解決命令／RPM 錯誤與 absence 區分）、0244 雙服務遮蔽、0095 service/socket、0203/0204 allow/deny 集合與不存在行為；再處理選用備份與多檔、GRUB BIOS/UEFI、動態 audit 路徑。不得把全檔案系統、GUI、PAM、audit 載入鏈、SSH Match、持久 sysctl 等難類別視為已完成。原 P0P1 HANDOFF 不重寫。
