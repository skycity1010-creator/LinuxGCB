# LinuxGCB FIX-1 任務：修正「服務未安裝」假阴性規則（離線開發）

## 背景（真機驗收 R1 實測證據，2026-10-31，RHEL9 192.168.1.61）
53 項候選已在真機全數執行。13 項 FAIL 中 6 項為政策假阴性：
服務**未安裝**時 `systemctl show <svc>.service --property=LoadState` 回傳 `LoadState=not-found`，
而規則要求 `r:^LoadState=loaded$`，導致 FAIL。基準意圖為「服務不存在或停用皆合格」。

實測對照：
- autofs/rsyncd/squid/smb/nmb/nftables/kdump：`is-enabled` 報 No such unit 或 disabled；`is-active`=inactive
- nftables 真機為 disabled+inactive，被 LoadState 規則誤判 FAIL（應 PASS）
- 真實缺失（判定正確、**不要改**）：cron 權限 6 項（0192/0194/0196/0198/0200/0202）、SSH PermitRootLogin（0269）

受影響條目：TWGCB-01-012-0030 (autofs)、0094 (rsyncd)、0097 (Squid)、0098 (Samba)、0101 (kdump)、0245 (nftables)。
注意各條 rules 結構不同（有的含 ActiveState/UnitFileState），逐一檢查。

## 硬性限制（與前批相同）
- offline development only。No SSH、no production API、no service changes、no sudo、no secrets、no external writes。
- Never execute remediation commands from Excel/DOCX. No scanning this dev machine as RHEL9.
- Synthetic fixtures labeled test-only. Preserve original xlsx/docx、TWGCB ID、307/7 scope 不變。
- 所有政策維持 UNVALIDATED 標記直到下一輪真機重掃。
- 只修上述 6 條（及同 pattern 的 service 檢查，若共用 helper 請修 helper 並確保其他條目不回歸）。
- 不做儀表板/報表新功能，不新增條目。

## 設計要求
1. 服務類檢查需同時接受：(a) 未安裝/not-found、(b) disabled+inactive；僅 installed+enabled 或 active 才算 FAIL。
2. 優先原生命令可實作（例如 `systemctl show ... -> r:^LoadState=(loaded|not-found)$` 搭配既有 condition 語意，或改用 `systemctl is-enabled` 輸出含 `not-found|disabled` 之 regex）。注意 Wazuh SCA rule 是「規則需全部/任一匹配」語意，負向邏輯要確認模擬器與實際 SCA 行為一致。
3. 更新離線模擬器/測試：新增 not-found 正反案例（未安裝→PASS、installed+enabled→FAIL、installed+disabled+inactive→PASS）。
4. 更新 docs/FIX1_REVIEW.md：逐條列出修改前/後 rules、預期真機結果（6 項應轉 PASS；0101 kdump 說明判定）。
5. `python3 -m unittest discover -s tests -v` 全數通過；`python3 -m linuxgcb build && python3 -m linuxgcb validate` 通過。

## 交付
- git commit（branch codex/linuxgcb-fix1）
- docs/FIX1_REVIEW.md 摘要 + 測試輸出
- 回報修改的檔案清單與每條 check id 的 before/after 一行摘要
