已完成 FIX-5：

- 900188 改用定向 `rpm -q` 三態單行模式。
- 79 項測試全過，build／validate 通過，維持 146 候選。
- 其餘 145 條 rules diff=0；既有 fixtures、證據、來源與 coverage_manifest 未變，政策維持 UNVALIDATED。
- 已新增 [FIX5_REVIEW.md](docs/FIX5_REVIEW.md)，記錄前後對照、R13 證據及 R6 誤判原因。

已嘗試提交，但 `.git` 唯讀，無法建立 `index.lock`。所有變更保留於工作目錄。