# LinuxGCB FIX-10 任務：依 Commander 裁定（2026-11-01）修正 900032 + 範本檔案

## Commander 裁定
「0032 產生一個範本檔案，做成功/失敗的驗證」

## 真機證據（2026-11-01）
- /etc/yum.conf → symlink 到 /etc/dnf/dnf.conf；main 有 gpgcheck=1、無 localpkg_gpgcheck → 真實缺失（維持 FAIL 正確）。
- /etc/yum.repos.d/ 僅 redhat.repo（358 bytes，純註解、0 個 section，系統未註冊 subscription-manager 自動生成）。
- 現行規則對「無 section 的 repo 檔」`not seen → return False` → FAIL。來源文字是「將全部之 gpgcheck 設定修改成 1」——無任何 gpgcheck 設定即無可修改項 → 應視為不適用（跳過），與 0244/0091 not-found 同族。

## 修改要求（只動 900032；其餘 306 條 rules diff 必須為零）
1. repo 檔（/etc/yum.repos.d/*）無任何 section → 跳過該檔（vacuously compliant）。
2. 有 section 的 repo 檔：維持現行嚴格判定（每個 section 皆需 gpgcheck=1 與 localpkg_gpgcheck=1）。
3. main（yum.conf/dnf.conf）：維持現行判定（兩 key 皆需 =1）。
4. 新增範本檔案 templates/gcb-gpgcheck.repo（repo 內，非部署檔）：合規範例 section 含 gpgcheck=1、localpkg_gpgcheck=1，附註解說明用途與真機驗證步驟。
5. docs/FIX10_REVIEW.md：裁定對照 + 前後語意 + 真機雙向驗證程序（apply 範本+補 main 兩 key → 預期 PASS；restore → 預期 FAIL）。

## 硬性限制
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets。
- 來源、TWGCB ID、307/7 scope、coverage_manifest、UNVALIDATED、既有 fixtures/證據檔不可改。
- 內嵌命令 w_strtok 雙引號包裝、單一 PASS commit、唯讀、命令內不可有 `->`。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過（新增回歸：純註解 repo 檔→跳過不影響判定；有 section 缺 key→FAIL；main 缺 localpkg_gpgcheck→FAIL）
- 306 條未動 rules diff=0
- git commit（.git 唯讀則保留工作目錄變更並回報）
