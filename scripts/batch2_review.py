"""Reproducible offline BATCH2 review, using source cells and emitted fixtures."""
import json
from linuxgcb.catalog import ROOT, registry
from linuxgcb.batch2 import ADDED, specs, expected


def cell(value):
    return str(value).replace('|','&#124;').replace('\n','<br>').replace('`','&#96;')


def main():
    controls={r['gcb_id']:r for r in json.loads((ROOT/'data/controls.json').read_text())}
    fixtures=json.loads((ROOT/'tests/fixtures/rule_outputs.json').read_text())['checks']
    text='''# BATCH2 離線候選審查

本批完成 registry 指定四類的全部未實作項目：**新增 44，53 → 97**，不是預估的 51／104。基線為 `tests/fixtures/batch2_baseline.json`（保存原 53 個 emitted check 完整物件、既有輸出 fixtures 的 canonical hash、來源及 R2/R3 hash）。307 included／7 excluded、所有 TWGCB/sca_id 不變；Nftables配置七項仍 excluded。未擴張其他類別。

| 類別 | registry 總數 | 批前已實作 | 新增 | 批後未實作 |
| --- | ---: | ---: | ---: | ---: |
| SSH設定 | 32 | 4 | 28 | 0 |
| cron設定 | 16 | 12 | 4 | 0 |
| SELinux | 7 | 1 | 6 | 0 |
| 安裝與維護軟體 | 6 | 0 | 6 | 0 |

## 沿用模式與必要差異

- 原有 53 checks（包括 description、rules 與 FIX-1 服務狀態組合）完整物件差異為零；firewalld 政策整檔亦不變。原有 tests 保留行為斷言，僅全域數量改為新增後數量，Q1/EXP-1 專屬斷言仍檢查原 53。新增 crond/sshd 是來源要求 enabled+active 的服務，且 sshd 要求 openssh-server 已安裝；不是停用服務，沒有新增停用服務以重寫 FIX-1。
- 每條 description 仍為 `合規值: <具體基準值> ｜ <治理備註>`，新增治理標籤為 BATCH2。0258 的組織授權清單無單一基準值，明示 `待確認（來源未提供單一基準值）`，不使用來源示例 smith/jones 冒充正式清單。
- SSH 以 `sshd -T` 預設情境有效值為主，沿用 Include/Match、使用者/來源矩陣限制。0255 以成功標記加規則層級否定排除非 Protocol 2，接受現代版本不輸出已移除的 Protocol 欄。0279 接受 no/delayed，以及 RHEL9 OpenSSH 8.0+ 的 yes（僅認證後壓縮）；此預設/等價依據寫在 description，仍須 RHEL9 引擎驗證。
- **Q1-01 差異不能隱瞞**：原專案不存在已實作的 exit-code 保護；既有測試明確要求非零且 stdout 匹配仍 raw PASS。因此不能同時「保留原 53 diff=0」又聲稱已修復它們。只為新增命令加入 `out=$(command); rc=$?` 緩衝保護；exit 0 才發布完整 stdout 與 `LINUXGCB_COMMAND_OK`，非零不發布 stdout、保留退出狀態。每個命令另有正向成功標記必要條件。只讀 shell 命令全部固定明列；不執行來源 F 欄的 remediation。引擎 argv/quoting、stderr 合併、輸出截斷與 timeout 均未真機驗證，execution_review 仍 blocked。
- 模擬器只對精確白名單的新增 emitted rules 支援 `not c:` 全規則否定，並將明確非零執行回 UNRESOLVED；原 53 的輸出模型保留。實際 guard 非零會提供空 stdout、無成功標記，因而至少一條必要規則 FAIL，不能 PASS。UNRESOLVED 是離線證據分類，不能宣稱 Wazuh 必然產生同名結果。
- 不使用 `!r:` 表達「整份輸出不存在」。隨附 [Wazuh 文件](references/creating-custom-policies.md) 的 content-negation 段落指出 `!r:` 是逐行判斷，任一無關行可能導致通過；本批使用 `not c:... -> r:禁止內容`，再以 all 加上成功標記，失敗或空輸出不能藉否定而假通過。
- 套件移除先成功列舉整個 RPM DB，再否定指定套件名稱，避免把 rpm 查詢錯誤解釋成未安裝。主機鑰匙依來源 find 集合檢查，必須至少有一把且不得有任何不符 metadata 的成員。不存在檔案以成功 find + 規則否定檢查，權限錯誤不得通過。
- DOCX 0272 同時包含修訂歷史 CountMax=0 與現行 CountMax=1；採用 XLSX F/G 與 DOCX 現行/修改後值 1，coverage manifest 另存 `docx_historical_cells`，不刪歷史或放寬成 0。

## 測試與保留限制

`python3 -m linuxgcb build`、`python3 -m linuxgcb validate`、`python3 -m unittest discover -s tests -v` 為驗收命令。測試結果保存於 `docs/BATCH2_TEST_OUTPUT.txt`。97 個候選皆 UNVALIDATED；coverage full=0 / partial=92 / blocked=5，execution_review 97 blocked。離線成功不等於 RHEL9／Wazuh 實機通過。

`python3 -m scripts.batch2_fixtures` 由已發出的 check/rule targets 加上獨立作者提供的正反輸出樣本重建新增 fixtures；`python3 -m scripts.batch2_review` 重建本文件。所有命令都只建置／測試本地資料，不掃描開發機冒充 RHEL9。唯一子程序 guard 測試先從 emitted shell 取出腳本，完整替換其中的 inventory 命令為合成 printf/exit，再執行；不會執行任何政策命令或設定方法。

每條至少 positive、negative、missing、empty、error、nonzero_matching；另外逐條 source predicate 反例，逐 target 缺失、權限失敗與非零匹配。範圍/基線測試核對原 53 checks 全物件、原 fixtures hash、原 controls/XLSX/R2/R3 hash；既有 FIX-1、報表與真實快照測試仍保留。邊界包括 1–4、1–600、1–60、所有權限位元及特殊位元、cipher/MAC/KEX 三者獨立變壞、好/壞鑰匙混合、Protocol 缺省與錯誤版本。

已知 partial 範圍：0107/0185/0186/0205/0284 的文字設定不是完整載入順序解析；0184 僅 /etc/default/grub，未宣稱已產生 grub.cfg/實際開機參數符合；0185 接受 targeted 或來源允許更嚴格的 mls；0258 授權清單仍須人工核准；0260 來源敘述文字提 600，但 F 命令與 G 期望為 640，依 F/G 實作並保留差異。0259–0262 只涵蓋來源 type f 集合，未解決 ACL、symlink 與額外 HostKey 路徑。0282/0283 的全檔案系統 find 有 timeout／掛載邊界限制。所有治理備註逐條保留於 description。

## 逐條規則與來源 cells

下表 F/G 為原始 XLSX 的設定方法／期望欄，等同 `controls.json.configuration_method`／`expected`；不修改原始資料。每行的 fixture 路徑均為 `tests/fixtures/rule_outputs.json#<sca_id>`。正反樣本依子規則列示，實際 fixture 合併同命令的輸出並補成功標記；「空集合」只有在命令成功與成功標記存在時才可能符合不存在條件。規則摘要前綴 `not` 表示整個輸出不得存在匹配行。位元子集合以簡寫呈現，完整 emitted regex 保存在政策中。

| sca_id / TWGCB ID | 規則摘要 | 正案例輸出（依子規則） | 反案例輸出（依子規則） | 合規值 | 來源 cell 與原 G 值 |
| --- | --- | --- | --- | --- | --- |
'''
    for row in registry():
        n=row['sca_id']-900000
        if n not in ADDED: continue
        source=controls[row['gcb_id']]
        summaries=[]
        for command,pattern,good,bad in specs()[n]:
            if len(pattern)>180: pattern='允許權限位元子集合（所有成員符合）' if n in (204,260,262) else pattern
            summaries.append(command+' → '+('not '+pattern[1:] if pattern.startswith('!') else pattern))
        good=[x[2] or '空集合' for x in specs()[n]]
        bad=[x[3] for x in specs()[n]]
        assert str(row['sca_id']) in fixtures
        text+='| '+' | '.join(map(cell,[str(row['sca_id'])+' / '+row['gcb_id']+' '+row['title'], '\n'.join(dict.fromkeys(summaries)), '\n'.join(good), '\n'.join(bad), expected(source),source['sheet']+'!F'+str(source['row'])+' / G'+str(source['row'])+'；G='+source['expected']]))+' |\n'
    (ROOT/'docs/BATCH2_REVIEW.md').write_text(text)

if __name__=='__main__': main()
