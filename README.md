# LinuxGCB P2 batch 1 離線候選版

本分支僅在隔離副本進行離線開發。政策全部 **UNVALIDATED**，未連線、未安裝 Agent、未掃描此開發機、未部署或重啟服務。SYNTHETIC 資料只供測試，不是真實掃描證據；本版不宣稱完整符合性。

使用 Python 3.10+ 標準函式庫，無安裝步驟、無外部依賴。請在本專案根目錄執行：

```bash
python3 -m linuxgcb build
python3 -m linuxgcb validate
python3 -m unittest discover -s tests -v
python3 -m linuxgcb report tests/fixtures/snapshot.json --out out/synthetic --now 2026-10-30T00:00:00Z
```

`build` 先核對原始 XLSX/DOCX hash，再重建可追溯 registry、53 項候選控制及逐項涵蓋 manifest及政策 hash；不重寫原始 controls.json。`validate` 僅驗證本版 JSON 格式 YAML 子集的結構與規則，不等於 Wazuh YAML 載入或 PCRE2 引擎驗收。CLI 不會執行政策內的任何命令。

報表輸出 `report.html`、`report.csv`、`summary.json`、原始匯入副本 `snapshot.json`。`out/` 已忽略，不進 git。正式資料不得使用測試時間；省略 `--now` 時採目前 UTC。報表目錄內同名檔案會覆寫，請為各次匯入指定不同目錄。

交付內容：

- `data/scope_registry.json`：314 個 ID 的來源 sheet/row、類別、原始期望、307/7 範圍與分類提案；全部 human_review_pending。
- `policies/`：base、firewalld、sshd 三份候選 SCA。實作 53 項（原有 7 項加本批 46 項），逐項清單見 [BATCH1_REVIEW](docs/BATCH1_REVIEW.md)；補充限制見[政策說明](docs/POLICIES.md)。其餘 254 個候選控制項未實作，明列 pending；7 個 Nftables 條目 excluded。
- `linuxgcb/`：可執行 CLI、完整母體治理報表、可注入 transport 的 Manager 分頁 collector。無 live transport、憑證讀取或網路連線。
- `tests/fixtures/`：具名 SYNTHETIC 快照及每項規則的正向／負向／缺資料／執行錯誤輸出。
- `templates/`、[部署與驗收](docs/DEPLOYMENT.md)、[資料與儀表板契約](docs/DATA_CONTRACT.md)：僅範本與設計，不是已部署 Dashboard。

計分以主機 × GCB 條目為單位。排除與有效核准不適用不進適用分母；未決適用性保守留在分母，另計 unresolved。通過率 = PASS/(PASS+FAIL)；達成率 = PASS/適用項；完整率 = (PASS+FAIL)/適用項。零分母為 JSON null／HTML None（N/A）。原生 Wazuh score 保留於原始快照，不混同治理分數。未完成補充檢核的 0108、0141、0269、0270 即使 raw passed 也列 MANUAL_PENDING；raw failed 仍列 FAIL。核准例外不更改 FAIL，過期例外不生效。stale 為獨立旗標，不能當成新掃描或新的通過證據。

測試涵蓋來源完整性、固定 ID、53 項規則輸出案例、所有 0000–7777 權限組合、分頁失配／部分失敗／摘要變更／冪等／過期、完整母體、分母、例外及 HTML/CSV 注入。模擬以 Python regex 逐行搜尋固定輸出，遵循官方 all 的 FAIL 優先及明確 N/A 案例；退出碼不決定成敗，未取得可靠輸出列 UNRESOLVED。不模擬 Wazuh 程序執行、PCRE2、timeout 與權限行為，因此不能取代 RHEL9 真機驗收。未提供 XLSX、PDF、live API、全量政策、端點 helper、寫入索引或排程。

有效依據是 `PLAN.md` 與 `docs/references/creating-custom-policies.md`、`how-it-works.md`、`how-to-configure.md`、`internal-options.md` 的既有離線快照；`sca-custom-policies.md` 為已知 soft404，未用作證據。未存取外部網站。來源 XLSX/DOCX 與既有 raw controls/inventory 均保留。

下一階段與未決事項見 [NEXT_STEPS.md](NEXT_STEPS.md)。Hermes 負責獨立重跑、審查、整合及外部溝通；本次未提交 commit。

本批統計：49 項完整語意候選／4 項部分候選，全部 live-unvalidated、execution_review pending、human_review_pending；「完整」只指明列來源要求已有候選規則，不代表已完成人工核准或真機符合。機器可讀對帳見 `data/coverage_manifest.json`。報表 SYNTHETIC 快照仍只有原有 7 筆觀察，新增規則不產生 PASS 或提高結果完整率。
