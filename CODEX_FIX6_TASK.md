# LinuxGCB FIX-6 任務：修正 P2B7 的 8 條規則缺陷（真機 R16 實證）

## 缺陷 1：家目錄家族 900079–900085 的 nologin 排除清單（6 條假阴性：080–085）
- 現行：跳過 shell 為 `/sbin/nologin` 或 `/bin/false` 的帳號。
- RHEL9 現實：服務帳號 shell 是 **`/usr/sbin/nologin`**（usrmerge），tss/clevis/libstoragemgmt/setroubleshoot/sshd 未被跳過 → 其 home（/、不存在目錄）污染判定 → 080–085 全 FAIL。
- 真機證據：debug 執行 check(80) 顯示 `USER clevis home /var/cache/clevis isdir False`、`USER tss home / want_uid 59 stat_uid 0` 等。
- 修正：排除清單改為 endswith('/nologin')（涵蓋 /sbin 與 /usr/sbin）或同時列入兩者；/bin/false、/usr/bin/false 同理。0079 修正後仍應 FAIL（/root 0550 非 700 子集，真實缺失），不得放寬 mode 語意。

## 缺陷 2：900303/900304 要求 opasswd.old 必須存在（2 條假阴性）
- 現行：`for p in ('/etc/security/opasswd','/etc/security/opasswd.old')` 兩檔都必須存在且 root:root / ≤644。
- 現實：opasswd.old 僅在 pwhistory 輪替後才生成；.61 只有 opasswd（root:root 600）。
- 修正：沿用 FIX-4 not-found 跳過模式——存在的檔案才檢查擁有權/權限；兩者都不存在時依來源文字（GCB 條目為「若存在則檢查」語意）→ 無檔案可檢查時 PASS（與 900144 同型）。

## 硬性限制
- 只動 900079–900085、900303、900304 這 8 條；其餘 228 條 rules diff 必須為零。
- 0032、0038、0073、0074、0091 為來源解讀爭議，本批**不得**順手修改（待 Commander 批）。
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets、no external writes beyond workspace。
- 來源、TWGCB ID、307/7 scope、coverage_manifest 236、政策 name UNVALIDATED、既有 fixtures/證據檔不可改。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過（含新增回歸：/usr/sbin/nologin 帳號被跳過、opasswd.old 缺失跳過、opasswd 存在但 644→FAIL 等）
- 228 條未動 rules diff=0
- docs/FIX6_REVIEW.md：前後對照 + R16 證據
- git commit（.git 唯讀則保留工作目錄變更並回報）
