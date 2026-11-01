# LinuxGCB FIX-10 / FIX-11 真機驗收（R24/R25/R26，2026-11-01）

## FIX-10（commit `c41f622`）：0032 GPG 簽章驗證
- 規則：`/etc/yum.repos.d/*` 無 section 的純註解檔（未註冊系統自動生成的 redhat.repo）視為不適用跳過；有 section 與 main 維持 gpgcheck=1 + localpkg_gpgcheck=1 雙 key 嚴格判定
- 範本：`templates/gcb-gpgcheck.repo`（停用 section、雙 key 合規）
- 137 測試全過；僅 900032 rules changed

### 雙向驗證（Commander 裁定「產生範本檔案，做成功/失敗的驗證」）
- **正向（R24）**：.61 備份後，main 補 `localpkg_gpgcheck=1` + 部署範本 → 引擎 900032 FAIL→**PASS**，其餘 306 條零翻轉
- **反向（R25）**：還原 main 與 symlink、移除範本（cmp 對帳備份一致）→ 900032 回到 **FAIL**
- 備份/還原全程可逆：`/root/gcb-fix10-backup`（已清除）

## FIX-11（commit `da409fb`）：0282/0283 find 加固
- R25 發現 sshd 900283（*.shosts）PASS→FAIL 意外翻轉；手動重跑同命令 rc=0/PASS → 判定為 **flaky 假 FAIL**：`find /` 遍歷 /proc 時瞬間條目消失 → rc≠0 → 成功標記缺失
- 修正：find 加 `-path /proc|/sys|/dev|/run -prune`（偽 FS 上 .shosts 無安全意義）；語意不變
- 測試框架：沿用 FIX-5 in-memory fixture overlay 模式（test_batch2/test_catalog_policy），歷史 fixtures 檔完全不動；各批次釘選測試 allow-set 補 282/283
- 137 測試全過；僅 900282/900283 rules changed；sshd 部署 sha256 `a8840428…`
- **R26**：sshd 32/32 滿分（900283 穩定 PASS），三政策對 R23 零翻轉

## 最終狀態（R26）
- base 270：128P/142F（47）｜firewalld 5：5P（100）｜sshd 32：32P（100）
- **總 307：165P/142F**
- 資料：`data/realhost_scan_20261101_r24.json` ~ `_r26.json`
