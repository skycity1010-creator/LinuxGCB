# LinuxGCB P2B8 任務：磁碟與檔案系統 46 條候選規則

## 起點
branch codex/linuxgcb-p2b8（FIX-6 後，236 候選）。目標：+46 = 282 候選。

## 條目（TWGCB-01-012-，全部 category=磁碟與檔案系統）
0001–0029、0031、0285–0300。SCA 數字 ID：TWGCB-01-012-0001 → 900001。
來源方法逐條從 docs/references/ GCB v1.2 來源文件擷取，不得自創檢查。

## 家族與慣例
- 核心模組停用類（0001–0003、0031、0285–0300，共 19 條）：依來源方法查 /etc/modprobe.d/*.conf 的 install/blacklist 行（排除註解）。模組在 RHEL9 是否存在不影響來源規定的設定檢查——設定缺失即 FAIL，不得因「模組不存在」放寬（與 audit 工具類不同：modprobe 設定是宣示性的，來源要求寫檔）。usb-storage（0031）同型。
- 掛載點存在與檔案系統類型（0004 tmpfs、0008/0009/0013/0014/0015 獨立分割）：讀 /proc/mounts 或來源指定方式；「獨立分割」= 該掛載點本身是獨立裝置（mountpoint 存在且非 root fs 的 bind/subpath）。
- 掛載選項類（0005–0007 /tmp、0010–0012 /var/tmp、0016–0017 home/dev-shm nodev、0018–0019 /dev/shm、0020–0022 可攜式、0023–0025 家目錄、0026–0028 NFS）：以 /proc/mounts 實際掛載選項為準（引擎讀檔即時值），排除註解類檔。無對應掛載點時依來源文字判定（可攜式/NFS 無掛載 → 按來源語意，不得假 PASS 也不得假 FAIL，寫入 REVIEW 說明）。
- 粘滯位（0029）：world-writable 目錄缺 sticky bit → fail-fast find（-type d -perm -0002 ! -perm -1000 -print -quit，-xdev）。

## 硬性規則（沿用 FIX-2~6、P2B2~B7 全部慣例）
1. 既有 236 條 rules diff 必須為零。
2. 內嵌 python3 -c 只讀、單一 PASS commit、w_strtok 雙引號包裝（argv 直傳，禁 sh -c 再包）。命令內不可有 `->`。
3. 正則排除註解行、key 前綴誤匹配、值前後空白。
4. 檔案掃描類一律 fail-fast（-quit / 找到即 exit）+ -xdev。
5. 來源方法與 RHEL9 現實不符：按來源文字實作，真實缺失留真機驗證，必要時 docs/P2B8_REVIEW.md 記錄來源解讀待批。
6. offline development only：No SSH、no production API、no service changes、no sudo、no secrets。
7. 政策 name 維持 UNVALIDATED；coverage_manifest 236→282；307/7 scope 不變；既有 fixtures/證據檔不可改。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過；build/validate 282 候選
- 236 條未動 rules diff=0
- docs/P2B8_REVIEW.md：逐條來源方法對照表 + 來源解讀待批清單（特別是無掛載點時可攜式/NFS 類的判定語意）
- git commit（.git 唯讀則保留工作目錄變更並回報）
