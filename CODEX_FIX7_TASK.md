# LinuxGCB FIX-7 任務：修正 P2B8 mountinfo stacked-mount 守衛過嚴（真機 R18 實證）

## 缺陷
P2B8 mountinfo() 對 /proc/self/mountinfo 重複掛載路徑直接 `raise ValueError('stacked mount requires review')` → check 例外 → FAIL。
RHEL9 正常現象：`/proc/sys/fs/binfmt_misc` 有兩條掛載（autofs 觸發 + 實際 binfmt_misc），uniq -d 實證。
→ 所有用 mountinfo() 的檢查被污染：0008、0009、0013、0014、0015、0016、0023、0024、0025。
其中 **0008（/var）與 0015（/home）在 .61 是獨立 LV，應 PASS 而 FAIL**（假阴性）；其餘修正後仍應 FAIL（真實缺失：/var/tmp、/var/log、/var/log/audit 非獨立；/home 掛載無 nodev/nosuid/noexec）。

## 修正要求（只動上述 9 條所屬 runtime 的 mountinfo 邏輯；其餘 rules 語意不變）
1. 重複路徑不再直接 raise：依 mountinfo 順序保留**最後一條**（實際掛載覆蓋 autofs 觸發），或僅當重複路徑落在被檢查路徑的子樹/祖先鏈上才 raise（二選一，寫入 REVIEW 說明選擇理由）。
2. 回歸測試：(a) binfmt_misc 雙掛載 + /var 獨立 LV → 0008 PASS；(b) 目標路徑本身重複掛載 → 仍 REVIEW/FAIL 保守側；(c) 0015 情境同 (a)。
3. 0019（/dev/shm noexec）等 FIXED 表類用 /proc/mounts 的邏輯不動——R18 已證其判定正確（.61 /dev/shm 確無 noexec，真實缺失）。
4. 0020–0022、0026–0028 的 REVIEW→passed 計數語意維持現狀（待批，不在本批範圍）。

## 硬性限制
- 其餘 273 條 rules diff 必須為零；0008/0015 之外的 7 條只允許因 mountinfo 修正而行為修正，判定語意（獨立分割/掛載選項）不得放寬。
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets。
- 來源、TWGCB ID、307/7 scope、coverage_manifest 282、UNVALIDATED、既有 fixtures/證據檔不可改。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過；build/validate 282 候選
- 未動 rules diff=0（除上述 9 條共享 runtime 者）
- docs/FIX7_REVIEW.md：前後對照 + R18 證據（uniq -d 輸出、0008/0015 應轉 PASS 推導）
- git commit（.git 唯讀則保留工作目錄變更並回報）
