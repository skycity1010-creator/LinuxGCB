已完成指定六條規則修改。

- 完整測試：133 項全部通過。
- 其餘 301 條 rules diff＝0；metadata、coverage_manifest、fixtures 與證據檔未改。
- 裁定對照：[FIX9_REVIEW.md](/home/skycity1010/projects/LinuxGCB-codex-fix9/docs/FIX9_REVIEW.md)。
- `.git` 為唯讀，`git add` 無法建立 `index.lock`，因此未建立 commit；所有變更已保留於工作目錄。