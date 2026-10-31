"""Rebuild exact source-method review; never execute source instructions."""
from linuxgcb.batch6 import ADDED, sources, caveat
from linuxgcb.catalog import ROOT, DOCX_HASH, XLSX_HASH
from linuxgcb.coverage import manifest


def main():
    m = manifest()
    entries = {e['sca_id']-900000:e for e in m['reviewed']}
    out = ['# P2B6 帳號與存取控制：42 條離線候選', '',
        '146 → 188；新增 0206–0241、0309–0314，全數 category=帳號與存取控制，SCA ID=900000+尾碼。來源 314、納入 307、排除 Nftables 7 不變。政策 name 維持 UNVALIDATED，42 條均為 partial、human_review_pending、execution_review=blocked，無真機符合宣稱。', '',
        '來源定位：docs/references/ 現有檔案為 Wazuh 引擎參考，沒有 GCB v1.2 文件。沿用既有 scripts.inventory.extract 讀取根目錄 XLSX；coverage.manifest 逐條核對根目錄 GCB v1.2 DOCX 的 ID、完整 configuration_method 與 expected，未新增檢查來源，也未執行來源設定腳本。', '',
        'XLSX SHA256：`'+XLSX_HASH+'`；DOCX SHA256：`'+DOCX_HASH+'`。下表逐字保留 extractor 方法內容（HTML 換行），來源歷史 cells 與現行 cells 仍保存在 coverage_manifest。', '',
        '| TWGCB ID / SCA | 標題 / expected | XLSX 工作表 / row | 來源 configuration_method | 解讀與待批 |',
        '| --- | --- | --- | --- | --- |']
    for n in sorted(ADDED):
        r=sources()[n]
        assert entries[n]['docx_cells'][-2] == r['configuration_method']
        cells=[r['gcb_id']+' / '+str(900000+n), r['title']+' / '+r['expected'],r['sheet']+' / '+str(r['row']),r['configuration_method'],caveat(n)]
        out.append('| '+' | '.join(c.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('|','&#124;').replace('\n','<br>') for c in cells)+' |')
    out += ['', '## 來源解讀待批清單', '',
        '- 0206：來源寫 Retry；解讀為 libpwquality 的 retry。0208 同查 PASS_MIN_LEN 與 minlen，不以其中一項替代。',
        '- 0207/0220/0222/0312–0314：讀 /etc/pam.d/system-auth、password-auth 渲染堆疊並跟隨 symlink；0220 僅 system-auth。來源 0220 腳本混用 pam_unix/pwquality，採任務指定的 pam_pwhistory remember>=3，待批。authselect custom profile、feature、apply-changes 與實際載入需真機證據。',
        '- 0221：要求 postlogin 第一個有效行。0222 三個來源檔一併檢查；libuser section 未限縮，複雜 section 覆寫待審。',
        '- 0223–0226：預設值可自動判定；既有帳號 chage 必須另提供人工證據。0226 useradd -D -f 對應 /etc/default/useradd INACTIVE。未讀 shadow 或秘密。',
        '- 0227、0228：來源明列 login.defs FAIL_DELAY 與 CREATE_HOME，依來源檢查；未改為 PAM faildelay 或 /etc/default/useradd CREATE_HOME。',
        '- 0229：排除註解，拒絕有效 NOPASSWD/!authenticate；僅允許來源 sudoers.d include，其他 include 保守失敗。完整 sudoers alias/續行語意待真機。',
        '- 0230：來源 limits.conf 或 limits.d；要求 * hard maxlogins，所有明確 maxlogins 為 1–10，覆寫與 pam_limits 生效待審。0231 定向 rpm -q kbd：0 installed、1 absent、其他錯誤不輸出 PASS。',
        '- 0232/0233/0237：只讀明列 dconf 系統來源檔；0234 讀 gdm custom.conf [daemon]。headless 缺檔失敗，不當作不適用或 PASS。dconf update、系統 profile/lock 實際載入及桌面有效值留真機驗證。',
        '- 0235：依來源 UID_MIN 而非提示的 SYS_UID_MAX；root/+ 排除，shell 另排除 sync/shutdown/halt。檢查 nologin/false 與唯讀 passwd -S 的 L/LK；讀取或命令錯誤失敗。未自行採用固定999邊界。',
        '- 0236：bashrc 與 profile/profile.d 均要求有效 TMOUT 1–900。只支援來源明確 assignment 子集；shell 條件、載入順序及 readonly/export 有效性待審。',
        '- 0239/0240/0309：以遮罩包含027判更低權限；007不包含禁止同群組寫入的位元，不依提示放寬。0239 同查 bashrc 與 profile/profile.d；0309 同查 .bash_profile 與 .bashrc。shell 條件分支與載入效力待審。',
        '- 0241：pam_wheel required use_uid 與 wheel 包含 root；其他允許成員屬人工核准清單，不自行臆測。0310 要求 even_deny_root 與 root_unlock_time>=60。', '',
        '## 執行機轉與驗證', '',
        '所有候選均為 /usr/bin/python3 -c 直接三個 argv，使用 quote_argument 雙引號編碼並以 w_strtok 模型還原；不包 sh -c、不安裝端點 helper。純讀取標準庫程式在所有 predicate 完成後才單次輸出 PASS。missing/error 無成功標記，regex ^PASS$ 不把空輸出視為成功。數值在 predicate 做範圍判定；設定 key 精確比對、排除註解、去除值前後空白。', '',
        'tests/test_p2b6.py 涵蓋42條範圍、完整 argv/compile、全部缺失無 PASS、數值上下界、註解/key前綴反例、渲染堆疊 symlink、隔離配置正反例、RPM三態；既有測試改為限定歷史ID集合或更新總數，未修改既有 fixtures/證據。FIX5 對可重建 registry/manifest 改逐項核對本批外的舊內容，歷史來源 hash 仍核對。', '',
        '驗證命令：python3 -m linuxgcb build；python3 -m linuxgcb validate；python3 -m unittest discover -s tests -v。測試輸出見 docs/P2B6_TEST_OUTPUT.txt。新測試另比對 HEAD 的146條原始 rules，diff=0；既有 fixtures、來源、證據與其他兩份政策均未修改。', '',
        '全程 offline：無 SSH、生產 API、服務更動、sudo 或秘密存取。尚無 RHEL9/Wazuh PCRE2、timeout 與實際有效設定驗收。', '',
        '交付限制：本環境明列 .git 為唯讀且禁止權限升級；依任務例外保留工作目錄變更，不繞過限制建立 commit。未追蹤 codex_p2b6.log 為既有會話檔，未納入交付。', '']
    (ROOT/'docs/P2B6_REVIEW.md').write_text('\n'.join(out))

if __name__ == '__main__':
    main()
