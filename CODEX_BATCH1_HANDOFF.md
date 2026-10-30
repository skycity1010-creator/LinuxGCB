已完成離線批次，保留可審查 diff，未 commit。

- 候選控制 **7 → 53（新增 46）**；49 full、4 partial（0108、0141、0269、0270）。剩餘 254 未實作；維持 **307 候選＋7 排除＝314**。
- 新增 ID（共同前綴 `TWGCB-01-012-`）：0030、0033、0047–0060、0094、0097、0098、0101、0132、0133、0141、0142、0174、0175、0178、0179、0183、0191–0202、0242、0256、0257、0301、0302。
- 修正退出碼、逐行匹配與 all/N/A 模擬語意；新增來源對照、fixtures、機器可讀 manifest，重建三份政策與 registry。
- 指定 build、validate、unittest、report、diff 檢查均通過；**27 tests OK**。Synthetic 報表完整率仍為 **0.98%**，未因新增規則增加。
- XLSX／DOCX hash 核對通過；原始 controls、inventory、來源文件與歷史 handoff 未變動。

逐項期望、限制、測試、變更檔案及後續建議見 [BATCH1_REVIEW.md](/home/skycity1010/projects/LinuxGCB-codex-p2-batch1/docs/BATCH1_REVIEW.md)。

全部仍為 **UNVALIDATED／人工審查待辦**；命令錯誤辨識、語系及真正 Wazuh/RHEL9 行為保留實機 gates。交由 Hermes 獨立審查與重測後決定整合。