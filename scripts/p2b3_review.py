"""Rebuild P2B3 offline review inventory from the source-bound definitions."""
from linuxgcb.catalog import ROOT
from linuxgcb.batch3 import ADDED, mechanism, caveat, sources


def main():
    lines=['# P2B3 離線審查：日誌與稽核 43 + 系統服務 6', '',
           '本批以工作區 FIX-3 起點為準新增 49 條：97 → 146 候選；來源 314、scope 307、Nftables 排除 7 不變，未實作 210 → 161。新增 49 條均為 partial、human_review_pending、execution_review=blocked、live_validation=UNVALIDATED；政策 name 保持 UNVALIDATED。候選數不等於已驗證符合數。', '',
           '三份政策由 base 62／firewalld 3／sshd 32 變為 base 111／firewalld 3／sshd 32。以 tests/fixtures/p2b3/baseline.json 保存批次前 97 個完整 checks；新測試逐物件核對，既有 97 條 rules diff=0（description、ID、condition 亦相同）。firewalld 與 sshd 政策位元不變。來源 XLSX、DOCX、controls/inventory、全部原 fixtures 及真機證據檔依 baseline hash 保護；不修改歷史 FIX3/R2/R3，工作區沒有新增或捏造 R6/R7 證據。R7 的 22 個真實缺失不在本批修正範圍。', '',
           '## 機轉與限制', '',
           '0092 使用 FIX-3 定向 rpm -q shell 三態：0 → INSTALLED、1 → ABSENT、其他退出碼不輸出。0096／0099／0100 也使用相同三態子命令，已安裝時依來源檢核服務；0096 保留來源允許的 SNMPv3 分支。0095 同查 avahi service/socket。systemctl 僅 show，disabled/masked 且 inactive，明確 not-found 且 inactive 視為停用；不從錯誤訊息或空值推論。', '',
           '其餘候選透過 sh -c 執行內嵌 /usr/bin/python3 標準函式庫解析器，沒有部署外部 helper。這是新增端點執行相依性，缺少解譯器即不合格，仍待 RHEL9/Wazuh 真機驗收。build 不執行這些命令。讀取或命令失敗、任一必要條件不成立均不輸出 PASS；成功才輸出一行 PASS，避免逐行存在匹配及 256 行截斷掩蓋集合內的違規項。SCA 使用精確 ^PASS$；規則主體以 fullmatch 檢查持久檔內每條來源規則，沒有以任意 audit 規則存在代替。', '',
           'FIX-2 quote_argument 編碼全部 shell 引數並驗證 w_strtok 還原為三個 argv；測試再核對 shell 第二層 Python 引數，且對隔離 audit fixture 執行完整實際 shell。所有規則檔匹配排除行首空白後的 #，全行錨定 token/路徑/perm/key，避免 sudoers/sudoers.d、路徑後綴與 key 後綴誤匹配。UID_MIN 取 login.defs 最後有效設定，不擅自沿用 1000。', '',
           'DOCX 0153 同時包含修訂前後且 expected 同為啟用；以 controls.json 的完整 configuration_method 選取現行 cells，歷史內容仍列 docx_historical_cells。0159 的 renameat-S 解讀為兩個 syscall flags；0173 的 -e 2--loginuid-immutable 解讀為兩行，均列為人工待核准差異。181/182 是 TWGCB ID 尾碼，不使用 Excel ordinal（來源沒有 0180）。', '',
           'journald 來源明文要求「新增」Compress=yes／Storage=persistent，故即使套件預設 Compress=yes，未設定也不自動合格；解析主檔 [Journal]、同名 drop-in 目錄優先序、字典排序、最後值及 /dev/null mask。rsyslog 保留舊式與來源範圍內新式 omfile action，複雜模板等保守留待審查。0308 依來源指定 stanza 與目錄權限檢核，並非僅搜 rsyslog 字樣。', '',
           '## 49 條逐項清單', '', '| TWGCB ID（SCA ID） | 標題／機轉 | Caveats |', '| --- | --- | --- |']
    for n in sorted(ADDED):
        row=sources()[n]
        cells=[row['gcb_id']+' ('+str(900000+n)+')',row['title']+'；'+mechanism(n),caveat(n)]
        lines.append('| '+' | '.join(c.replace('|','&#124;').replace('\n',' ') for c in cells)+' |')
    lines += ['', '## 檔案清單', '',
              '- linuxgcb/batch3.py：49 個 ID、來源規則、內嵌程式組裝、機轉／合規值／caveats。',
              '- linuxgcb/p2b3_runtime.py：唯讀解析與集合檢核；只嵌入各控制實際所需函式。',
              '- linuxgcb/catalog.py、quality.py、expected.py、policy.py、coverage.py：registry、狀態、合規值、allowlist 與 manifest 整合。',
              '- data/scope_registry.json、coverage_manifest.json、policy_hashes.json；policies/linuxgcb_base.yml：可重建產物。',
              '- scripts/p2b3_fixtures.py、p2b3_review.py：重建 test-only fixtures 與本文件。',
              '- tests/fixtures/p2b3/baseline.json、cases.json；tests/test_p2b3.py：97 條基線、49 條輸入樹與輸出矩陣。',
              '- tests/test_batch2.py、test_catalog_policy.py、test_expected.py、test_fix3.py、test_quality_q1.py、test_report.py：既有測試限定歷史 ID 集合／新增總數；合成 snapshot 只在記憶體綁定當前 hash，保留報表拒絕錯誤 hash 的測試。',
              '- README.md：本批入口；docs/P2B3_REVIEW.md、P2B3_TEST_OUTPUT.txt：審查與離線驗證結果。', '',
              '## 驗證與交付', '',
              '重建命令：python3 -m scripts.p2b3_fixtures；python3 -m scripts.p2b3_review；python3 -m linuxgcb build；python3 -m linuxgcb validate。完整測試（TMPDIR 指向工作區 out/p2b3-tmp）python3 -m unittest discover -s tests -v：74 tests，OK。輸出見 P2B3_TEST_OUTPUT.txt。', '',
              '每條都有 positive／negative／missing／empty／error；另保留 nonzero_matching 顯示模擬器只看 stdout 的界線，不能把手寫 PASS+exit 2 當成真實 wrapper 行為。audit/AIDE/immutable 加註解反例，套件加 rpm_other_error；測試實際三態 shell 的退出碼 0/1/2/3/126/127，偽造匹配輸出也不能逸出失敗分支。', '',
              '額外執行實際解析器：每個 audit 子規則逐一移除/註解/改 key/加後綴、UID_MIN 覆寫、超過 600 行前置內容、metadata 權限與特殊位元、auditd 最後值與數值邊界、journald sections/drop-in 覆寫、rsyslog 兩種語法、特權程式新增、sudo 路徑變更、不變模式覆寫及自然排序。所有讀取導向 test-only 暫存樹，UID/GID 與 systemctl/RPM 僅 mock，不讀真機設定、不執行服務操作。', '',
              '本次離線驗收不等於 Wazuh PCRE2／wm_exec 或 RHEL9 真機驗收；Python regex 與 argv 模型的限制仍保留。未使用 SSH、生產 API、sudo、網路或秘密，也未執行 Excel 設定方法。', '',
              '本環境 permission profile 將 .git 列為唯讀；依任務允許的例外保留工作目錄變更，不嘗試繞過限制建立 commit。既有未追蹤 codex_p2b3.log 為會話檔，不列入交付。', '']
    (ROOT/'docs/P2B3_REVIEW.md').write_text('\n'.join(lines))

if __name__=='__main__': main()
