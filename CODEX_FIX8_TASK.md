# LinuxGCB FIX-8 任務：修正 900244（iptables 服務不存在時的 not-found 語意）

## 真機證據（R21，2026-11-01）
- .61：`rpm -q iptables-services` → 未安裝；`systemctl is-enabled iptables` → "No such file or directory"；is-active → inactive。
- GCB 0244 expected「停用」：服務單元不存在 → 不可能啟用/執行 → 語意上已停用（vacuously compliant）。
- 現行規則把 not-found 判 FAIL → 假阴性。與 FIX-4（audisp 工具不存在跳過）、FIX-6（opasswd.old）、FIX-7（掛載語意）同型。

## 修正要求（只動 900244；其餘 306 條 rules diff 必須為零）
1. systemctl is-enabled 對不存在單元的輸出（Failed to get unit file state / not-found）→ 視為停用 → PASS；is-active 必須同時 inactive（active 即 FAIL）。
2. 存在單元維持原判定：enabled → FAIL；disabled/masked + inactive → PASS。
3. 錯誤路徑（systemctl 無法執行、rc 異常非 not-found 語意）→ 無輸出 → FAIL 安全側維持。
4. ip6tables 同型處理（0244 涵蓋兩者）。

## 硬性限制
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets。
- 來源、TWGCB ID、307/7 scope、coverage_manifest 307、UNVALIDATED、既有 fixtures/證據檔不可改。
- 0246 的 public 判定維持現狀（待批，不在本批）。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過（新增回歸：not-found→PASS、enabled→FAIL、disabled+inactive→PASS、active→FAIL）
- 306 條未動 rules diff=0
- docs/FIX8_REVIEW.md：前後對照 + R21 證據
- git commit（.git 唯讀則保留工作目錄變更並回報）
