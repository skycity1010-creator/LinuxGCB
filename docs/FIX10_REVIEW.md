# FIX-10 Commander 裁定對照（2026-11-01）

基準 commit：`12851d61d23b8a7bbf413e01dd6db0abc5c420aa`。
Commander：「0032 產生一個範本檔案，做成功/失敗的驗證」。

| 對象 | 修改前 | 修改後 |
| --- | --- | --- |
| 900032，repo 無 section | `not seen` 判 FAIL | 跳過整個檔案，vacuously compliant；與 0244/0091 無對象裁定同族 |
| repo 有 section | 每個 section 均需兩 key =1 | 維持嚴格判定，停用 section 也需符合 |
| yum.conf / dnf.conf | main 均需 gpgcheck=1、localpkg_gpgcheck=1 | 不變，缺檔、缺 main、缺 key 或讀取錯誤不輸出 PASS |

依任務提供的真機證據：yum.conf 是 dnf.conf 的 symlink，main 有 gpgcheck=1，缺 localpkg_gpgcheck；redhat.repo 為 358 bytes 純註解、零 section。修正後仍應 FAIL，原因是 main 真實缺失；零 section repo 不再造成額外失敗。此證據為使用者提供，本次沒有連線重驗。

僅 900032 rules 改變，其餘 306 條 rules 位元組相同；metadata、來源、TWGCB ID、307 候選／7 排除、coverage_manifest 與 UNVALIDATED 不變。共用 runtime 對其他 ID 還原原內嵌內容。命令維持 w_strtok 雙引號 argv、唯讀、單一 PASS 輸出，命令內不含箭頭分隔符。同步更新政策 hash。歷史範圍測試僅在累計差異集合加入 0032；既有 fixtures、證據檔不變。

## 真機雙向驗證程序（供核准操作者後續執行）

本次只離線開發及合成測試，以下操作未執行。`templates/gcb-gpgcheck.repo` 是 repo 內範本，沒有自動部署機制；enabled=0，無套件來源，無須安裝套件、重啟服務或呼叫 subscription-manager。

1. 記錄原始 900032 結果與時間。唯讀確認 yum.conf/dnf.conf 的 symlink 與實體目標、main 內容及 repo 清單；應符合上述缺失並得到 FAIL。保存原檔位元組、連結目標與權限供還原；備份存於 repo 掃描目錄以外，避免被當作檢查輸入。
2. 確認 `/etc/yum.repos.d/gcb-gpgcheck.repo` 不存在，若已存在則先保存其內容與 metadata。人工將範本放入該路徑。它含一個合規 section，但 main 仍缺 key，此時檢查仍應 FAIL，可隔離 main 原因。
3. 在 yum.conf/dnf.conf 實際指向的檔案之 `[main]` 補齊兩 key，均為 1；若共享目標只編輯一次，保留原 symlink。避免留下衝突的重複設定。其餘有 section 的 repo 也必須原已合規；若有其他缺失先記錄，不將意外 FAIL 宣稱成功。
4. 只執行新政策中 900032 的唯讀檢查，記錄政策 hash、時間與結果：預期 PASS。範本本身不足以修復 main；本步需同時滿足兩者。
5. 還原 main 實體檔原始內容、權限及原 symlink；移除本次新增範本（若原已存在則還原原檔），確認其他 repo 未改。再執行同一版本 900032，預期 FAIL，因 main 回到缺 localpkg_gpgcheck 的原狀。保存前後結果；操作中斷也應完成還原。

## 離線驗證

新增回歸透過 w_strtok 解析實際內嵌命令，僅替換 ROOT 到合成暫存樹，涵蓋純註解／無 section repo 跳過、有 section 缺任一 key 或值為 0 失敗、main 缺 key 失敗、yum symlink、範本套用加 main 修補 PASS 與 restore FAIL，並比對全部 307 條及保護檔案。

驗收結果：`python3 -m unittest discover -s tests -v` 共 137 tests 全過（16.514 秒）；`python3 -m linuxgcb validate` 通過，307 候選仍為 UNVALIDATED；`git diff --check` 通過。相對基準逐條比對：僅 900032 rules 改變、其餘 306 條 rules 零差異，全部 check metadata 不變。

環境權限明列 `.git` 唯讀，故未建立 commit，保留工作目錄變更。原有未追蹤 `codex_fix10.log` 不屬本次修改，未加入交付內容。全程未使用 SSH、production API、sudo、secrets 或變更服務。
