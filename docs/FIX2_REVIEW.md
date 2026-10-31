# FIX-2：wm_exec 命令引號修正

依使用者提供的 R5 真機證據（2026-10-31，agent 010，Wazuh 4.14.9），P2B2 新增 44 條因 argv 分詞錯誤全 FAIL。本次僅離線修正，不代表真機重新驗證；政策 name 保持 UNVALIDATED。

## w_strtok 規則與改寫

wm_exec 不經 shell，分詞後直接 execvp。雙引號成對分組並剝除；反斜線跳脫下一字元；單引號是普通字元。因此原先使用 shlex.quote 的外層單引號不能保留完整 sh -c 腳本。

以下為 JSON 解碼後的規則字串：

原先：
```text
c:/bin/sh -c 'out=$(/usr/sbin/sshd -T); rc=$?; if [ "$rc" -eq 0 ]; then printf "%s\n" "$out" "LINUXGCB_COMMAND_OK"; else exit "$rc"; fi' -> r:^usepam yes$
```

修正：
```text
c:/bin/sh -c "out=$(/usr/sbin/sshd -T); rc=$?; if [ \"$rc\" -eq 0 ]; then printf '%s\\n' \"$out\" 'LINUXGCB_COMMAND_OK'; else exit $rc; fi" -> r:^usepam yes$
```

政策以 json.dumps 編碼：雙引號寫為 `\"`，反斜線寫為 `\\`。printf 格式中的反斜線也須經 argv 層跳脫，才能在 shell 層保留 `\n`；不能只跳脫雙引號。

## 模擬器與回歸測試

`linuxgcb/argv.py` 提供獨立 w_strtok 模型及單一 argv 編碼器，編碼時先驗證往返。模型不執行 shell 展開；對未成對雙引號或末尾反斜線採保守拒絕，這是離線模型邊界，並未宣稱涵蓋 Wazuh 的所有異常輸入行為。

BATCH2 產生器使用此編碼器；模擬器 parse_rule 對全部新規則驗證恰有三個 argv，前兩個為 /bin/sh、-c。guard 測試改用 w_strtok，移除原先錯誤的 shlex.split。shlex.quote 僅用於真正 shell 層的字串參數。

`tests/test_fix2.py` 對所有 44 條的來源命令重建舊版，經模型分詞後以 sh -n 驗證語法失敗（不執行來源命令），再確認空輸出為 FAIL。新版驗證完整腳本 argv，並只以 printf/exit 合成命令比較正反輸出語意；既有 guard 測試涵蓋退出碼 0、1、2、126、127，確認失敗時不發布任何 stdout 或成功標記。合成 fixtures 涵蓋每個 predicate 的正反案例。

wm_exec 正常結束仍回 0，故模擬器不以 exit_code 覆蓋逐行輸出匹配，包含新 44 條。刻意提供「非零但含成功標記」的矛盾觀察仍可匹配 PASS；真正失敗防護由 shell guard 緩衝輸出並在成功後發布。Q1-01 維持。

## 驗證結果與範圍

- `python3 -m unittest discover -s tests -v`：60 tests，OK。
- `python3 -m linuxgcb build` 及 `python3 -m linuxgcb validate`：97 候選，307/7 scope 不變。
- 與任務開始 HEAD 比對：舊 53 條完整 check（含 rules）完全相同；44 條新 check 僅 rules 改變，description、compliance 與 predicate 不變。
- 更新政策 hash、44 條合成 rule_outputs 與合成 snapshot 的政策 hash；R2/R3 fixtures、batch2_baseline、xlsx、controls.json 不變。
- 無 SSH、production API、sudo、服務操作或來源設定命令執行。未執行真機重掃。
