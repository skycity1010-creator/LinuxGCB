已完成 FIX-8，只修改 900244 規則。

- iptables／ip6tables：not-found 或 disabled／masked，且 inactive → PASS。
- enabled、active、執行錯誤或異常 rc → 無輸出、FAIL。
- 其餘 306 條完整 checks diff=0；0246、coverage_manifest、來源與既有證據未改。
- 128 項測試全過；build、validate、diff 檢查通過。

前後對照與 R21 證據已記錄於 [FIX8_REVIEW.md](/home/skycity1010/projects/LinuxGCB-codex-fix8/docs/FIX8_REVIEW.md)。

`.git` 為唯讀，未建立 commit；變更保留於工作目錄。