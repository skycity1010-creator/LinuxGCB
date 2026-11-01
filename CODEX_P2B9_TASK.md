# LinuxGCB P2B9 任務：網路設定 23 條候選規則（最後一批）

## 起點
branch codex/linuxgcb-p2b9（FIX-7 後，282 候選）。目標：+23 = 305 候選（scope 307 全數覆蓋，7 條 Nftables 排除）。

## 條目（TWGCB-01-012-，全部 category=網路設定）
0109–0131。SCA 數字 ID：TWGCB-01-012-0109 → 900109。
來源方法逐條從 docs/references/ GCB v1.2 來源文件擷取，不得自創檢查。

## 家族與慣例
- sysctl 網路參數（0109–0125）：send_redirects、accept_source_route、accept_redirects、secure_redirects、log_martians、accept_icmp_redirects（廣播/錯誤類）、rp_filter、tcp_syncookies、accept_ra 等，依來源逐條對應 key。
  - 「所有網路介面」類：查 sysctl 設定值（/etc/sysctl.conf、/etc/sysctl.d/*.conf，排除註解）**且**若來源要求含 /proc/sys 即時值則依來源文字；「預設網路介面」類查 default 鍵。數值 expected 在規則層做等值判定。
  - 注意 per-interface 鍵（net.ipv4.conf.all.*、default.*）：來源方法寫 sysctl -w 或寫檔，規則按來源指定來源（設定檔值 vs /proc 即時值）判定，REVIEW 檔說明選擇。
- 協定模組停用（0126–0129：dccp/sctp/rds/tipc）：/etc/modprobe.d/*.conf install/blacklist 行（P2B8 同型）。
- 無線（0130）：依來源方法（modprobe.d 對 wireless/cfg80211 類或 rfkill，照來源文字）。
- 混雜模式（0131）：依來源方法（ip link 輸出 PROMISC 或 ifconfig；引擎命令用來源指定者，唯讀）。

## 硬性規則（沿用全部既有慣例）
1. 既有 282 條 rules diff 必須為零。
2. 內嵌 python3 -c 只讀、單一 PASS commit、w_strtok 雙引號包裝。命令內不可有 `->`。
3. 正則排除註解行、key 前綴誤匹配（all. vs default. 不得互相誤匹配）、值前後空白。
4. 掃描/命令類 fail-fast。
5. 來源與 RHEL9 現實不符：按來源文字實作，docs/P2B9_REVIEW.md 記錄來源解讀待批。
6. offline development only：No SSH、no production API、no service changes、no sudo、no secrets。
7. 政策 name 維持 UNVALIDATED；coverage_manifest 282→305；307/7 scope 不變；既有 fixtures/證據檔不可改。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過；build/validate 305 候選
- 282 條未動 rules diff=0
- docs/P2B9_REVIEW.md：逐條來源對照 + 待批清單（含 all./default. 鍵判定來源選擇、0131 命令選擇）
- git commit（.git 唯讀則保留工作目錄變更並回報）
