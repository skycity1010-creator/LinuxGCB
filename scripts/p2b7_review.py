"""Rebuild P2B7 review from hash-verified v1.2 source tables; execute no checks."""
from linuxgcb.batch7 import ADDED, sources, caveat
from linuxgcb.catalog import ROOT, DOCX_HASH, XLSX_HASH
from linuxgcb.coverage import manifest
from linuxgcb.p2b7_runtime import scan_argv


def main():
    entries = {e['sca_id']-900000:e for e in manifest()['reviewed']}
    out = ['# P2B7 系統設定與維護：48 條離線候選', '',
        '188 → 236；0032、0034–0044、0061–0091、0303–0307，共48條；category 全為系統設定與維護，SCA ID=900000+尾碼。來源314、納入307、排除Nftables 7不變。政策name維持UNVALIDATED；本批均partial、human_review_pending、execution_review=blocked，沒有真機符合宣稱。', '',
        '## 來源與可重建性', '',
        '原有 docs/references/ 只有Wazuh參考文件。本批將根目錄GCB v1.2 DOCX逐位元複製至 [docs/references/gcb-rhel9-v1.2.docx](references/gcb-rhel9-v1.2.docx)，根目錄來源與既有證據不改。batch7.sources 逐條直接擷取此參考文件的表格configuration_method，核對XLSX當前版本的ID、完整方法與expected；歷史差異表格不混用。coverage_manifest另核對根目錄DOCX並保留historical_cells。', '',
        'DOCX SHA256：`'+DOCX_HASH+'`；XLSX SHA256：`'+XLSX_HASH+'`。', '',
        '下表來源方法全文逐字保留，僅轉義Markdown/HTML並以<br>表示換行。解讀欄列出實作範圍與待批事項。', '',
        '## 逐條來源方法對照表', '',
        '| TWGCB ID / SCA | 標題 / expected | XLSX sheet / row | DOCX configuration_method | 實作與待批 |',
        '| --- | --- | --- | --- | --- |']
    for n in sorted(ADDED):
        r = sources()[n]
        assert entries[n]['docx_cells'][-2] == r['configuration_method']
        cells = [r['gcb_id']+' / '+str(900000+n),r['title']+' / '+r['expected'],r['sheet']+' / '+str(r['row']),r['configuration_method'],caveat(n)]
        out.append('| '+' | '.join(c.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('|','&#124;').replace('\n','<br>') for c in cells)+' |')
    out += ['', '## 來源解讀待批清單', '',
        '- 0032：來源main與所有repo檔gpgcheck/localpkg_gpgcheck，靜態查精確key及值1；套件管理器實際繼承、重複section與include效力待真機。',
        '- 0034/0035：僅未限定Defaults的靜態子集；限定使用者/主機Defaults、include、續行與覆寫語意待審。logfile接受來源任意非空絕對路徑，sudo.log是範例。',
        '- 0036：只確認定向rpm -q aide已安裝，三態0/1/其他錯誤；來源初始化AIDE資料庫與實際生效另審，不執行安裝/初始化。',
        '- 0037：來源root crontab，範例每天5點；按expected每天接受合法固定分時。本批也按任務接受/etc/cron.daily/可執行檔含明確/usr/sbin/aide --check。cron.daily替代與實際執行需批；無檔、註解、非執行檔不PASS。',
        '- 0038/0039：來源BIOS列grub.cfg、grubenv、存在時user.cfg；UEFI讀fstab /boot/efi列uid=0/gid=0或fmask=0177。任務提示的/boot/loader/entries未在來源列出，不自行增加。fstab多列、掛載與開機模式的實際效力待審。',
        '- 0040：以grub2-setpassword產生的user.cfg之GRUB2_PASSWORD PBKDF2格式作靜態候選；來源grub.cfg重建及密碼載入鏈無自動真機證據。此產物格式解讀待批。',
        '- 0041：照來源讀/usr/lib/systemd/system/rescue.service與emergency.service的ExecStart；不自行改成其他single-user方法。單元section、drop-in與實際啟動鑑別待真機。',
        '- 0042：持久設定fs.suid_dumpable=0、kernel.core_pattern=|/bin/false及limits * hard core 0；來源條件性coredump Storage=none/ProcessSizeMax=0與socket mask尚待適用性和真機證據。0043只查來源持久randomize_va_space=2；0307精確ptrace_scope=1，未放寬2/3。',
        '- 0044：來源明確grep /etc/crypto-policies/config之FUTURE/FIPS，本批照該來源；未用CURRENT.pol或自行變更加密原則。有效policy與重開機結果待審。',
        '- 0061–0065：來源逐磁區；候選以/proc/self/mountinfo的本機檔案系統白名單ext2/ext3/ext4/xfs/btrfs/vfat/f2fs/jfs/reiserfs列出掛載點，排除pseudo/network。未列白名單檔案系統、bind掛載、子磁區、離線/未掛載磁區與NSS一致性待審；沒有可辨識磁區不PASS。來源原本允許根目錄磁區，因此仍可能遍歷整個單一磁區，乾淨大型磁區可逾時，逾時不PASS。',
        '- 0066–0071：只掃來源命令/程式庫目錄，保留-L並新增-xdev及fail-fast。0068來源find允許root/tty/slocate/lock但expected寫root，依方法保留四群組，需核准。0066/0069依來源-perm /0022，未自行改成其他位元檢查。',
        '- 0072：讀shadow只判空密碼欄，非空!/*視為鎖定；不列出帳號或雜湊。0075–0077精確來源行首+:。0078只容root的UID=0。',
        '- 0073/0074：來源echo $PATH代表root實際環境；離線候選不執行shell，順序解析/etc/profile、/root/.bash_profile、/root/.bashrc的literal PATH及有限$PATH展開；動態語法無PASS。條件分支、profile.d、其他登入檔與執行中PATH需人工證據。0074只驗存在目錄且無022寫入位元。',
        '- 0079–0082：照來源passwd帳號與家目錄集合，排除halt/sync/shutdown名稱前綴與/sbin/nologin、/bin/false；包含root，不自行只限/home/*。0079採700位元子集，0080/81比UID/主要GID；缺家目錄失敗。0082只讀一層.[A-Za-z0-9]*普通檔metadata，略過symlink，不遞迴。',
        '- 0083–0085：來源腳本明確排除root/halt/sync/shutdown名稱前綴且略過symlink；依來源只禁其他符合帳號家目錄中的普通.forward/.netrc/.rhosts，和任務提示含/root有差異，待批；不讀檔案內容。',
        '- 0086–0090：本機passwd/group之主要GID存在性、整數UID/GID與名稱唯一性，未推測遠端NSS。0091要求shadow群組存在、補充成員空且沒有主要GID引用；缺shadow群組保守失敗，缺群組適用性需批。',
        '- 0303/0304：來源沒有缺檔豁免，opasswd和opasswd.old兩者必須存在；缺檔不PASS。只讀metadata，完全不讀opasswd內容。0305排除註解與空白後禁/nologin結尾。0306檢查OPTIONS含-F 2且無-u root；實際執行身分與重啟生效待審。', '',
        '## 掃描類命令與 fail-fast', '',
        '0061–0071全部以Python subprocess argv直接執行/usr/bin/find，不經sh。每個find皆-xdev；/proc、/sys、/dev、/run以-prune排除；違規predicate後只接-print -quit，找到第一個違規立即停止，Python亦立即返回False，不繼續其他磁區。不呼叫ls、不使用-exec、不輸出正常檔案。外部stdout/stderr只在記憶體判定，候選對引擎僅在全部成功時輸出PASS；違規/錯誤/逾時無PASS。', '',
        '0061–0065逐一處理來源本機磁區，使用24秒整體子程序預算（各次timeout採剩餘秒數），避免每個磁區重新拿24秒；不保證乾淨大型磁區能在引擎預設30秒內完成。0066–0071固定來源目錄；-L依來源保留。缺少目錄、find非零、stderr或任何違規均不PASS。以下為候選實際argv，0061–0065以/示範分區參數，實際由mountinfo提供：', '']
    for n in range(61,72):
        out += ['- `'+str(n).zfill(4)+'`: `'+repr(scan_argv(n,'/'))+'`']
    out += ['',
        '家目錄0079–0085不遞迴全檔案系統；逐來源帳號與單層目錄，遇第一個違規立即return False。0082 glob限單層，無跨磁區遞迴。', '',
        '## 驗證與交付', '',
        '所有內嵌命令為/usr/bin/python3 -c三個argv，quote_argument雙引號包裝並驗w_strtok roundtrip；不包sh -c；命令內無箭頭分隔字串。只使用唯讀標準庫/定向rpm/find。成功標記只有一處print，全部predicate完成才commit；錯誤與缺失不成功。精確key、排除註解、去除值前後空白；數值條件在Python規則層判定。', '',
        'tests/test_p2b7.py涵蓋48條隔離正例/缺失/錯誤無commit、argv/compile、sysctl數值邊界與註解/前綴反例、rpm三態、find範圍/-quit/首個違規即停/錯誤逾時、帳號唯一性與鎖定、家目錄與PATH、GRUB BIOS/UEFI、opasswd缺檔。歷史測試僅更新總數與新增ID排除，並將舊HEAD依賴固定至原歷史commit，避免分支推進造成誤比。既有fixtures、證據、來源及188條完整checks保持原樣；新測試比對起點6788fdc，188條rules diff=0。', '',
        '驗證：python3 -m linuxgcb build；python3 -m linuxgcb validate；python3 -m unittest discover -s tests -v。完整結果見[P2B7_TEST_OUTPUT.txt](P2B7_TEST_OUTPUT.txt)。重建本文件：python3 -m scripts.p2b7_review。', '',
        '全程offline development only：沒有SSH、生產API、服務變更、sudo或主機秘密存取；帳號檔解析只在隔離測試樹執行。RHEL9/Wazuh PCRE2、實際PATH、開機與設定效力及掃描timeout仍需核准真機驗證。', '',
        '交付限制：環境明列.git唯讀且禁止權限升級；依任務例外保留工作目錄變更，未嘗試繞過限制建立commit。既有未追蹤codex_p2b7.log為會話檔，不屬交付。', '']
    (ROOT/'docs/P2B7_REVIEW.md').write_text('\n'.join(out))


if __name__ == '__main__':
    main()
