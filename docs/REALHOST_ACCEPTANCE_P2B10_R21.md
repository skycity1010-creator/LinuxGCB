# LinuxGCB P2B10 真機驗收（R21，2026-11-01）

P2B10 commit `7a8a3db`：Firewalld 配置 2 條（0244、0246）入 `linuxgcb_firewalld.yml`，**307/307 scope 全數實作**（7 條 Nftables 依計畫排除）。

## 驗證鏈
- 125 測試全過（錯誤路徑已含 subprocess mock）、build/validate 307 候選
- 三政策檔逐 check 比對：base/sshd diff=0，firewalld 僅新增 2 條
- Manager 部署 sha256 對帳：firewalld `143ec625…`
- R21：base/sshd 零翻轉；firewalld 3→5 條

## 新增 2 條結果
- **0246 PASS**：firewall-cmd 預設區域 public（來源要求「須設定」；public 是否可接受 → 待批）
- **0244 FAIL → 規則缺陷 → FIX-8**：.61 未安裝 iptables-services，單元不存在（is-enabled → No such file、is-active → inactive）→ 服務不存在即停用（vacuously compliant），現行規則把 not-found 判 FAIL。與 FIX-4/6/7 not-found 同型

## R21 分數
- base 270：128P/142F（47）；firewalld 5：4P/1F（80）；sshd 32/32（100）
- 總候選 307：164P/143F
- 資料：`data/realhost_scan_20261101_r21.json`
