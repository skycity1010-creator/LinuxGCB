"""Rebuild review from hash-verified per-control reference methods."""
from linuxgcb.batch8 import ADDED, sources, caveat
from linuxgcb.catalog import ROOT, DOCX_HASH, XLSX_HASH
from linuxgcb.coverage import manifest
from linuxgcb.p2b8_runtime import scan_argv


def main():
    entries={e['sca_id']-900000:e for e in manifest()['reviewed']}
    out=['# P2B8 磁碟與檔案系統：46 條離線候選','',
        '236 → 282；0001–0029、0031、0285–0300；category 全為磁碟與檔案系統，SCA ID=900000+尾碼。來源314、納入307、排除7不變。政策name維持UNVALIDATED；本批均partial、human_review_pending、execution_review=blocked，沒有真機符合宣稱。','',
        '## 來源與重建','',
        '逐條讀取 docs/references/gcb-rhel9-v1.2.docx 的 configuration_method，與既有 XLSX 當前版本 ID、完整方法及 expected 核對，不混用歷史修改表。來源檔與歷史證據不改。下表全文只轉義 Markdown/HTML 與換行。','',
        'DOCX SHA256：`'+DOCX_HASH+'`；XLSX SHA256：`'+XLSX_HASH+'`。','',
        '數量校正：任務家族說明寫19條模組，但0001–0003(3)+0031(1)+0285–0300(16)=20條；其他26條，合計46，依指定ID完整實作。','',
        '## 逐條來源方法對照表','',
        '| TWGCB ID / SCA | 標題 / expected | XLSX sheet / row | DOCX configuration_method | 實作與待批 |',
        '| --- | --- | --- | --- | --- |']
    for n in sorted(ADDED):
        r=sources()[n];assert entries[n]['docx_cells'][-2]==r['configuration_method']
        cells=[r['gcb_id']+' / '+str(900000+n),r['title']+' / '+r['expected'],r['sheet']+' / '+str(r['row']),r['configuration_method'],caveat(n)]
        out.append('| '+' | '.join(c.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('|','&#124;').replace('\n','<br>') for c in cells)+' |')
    out += ['', '## 來源解讀待批清單','',
        '- 模組20條：依來源精確 install 模組 /bin/true 及 blacklist 模組，從 /etc/modprobe.d/*.conf 搜尋、移除註解並分詞，允許前後空白，拒絕前綴誤匹配、額外參數及衝突install。兩宣告可跨檔。來源模組拼字全部保留，包含 ext、fat、nfs_common、smbfs_common；RHEL9不存在仍必須寫來源設定，缺失FAIL。rmmod/modprobe -r、重開機及載入狀態只留真機，不執行。宣告覆寫、破折號與底線等效性待批。',
        '- 0004與固定掛載選項：依任務讀 /proc/mounts 即時值，完全不以註解或fstab靜態文字給PASS。/tmp 類型必須tmpfs；固定掛載點缺失FAIL，來源0017–0019明確要求缺失時新增。重複固定掛載點不PASS。持久化與開機效力留真機。',
        '- 0008/0009/0013/0014/0015：掛載點須在mountinfo中，root欄=/、非0開頭裝置號且與所有祖先裝置號不同。根檔案系統bind、subpath與祖先分割的bind不算獨立分割。不同裝置整體bind、特殊檔案系統、Btrfs子卷與stacked mounts需真機審；stacked mounts錯誤不PASS。',
        '- 0020–0022：來源mount未提供自動辨識可攜式的predicate。本候選使用sysfs block removable與partition父裝置；確定有可攜掛載時檢查全部對象，任何缺option即違規；其他裝置無法分類時回REVIEW。USB固定式、非block可攜裝置、裝置別名、namespace與硬體政策仍需核准，不能宣稱辨識完整。',
        '- 0023–0025：精確來源 UID>=1000 且名稱不為nobody，不另按shell篩選；只查家目錄本身的獨立掛載，不自行擴張成每個家目錄都必須獨立。無符合對象REVIEW；獨立裝置定義及來源fstab改即時掛載的差異需批。',
        '- 0026–0028：來源先grep fstab確認是否有NFS，且只有「若發現有掛載」才設定。依任務改用即時nfs/nfs4類型精確匹配；沒有即時NFS時REVIEW，不推論已符合或違規。fstab存在但尚未掛載、autofs觸發與namespace適用性仍待核准。',
        '- 無掛載點語意（0020–0028）：條件未成立或可攜辨識不完整時 check 回傳None，只輸出REVIEW，不輸出PASS。SCA二元正則無法表達自訂第三態，候選模式明列 ^PASS$|^REVIEW$，因此引擎可能記錄raw passed；這是避免將無適用對象記成違規的暫定輸出編碼，不是符合性PASS，也不是已核准N/A。現有報表會因partial/blocked保留MANUAL_PENDING。必須審查command/evidence的REVIEW與硬體/掛載證據後核准適用性，禁止以raw passed當驗收符合。若要求引擎原生第三態，需要另審引擎適用性設計；本批不冒稱已完成真機語意驗證。',
        '- 0029：依來源 df --local -P 列出本機掛載磁區，逐一用下列find，只讀不chmod。遇違規、stderr、非零、解析錯誤或逾時均不PASS。df使用換行/空白欄位；含空白或換行之特殊掛載點不PASS，特殊名稱和大型乾淨磁區逾時待真機。無磁區不PASS。','',
        '## fail-fast 與 argv','',
        '`'+repr(scan_argv('/'))+'`','',
        '每個find都有-xdev、-print -quit，第一個違規即返回，不掃後續磁區；df與find共用24秒整體預算。不使用shell、不安裝helper、不呼叫mount/remount、modprobe、rmmod或chmod。內嵌 /usr/bin/python3 -c 僅3個argv，使用w_strtok雙引號roundtrip；命令內沒有箭頭分隔字串；只有全部predicate成功才從單一print提交PASS。REVIEW另用獨立標記。所有測試用隔離樹與mock subprocess，不執行主機find或讀取主機帳號檔。','',
        '## 驗證與交付','',
        'tests/test_p2b8.py涵蓋46條來源與argv、單一PASS、模組精確key/註解/空白/衝突、掛載選項token與缺失、bind/subpath、sysfs父裝置、條件式REVIEW/負例、find首個違規即停與錯誤逾時。比對起點d5e32f0：236條完整checks保持原樣，rules diff=0；既有fixtures與證據檔不改。歷史測試僅更新總數、新ID排除及manifest新增集合比較；報表原未實作900001反例改用仍未實作900109。','',
        '重建：python3 -m scripts.p2b8_review；python3 -m linuxgcb build；python3 -m linuxgcb validate；python3 -m unittest discover -s tests -v。完整測試結果見P2B8_TEST_OUTPUT.txt。','',
        '全程offline development only：無SSH、生產API、服務變更、sudo、網路請求或秘密讀取。環境將.git列唯讀且禁止提權，依任務例外保留工作目錄變更，不繞過限制建立commit。','']
    (ROOT/'docs/P2B8_REVIEW.md').write_text('\n'.join(out))


if __name__=='__main__':main()
