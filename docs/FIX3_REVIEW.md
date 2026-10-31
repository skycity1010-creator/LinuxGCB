# FIX3 離線審查（2026-10-31）

## R6 真機證據摘要

依任務提供的 R6 證據：FIX-2 後 97 條全執行，22 項新 FAIL 中有 15 項真實缺失、7 項假陰性。本次未連線真機、未新增或改寫真機證據。

900102/103/104/105/106/900189 使用 rpm -qa 全量清單；RHEL9 約 500 套件。wm_sca.c:1749 的 OS_StrBreak('\n', out, 256) 只保留前 256 行，末尾 LINUXGCB_COMMAND_OK 被截斷，成功標記規則 FAIL，導致整條 FAIL。

900205 的真機設定為 `cron.* action(type="omfile" file="/var/log/cron")`，舊正則只接受 `cron.* /var/log/cron`。

15 項真實缺失 900187/188/203/204/258/263/265/266/272/273/275/276/277/280/315 規則完全不變，包含仍採全量查詢的 900188；本次沒有放寬或宣稱修復這些缺失。

## 修正語意

六條套件規則定向查詢，rpm 回 0 只輸出 INSTALLED；回 1 只輸出 ABSENT；其他退出碼保留且不發布 stdout。只接受 ^ABSENT$，不以空輸出或錯誤推論合格。外層沿用 FIX-2 quote_argument 與 w_strtok 三個 argv 契約，腳本無未跳脫的內層雙引號。

900205 同時接受兩種指定語法，仍要求成功讀取來源設定與成功標記；註解、錯誤 facility、錯誤 action type 與錯誤路徑均不通過。JSON 政策內 action 雙引號以 `\"` 編碼，正則括號以 `\\` 編碼保留跳脫。

## 七條前後對照

以下為 emitted rules 的 JSON 字串表示，完整保留跳脫層級。

### 900102

修改前：
```json
[
  "not c:/bin/sh -c \"out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\\\n'); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^ypbind$",
  "c:/bin/sh -c \"out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\\\n'); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^LINUXGCB_COMMAND_OK$"
]
```

修改後：
```json
[
  "c:/bin/sh -c \"out=$(rpm -q ypbind 2>/dev/null); rc=$?; case $rc in 0) echo INSTALLED;; 1) echo ABSENT;; *) exit $rc;; esac\" -> r:^ABSENT$"
]
```

### 900103

修改前：
```json
[
  "not c:/bin/sh -c \"out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\\\n'); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^telnet$",
  "c:/bin/sh -c \"out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\\\n'); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^LINUXGCB_COMMAND_OK$"
]
```

修改後：
```json
[
  "c:/bin/sh -c \"out=$(rpm -q telnet 2>/dev/null); rc=$?; case $rc in 0) echo INSTALLED;; 1) echo ABSENT;; *) exit $rc;; esac\" -> r:^ABSENT$"
]
```

### 900104

修改前：
```json
[
  "not c:/bin/sh -c \"out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\\\n'); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^telnet-server$",
  "c:/bin/sh -c \"out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\\\n'); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^LINUXGCB_COMMAND_OK$"
]
```

修改後：
```json
[
  "c:/bin/sh -c \"out=$(rpm -q telnet-server 2>/dev/null); rc=$?; case $rc in 0) echo INSTALLED;; 1) echo ABSENT;; *) exit $rc;; esac\" -> r:^ABSENT$"
]
```

### 900105

修改前：
```json
[
  "not c:/bin/sh -c \"out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\\\n'); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^rsh-server$",
  "c:/bin/sh -c \"out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\\\n'); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^LINUXGCB_COMMAND_OK$"
]
```

修改後：
```json
[
  "c:/bin/sh -c \"out=$(rpm -q rsh-server 2>/dev/null); rc=$?; case $rc in 0) echo INSTALLED;; 1) echo ABSENT;; *) exit $rc;; esac\" -> r:^ABSENT$"
]
```

### 900106

修改前：
```json
[
  "not c:/bin/sh -c \"out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\\\n'); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^tftp-server$",
  "c:/bin/sh -c \"out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\\\n'); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^LINUXGCB_COMMAND_OK$"
]
```

修改後：
```json
[
  "c:/bin/sh -c \"out=$(rpm -q tftp-server 2>/dev/null); rc=$?; case $rc in 0) echo INSTALLED;; 1) echo ABSENT;; *) exit $rc;; esac\" -> r:^ABSENT$"
]
```

### 900189

修改前：
```json
[
  "not c:/bin/sh -c \"out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\\\n'); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^mcstrans$",
  "c:/bin/sh -c \"out=$(/usr/bin/rpm -qa --queryformat '%{NAME}\\\\n'); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^LINUXGCB_COMMAND_OK$"
]
```

修改後：
```json
[
  "c:/bin/sh -c \"out=$(rpm -q mcstrans 2>/dev/null); rc=$?; case $rc in 0) echo INSTALLED;; 1) echo ABSENT;; *) exit $rc;; esac\" -> r:^ABSENT$"
]
```

### 900205

修改前：
```json
[
  "c:/bin/sh -c \"out=$(/usr/bin/cat /etc/rsyslog.conf && /usr/bin/find /etc/rsyslog.d -maxdepth 1 -type f -name '*.conf' -exec /usr/bin/cat {} +); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^[ \\t]*cron[.][*][ \\t]+/var/log/cron[ \\t]*$",
  "c:/bin/sh -c \"out=$(/usr/bin/cat /etc/rsyslog.conf && /usr/bin/find /etc/rsyslog.d -maxdepth 1 -type f -name '*.conf' -exec /usr/bin/cat {} +); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^LINUXGCB_COMMAND_OK$"
]
```

修改後：
```json
[
  "c:/bin/sh -c \"out=$(/usr/bin/cat /etc/rsyslog.conf && /usr/bin/find /etc/rsyslog.d -maxdepth 1 -type f -name '*.conf' -exec /usr/bin/cat {} +); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^[ \\t]*cron[.][*][ \\t]+(/var/log/cron|action\\(type=\"omfile\"[ \\t]+file=\"/var/log/cron\"\\))[ \\t]*$",
  "c:/bin/sh -c \"out=$(/usr/bin/cat /etc/rsyslog.conf && /usr/bin/find /etc/rsyslog.d -maxdepth 1 -type f -name '*.conf' -exec /usr/bin/cat {} +); rc=$?; if [ \\\"$rc\\\" -eq 0 ]; then printf '%s\\\\n' \\\"$out\\\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi\" -> r:^LINUXGCB_COMMAND_OK$"
]
```

## 模擬與驗證

simulate 對 stdout 依 LF 分行後只比對前 256 行，正向及 not 規則均使用相同上限。未改變 exit_code、stderr 與未知觀察的既有處理；空 stdout 仍為 FAIL，尚未取得可靠輸出則為 UNRESOLVED。本模型不新增 NOT_FOUND 公開狀態，真機 NOT_FOUND 不合格在此以 FAIL 表達。Python regex 與離線 argv 模型仍非真機 PCRE2／執行驗收。

tests/test_fix3.py 驗證六條歷史規則在 500 行清單後標記被截斷時 FAIL、新單行 ABSENT 時 PASS；另驗證第 256／257 行邊界、否定規則截斷行為、六套件退出碼 0/1/2/3/126/127，及 cron 新舊語法與反例。只執行替換後的 printf/exit 合成命令，沒有執行 rpm 或政策命令。

fix3_baseline.json 保存任務開始時的 97 個 checks 與受保護檔案 hash；測試要求恰好指定 7 個 rules 改變，其餘 90 個完整 checks 相同，7 條非 rules 欄位亦相同。原始 XLSX/DOCX、來源資料、TWGCB mapping、307/7 scope 與 R2/R3 fixtures 不變；workspace 無 R6 fixture，本次亦未建立替代證據。政策 name 保持 UNVALIDATED。

合成 rule_outputs 僅變更六套件情境；900205 原合成舊式輸出仍有效。合成 snapshot 僅同步政策 hash。FIX2 guard 測試保留其餘 38 條覆蓋，六條改由 FIX3 三態測試涵蓋。

- `python3 -m unittest discover -s tests -v`：64 tests，OK。
- `python3 -m linuxgcb build`、`python3 -m linuxgcb validate`：97 候選，通過。
- 指定 7 條 rules 有變更，其餘 90 條 rules diff=0；15 項真實缺失不變。
- 無 SSH、生產 API、sudo、服務變更、秘密讀取、外部寫入或 Excel 設定方法執行；未做真機重掃。
