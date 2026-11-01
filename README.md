# LinuxGCB — RHEL9 政府組態基準（GCB v1.2）Wazuh SCA 候選政策

**狀態：VERIFIED**（2026-11-01 真機驗收與人工複審完成）
**涵蓋：307/307 條目全數實作**（母體 314 條，Nftables 7 條不在範圍）

本專案將「TWGCB-01-012 Red Hat Enterprise Linux 9 政府組態基準 v1.2」轉為
[Wazuh](https://wazuh.com/) SCA（Security Configuration Assessment）政策，
並在 RHEL 9 真機（agent010）以 29 輪引擎掃描完成正/負向實證。

## 最終結果（R29，2026-11-01）

| 政策 | 條目 | PASS | FAIL | Score |
|---|---|---|---|---|
| `linuxgcb_base.yml` | 270 | 128 | 142 | 47 |
| `linuxgcb_sshd.yml` | 32 | 32 | 0 | 100 |
| `linuxgcb_firewalld.yml` | 5 | 5 | 0 | 100 |
| **合計** | **307** | **165** | **142** | — |

- 142 條 FAIL 均為受測主機**真實缺失**（逐條真機對帳確認，非規則假阴性）。
- 其中 2 條（0187 SELinux、0229 sudoers NOPASSWD）為 **accepted finding**：
  管理師裁定維持 FAIL、不矯正系統設定（見 `docs/EXCEPTIONS.md`）。
- 4 條（108/141/269/270）coverage partial：檢查範圍僅涵蓋來源部分語意，報表列 MANUAL_PENDING。

## 快速開始

```bash
# 需求：Python 3（stdlib only）；來源基準文件（.docx/.xlsx）需放置於 repo 根目錄
python3 -m linuxgcb build      # 重建 scope registry 與三份候選政策
python3 -m linuxgcb validate   # 離線結構與來源對帳（307 候選）
python3 scripts/entry_list_html.py   # 重新產生條目清單 HTML
python3 -m unittest discover -s tests  # 137 項離線測試
```

## 條目清單（HTML）

`reports/entry_list_20261101.html` — **由原始 Excel/Word 基準檔產生**，315 條基準原文
（項次、類別、名稱、說明、設定方法、GCB 設定值；不含實機檢核結果）：
- 置頂搜尋框（捲動時固定）：輸入條目 ID（`0187`、`TWGCB-01-012-0187`）自動跳轉並高亮；類別下拉與關鍵字過濾
- ⚠ 原始檔不一致偵測：Excel 列表缺 0180（僅見於 Word），已補入並旗標，見 `docs/SOURCE_DISCREPANCY_0180.md`
- 含實機 R29 結果的備用清單：`scripts/entry_list_scan_html.py` → `reports/entry_list_scan_20261101.html`

## 部署到 Wazuh Manager

```bash
# 政策安裝（Manager 端）
sudo install -o wazuh -g wazuh -m 644 policies/linuxgcb_*.yml /var/ossec/etc/shared/linuxgcb/
# agent.conf 掛 3 政策後，觸發掃描：PUT /agents/restart?agents_list=<agent_id>
```

Wazuh 4.14 無 on-demand SCA scan API，以 agent restart 觸發掃描。

## 目錄結構

```
linuxgcb/            產生器與規則源碼（政策 yml 是 build 產物，規則源碼在 *_runtime.py）
policies/            三份候選政策（base 270 / sshd 32 / firewalld 5）
templates/           合規範本（gcb-gpgcheck.repo，供雙向驗證）
tests/               137 項離線測試（逐 check 釘選 rules 欄位）
data/                controls.json（314 條來源解析）、scope_registry、coverage_manifest、
                     realhost_scan_*_r{2..29}.json（29 輪真機掃描結果）
docs/                驗收報告鏈（REALHOST_ACCEPTANCE_*）、Commander 裁定、例外登記、最終結算
reports/             HTML/CSV 報表、snapshot、entry_list HTML
scripts/             entry_list_html.py（清單產生器）
archive/             早期廢棄工作區殘留
```

## 驗證方法學（摘要）

1. **規則源碼 → build → 政策 yml**：規則以 `inspect.getsource` 嵌入，yml 不可手改。
2. **真機對帳**：以 w_strtok→argv 直接執行規則命令（忠於引擎），不可包 `sh -c`。
3. **正向 fixture 雙向驗證**：先備份 → 套合規 fixture → 掃描轉 PASS → 完整還原 → 掃描回 FAIL，
   同時證明正/負路徑與還原乾淨（R9/R10、R12、R24/R25）。
4. **逐 check 翻轉集合比對**：每批 FIX 部署後，翻轉集合必須恰好等於目標 ID（零 side-effect）。
5. **釘選測試**：各批次測試逐 check 釘選 `rules` 欄位；改規則需同步 allow-set。

完整歷程見 `docs/FINAL_SETTLEMENT_20261101.md` 與 `docs/REALHOST_ACCEPTANCE_*.md`。

## 治理欄位

每條目含治理中繼資料（`data/scope_registry.json`）：
`offline_review`、`execution_review`、`coverage`、`source_approval`、
`live_validation=VALIDATED`、`verified_on=2026-11-01`、`verified_by=Commander`。

## 授權與來源

基準條目解析自 `TWGCB-01-012 Red Hat Enterprise Linux 9 政府組態基準說明文件(伺服器) v1.2`
（TWGCB 電子政府組態基準）。本 repo 之政策、規則源碼、測試與報告為本專案產出；
來源基準文件之權利屬其發布機關。批次開發歷史見 `docs/README_BATCH_HISTORY.md`。
