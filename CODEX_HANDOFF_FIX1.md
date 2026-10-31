修正完成；42 個測試、build、validate 全數通過。所有政策維持 **UNVALIDATED**，原始文件與 307／7 範圍不變。

| Check ID | Before → After |
|---|---|
| 0030 | autofs 必須 loaded＋disabled → 接受不存在或 disabled/masked＋inactive |
| 0094 | rsyncd 必須 masked → 接受不存在或 disabled/masked＋inactive |
| 0097 | squid 必須 masked → 接受不存在或 disabled/masked＋inactive |
| 0098 | 僅 smb 必須 masked → smb、nmb 均接受不存在或 disabled/masked＋inactive |
| 0101 | kdump 必須 enabled＋active → 依本次要求接受不存在或停用；來源差異已註明 |
| 0245 | nftables 必須 masked → disabled＋inactive 可 PASS |

修改檔案共 13 個：`linuxgcb/{batch1,policy}.py`、兩份 base/firewalld policies、coverage manifest／policy hashes、兩份 fixtures、三份測試，以及以下文件：

- [完整 review 與檔案清單](docs/FIX1_REVIEW.md)
- [測試輸出](docs/FIX1_TEST_OUTPUT.txt)

**Commit 未完成**：目前分支為 `codex/linuxgcb-fix1`，但環境將 `.git` 設為唯讀，無法建立 `index.lock`。修改均保留於工作目錄；既有 `codex_fix1.log` 未修改。