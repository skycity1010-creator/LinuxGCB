# LinuxGCB P2-BATCH2 任務：擴充 51 項候選檢核（離線開發）

## 範圍（以整類為單位，從 scope_registry 的 unimplemented 選）
僅實作下列類別的未實作條目（合計約 51 項，實際以 registry 為準）：
1. **SSH設定** 剩餘全部（32 總 - 4 已實作 = 28）
2. **cron設定** 剩餘全部（16 - 6 = 10）
3. **SELinux** 全部未實作（7）
4. **安裝與維護軟體** 全部未實作（6）
其餘類別（日誌與稽核、帳號與存取控制、網路、磁碟、系統服務、系統設定與維護）本批不做。
Nftables配置 7 項維持 EXCLUDED。

## 必須沿用的已驗證模式（不得重新發明）
1. **服務類**（FIX-1 已真機驗證）：未安裝/ masked / disabled+inactive 皆合格；
   `LoadState=(loaded|masked|not-found)` + `ActiveState=inactive` + 組合查詢 `^(LoadState=not-found|UnitFileState=(disabled|masked))$`。
2. **description 格式**（EXP-1 已真機驗證）：`合規值: <具體基準值> ｜ <來源/治理備註>`；
   合規值從來源 controls.json 設定方法抽出，抽不出者寫 `合規值: 待確認（來源未提供單一基準值）`，不得編造。
3. **SSH 條目**：以 `sshd -T` 有效值為主（Q1 已標記 Include/Match 限制，沿用 same caveat）；
   來源要求「不存在某參數或為預設值」者，用 `condition: none` 或否定規則精確表達，並在 description 註明預設值依據（RHEL9 OpenSSH 8.0+ 預設）。
4. **命令失敗不得假性 PASS**（Q1-01）：規則要能區分「命令成功且輸出符合」與「命令失敗但碰巧輸出符合」；沿用既有 exit-code 處理模式與 fixtures。
5. 每條 check：compliance.twgcb 帶 TWGCB ID、regex_type pcre2、id 沿用 registry 配置的 sca_id。

## 測試要求（每條至少）
- 正反案例 fixtures（符合/不符合輸出）、缺目標案例、命令失敗案例
- 模擬器與 emitted rules 一致（從 emitted rules 衍生 fixtures）
- 全部既有測試不得回歸

## 硬性限制
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets、no external writes beyond workspace。
- 不得執行 Excel「設定方法」內容；不得掃描開發機冒充 RHEL9。
- 來源 xlsx/controls.json、TWGCB ID、307/7 scope、既有 53 條 rules 不可改動。
- 政策 name 維持 UNVALIDATED；R2/R3 fixtures 數值不可改。
- 不做儀表板/排程/寄送功能。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過；`build && validate` 過（候選數 53→104）
- 既有 53 條 emitted rules diff 為零（防回歸）
- docs/BATCH2_REVIEW.md：逐條 id/TWGCB/規則摘要/正反案例/合規值來源 cell 對照
- git commit（.git 唯讀則保留工作目錄變更並回報）
