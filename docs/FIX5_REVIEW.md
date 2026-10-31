# FIX5 離線審查：900188 setroubleshoot

## R13 證據與 R6 誤判

依本次任務提供的 R13（2026-11-01）真機證據摘要：.61 執行 `rpm -q setroubleshoot` 確認未安裝（ABSENT），但 900188 在 R6～R13 持續 FAIL。本次未連線重驗；此處記錄使用者提供的證據，並非新增真機掃描結果。

舊規則查詢約 500 個 RHEL9 套件，將 LINUXGCB_COMMAND_OK 放在清單末尾。FIX-3 已確立 wm_sca.c:1749 的 OS_StrBreak('\n', out, 256) 截斷模型：引擎只比對前 256 行，末尾標記消失，成功標記規則 FAIL，整條 all 檢核因此 FAIL，即使 setroubleshoot 不存在亦然。

R6 當時未跑定向 `rpm -q setroubleshoot` 對照，將 900188 誤歸為真實缺失；FIX-3 因此只修 900102/103/104/105/106/900189，漏掉同型的 900188。既有 FIX-3 審查與真機證據保留原樣，此文件記錄後續更正。

## 前後對照

修改前（兩條規則共用全量查詢）：

```text
not c:/bin/sh -c "out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\n'); rc=$?; if [ \"$rc\" -eq 0 ]; then printf '%s\\n' \"$out\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi" -> r:^setroubleshoot$
c:/bin/sh -c "out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\n'); rc=$?; if [ \"$rc\" -eq 0 ]; then printf '%s\\n' \"$out\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi" -> r:^LINUXGCB_COMMAND_OK$
```

修改後（沿用 FIX-3 的 w_strtok 雙引號包裝，單條規則）：

```text
c:/bin/sh -c "out=$(rpm -q setroubleshoot 2>/dev/null); rc=$?; case $rc in 0) echo INSTALLED;; 1) echo ABSENT;; *) exit $rc;; esac" -> r:^ABSENT$
```

rpm 退出 0 → INSTALLED → FAIL；退出 1 → ABSENT → PASS；其他退出碼保留原碼、stdout 為空 → FAIL。查詢輸出先緩衝且不發布，rpm 原始文字即使含 ABSENT 或成功標記也不影響判斷。正常結果只有一行，不再有全量清單超過 256 行而遺失標記的問題。

## 回歸、範圍與驗收

- tests/test_fix5.py 精確驗證 emitted 規則、w_strtok 的三個 argv，以及退出碼 0/1/2/3/126/127。以含 500 行 ABSENT 與成功標記的合成輸出替換完整 rpm 查詢，再執行 printf/exit shell builtins；沒有執行 rpm 或政策命令。
- tests/test_fix3.py 保留歷史 900188 的 255/256/500 行標記與否定規則截斷測試；舊規則只加入測試限定 allowlist，未放寬正式解析器。
- 既有歷史基準測試僅容許 900188 的 rules 差異，其他欄位照常比對。既有 fixtures 不改寫；通用測試僅在記憶體中覆蓋 900188 的合成案例。
- tests/fix5_baseline.json 保存修改前 146 checks 及來源、既有 fixtures、data 的 hash（政策 hash 檔因規則重建而排除）。驗證恰好只有 900188 rules 改變，其餘 145 條完整 checks 相同；900188 其他欄位也完全相同。
- 來源、TWGCB ID、307/7 scope、coverage_manifest 與既有真機證據均未改。政策 name 維持 UNVALIDATED，候選數維持 146。重建只同步 base 政策及其 policy_hashes。
- 全程離線，沒有 SSH、生產 API、服務變更、sudo、秘密讀取或工作目錄之外外部寫入；未宣稱完成真機引擎驗收。

驗收結果：`python3 -m unittest discover -s tests -v`：79 tests，OK；`python3 -m linuxgcb build && python3 -m linuxgcb validate`：通過，314 項、307 候選範圍／7 排除、146 候選規則。其餘 145 條 rules diff=0。

提交結果：已嘗試 `git add ... && git commit`，因 .git 唯讀，建立 .git/index.lock 時回報 Read-only file system，未能進入 commit。所有修改保留於工作目錄；原有未追蹤 codex_fix5.log 未修改、未納入提交清單。
