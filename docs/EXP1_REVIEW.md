# EXP-1 合規設定值審查

本次僅離線處理報告文字，53 項 description 使用 `合規值: <value> ｜ Q1 ...`；既有 Q1 文字原樣保留。來源 XLSX、DOCX、controls.json、TWGCB ID 與 307/7 範圍不變，政策仍為 UNVALIDATED。expected 不表示已驗證符合，也不執行設定方法。

來源為 data/controls.json，對照原始 XLSX 的 F 欄（設定方法／configuration_method）與 G 欄（基準值／expected）。數值、權限、所有權直接保留 G 欄；套件名稱、systemctl 狀態及參數名稱由 F 欄補足。`--now enable` 對應 enabled+active，disable 對應 disabled+inactive，mask 對應 masked+inactive。來源 mask 要求照錄，即使目前候選規則接受其他狀態，也不放寬來源基準。未安裝並未在這些來源列明為合規替代值，因此不加入。

53 項均可明確抽出，無待確認項。其他來源若無明確值則使用 `待確認（來源未提供單一基準值）`。權限「更低」保留來源文字，其位元語意及既有 Q1 限制仍須審查。

| TWGCB ID | 合規值 | 來源 cell（工作表!欄列）／JSON 欄位 |
|---|---|---|
| TWGCB-01-012-0030 | autofs disabled+inactive | 基本項目!G34 expected；F34 configuration_method |
| TWGCB-01-012-0033 | sudo 已安裝 | 基本項目!G37 expected；F37 configuration_method |
| TWGCB-01-012-0045 | root:root | 基本項目!G49 expected；F49 configuration_method |
| TWGCB-01-012-0046 | 644或更低權限 | 基本項目!G50 expected；F50 configuration_method |
| TWGCB-01-012-0047 | root:root或root:shadow | 基本項目!G51 expected；F51 configuration_method |
| TWGCB-01-012-0048 | 000 | 基本項目!G52 expected；F52 configuration_method |
| TWGCB-01-012-0049 | root:root | 基本項目!G53 expected；F53 configuration_method |
| TWGCB-01-012-0050 | 644或更低權限 | 基本項目!G54 expected；F54 configuration_method |
| TWGCB-01-012-0051 | root:root或root:shadow | 基本項目!G55 expected；F55 configuration_method |
| TWGCB-01-012-0052 | 000 | 基本項目!G56 expected；F56 configuration_method |
| TWGCB-01-012-0053 | root:root | 基本項目!G57 expected；F57 configuration_method |
| TWGCB-01-012-0054 | 644或更低權限 | 基本項目!G58 expected；F58 configuration_method |
| TWGCB-01-012-0055 | root:root或root:shadow | 基本項目!G59 expected；F59 configuration_method |
| TWGCB-01-012-0056 | 000 | 基本項目!G60 expected；F60 configuration_method |
| TWGCB-01-012-0057 | root:root | 基本項目!G61 expected；F61 configuration_method |
| TWGCB-01-012-0058 | 644或更低權限 | 基本項目!G62 expected；F62 configuration_method |
| TWGCB-01-012-0059 | root:root或root:shadow | 基本項目!G63 expected；F63 configuration_method |
| TWGCB-01-012-0060 | 000 | 基本項目!G64 expected；F64 configuration_method |
| TWGCB-01-012-0094 | rsyncd masked+inactive | 基本項目!G98 expected；F98 configuration_method |
| TWGCB-01-012-0097 | squid masked+inactive | 基本項目!G101 expected；F101 configuration_method |
| TWGCB-01-012-0098 | smb masked+inactive | 基本項目!G102 expected；F102 configuration_method |
| TWGCB-01-012-0101 | kdump.service enabled+active | 基本項目!G105 expected；F105 configuration_method |
| TWGCB-01-012-0108 | net.ipv4.ip_forward=0；net.ipv6.conf.all.forwarding=0 | 基本項目!G112 expected；F112 configuration_method |
| TWGCB-01-012-0132 | audit audit-libs 已安裝 | 基本項目!G136 expected；F136 configuration_method |
| TWGCB-01-012-0133 | auditd enabled+active | 基本項目!G137 expected；F137 configuration_method |
| TWGCB-01-012-0141 | 600或更低權限 | 基本項目!G145 expected；F145 configuration_method |
| TWGCB-01-012-0142 | 640或更低權限 | 基本項目!G146 expected；F146 configuration_method |
| TWGCB-01-012-0174 | rsyslog 已安裝 | 基本項目!G178 expected；F178 configuration_method |
| TWGCB-01-012-0175 | rsyslog enabled+active | 基本項目!G179 expected；F179 configuration_method |
| TWGCB-01-012-0178 | root:root | 基本項目!G182 expected；F182 configuration_method |
| TWGCB-01-012-0179 | root:root | 基本項目!G183 expected；F183 configuration_method |
| TWGCB-01-012-0183 | libselinux 已安裝 | 基本項目!G186 expected；F186 configuration_method |
| TWGCB-01-012-0191 | root:root | 基本項目!G194 expected；F194 configuration_method |
| TWGCB-01-012-0192 | 600或更低權限 | 基本項目!G195 expected；F195 configuration_method |
| TWGCB-01-012-0193 | root:root | 基本項目!G196 expected；F196 configuration_method |
| TWGCB-01-012-0194 | 700或更低權限 | 基本項目!G197 expected；F197 configuration_method |
| TWGCB-01-012-0195 | root:root | 基本項目!G198 expected；F198 configuration_method |
| TWGCB-01-012-0196 | 700或更低權限 | 基本項目!G199 expected；F199 configuration_method |
| TWGCB-01-012-0197 | root:root | 基本項目!G200 expected；F200 configuration_method |
| TWGCB-01-012-0198 | 700或更低權限 | 基本項目!G201 expected；F201 configuration_method |
| TWGCB-01-012-0199 | root:root | 基本項目!G202 expected；F202 configuration_method |
| TWGCB-01-012-0200 | 700或更低權限 | 基本項目!G203 expected；F203 configuration_method |
| TWGCB-01-012-0201 | root:root | 基本項目!G204 expected；F204 configuration_method |
| TWGCB-01-012-0202 | 700或更低權限 | 基本項目!G205 expected；F205 configuration_method |
| TWGCB-01-012-0301 | root:root | 基本項目!G261 expected；F261 configuration_method |
| TWGCB-01-012-0302 | 644或更低權限 | 基本項目!G262 expected；F262 configuration_method |
| TWGCB-01-012-0242 | firewalld 已安裝 | Firewalld防火牆!G5 expected；F5 configuration_method |
| TWGCB-01-012-0243 | firewalld enabled+active | Firewalld防火牆!G6 expected；F6 configuration_method |
| TWGCB-01-012-0245 | nftables masked+inactive | Firewalld防火牆!G8 expected；F8 configuration_method |
| TWGCB-01-012-0256 | root:root | SSH伺服器!G7 expected；F7 configuration_method |
| TWGCB-01-012-0257 | 600或更低權限 | SSH伺服器!G8 expected；F8 configuration_method |
| TWGCB-01-012-0269 | PermitRootLogin no | SSH伺服器!G20 expected；F20 configuration_method |
| TWGCB-01-012-0270 | PermitEmptyPasswords no | SSH伺服器!G21 expected；F21 configuration_method |

報表契約：優先解析原始 check.description 前綴；缺少時可用目前本地政策 description，expected_status 明示 `policy_description_fallback; raw_prefix_missing`。兩者均無前綴時 expected 留空，標記 `prefix_missing`。原始前綴存在時標記 `raw_description`。不採信輸入的獨立 expected 欄。snapshot 附加 expected／expected_status，不覆寫 description、result、command 或任何真實觀察。報表重新解析 description；本地政策補充值不是掃描時的政策證據。

R2／R3 真實 fixture 未改動，其歷史 description 無此前綴，故 53 筆觀察均使用明示的本地政策補充。合成 tests/fixtures/snapshot.json 保留 synthetic=true、SYNTHETIC／test-only 標示並同步政策 hash。CSV／HTML 原本已有 expected 欄，本次將其改為 description 解析結果並加入 expected_status。

驗證：`python3 -m unittest discover -s tests -v`（49 tests 全過）；`python3 -m linuxgcb build`、`python3 -m linuxgcb validate` 通過。R3 snapshot → report 的 CSV 314 列中，53 條 raw 觀察 expected 全非空。比對 HEAD 三份政策，除了 check.description，其餘內容完全相同（含 rules、condition、requirements、policy name）；原 Q1 後綴逐字相同。

可重現 R3 驗收：

```bash
python3 -m linuxgcb snapshot tests/fixtures/realhost_r3.json --out out/exp1-r3/snapshot.json
python3 -m linuxgcb report out/exp1-r3/snapshot.json --out out/exp1-r3/report --now 2026-10-31T23:00:00Z
```
