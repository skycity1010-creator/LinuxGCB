已完成修正與[審查文件](docs/FIX6_REVIEW.md)。

- 104 項測試全過；validate 通過，維持 236 項。
- usrmerge nologin/false 帳號正確排除；缺失 opasswd 檔案略過。
- `/root` 0550 仍 FAIL。
- 明列 ID 共 **9 條**，其餘 **227 條 rules diff=0**。
- 依 ≤0644 語意保留 **0644 PASS、0664 FAIL**；任務中的「644→FAIL」與此矛盾，已記錄。
- 來源、scope、manifest、fixtures、既有證據未改。

`.git` 唯讀，未建立 commit；變更已保留於工作目錄。