# LinuxGCB P2B9 真機驗收（R20，2026-11-01）

P2B9 commit `21e56db`：網路設定 23 條（0109–0131），base 247→270，三政策總候選 **305/307**（7 條 Nftables 排除；剩 0244、0246 兩條 Firewalld 配置 pending）。

## 驗證鏈
- Codex 產出 120 測試中 1 失敗：錯誤路徑測試未 patch `subprocess.run`，0131 在沙箱真實跑 `ip link` 得 PASS。**父端修測試隔離**（規則本身無錯：真機跑 ip link 是預期行為），補 patch 後 120 全過
- 既有 282 條 rules diff=0、build/validate 305 候選
- Manager 部署 sha256 對帳：`2bc55700…`
- R20：base 270 全執行，**舊 247 條零翻轉**
- 新增 23 條：**1 PASS / 22 FAIL**

## 結果分類
- PASS：0131 混雜模式（真機 ip link 無 PROMISC）
- 真實缺失 22 條：
  - sysctl 17 條（0109–0125）：/etc/sysctl.conf 與 /etc/sysctl.d/ 完全沒有網路加固條目；真機即時值 send_redirects=1、rp_filter=0、log_martians=0、accept_ra=1 均不符基準。**注意 0123 tcp_syncookies：核心預設已是 1，但來源方法要求明確寫入 sysctl 設定檔 → 明確設定缺失，與 0043 ASLR 同型解讀**
  - 協定模組 4 條（0126–0129 dccp/sctp/rds/tipc）：/etc/modprobe.d/ 無 install/blacklist
  - 0130 無線：rfkill 存在但無 'disabled' 狀態、無 modprobe 停用設定、無無線硬體 → 按來源文字仍屬設定缺失

## R20 分數
- base 270：128P/142F（47）；sshd 32/32（100）；firewalld 3/3（100）
- 資料：`data/realhost_scan_20261101_r20.json`

## 專案覆蓋結算
- 305/307 已實作；剩 0244（iptables 服務停用）、0246（firewalld 預設區域）→ P2B10 小批可結案
- 累計 FIX 批：FIX-3~7 共修 26 條規則缺陷；待批來源語意：0032/0038/0073/0074/0091、0020–0022/0026–0028/0023–0025（REVIEW 計 passed）、0123（明確設定要求）
