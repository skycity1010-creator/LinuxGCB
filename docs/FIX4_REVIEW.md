# FIX4 離線審查

## R9 證據摘要

依任務提供的 2026-11-01 R9 正向 fixture 驗證摘要：完整 GCB 合規 fixture 套用後，P2B3 的 38 條 FAIL 中 35 條經引擎驗證轉 PASS，剩餘 900176、900143、900144 為本次修正範圍。

900176：RHEL9 預設 imuxsock module 的 FileCreateMode="0644" 屬 state file 參數，舊規則誤當日誌模式，即使明確宣告 $FileCreateMode 0640 仍 FAIL。

900143/144：來源九工具含 audisp-remote、audisp-syslog；依提供的真機證據，RHEL9 audit 3.x 已無這兩個 plugin 工具，舊規則對缺失路徑 stat 拋錯，導致 FAIL。

任務引用的 docs/FIXTURE_VALIDATION_R9_R10.md 與 r8/r9/r10 scan JSON 未出現在本工作目錄；以上為使用者提供的證據摘要，未自行重驗或建立替代真機證據。此次僅離線開發，未做 SSH、生產 API、sudo、服務變更、秘密讀取、工作目錄以外外部寫入或 Excel 設定方法執行。

## 三條前後對照

| 規則 | 修改前 | 修改後 |
| --- | --- | --- |
| 900176 / 0176 | 從所有有效設定行抽取 fileCreateMode，誤納入 module 參數 | 只從同時含 action( 與 omfile、且不含 module( 的行抽取 override；原 $FileCreateMode 宣告格式與 <=0640 位元遮罩驗證完全保留 |
| 900143 / 0143 | 九工具每個 stat 都必須成功，mode 位元子集合 <=0750 | 原九工具清單不變；僅 FileNotFoundError 跳過，存在工具仍逐一套用原 <=0750 遮罩；其他 OSError 仍失敗 |
| 900144 / 0144 | 九工具每個 stat 都必須成功，UID/GID 均須 0 | 原九工具清單不變；僅 FileNotFoundError 跳過，存在工具 UID/GID 仍均須 0；其他 OSError 仍失敗 |

metadata() 本身未修改；新增 helper 僅由 0143/0144 引用。兩條分別檢查 mode 與 owner，未增加或刪除彼此的檢核責任。全數工具不存在時依「存在者必符合」的全稱語意 PASS。stat 沿用跟隨 symlink 的既有行為，失效 symlink 的 FileNotFoundError 亦跳過。

0176 維持逐行解析；複雜多行 action、模板與 include 完整語意仍待人工審查。

## 來源解讀待批

caveats 已記錄：「RHEL9 audit 3.x 無 audisp plugin；不存在工具跳過之來源解讀待批」。

沿用 FIX-1 not-found 的解讀先例，工具缺失不代表權限不合規；此解讀仍待來源審查核准，未宣稱政策已完成真機驗收。政策 name 保持 UNVALIDATED，human_review_pending / execution_review=blocked 維持原值。

## 回歸與範圍

tests/test_fix4.py 執行實際 emitted Python、驗證 shell/Python argv round trip，並將輸出交給 simulate：

- 0176：imuxsock 0644 + $FileCreateMode 0640 → PASS；僅 imuxsock 0644 → FAIL；加入 omfile action 0666 → FAIL；另涵蓋合規 action、非 omfile、module 排除與無效宣告。
- 0143/0144：九工具全存在 0750/root → PASS；七存在、兩 audisp 缺失 → PASS；逐一讓任一存在工具 0755 → 0143 FAIL；逐一讓任一存在工具 UID 或 GID 非 0 → 0144 FAIL。兩種工具集合均覆蓋，stat PermissionError 仍 FAIL。
- 原 P2B3 metadata 測試將全缺失預期同步為 PASS，錯誤情境改為實際模擬 stat PermissionError，避免以不存在冒充讀取錯誤。
- fix4_baseline.json 保存任務開始的 146 checks 與既有非 P2B3 fixtures、來源檔案 hash。恰好指定三條 rules 有變，其餘 143 條完整 checks 相同；15 項 R6 真實缺失及 FIX-1/2/3 規則不變。
- 原始來源、TWGCB ID、307/7 scope、既有真機與 R2/R3 fixtures 不變。coverage_manifest 仍為 146 候選；重建僅同步相關 caveats、政策與 hash。P2B3 合成輸出 fixture 僅同步三條 command key。

驗收結果：

- python3 -m unittest discover -s tests -v：77 tests，OK。
- python3 -m linuxgcb build：314 項，307 候選範圍 / 7 排除，146 項候選規則，UNVALIDATED。
- python3 -m linuxgcb validate：146 候選，通過。
- 其餘 143 條 rules diff=0。

提交結果：已嘗試 git add / git commit；因 .git 為唯讀，建立 .git/index.lock 時回報 Read-only file system，未產生 commit。所有變更保留於工作目錄；既有未追蹤 codex_fix4.log 未納入本次修改。
