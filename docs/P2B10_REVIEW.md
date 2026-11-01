# P2B10 Firewalld：最後 2 條離線候選

305 → 307 候選；source=314、scope=307、excluded=7、remaining=0。scope 全數已有候選實作，並非全數通過驗證。全數維持 UNVALIDATED、human_review_pending、execution_review=blocked；本批 coverage=partial。

來源：docs/references/gcb-rhel9-v1.2.docx 當前完整條目，與原 XLSX 方法及 expected 逐條比對，排除歷史修改表。
DOCX SHA256：`986effd9501b1fd97776129c6691cf8fc98246bd04514347322f3337508e0e5b`；XLSX SHA256：`7d752b639a1e780df08814c6252efadd3ea2711eaa5c9d91c070b84a296c0247`。

| TWGCB / SCA | 標題 / expected | XLSX sheet / row | DOCX configuration_method 全文 | 唯讀對應與待批 |
| --- | --- | --- | --- | --- |
| TWGCB-01-012-0244 / 900244 | iptables服務 / 停用 | Firewalld防火牆 / 7 | 開啟終端機，執行以下指令，停用並遮蔽iptables與ip6tables服務： <br>#systemctl --now mask iptables<br>#systemctl --now mask ip6tables | 來源 --now mask 涵蓋 iptables 與 ip6tables；唯讀 is-enabled 須 masked/rc1，is-active 須 inactive/rc3；disabled 不等同遮蔽，缺服務不豁免。 P2B10 UNVALIDATED；human_review_pending；execution_review=blocked；來源與引擎語意待批。 |
| TWGCB-01-012-0246 / 900246 | firewalld防火牆預設區域 / 須設定預設區域 | Firewalld防火牆 / 9 | 開啟終端機，執行以下指令設定預設區域：<br>#firewall-cmd --set-default-zone=(區域名稱)<br>設定預設區域為public之範例如下:<br>#firewall-cmd --set-default-zone=public | 以 --get-default-zone 唯讀對應來源設定區域；有效非空區域名稱即可，public 為來源允許範例；不推論是否曾人工設定。 P2B10 UNVALIDATED；human_review_pending；execution_review=blocked；來源與引擎語意待批。 |

## 待批清單

- 0244：來源方法是 systemctl --now mask iptables 及 ip6tables，未提供查詢命令。候選以同一工具的 is-enabled SERVICE 與 is-active SERVICE 唯讀對應兩種狀態，不執行 mask。兩個服務均必須 masked（rc=1）且 inactive（rc=3），disabled（rc=1）僅表示停用，不能滿足來源遮蔽要求；masked/rc=0 等不一致組合亦拒絕。單元不存在、failed、unknown、空輸出均不豁免。查詢對應與 RHEL9 回傳碼語意仍待人工核准及真機確認。
- 0246：來源方法為 firewall-cmd --set-default-zone=(區域名稱)，且明列 public 為範例，未提供查詢命令。候選以 firewall-cmd --get-default-zone 唯讀觀察，rc=0、stderr 空、單一有效非空區域名稱才成功；允許 public，不自創排除 public 的要求。名稱採英數或底線開頭、後續英數/底線/連字號，移除外側空白；名稱語法與空白正規化待批。此查詢只能證明目前預設區域存在，不能證明曾經人工設定或區域安全性。
- 共通：絕對路徑、LC_ALL=C、timeout=8、capture_output、無 shell；非預期 rc、stderr、缺命令、權限、逾時及解析錯誤一律無輸出，規則 ^PASS$ 為 FAIL。僅在全部條件成立後單一 PASS commit；內嵌命令以 w_strtok 雙引號包裝、三個 argv、命令內無箭頭。候選引擎 argv、輸出緩衝、PCRE2 與真機執行仍待批。

## 驗證與交付

- python3 -m linuxgcb build 與 validate：307 候選；manifest=307/7、remaining=0、live_validated=0。
- python3 -m unittest discover -s tests -v：125 項通過。新測試透過 patch subprocess.run 模擬兩個服務、狀態/rc 組合、public/其他區域、空輸出、stderr、非零、權限、缺命令與逾時，無實際 systemctl/firewall-cmd 呼叫。
- 相對起點 21e56dbc1040ce26defdb972bf7e12a37de382d2，既有 305 個完整 checks、policy 與 requirements 不變（rules diff=0）。新增 900244、900246 均位於 linuxgcb_firewalld.yml，與既有 3 條同家族；base/sshd 政策不變。
- 歷史測試僅更新現行數量、新批次排除集合及證據比較起點；report 非法 ID 測試改用已排除的 900247，因 900244 現已實作。既有 fixtures、來源、證據檔均未改。git diff --check 通過。
- offline development only：無 SSH、生產 API、sudo、服務變更或秘密讀取。環境明列 .git 唯讀，依任務例外保留工作目錄變更，未嘗試繞過限制提交。
