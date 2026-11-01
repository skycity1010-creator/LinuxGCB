# LinuxGCB P2B10 任務：Firewalld 配置最後 2 條（0244、0246）

## 起點
branch codex/linuxgcb-p2b10（P2B9 後，305 候選）。目標：+2 = 307 候選（scope 307 全數實作）。

## 條目
- TWGCB-01-012-0244 / 900244：iptables 服務停用（expected 停用）
- TWGCB-01-012-0246 / 900246：firewalld 防火牆預設區域須設定
來源方法逐條從 docs/references/ GCB v1.2 來源文件擷取，不得自創檢查。

## 慣例
- 0244：systemd 服務狀態類——依來源方法（systemctl is-enabled/is-active iptables；規則命令用來源指定者，唯讀；注意 systemctl 輸出非零退出碼的處理：is-enabled disabled/masked 的輸出與 rc 語意要照來源文字，錯誤→無輸出→FAIL 安全側）。
- 0246：firewalld 預設區域——依來源方法（firewall-cmd --get-default-zone 輸出非空/非 public 預設之判定照來源文字；firewalld 政策檔 linuxgcb_firewalld.yml 家族，與既有 3 條同檔）。
- 既有 305 條 rules diff 必須為零；2 條新增放 linuxgcb_firewalld.yml（同家族）。
- 內嵌命令 w_strtok 雙引號包裝、單一 PASS commit、唯讀、命令內不可有 `->`。
- offline development only：No SSH、no production API、no service changes、no sudo、no secrets。
- coverage_manifest 305→307；307/7 scope、UNVALIDATED、既有 fixtures/證據檔不可改。

## 驗收
- `python3 -m unittest discover -s tests -v` 全過（含 systemctl/firewall-cmd 輸出模擬與錯誤路徑；錯誤路徑測試必須 patch subprocess.run，勿重蹈 P2B9 測試隔離缺陷）
- 305 條未動 rules diff=0
- docs/P2B10_REVIEW.md：逐條來源對照 + 待批清單
- git commit（.git 唯讀則保留工作目錄變更並回報）
