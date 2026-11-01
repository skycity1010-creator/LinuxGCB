# LinuxGCB 例外登記

| ID | 條目 | 狀態 | 理由 | Approver | 到期 | 工單 |
|---|---|---|---|---|---|---|
| TWGCB-01-012-0187 | 未受限程序（.61 / agent010） | FAIL（Commander 裁定維持 FAIL，不矯正系統設定） | Wazuh agent 5 程序執行於 unconfined_service_t；RHEL9 無 Wazuh 官方 SELinux policy，chcon 檔案標籤不改變 systemd 服務域（實測無效已復原）。Commander 2026-11-01 裁定：依現在檢核方式，不修改規則、不矯正系統，呈現 FAIL | Commander（2026-11-01 於 Discord thread） | — | — |
| TWGCB-01-012-0229 | sudo 執行需鑑別（.61 / agent010） | FAIL（Commander 裁定維持 FAIL，不矯正系統設定） | .61 sudoers 有 %wheel NOPASSWD: ALL（自動化 sudo -n 依賴）；GCB 要求移除。Commander 2026-11-01 裁定：依現在檢核方式，不修改規則、不矯正系統，呈現 FAIL | Commander（2026-11-01 於 Discord thread） | — | — |

備註：依治理原則，例外不將原 FAIL 改 PASS；儀表板/報表須另列 exception 旗標。0187/0229 為「已裁定的真實缺失（accepted finding）」，非豁免——掃描結果維持 FAIL。
