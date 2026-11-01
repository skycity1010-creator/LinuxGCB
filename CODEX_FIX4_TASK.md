# LinuxGCB FIX-4 任務：修正 3 條假阴性（imuxsock 誤匹配 + audisp 工具不存在）

## 真機證據（R9 fixture 正向驗證，2026-11-01，docs/FIXTURE_VALIDATION_R9_R10.md）
套用完整 GCB 合規 fixture 後，P2B3 38 條 FAIL 中 35 條 FAIL→PASS（引擎實證），3 條仍 FAIL：
- 900176（0176）：RHEL9 預設 /etc/rsyslog.conf 含 `module(load="imuxsock" SysSock.Use="off")` 段內 `FileCreateMode="0644"`（imuxsock state file 參數，非日誌檔案建立模式）。rsyslog_mode() 的 overrides 正則 `fileCreateMode\s*=\s*"([^"]*)"` 把 module 參數誤當日誌模式，0644 & ~0640 ≠ 0 → 即使已明確設 `$FileCreateMode 0640` 仍 FAIL。真機已驗證此路徑。
- 900143/900144（0143/0144）：來源 9 工具清單含 audisp-remote、audisp-syslog；RHEL9 audit 3.x 已移除 audisp plugin 系統，該二檔在 RHEL9 不存在（真機確認）。metadata() 對不存在檔拋 OSError → all() 永遠 False → 任何 RHEL9 都不可能 PASS。

## 修正要求（只動這 3 條；其餘 143 條 rules diff 必須為零）
1. 900176：rsyslog_mode() overrides 只從含 `action(` 且含 `omfile` 的行抽取 fileCreateMode；`module(` 行一律排除。保留既有 $FileCreateMode 宣告驗證邏輯不變。
2. 900143/900144：工具清單檢核改為「存在者必符合 mode/owner；不存在者跳過」，與 FIX-1 not-found 先例一致；caveats 必須記錄「RHEL9 audit 3.x 無 audisp plugin；不存在工具跳過之來源解讀待批」。不得放寬存在工具的 mode/owner 標準。
3. 回歸測試：
   - 900176：fixture 加「imuxsock FileCreateMode=0644 + $FileCreateMode 0640」→ PASS；「imuxsock 0644 + 無 $FileCreateMode」→ FAIL；「action(omfile) fileCreateMode=0666」→ FAIL。
   - 900143/144：「9 工具全存在 750/root」→ PASS；「7 存在 750 + 2 不存在」→ PASS（新行為）；「任一存在者 755」→ FAIL；「存在者 owner 非 root」→ FAIL。
4. docs/FIX4_REVIEW.md：3 條前後對照 + R9 證據摘要 + 來源解讀待批事項。

## 硬性限制
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets、no external writes beyond workspace。
- 不得執行 Excel「設定方法」；來源、TWGCB ID、307/7 scope、其餘 143 條 rules 不可改。
- 15 項 R6 真實缺失規則與 FIX-1/2/3 修正不得放寬；政策 name 維持 UNVALIDATED；R2/R3/R6/R7 fixtures 與真機證據檔（含 r8/r9/r10 scan json）不可改。
- coverage_manifest 維持 146 候選。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過；`python3 -m linuxgcb build && python3 -m linuxgcb validate` 過（146 候選）
- 143 條未動 rules diff=0；3 條修正通過上述回歸矩陣
- git commit（.git 唯讀則保留工作目錄變更並回報）
