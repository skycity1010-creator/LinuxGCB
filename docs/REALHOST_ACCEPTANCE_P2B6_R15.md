# LinuxGCB P2B6 真機驗收（R15，2026-11-01）

P2B6 commit `6788fdc`：帳號與存取控制 42 條（0206–0241、0309–0314），base 111→153，三政策總候選 188。

## 驗證鏈
- 父端獨立驗證：87 測試全過、build/validate 188 候選、既有 146 條 rules diff=0、新增 42、無移除
- Manager 部署 sha256 對帳：`9abd4893…`
- R15 引擎掃描：base 153 條全執行，**舊 146 條零翻轉**（無 side-effect）
- 新增 42 條：**7 PASS / 35 FAIL**，FAIL 全部真機對帳為真實缺失：
  - pwquality.conf 全預設（0206–0217、0311）
  - faillock.conf 全預設（0218、0219、0310）
  - login.defs：PASS_MAX_DAYS 99999、PASS_MIN_DAYS 0、PASS_WARN_AGE 7、UMASK 022、FAIL_DELAY 未設（0223–0225、0227、0240）
  - INACTIVE=-1（0226）、TMOUT 未設（0236）、umask 027 未設（0239、0309）
  - dconf 不存在（0232、0233、0237）、limits 無 maxlogins（0230）、pam_wheel 註解（0241）、nullok 存在（0312）、enforce_for_root/remember 未設（0207、0220）
  - **0229：/etc/sudoers `%wheel NOPASSWD: ALL`**——為 .61 自動化便利設定，本身即 GCB 違規；修復需移除 NOPASSWD，將影響 `sudo -n` 自動化，待 Commander 決定
  - 0221：postlogin 既有 `optional pam_lastlog.so … showfailed`，來源要求 `required` 於最上方 → 保守判 FAIL（來源解讀待批）
- PASS 7 條：0222 sha512、0228 CREATE_HOME、0231 kbd、0235 系統帳號 nologin、0238 root GID 0、0313 pam_pwquality、0314 pam_unix（RHEL9 預設即合規）

## 來源解讀待批（P2B6_REVIEW.md 完整表）
- 0206：來源 `Retry = 3` 大寫 → libpwquality 小寫 retry
- 0208：同時要求 PASS_MIN_LEN 12 + minlen 12
- 0220：來源腳本模組混用 → 採 pam_pwhistory remember≥3
- 0223–0225：只查 login.defs 預設值，既有帳號 chage 效果不讀 shadow
- 0235：依來源 UID_MIN（非 SYS_UID_MAX）
- 0236/0239：bashrc 與 profile/profile.d 同時要求，靜態宣告子集
- 0241：wheel 須含 root，成員名單需人工核准
- 0221：required 於最上方（既有 optional 行不採）

## R15 分數
- base 153：80P/73F（52）；sshd 32/32（100）；firewalld 3/3（100）
- 資料：`data/realhost_scan_20261101_r15.json`
