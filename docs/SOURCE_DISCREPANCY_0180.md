# 來源差異：TWGCB-01-012-0180（Excel 列表缺漏）

發現日期：2026-11-01（產生原始條目清單 HTML 時）

## 事實
- **Word 說明文件**（TWGCB-01-012_...v1.2_1140612.docx）含 **315** 個唯一 TWGCB ID。
- **Excel 列表**（政府組態基準列表.xlsx，4 工作表）含 **314** 個 ID：
  基本項目表從 0179 直接跳到 0181，**缺 0180**。
- 專案母體（controls.json／scope_registry 314 條）解析自 Excel，因此
  **0180 不在已實作的 307 條範圍內**。

## 0180 條目內容（取自 Word）
- 名稱：設定journald將日誌發送到rsyslog
- 類別：日誌與稽核
- GCB 設定值：`yes`
- 設定方法：編輯 `/etc/systemd/journald.conf`，新增 `ForwardToSyslog=yes`

## 影響
- 若補入，母體應為 315、scope 308（0180 非 Nftables 類）。
- 現有掃描結果（R29 165P/142F）不含 0180。
- 注意：`.61` 現行 journald 未明確設定 ForwardToSyslog（P2B3 期間已對帳過
  journald 預設值語意），補入後預期為 FAIL（真實缺失）或依來源語意待批。

## 待 Commander 決策
1. 是否以 Word 為準補入 0180（母體 315、候選 308），開一批實作＋真機驗證。
2. 或確認 Excel 列表為权威版本、0180 屬基準文件自身不一致，記錄不處理。

## 處置現況
- `scripts/entry_list_html.py` 已改為直接解析 Excel＋Word 原始檔，
  清單為 315 條，0180 以琥珀色旗標標示「Excel 列表缺漏：僅見於 Word 說明文件」。
- 政策與掃描鏈（307 條）未變動。
