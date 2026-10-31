# FIX-1 服務未安裝假陰性修正

日期：2026-10-31；分支：`codex/linuxgcb-fix1`。基線：`0727a3987424e934df1db29f436481e7c5cfd928`。

依本次 R1 任務證據修正 6 個既有 check；僅離線開發，沒有 SSH、API、sudo、服務變更、開發機掃描或執行 Excel/DOCX 修復命令。所有 fixture 都是 **SYNTHETIC TEST ONLY**，不代表真機驗收。原 XLSX/DOCX、TWGCB ID、314 = 307 候選 + 7 排除、53 個候選 check 保持不變。

## 判定與 SCA 語意

每個 unit 仍採 `condition: all`，三條規則全部必要：

1. LoadState 為 loaded、masked 或明確 not-found。
2. ActiveState 為 inactive。
3. 同一次 `systemctl show --property=LoadState --property=UnitFileState` 輸出中，至少一行是 `LoadState=not-found` 或 `UnitFileState=disabled|masked`。

第 3 條的 OR 位於單一正向 regex 裡，使用 SCA「輸出任一行匹配」語意；不是把 check 改成 any。依據為儲存庫既有 `docs/references/creating-custom-policies.md` 的 Condition、Content checks、Rule syntax for commands；本次沒有瀏覽外網。模擬器既有 all 與逐 LF 行匹配維持不變，新增固定 alternation 模式由 supported_patterns 取自 definitions；補充 simulate 說明與 FIX-1 狀態矩陣。未引入 `not` 或 `!r:`，避免錯誤訊息、空輸出被反向當成合格。

not-found 的 UnitFileState 常為空值或省略，所以不能只擴大 LoadState regex，還要求 UnitFileState=disabled。這裡以明確 LoadState 行接受不存在；空輸出、stderr 的 No such unit 都不足以 PASS。已安裝 disabled+inactive、masked+inactive 為 PASS；enabled+inactive、disabled+active、enabled+active 為 FAIL。static、alias、indirect、runtime、failed、暫態及未知狀態維持保守 FAIL，沒有擴大為自動核准。

Samba 同一個 check 同時要求 smb 與 nmb 各自三條規則通過，沒有新增條目。auditd／rsyslog／firewalld 仍要求 loaded+enabled+active；其餘 47 個 emitted checks 與基線逐物件相等。cron 權限 0192/0194/0196/0198/0200/0202 與 SSH 0269 完全未修改。

## 逐條 before / after 摘要與預期 R1 結果

以下 suffix 均為 TWGCB-01-012-；SCA ID 為 900000 + suffix。這是**下一輪真機重掃的預期**，不是本次已觀察 PASS。

| Check ID | Before | After | 預期真機結果 |
| --- | --- | --- | --- |
| 0030 / 900030 | autofs loaded+inactive+disabled | not-found 或 disabled/masked，且 inactive | 未安裝 → PASS |
| 0094 / 900094 | rsyncd masked+inactive+masked | not-found 或 disabled/masked，且 inactive | 未安裝或 disabled+inactive → PASS |
| 0097 / 900097 | squid masked+inactive+masked | not-found 或 disabled/masked，且 inactive | 未安裝或 disabled+inactive → PASS |
| 0098 / 900098 | 僅 smb masked+inactive+masked | smb、nmb 各自 not-found 或 disabled/masked，且 inactive | 兩者未安裝或 disabled+inactive → PASS；任一 enabled/active → FAIL |
| 0101 / 900101 | kdump loaded+active+enabled | not-found 或 disabled/masked，且 inactive | 依本次證據的未安裝或 disabled+inactive → PASS |
| 0245 / 900245 | nftables masked+inactive+masked | not-found 或 disabled/masked，且 inactive | R1 disabled+inactive → PASS，無需 masked |

**0101 kdump 特別說明：**原始 XLSX/DOCX 與 registry.expected 仍是「啟用」，原政策也要求 enabled+active；其失敗並不只是 LoadState 過嚴。本次依使用者明確將 0101 納入「不存在或停用皆合格」的 FIX-1 要求改動實作，enabled/active 會改判 FAIL。保留來源原文，不把任務意圖覆寫為來源事實；此差異已記在 coverage_manifest 的 caveats，下一輪必須確認 kdump 適用性與意圖，才可談驗證核准。

## 完整逐條 rules

### TWGCB-01-012-0030 autofs服務 / 900030

Before (`condition: all`)：

```text
c:/usr/bin/systemctl show autofs.service --property=LoadState -> r:^LoadState=loaded$
c:/usr/bin/systemctl show autofs.service --property=ActiveState -> r:^ActiveState=inactive$
c:/usr/bin/systemctl show autofs.service --property=UnitFileState -> r:^UnitFileState=disabled$
```

After (`condition: all`)：

```text
c:/usr/bin/systemctl show autofs.service --property=LoadState -> r:^LoadState=(loaded|masked|not-found)$
c:/usr/bin/systemctl show autofs.service --property=ActiveState -> r:^ActiveState=inactive$
c:/usr/bin/systemctl show autofs.service --property=LoadState --property=UnitFileState -> r:^(LoadState=not-found|UnitFileState=(disabled|masked))$
```

### TWGCB-01-012-0094 rsyncd服務 / 900094

Before (`condition: all`)：

```text
c:/usr/bin/systemctl show rsyncd.service --property=LoadState -> r:^LoadState=masked$
c:/usr/bin/systemctl show rsyncd.service --property=ActiveState -> r:^ActiveState=inactive$
c:/usr/bin/systemctl show rsyncd.service --property=UnitFileState -> r:^UnitFileState=masked$
```

After (`condition: all`)：

```text
c:/usr/bin/systemctl show rsyncd.service --property=LoadState -> r:^LoadState=(loaded|masked|not-found)$
c:/usr/bin/systemctl show rsyncd.service --property=ActiveState -> r:^ActiveState=inactive$
c:/usr/bin/systemctl show rsyncd.service --property=LoadState --property=UnitFileState -> r:^(LoadState=not-found|UnitFileState=(disabled|masked))$
```

### TWGCB-01-012-0097 Squid服務 / 900097

Before (`condition: all`)：

```text
c:/usr/bin/systemctl show squid.service --property=LoadState -> r:^LoadState=masked$
c:/usr/bin/systemctl show squid.service --property=ActiveState -> r:^ActiveState=inactive$
c:/usr/bin/systemctl show squid.service --property=UnitFileState -> r:^UnitFileState=masked$
```

After (`condition: all`)：

```text
c:/usr/bin/systemctl show squid.service --property=LoadState -> r:^LoadState=(loaded|masked|not-found)$
c:/usr/bin/systemctl show squid.service --property=ActiveState -> r:^ActiveState=inactive$
c:/usr/bin/systemctl show squid.service --property=LoadState --property=UnitFileState -> r:^(LoadState=not-found|UnitFileState=(disabled|masked))$
```

### TWGCB-01-012-0098 Samba服務 / 900098

Before (`condition: all`)：

```text
c:/usr/bin/systemctl show smb.service --property=LoadState -> r:^LoadState=masked$
c:/usr/bin/systemctl show smb.service --property=ActiveState -> r:^ActiveState=inactive$
c:/usr/bin/systemctl show smb.service --property=UnitFileState -> r:^UnitFileState=masked$
```

After (`condition: all`)：

```text
c:/usr/bin/systemctl show smb.service --property=LoadState -> r:^LoadState=(loaded|masked|not-found)$
c:/usr/bin/systemctl show smb.service --property=ActiveState -> r:^ActiveState=inactive$
c:/usr/bin/systemctl show smb.service --property=LoadState --property=UnitFileState -> r:^(LoadState=not-found|UnitFileState=(disabled|masked))$
c:/usr/bin/systemctl show nmb.service --property=LoadState -> r:^LoadState=(loaded|masked|not-found)$
c:/usr/bin/systemctl show nmb.service --property=ActiveState -> r:^ActiveState=inactive$
c:/usr/bin/systemctl show nmb.service --property=LoadState --property=UnitFileState -> r:^(LoadState=not-found|UnitFileState=(disabled|masked))$
```

### TWGCB-01-012-0101 kdump服務 / 900101

Before (`condition: all`)：

```text
c:/usr/bin/systemctl show kdump.service --property=LoadState -> r:^LoadState=loaded$
c:/usr/bin/systemctl show kdump.service --property=ActiveState -> r:^ActiveState=active$
c:/usr/bin/systemctl show kdump.service --property=UnitFileState -> r:^UnitFileState=enabled$
```

After (`condition: all`)：

```text
c:/usr/bin/systemctl show kdump.service --property=LoadState -> r:^LoadState=(loaded|masked|not-found)$
c:/usr/bin/systemctl show kdump.service --property=ActiveState -> r:^ActiveState=inactive$
c:/usr/bin/systemctl show kdump.service --property=LoadState --property=UnitFileState -> r:^(LoadState=not-found|UnitFileState=(disabled|masked))$
```

### TWGCB-01-012-0245 nftables服務 / 900245

Before (`condition: all`)：

```text
c:/usr/bin/systemctl show nftables.service --property=LoadState -> r:^LoadState=masked$
c:/usr/bin/systemctl show nftables.service --property=ActiveState -> r:^ActiveState=inactive$
c:/usr/bin/systemctl show nftables.service --property=UnitFileState -> r:^UnitFileState=masked$
```

After (`condition: all`)：

```text
c:/usr/bin/systemctl show nftables.service --property=LoadState -> r:^LoadState=(loaded|masked|not-found)$
c:/usr/bin/systemctl show nftables.service --property=ActiveState -> r:^ActiveState=inactive$
c:/usr/bin/systemctl show nftables.service --property=LoadState --property=UnitFileState -> r:^(LoadState=not-found|UnitFileState=(disabled|masked))$
```

## 離線驗證與邊界

實際執行輸出見 [FIX1_TEST_OUTPUT.txt](FIX1_TEST_OUTPUT.txt)。

```text
python3 -m linuxgcb build
314 項；307 候選／7 排除；53 項候選規則，UNVALIDATED／人工審查待完成
python3 -m linuxgcb validate
UNVALIDATED：離線結構檢查通過，候選控制項數 53
python3 -m unittest discover -s tests -v
Ran 42 tests
OK
```

新增 4 個測試方法，涵蓋 6 ID／7 units 的 not-found、enabled、disabled、masked、active、未知狀態、錯誤與空輸出，以及必要服務不得接受未安裝。已安裝狀態矩陣為 7 × 4 LoadState × 9 UnitFileState × 5 ActiveState = 1260 組；另測未安裝且空值／省略 UnitFileState、Samba 任一成員不合格不能被另一個 PASS 掩蓋。既有 53 項正反案例、來源 hash、scope、報表保守治理與 metadata 測試全數通過。snapshot 僅同步政策 hashes，未修改任何觀察或掃描結果。初次全測因 snapshot 尚持有舊政策 hashes 出現 11 errors；同步合成 snapshot 的 hashes 後全數通過，未放寬 hash 驗證。

`git diff --check` 通過。原始來源 SHA256 與既有常數相等：

- XLSX：`7d752b639a1e780df08814c6252efadd3ea2711eaa5c9d91c070b84a296c0247`
- DOCX：`986effd9501b1fd97776129c6691cf8fc98246bd04514347322f3337508e0e5b`

所有政策與 registry.live_validation 維持 **UNVALIDATED**；coverage／execution 的 Q1 gates 不解除，raw PASS 不升格為 verified compliance。歷史 QUALITY_REVIEW_Q1.md 敘述保留為當時基線，本文件記錄 FIX-1 差異。多次 systemctl 查詢仍非原子，socket/alias 啟動路徑、目標 Wazuh PCRE2／argv／stderr／timeout／非零退出碼處理仍待真機驗證。合成 stdout 匹配模型不保證引擎對執行錯誤的行為；下一輪須核對 6 項與必要服務的實際結果。

## 修改檔案

- `linuxgcb/batch1.py`：共用停用服務原生命令規則、Samba 雙 unit 與 caveats。
- `linuxgcb/policy.py`：0245 使用共用規則、補充離線模擬器契約。
- `policies/linuxgcb_base.yml`、`policies/linuxgcb_firewalld.yml`：僅 6 項 emitted checks 改變。
- `data/coverage_manifest.json`、`data/policy_hashes.json`：重建說明與政策 hashes。
- `tests/fixtures/rule_outputs.json`：6 項合成正反及 not-found 案例。
- `tests/fixtures/snapshot.json`：僅更新合成政策 hashes。
- `tests/test_fix1.py`：新增狀態矩陣與必要服務回歸。
- `tests/test_catalog_policy.py`、`tests/test_quality_q1.py`：更新舊的「不存在一律 FAIL」測試契約；啟用組原有矩陣保留。
- `docs/FIX1_REVIEW.md`、`docs/FIX1_TEST_OUTPUT.txt`：審查與測試輸出。

工作目錄原有未追蹤 `codex_fix1.log` 未修改、未納入提交。

## 提交狀態

目前分支已是 `codex/linuxgcb-fix1`。已嘗試 git add 與 git commit，但環境將 `.git` 設為唯讀，兩者皆回報 `fatal: Unable to create .../.git/index.lock: Read-only file system`，所以本次無法建立 commit。未繞過權限或變更 `.git`；修改保留於工作目錄。可寫入 Git 的環境可用上列 13 個檔案明確暫存後提交，勿納入原有 `codex_fix1.log`。建議訊息：`fix: accept absent or disabled services for FIX-1 checks`。
