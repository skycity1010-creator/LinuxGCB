# LinuxGCB Commander 裁定記錄（2026-11-01，Discord thread 1565973371861336065）

Commander 對全部待確認條目之裁定：

| 條目 | 裁定 | 處置 |
|---|---|---|
| 0020-0022、0026-0028 | 系統中沒有這種檔案系統時，算通過 | 現行 REVIEW→passed 語意採認，規則不動 |
| 0023-0025 | LV 的分割區也視為獨立檔案系統 | FIX-9：home 所在掛載點（含 LV、最長前綴）視為獨立 FS → .61 的 /home LV 無 nodev/nosuid/noexec → 將轉 FAIL（真實缺失） |
| 0032 | 產生一個範本檔案，做成功/失敗的驗證 | FIX-10：無 section 之 repo 檔（如未註冊之 redhat.repo）視為不適用跳過；另建合規範本 repo 檔，真機做 PASS/FAIL 雙向驗證 |
| 0038 | EFI 需在 fstab 加 uid=0,gid=0 才算通過 | 現行規則已如此要求，維持 FAIL（.61 用 umask=0077 無 uid/gid 欄） |
| 0073/0074 | 同意建議（展開 $HOME 後判定） | FIX-9：$HOME→/root、$PATH→RHEL9 預設展開後逐元素判定 |
| 0091 | 沒有 shadow 群組視為通過 | FIX-9：/etc/group 無 shadow → PASS |
| 0123 | 依建議（維持 FAIL） | 規則不動；修復＝寫一行 sysctl 設定檔 |
| 0246 | 依建議（public 可接受） | 已 PASS，追認完成 |
| 0143/0144 | 依文件內容檢查，不存在視為通過，不檢查替代版本工具 | FIX-4 語意採認（跳過不存在工具、只查來源清單） |
| 0176 | 依現在檢核方式，不用修改 | FIX-4 語意採認（只認 omfile action 行） |
| 0187 | 依現在檢核方式，不矯正系統設定，呈現 FAIL | 見 EXCEPTIONS.md（accepted finding） |
| 0229 | 依現在檢核方式，不矯正系統設定，呈現 FAIL | 見 EXCEPTIONS.md（accepted finding） |
| 其他 | 依建議進行 | 0020-0028 報表標 N/A 語意、FIX-4 追認等 |

## 影響
- FIX-9（6 條規則）：0023-0025、0073、0074、0091
- FIX-10（1 條規則 + 範本檔）：0032
- 0187/0229：規則與系統都不動，報表列 accepted finding
- 0038/0123：維持 FAIL，屬可修復之真實缺失
