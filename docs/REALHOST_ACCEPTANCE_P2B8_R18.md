# LinuxGCB P2B8 真機驗收（R18，2026-11-01）

P2B8 commit `971fbc5`：磁碟與檔案系統 46 條（0001–0029、0031、0285–0300），base 201→247，三政策總候選 282。

## 驗證鏈
- 父端獨立驗證：111 測試全過、282 候選、既有 236 條 rules diff=0、find 類全 fail-fast
- Manager 部署 sha256 對帳：`f146e864…`
- R18：base 247 全執行，**舊 236 條零翻轉**
- 新增 46 條：**9 PASS / 37 FAIL**

## 9 PASS
- 0017/0018：/dev/shm nodev/nosuid（RHEL9 預設）
- 0020–0022（可攜式）、0026–0028（NFS）：無對應掛載 → 規則輸出 REVIEW，regex 計為 passed（**適用性語意待批**，非實證符合）
- 0029：world-writable 目錄粘滯位（真機無違規）

## 37 FAIL 分類
**規則缺陷 2 條 → FIX-7（Codex 開發中）**
- 0008（/var）、0015（/home）：mountinfo() 對重複掛載路徑直接 raise，但 RHEL9 `/proc/sys/fs/binfmt_misc` 正常有雙掛載（autofs 觸發＋實際掛載，uniq -d 實證）→ 污染所有 mountinfo 類檢查。.61 的 /var、/home 確為獨立 LV，應 PASS
- 同守衛也污染 0009/0013/0014/0016/0023/0024/0025 的判定路徑（這 7 條修正後仍 FAIL，因真實缺失）

**真實缺失 35 條**
- 19 條模組停用（0001–0003、0031、0285–0300）：/etc/modprobe.d/ 僅 firewalld-sysctls.conf、tuned.conf，無任何 install/blacklist 行
- 0004–0007：/tmp 為 xfs（非 tmpfs）且無 nodev/nosuid/noexec
- 0009–0012：/var/tmp 非獨立分割、無選項
- 0013/0014：/var/log、/var/log/audit 非獨立分割
- 0016、0023–0025：/home 掛載無 nodev/nosuid/noexec
- 0019：/dev/shm 無 noexec（真機 findmnt 實證）

## R18 分數
- base 247：120P/127F（48）；sshd 32/32（100）；firewalld 3/3（100）
- 資料：`data/realhost_scan_20261101_r18.json`

## FIX-7 追補（R19，2026-11-01）
FIX-7 commit `04a49c0`（mountinfo 重複路徑保留最後一條；stacked 守衛限於目標子樹）部署後 R19：
- 翻轉 = [900008, 900013, 900014, 900015, 900023, 900024, 900025]，其餘零翻轉
- **0008/0013/0014/0015 轉 PASS 正確**：.61 實測 /var、/var/log、/var/log/audit、/home 皆為獨立 LV（先前 R18 驗收誤記 /var/log、/var/log/audit 為非獨立，已更正——grep 漏查子掛載點）
- **0023–0025 轉 PASS 為 REVIEW 語意**：使用者家目錄（/home/skycity1010）非獨立掛載點 → selected 空 → REVIEW→passed。與 0016（直接查 /home 掛載 nodev，FAIL）語意不一致；若解讀為「檢查家目錄所在掛載點」則應 FAIL → 與 0020–0022、0026–0028 同列**待批語意**
- 0009（/var/tmp 非獨立）、0016（/home 無 nodev）維持 FAIL，正確
- base 247：127P/120F（51）；資料 `data/realhost_scan_20261101_r19.json`
