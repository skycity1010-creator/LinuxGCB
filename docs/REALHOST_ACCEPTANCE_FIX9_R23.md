# LinuxGCB FIX-9 真機驗收（R23，2026-11-01）

FIX-9 commit `12851d6`：依 Commander 2026-11-01 裁定修改 6 條規則。

## 規則語意
- **0023-0025**：home 所在掛載點（含 LV，/proc/self/mountinfo 最長前綴）視為獨立 FS → 檢查該掛載 nodev/nosuid/noexec
- **0073/0074**：root PATH 靜態解析，$HOME→/root、$PATH→RHEL9 預設展開；跳過含位置參數（$1..）的函式範本（pathmunge）
- **0091**：/etc/group 無 shadow 群組 → PASS

## 驗證鏈
- 133 測試全過、build/validate 307 候選
- 三政策檔逐 check 比對 `3fb7fea`：僅 900023/024/025/073/074/091 rules changed，其餘 diff=0
- 真機本機預驗（w_strtok→argv）：073/074/091 PASS、023/024/025 FAIL（/home LV 無選項）
- 部署 Manager sha256 `8b4896e2…`
- R23 引擎翻轉集合恰好：
  - 900023/024/025 passed→**failed**（/home 是 LV 獨立掛載但無 nodev/nosuid/noexec，真實缺失浮現，符合裁定）
  - 900073/074 failed→**passed**（$HOME 展開後皆絕對路徑、目錄非 group/world-writable）
  - 900091 failed→**passed**（RHEL9 無 shadow 群組）
  - base/sshd/firewalld 其餘零翻轉

## R23 分數
- base 270：128P/142F（47）；firewalld 5/5（100）；sshd 32/32（100）
- 總候選 307：165P/142F
- 資料：`data/realhost_scan_20261101_r23.json`
