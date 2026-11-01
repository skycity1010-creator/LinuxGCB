# FIX-9 Commander 裁定對照（2026-11-01）

基準 commit：`3fb7feaf51722dc03caf88ea4d7a2c28d96a1930`。只修改下列六條 rules；307 條中其餘 301 條 rules 完全相同，七份政策的 metadata、TWGCB ID、來源與範圍保持原樣。

| 規則 | 裁定 | 修改前 | 修改後 |
| --- | --- | --- | --- |
| 900023 | LV 分割區也視為獨立檔案系統 | home 本身須是獨立掛載點，從 /proc/mounts 查 nodev；無對象 REVIEW | 依 login.defs UID_MIN（未設定時 1000）選帳號，排除 nobody；mountinfo 最長路徑前綴找 home 所在掛載，非根且非偽檔案系統須有 nodev；全部跳過 PASS |
| 900024 | 同上 | 同 0023，查 nosuid | 同 0023，查 nosuid |
| 900025 | 同上 | 同 0023，查 noexec | 同 0023，查 noexec |
| 900073 | 展開 $HOME 後判定 | 僅三個啟動檔，受限 $PATH 展開；$HOME 無法解析 | 靜態讀 /etc/profile、/etc/profile.d/*.sh、/root/.bash_profile、/root/.bashrc 的 PATH 指派；每筆展開後逐元素檢查，空、`.`、`..` 或非絕對路徑 FAIL |
| 900074 | 同意展開後檢查 | 沿用舊 PATH 解析，目錄不存在也 FAIL | 同 0073 的展開集合；存在的目錄有 group/world write 位元即 FAIL，不存在跳過 |
| 900091 | 無 shadow 群組視為通過 | 必須存在唯一 shadow 群組，無補充及主要 GID 成員 | 無 shadow 群組 PASS；存在時維持原成員與主要 GID 判定 |

`$HOME`、`${HOME}` 固定展開為 `/root`；`$PATH`、`${PATH}` 每筆固定展開為 RHEL9 預設 `/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`。不執行啟動檔；無 PATH 指派、讀取錯誤或不支援的動態語法不輸出 PASS。

home 比對以路徑分隔邊界為準，重複掛載路徑採最後一筆；掛載 options 取 mountinfo 的每掛載點選項欄，精確比對 token。LV 不受裝置名稱或與祖先裝置號相同的限制。先找 home 實際所在最深掛載，再排除偽檔案系統；root 掛載跳過。缺 mountinfo 根記錄、帳號格式或必要檔案讀取錯誤不輸出 PASS。

實作由 batch7/batch8 只對指定 ID 內嵌 FIX9 override，保留其餘候選命令位元組；命令仍由 w_strtok 雙引號包裝、唯讀、單一 `print('PASS')`，命令內無 `->`。0020–0022、0026–0028 未改。更新政策 hash 配合政策變更；coverage_manifest、scope_registry、UNVALIDATED、既有 fixtures、來源及證據檔未改。

驗證：`python3 -m unittest discover -s tests -v`，133 tests 全過（16.451 秒）；`git diff --check` 通過。新增合成暫存樹回歸涵蓋 LV 缺/具選項、root 跳過、UID_MIN、最長前綴及邊界、重複路徑、偽檔案系統、HOME/PATH 兩種展開、危險 PATH 元素、所有指派均檢查、缺目錄跳過、目錄 022 位元、無 shadow/空成員/補充成員/主要 GID 成員，以及六條修改範圍與保護檔案。歷史測試僅調整 FIX9 已裁定的語意與規則差異斷言，繼續檢查其餘規則及 metadata。

全程離線，未連線 SSH/API、未操作服務、未使用 sudo 或讀取 secrets。候選仍為 UNVALIDATED；本次驗證只使用合成輸入。
