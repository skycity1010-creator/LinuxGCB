已完成 FIX-10：

- 900032 跳過無 section 的 repo；有 section 與 main 維持雙 key 嚴格判定。
- 新增[範本](templates/gcb-gpgcheck.repo)及[裁定與雙向驗證程序](docs/FIX10_REVIEW.md)。
- 137 項測試全過，離線 validate 與 diff 檢查通過。
- 其餘 306 條 rules 零差異；保護檔案與 UNVALIDATED 不變。

全程離線，未操作真機。`.git` 為唯讀，未建立 commit，變更已保留於工作目錄。