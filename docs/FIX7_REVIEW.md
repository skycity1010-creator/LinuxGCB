# FIX7：P2B8 mountinfo stacked-mount 守衛範圍

基準 commit：`971fbc51601a08352ee80aadb15a23a68e4aab78`。僅 0008、0009、0013、0014、0015、0016、0023、0024、0025 的內嵌 runtime 更新；其餘 273 條完整 checks 與 rules 不變。

## 前後對照與選擇理由

修正前，mountinfo 任一重複掛載點立即拋出 ValueError，外層捕捉後不輸出 PASS，導致不相關的 binfmt_misc 雙掛載污染獨立分割檢查。

採用任務選項二：記錄重複路徑，在 independent(path, info) 僅針對目標本身、祖先鏈或子樹的重複掛載拋出 ValueError。路徑以 `/` 邊界比較，`/variable` 不屬於 `/var` 子樹。解析時雖保存最後一筆資料，相關重複掛載一律先拒絕，絕不憑最後一筆給 PASS；不相關重複路徑不參與目標獨立性判定。這避免假定 mountinfo 列出順序能證明可見的頂層掛載，也符合目標重複掛載仍須保守 FAIL 的驗收要求。

原 p2b8_runtime.py 保持原樣；batch8.script() 僅對指定九條加入 fix7_runtime.py 的兩個函式覆寫。0016 雖在指定名單內，實際仍使用原 FIXED 分支與 /proc/mounts，沒有改變掛載選項判斷。獨立分割仍要求精確掛載點、root=/、非 0: 裝置號，且裝置不同於所有祖先；bind/subpath、缺掛載及解析錯誤仍不通過。0023–0025 的帳號篩選、獨立家目錄選取及選項要求不變。

## R18 證據與 .61 推導

以下為任務提供的 R18 真機觀察，非本次離線執行所得；本工作區沒有找到 R18 原始輸出檔，未連線補採，也未製造完整真機紀錄。

任務所述 mountinfo 掛載點欄位 `uniq -d` 輸出：

```text
/proc/sys/fs/binfmt_misc
```

任務指出這是 autofs 觸發與實際 binfmt_misc 兩筆，且 .61 的 /var、/home 為獨立 LV。離線合成相同結構（不同裝置號、root=/）重現，不將合成裝置號當作真機證據。

| 規則 | 修正前 | 修正後預期及理由 |
| --- | --- | --- |
| 0008 /var | 不相關重複掛載引發 FAIL | PASS：獨立 LV，binfmt_misc 不在 /var 祖先或子樹 |
| 0015 /home | 不相關重複掛載引發 FAIL | PASS：獨立 LV，binfmt_misc 不在 /home 祖先或子樹 |
| 0009、0013、0014 | FAIL | 仍 FAIL：/var/tmp、/var/log、/var/log/audit 非獨立分割 |
| 0016、0023–0025 | FAIL | 仍 FAIL：相關 /home 掛載缺 nodev/nosuid/noexec；0023–0025 依既有帳號家目錄適用條件判定 |
| 0019 /dev/shm | FAIL | 仍 FAIL：缺 noexec，原 /proc/mounts runtime 完全未改 |
| 目標、祖先或子樹重複掛載 | FAIL | 仍 FAIL：ValueError 經原外層捕捉，不輸出 PASS/REVIEW |

0008/0015 轉 PASS 是根據任務給定真機條件與合成回歸的推導，並非本次重新驗證 .61。政策仍為 UNVALIDATED、partial、human_review_pending、execution_review=blocked。

0020–0022、0026–0028 的 REVIEW 輸出、正則與 raw passed 計數語意全部不變，仍待批。本批未修改來源、TWGCB ID、307/7 scope、282 coverage_manifest、既有 fixtures 或證據檔。

## 驗證

`tests/test_fix7.py` 執行實際產出的內嵌程式，覆蓋 binfmt_misc 雙掛載與 /var、/home 獨立 LV、缺分割與選項、補足選項後 PASS、目標／祖先／子樹重複掛載（含逆序）、路徑邊界、bind/subpath、同祖先裝置、0: 裝置及解析錯誤。另以基準 commit 比較九條以外的完整 checks、九條的非 rules 欄位、coverage_manifest、scope_registry 與保護檔案。

執行命令：

```text
python3 -m unittest discover -s tests -v
python3 -m linuxgcb build
python3 -m linuxgcb validate
git diff --check
```

完整 unittest：115 項全過（15.271 秒）。原 P2B7/P2B8 測試的證據差異基準更新至本次起點：舊基準早於 P2B8，會把已提交的 P2B8_TEST_OUTPUT.txt 新增誤報為本次變更；歷史規則比較保持原基準。證據檔內容未改。

build/validate：314 來源、307 候選範圍／7 排除、282 候選規則，UNVALIDATED；其餘 273 條完整 checks diff=0。僅 base 政策及其 policy_hash 更新；coverage_manifest 與 scope_registry 位元組不變。

全程離線，無 SSH、生產 API、服務變更、sudo、秘密讀取或網路操作。環境權限明列 .git 唯讀，依任務例外不嘗試寫入或繞過限制建立 commit，保留工作目錄變更。
