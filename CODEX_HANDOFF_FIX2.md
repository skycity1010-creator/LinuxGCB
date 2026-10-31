已完成 FIX-2，變更保留於工作目錄。

- 新 44 條 rules 改用雙引號包裝，通過 w_strtok 模型驗證；舊 53 條完整 check diff=0。
- 新增舊版失敗回歸測試，保留 description、合規值及正則。
- 60 項測試全過；build、validate 通過（97 候選）。
- R2/R3 fixtures 與來源資料未改，全程離線。

詳見 [FIX2_REVIEW.md](/home/skycity1010/projects/LinuxGCB-codex-fix2/docs/FIX2_REVIEW.md)。

已嘗試 commit，但 `.git` 為唯讀，無法建立 `index.lock`，因此未提交。