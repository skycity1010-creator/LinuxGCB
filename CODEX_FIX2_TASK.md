# LinuxGCB FIX-2 任務：修正 44 條新 check 的命令引號（真機實測全 FAIL）

## 真機證據（R5，2026-10-31，agent 010 / Wazuh 4.14.9）
P2B2 新增 44 條部署後真機掃描：44 條全 FAIL（舊 53 條結果不變）。
根因（已讀 4.14.9 原始碼確認）：
- `wm_exec()` 以 `w_strtok(command)` 分詞後直接 `execvp()`，**不經過 shell**。
- `w_strtok()` 只認 **雙引號**（成對、会被剝除、組內空格保留）與 **反斜線跳脫**；**單引號是一般字元**。
- 因此 `c:/bin/sh -c 'out=$(...); rc=$?; ...'` 被切成多個 argv，sh 只收到 `out=$(/usr/sbin/sshd` → 語法錯誤 → 無輸出 → FAIL。
- 另：`wm_exec` 正常結束（含非零退出碼）回 0，輸出照樣逐行比對 → 引擎不檢查退出碼，exit-guard 必須由命令自己做（Q1-01 維持）。

## 修正要求（僅動 P2B2 新增的 44 條；舊 53 條 rules diff 必須為零）
1. 命令包裝改為 w_strtok 相容語法：sh -c 的腳本用**雙引號**包一組，腳本內需要 shell 雙引號處寫 `\"`，shell 內字串改用單引號。例（政策檔內的最終規則字串，非 JSON 轉義前）：
   `c:/bin/sh -c "out=$(/usr/sbin/sshd -T); rc=$?; if [ \"$rc\" -eq 0 ]; then printf '%s\n' \"$out\" LINUXGCB_COMMAND_OK; else exit $rc; fi" -> r:^usepam yes$`
   注意政策檔是 JSON：字串內 `"` 寫 `\"`、`\` 寫 `\\`（即 `\"` 在檔內是 `\\\"`）。
2. **模擬器必須先實作 w_strtok 模型**（雙引號成對分組+剝除、`\\x` 跳脫、單引號一般字元），再由模型產生/驗證命令語意；不得只改政策不改模擬器。
3. 回歸測試：以 w_strtok 模型重現本次真機失敗（單引號版 → 分詞後 sh 收到錯誤 argv → FAIL），雙引號版 → 正確 argv → 正反案例如預期。
4. 每條 44 check 的 rules 全部改寫；command 語意（被檢对象、正則）不變；description/合規值不變。
5. docs/FIX2_REVIEW.md：w_strtok 規則摘要、改寫前後對照、模擬器模型說明。

## 硬性限制
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets、no external writes beyond workspace。
- 不得執行 Excel「設定方法」；來源 xlsx/controls.json、TWGCB ID、307/7 scope、舊 53 條 rules 不可改。
- 政策 name 維持 UNVALIDATED；R2/R3 fixtures 不可改。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過；`build && validate` 過（97 候選）
- 舊 53 條 emitted rules diff=0；44 條新 rules 全部為雙引號包裝且通過 w_strtok 模型
- git commit（.git 唯讀則保留工作目錄變更並回報）
