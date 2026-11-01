# LinuxGCB P2B6 任務：帳號與存取控制 42 條候選規則

## 起點
branch codex/linuxgcb-p2b6（FIX-5 後，146 候選）。目標：+42 = 188 候選。

## 條目（TWGCB-01-012-，全部 category=帳號與存取控制）
0206–0241、0309–0314。SCA 數字 ID：TWGCB-01-012-0206 → 900206。
來源方法逐條從 docs/references/ 的 GCB v1.2 來源文件擷取（沿用既有 extractor 流程），不得自創檢查。

## 家族與既有慣例
- pwquality（0206–0217、0311、0313）：/etc/security/pwquality.conf key=value，排除註解；0313 為 /etc/pam.d/ 中 pam_pwquality 啟用。
- faillock（0218、0219、0310）：/etc/security/faillock.conf deny/unlock_time（root 相關依來源）。
- PAM 堆疊（0207、0220–0222、0227、0229、0232?、0241、0312、0314）：RHEL9 走 authselect，/etc/pam.d/system-auth 與 password 為符號連結至 /etc/authselect/；引擎讀檔會解析符號連結——檢查渲染後堆疊檔中的模組行（pam_pwhistory remember、pam_unix sha512/nullok、pam_faildelay delay、pam_wheel use_uid、sudoers NOPASSWD 依來源）。
- login.defs（0208?、0223–0226、0240）：PASS_MIN_DAYS/PASS_MAX_DAYS/PASS_WARN_AGE/UMASK，排除註解。
- 帳號檔（0235、0238）：/etc/passwd awk（0235：UID < SYS_UID_MAX(999) 者 shell 須 nologin/false；0238：root GID=0）。
- umask（0239、0309）：依來源方法（/etc/profile.d 或 /etc/bashrc 的 umask 007/027；0309 root 於 /root/.bashrc）。
- useradd（0228）：/etc/default/useradd CREATE_HOME yes。
- limits（0230）：/etc/security/limits.conf maxlogins ≤10（排除註解）。
- kbd（0231）：rpm -q kbd 三態定向模式（FIX-3/5 慣例，禁 rpm -qa 全量清單）。
- TMOUT（0236）：/etc/profile 或 /etc/bashrc 的 TMOUT ≤900 且 >0。
- GNOME/dconf（0232–0234、0237）：依來源方法讀 dconf 系統 db（/etc/dconf/db/...）或 gsettings 來源檔；headless 主機無 user db 屬正常，按來源文字判定，不得假 PASS。

## 硬性規則（沿用 FIX-2/3/4/5 與 P2B2/B3 全部慣例）
1. 既有 146 條 rules diff 必須為零。
2. 內嵌 python3 -c 只讀、單一 PASS commit、w_strtok 雙引號包裝（argv 直傳，禁 sh -c 再包一層）。
3. 正則排除註解行、key 前綴誤匹配（如 `^key\s*=`）、值前後空白。
4. 數值型 expected（≤/≥/>0）在規則層做範圍判定（awk/python），不得只查 key 存在。
5. 套件檢查一律定向 rpm -q 三態。
6. 來源方法與 RHEL9 現實不符時（如 dconf 未安裝）：按來源文字實作，真實缺失留真機驗證，不得放寬成假 PASS；必要時在 docs/P2B6_REVIEW.md 記錄來源解讀待批。
7. offline development only：No SSH、no production API、no service changes、no sudo、no secrets。
8. 政策 name 維持 UNVALIDATED；coverage_manifest 146→188；307/7 scope 不變；既有 fixtures/證據檔不可改。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過；build/validate 188 候選
- 146 條未動 rules diff=0
- docs/P2B6_REVIEW.md：逐條來源方法對照表 + 來源解讀待批清單
- git commit（.git 唯讀則保留工作目錄變更並回報）
