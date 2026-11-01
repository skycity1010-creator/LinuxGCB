已完成 0244、0246，均加入 `linuxgcb_firewalld.yml`。

- 候選 305→307；scope 307／排除7，維持 UNVALIDATED。
- 完整 unittest：125 項全過，命令錯誤路徑均使用 mock。
- 既有305條 rules diff=0；fixtures／證據檔未改。
- build、validate、`git diff --check` 通過。
- [P2B10_REVIEW.md](/home/skycity1010/projects/LinuxGCB-codex-p2b10/docs/P2B10_REVIEW.md) 已包含來源對照與待批清單。

來源允許 `public`；0244 同時涵蓋 iptables、ip6tables。因 `.git` 明列唯讀，未提交，變更保留於工作目錄。