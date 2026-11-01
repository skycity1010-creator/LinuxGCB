# LinuxGCB FIX-5 任務：修正 900188（setroubleshoot 套件檢核的 rpm -qa 截斷假阴性）

## 真機證據（R13，2026-11-01）
- .61 真機 `rpm -q setroubleshoot` → 未安裝（ABSENT），但 900188 在 R6~R13 持續 FAIL。
- 規則用 `rpm -qa --queryformat '%{NAME}\n'` 全量清單 + 末行 LINUXGCB_COMMAND_OK 標記：引擎 OS_StrBreak 只取前 256 行（FIX-3 已確立的截斷模型），RHEL9 約 500 套件 → 標記被截掉 → 標記規則 FAIL → 整條 FAIL。
- 與 FIX-3 修正的 900102/103/104/105/106/900189 完全同型；該 6 條已改定向 rpm -q 三態，900188 當時被誤歸為真實缺失而漏修。

## 修正要求（只動 900188；其餘 145 條 rules diff 必須為零）
1. 改 FIX-3/4 定向三態單行模式：
   `c:/bin/sh -c "out=$(rpm -q setroubleshoot 2>/dev/null); rc=$?; case $rc in 0) echo INSTALLED;; 1) echo ABSENT;; *) exit $rc;; esac" -> r:^ABSENT$`
   （沿用 w_strtok 雙引號包裝；其他非零退出碼 → 無輸出 → 不合格。）
2. 回歸測試：ABSENT→PASS；INSTALLED→FAIL；rpm 錯誤退出→FAIL；截斷模型（>256 行）不適用單行輸出但保留既有模型測試。
3. docs/FIX5_REVIEW.md：前後對照 + R13 證據 + 說明 R6 誤判原因（當時未跑定向查詢對照）。

## 硬性限制
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets、no external writes beyond workspace。
- 來源、TWGCB ID、307/7 scope、其餘 145 條 rules 不可改；政策 name 維持 UNVALIDATED；既有 fixtures 與真機證據檔（r2/r3/r6/r7/r8/r9/r10/r11/r12）不可改。
- coverage_manifest 維持 146 候選。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過；`python3 -m linuxgcb build && python3 -m linuxgcb validate` 過（146 候選）
- 145 條未動 rules diff=0
- git commit（.git 唯讀則保留工作目錄變更並回報）
