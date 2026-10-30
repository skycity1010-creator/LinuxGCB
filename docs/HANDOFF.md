# 第一版離線交接紀錄

工作目錄為 `/home/skycity1010/projects/LinuxGCB-codex-p0p1`，分支 `codex/linuxgcb-p0p1`。未提交 commit；新增檔案保持可檢視、未追蹤狀態。沒有修改父專案、原始 XLSX/DOCX、既有 data/controls.json 或 inventory.json。沒有連線、掃描開發機、讀取秘密、安裝依賴、部署或服務變更。

## 新增檔案

- `.gitignore`、`README.md`、`NEXT_STEPS.md`。
- `data/scope_registry.json`、`data/policy_hashes.json`。
- `linuxgcb/__init__.py`、`__main__.py`、`catalog.py`、`policy.py`、`collector.py`、`report.py`。
- `policies/linuxgcb_base.yml`、`linuxgcb_firewalld.yml`、`linuxgcb_sshd.yml`。
- `tests/test_catalog_policy.py`、`test_collector.py`、`test_report.py`。
- `tests/fixtures/rule_outputs.json`、`snapshot.json`（皆 SYNTHETIC TEST ONLY）。
- `templates/agent.conf.example`、`index-mapping.json`。
- `docs/POLICIES.md`、`DATA_CONTRACT.md`、`DEPLOYMENT.md`、本交接紀錄。

## 確認結果

314 個唯一來源 ID、314 個唯一數字 SCA-ID、307 候選／7 排除。270 基本 + 5 Firewalld + 32 SSH。0180 不補造；0245 保留。數字範圍提案 900000–900999，實際撞號待查；全部 314 項 human_review_pending。

七項候選實作為 TWGCB-01-012-0045、0046、0108、0243、0245、0269、0270。0108、0269、0270 是局部檢核，raw passed 仍保留 MANUAL_PENDING；其餘 300 候選項未實作。全部政策 UNVALIDATED。

XLSX SHA256：`7d752b639a1e780df08814c6252efadd3ea2711eaa5c9d91c070b84a296c0247`。

DOCX SHA256：`986effd9501b1fd97776129c6691cf8fc98246bd04514347322f3337508e0e5b`。

2026-10-30 最終執行紀錄；下列命令均以 subprocess 分別檢查 returncode：

| 命令 | 結果 |
| --- | --- |
| `python3 -m linuxgcb build` | exit 0，314／307／7 |
| `python3 -m linuxgcb validate` | exit 0，7 項候選規則結構通過 |
| `python3 -m unittest discover -s tests -v` | exit 0，22 tests，OK |
| `python3 -m linuxgcb report tests/fixtures/snapshot.json --out out/synthetic --now 2026-10-30T00:00:00Z` | exit 0，完整 SYNTHETIC 報表 |
| `git diff --check` | exit 0（既有受追蹤檔案無差異；新增檔案由目錄直接檢視） |

SYNTHETIC 產物為 `out/synthetic/report.html`、`report.csv`、`summary.json`、`snapshot.json`，已由 .gitignore 排除。314 列：PASS 2、FAIL 1、ERROR 1、MANUAL_PENDING 303、EXCLUDED 7；適用分母 307、unresolved 0。通過率 66.67%、達成率 0.65%、完整率 0.98%；這些只描述測試資料，不是環境符合性指標。

## 限制與待決

完整限制見 README、POLICIES 與 DATA_CONTRACT。沒有 live API transport 或多政策自動轉接；現有 collector 只接受注入 transport，嚴格拒絕不完整快照。Python 固定輸出模擬不等於 Wazuh／PCRE2 引擎驗收。來源分類並非核准語意審查，未宣稱完整符合性或真機驗證。

阻擋正式部署的主要事項是實際 RHEL/Wazuh 版本與試點、ID 撞號、API schema/hash/時間欄位與一致性、sysctl 持久設定、SSH 情境矩陣、真實錯誤／N/A 聚合及核准角色名單。所有 RHEL9 integration gates 列於 DEPLOYMENT.md，皆未勾選；Hermes 獨立重跑及審查後再決定整合。
