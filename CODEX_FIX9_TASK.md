# LinuxGCB FIX-9 任務：依 Commander 裁定（2026-11-01）修改 6 條規則

## Commander 裁定原文（節錄）
- 0023-0025：「lv的分割區也視為獨立檔案系統」
- 0073/0074：同意建議（展開 $HOME 後判定）
- 0091：「沒有shadow群組視為通過」

## 修改要求（只動 900023、900024、900025、900073、900074、900091；其餘 301 條 rules diff 必須為零）

### 900023/900024/900025（使用者家目錄 nodev/nosuid/noexec）
- 來源條件：「若發現使用者家目錄掛載在獨立檔案系統，則該掛載須有 nodev/nosuid/noexec」。
- 裁定：LVM 分割區（/dev/mapper/*）掛載視為獨立檔案系統。
- 新語意：對每個 UID>=1000（讀 /etc/login.defs）且非 nobody 的帳號，取 home（/etc/passwd 第 6 欄），以 /proc/self/mountinfo 最長前綴比對找出 home 所在掛載點；若該掛載點不是 / 根掛載（即 home 落在獨立掛載，含 LV）→ 條件成立 → 檢查該掛載 options 是否含所需選項；缺 → FAIL。home 在 / 根掛載 → 條件不成立 → 該帳號跳過。全部帳號跳過 → PASS（來源條件式）。
- 注意 FIX-7 已定的 mountinfo 重複路徑取最後一條、偽檔案系統排除慣例沿用。

### 900073/900074（root PATH）
- 來源：echo $PATH 不得含 '.'、'..'、非 '/' 開頭元素、空元素（0073）；PATH 目錄不得 group/world-writable（0074）。
- 裁定：靜態解析 root 的 PATH 設定（/root/.bashrc、/root/.bash_profile、/etc/profile、/etc/profile.d/*.sh 中 PATH= 指派），將 `$HOME`/`${HOME}` 展開為 /root，`$PATH` 展開為 /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin（RHEL9 預設），逐元素判定。
- 0073：展開後任一元素為 '.'、'..'、非 '/' 開頭或空 → FAIL；否則 PASS。
- 0074：展開後存在的目錄若 group- 或 world-writable → FAIL；不存在的目錄跳過；全部合格 → PASS。

### 900091（shadow 群組）
- 來源：列舉 shadow 群組成員，如有則移除。
- 裁定：/etc/group 無 shadow 群組 → 視為無成員 → PASS。存在則照原判定（有成員 FAIL、無成員 PASS）。

## 硬性限制
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets。
- 來源、TWGCB ID、307/7 scope、coverage_manifest、UNVALIDATED、既有 fixtures/證據檔不可改。
- 0020-0022/0026-0028 現行 REVIEW→passed 語意已獲裁定採認，本批不動。
- 內嵌命令 w_strtok 雙引號包裝、單一 PASS commit、唯讀、命令內不可有 `->`。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過（新增回歸：LV home→檢查選項、home 在 / →跳過、無 shadow→PASS、$HOME 展開後絕對路徑→PASS、'.' 元素→FAIL、不存在目錄跳過）
- 301 條未動 rules diff=0
- docs/FIX9_REVIEW.md：Commander 裁定對照表（逐條前後語意）
- git commit（.git 唯讀則保留工作目錄變更並回報）
