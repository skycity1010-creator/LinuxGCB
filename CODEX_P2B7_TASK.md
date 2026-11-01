# LinuxGCB P2B7 任務：系統設定與維護 48 條候選規則

## 起點
branch codex/linuxgcb-p2b7（P2B6 後，188 候選）。目標：+48 = 236 候選。

## 條目（TWGCB-01-012-，全部 category=系統設定與維護）
0032, 0034–0044, 0061–0091, 0303–0307。SCA 數字 ID：TWGCB-01-012-0032 → 900032。
來源方法逐條從 docs/references/ GCB v1.2 來源文件擷取，不得自創檢查。

## 家族與慣例
- 套件（0036 AIDE）：定向 rpm -q 三態（禁 rpm -qa 全量）。
- cron 排程（0037 aidecheck 每天）：依來源方法查 /etc/cron.daily/ 對應檔存在與內容。
- GRUB（0038–0041）：/boot/grub2/grub.cfg、/boot/loader/entries/、grub2/user.cfg 擁有權/權限/通行碼；0041 依來源（emergency/single-user 鑑別）。
- sysctl（0042 fs.suid_dumpable=0、0043 randomize_va_space=2、00307 yama.ptrace_scope）：讀 /etc/sysctl.conf 與 /etc/sysctl.d/*.conf 設定值（排除註解），0042 另含 limits hard core 0 依來源。
- crypto policy（0044）：/etc/crypto-policies/state/CURRENT.pol 或 update-crypto-policies --show 等來源指定方式，FUTURE 或 FIPS。
- sudo（0034 use_pty、0035 logfile）：grep /etc/sudoers 與 /etc/sudoers.d/*（排除註解）。
- 檔案系統掃描類（0061–0071）：**必須 fail-fast**：find 加 `-xdev`、排除 /proc /sys /dev 等 pseudo fs（依來源），找到第一個違規即 `-print -quit` 結束；只輸出違規清單或 PASS 標記。全 FS find 會撞引擎命令逾時（預設 30s），-quit 是硬性要求。
- 帳號檔類（0072–0091、0303–0305）：/etc/passwd、shadow、group 解析（python3 唯讀）；0072 查 shadow 空密碼欄與鎖定；0073/0074 root PATH（/root/.bashrc 等依來源）；0086/0087–0090 唯一性與存在性；0091 shadow 群組成員空；0303/0304 opasswd 檔（不存在時依來源文字判定，不得假 PASS）。
- 家目錄類（0079–0085）：/home/* 與 /root 依來源（含 .forward/.netrc/.rhosts 不存在）。
- /etc/shells（0305）、chronyd OPTIONS（0306 /etc/sysconfig/chronyd -F 2）。

## 硬性規則（沿用 FIX-2/3/4/5、P2B2/B3/B6 全部慣例）
1. 既有 188 條 rules diff 必須為零。
2. 內嵌 python3 -c 只讀、單一 PASS commit、w_strtok 雙引號包裝（argv 直傳，禁 sh -c 再包）。命令內不可有 `->`。
3. 正則排除註解行、key 前綴誤匹配、值前後空白。
4. 數值型 expected 在規則層做範圍判定。
5. 檔案掃描類一律 fail-fast（-quit / 找到即 exit），並限制在來源指定目錄與 -xdev；避免全 FS 掃描。
6. 來源方法與 RHEL9 現實不符：按來源文字實作，真實缺失留真機驗證，必要時 docs/P2B7_REVIEW.md 記錄來源解讀待批。
7. offline development only：No SSH、no production API、no service changes、no sudo、no secrets。
8. 政策 name 維持 UNVALIDATED；coverage_manifest 188→236；307/7 scope 不變；既有 fixtures/證據檔不可改。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過；build/validate 236 候選
- 188 條未動 rules diff=0
- docs/P2B7_REVIEW.md：逐條來源方法對照表 + 來源解讀待批清單 + 掃描類命令的 fail-fast 說明
- git commit（.git 唯讀則保留工作目錄變更並回報）
