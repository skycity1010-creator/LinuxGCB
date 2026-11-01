# LinuxGCB P2B7 真機驗收（R16，2026-11-01）

P2B7 commit `bc2cfbb`：系統設定與維護 48 條（0032、0034–0044、0061–0091、0303–0307），base 153→201，三政策總候選 236。

## 驗證鏈
- 父端獨立驗證：101 測試全過、236 候選、既有 188 條 rules diff=0、find 類全 fail-fast
- Manager 部署 sha256 對帳：`8c11fca6…`
- R16：base 201 全執行，**舊 153 條零翻轉**
- 新增 48 條：**23 PASS / 25 FAIL**

## 25 FAIL 分類（逐條真機對帳）
**規則缺陷 8 條 → FIX-6（Codex 開發中）**
- 900080–900085：家目錄家族排除清單只列 `/sbin/nologin`，RHEL9 服務帳號用 `/usr/sbin/nologin`（usrmerge）→ tss/clevis/sshd 等未跳過污染判定（debug 實證 `USER clevis home /var/cache/clevis isdir False`）
- 900303/900304：要求 `/etc/security/opasswd.old` 必須存在；該檔僅 pwhistory 輪替後生成（FIX-4 not-found 跳過同型）

**來源解讀爭議 5 條（待 Commander 批，未改規則）**
- 900032：要求所有 /etc/yum.repos.d section gpgcheck=1 + localpkg_gpgcheck；redhat.repo 全無 gpgcheck 行
- 900038：EFI 系統查 fstab 需 `uid=0,gid=0`；.61 用 `umask=0077`（vfat 功能等價但字面不符）
- 900073/900074：root PATH 靜態解析無法展開 `$HOME/.local/bin`
- 900091：RHEL9 無 shadow 群組，規則要求群組必須存在

**真實缺失 12 條**
- 0034 sudo use_pty、0035 sudo logfile、0036 AIDE 未裝、0037 aidecheck 排程、0039 loader entry 644（需 600）、0040 GRUB 通行碼、0042 core dump（limits+sysctl）、0043 randomize_va_space 未明確設定、0044 crypto policy DEFAULT（需 FUTURE/FIPS）、0071 /lib/.build-id group bin、0079 /root 0550（需 700 子集）、0307 ptrace_scope=0

## R16 分數
- base 201：103P/98F（51）；sshd 32/32（100）；firewalld 3/3（100）
- 資料：`data/realhost_scan_20261101_r16.json`

## FIX-6 追補（R17，2026-11-01）
FIX-6 commit `d5e32f0`（家目錄家族跳過 `/usr/sbin/nologin`；opasswd/opasswd.old not-found 跳過）部署後 R17：
- **翻轉集合恰好 = [900080–900085, 900303, 900304]**，其餘零翻轉；900079 維持 FAIL（/root 0550 真實缺失，符合預期）
- base 201：111P/90F（55）；sshd/firewalld 維持滿分
- 資料：`data/realhost_scan_20261101_r17.json`
