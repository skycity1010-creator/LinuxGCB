# LinuxGCB FIX-3 任務：修正 7 條假阴性（rpm 截斷 + rsyslog 語法）

## 真機證據（R6，2026-10-31，FIX-2 後 97 條全執行）
22 項新 FAIL 經真機實值比對：**15 項真實缺失、7 項假阴性**：
- 900102/103/104/105/106/900189（NIS/telnet×2/rsh/tftp/mcstrans 套件應為「未安裝=合格」）：
  規則用 `rpm -qa` 全量清單，**引擎 `OS_StrBreak('\n', out, 256)` 只取前 256 行**（wm_sca.c:1749），
  RHEL9 約 500 套件 → 末行 `LINUXGCB_COMMAND_OK` 標記被截掉 → 標記規則 FAIL → 整條 FAIL。
- 900205（cron 日誌）：正則只認舊式 `cron.* /var/log/cron`，RHEL9 rsyslog 為
  `cron.* action(type="omfile" file="/var/log/cron")` → 誤判。

## 修正要求（只動這 7 條；其餘 90 條 rules diff 必須為零）
1. 套件不存在類改「定向查詢 + 三態輸出」單行模式（杜絕截斷風險）：
   `c:/bin/sh -c "out=$(rpm -q PKG 2>/dev/null); rc=$?; case $rc in 0) echo INSTALLED;; 1) echo ABSENT;; *) exit $rc;; esac" -> r:^ABSENT$`
   （rpm -q 未安裝回 1；其他非零 → 無輸出 → NOT_FOUND → 不合格，錯誤不得冒充合格。）
   注意 sh -c 內不可有未跳脫雙引號；沿用 FIX-2 的 w_strtok 雙引號包裝。
2. 900205 正則擴為同時接受 `cron.* /var/log/cron` 與 `cron.* action(type="omfile" file="/var/log/cron")` 兩種語法（action 內含雙引號處用 \\\" 跳脫）。
3. **模擬器實作 256 行輸出截斷模型**（引擎只比對前 256 行），並加回歸測試：
   >256 行輸出 + 標記在末行 → 模擬結果必須重現 FAIL；修正後單行輸出 → PASS。
4. docs/FIX3_REVIEW.md：7 條前後對照 + 真機 R6 證據摘要。

## 硬性限制
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets、no external writes beyond workspace。
- 不得執行 Excel「設定方法」；來源、TWGCB ID、307/7 scope、其餘 90 條 rules 不可改。
- 15 項真實缺失（900187/188/203/204/258/263/265/266/272/273/275/276/277/280/315）規則不得放寬。
- 政策 name 維持 UNVALIDATED；R2/R3/R6 fixtures 不可改。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過；`build && validate` 過（97 候選）
- 90 條未動 rules diff=0；7 條修正通過截斷模型回歸測試
- git commit（.git 唯讀則保留工作目錄變更並回報）
