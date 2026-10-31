已完成 FIX-7，採用「僅目標、祖先或子樹重複掛載才拒絕」策略。

- 115 項測試全過；build/validate 通過，維持 282 候選。
- 0008／0015 合成 R18 情境 PASS；目標重複掛載及真實缺失仍 FAIL。
- 僅指定 9 條 rules 更新，其餘 273 條完整 checks diff=0。
- 0019、REVIEW 計數語意、scope、coverage_manifest、來源及既有證據未改。
- [FIX7_REVIEW.md](/home/skycity1010/projects/LinuxGCB-codex-fix7/docs/FIX7_REVIEW.md) 已記錄選擇理由、前後對照與 R18 證據來源限制。

全程離線。`.git` 明列唯讀，未建立 commit，變更保留於工作目錄。