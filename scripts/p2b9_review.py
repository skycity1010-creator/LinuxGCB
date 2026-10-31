"""Rebuild P2B9 review from verified DOCX methods."""
from linuxgcb.batch9 import ADDED, sources, caveat, rules
from linuxgcb.catalog import ROOT, DOCX_HASH, XLSX_HASH
from linuxgcb.coverage import manifest


def main():
    entries={e['sca_id']-900000:e for e in manifest()['reviewed']}
    out=['# P2B9 網路設定：23 條離線候選','',
         '282 → 305；0109–0131；全部 category=網路設定；SCA ID=900000+尾碼。來源314、scope307、排除7不變。政策 name 維持 UNVALIDATED；本批 coverage=partial、human_review_pending、execution_review=blocked。', '',
         '數量解讀：305 是候選數，不是 scope307 全數已實作。0244 iptables服務與0246 firewalld防火牆預設區域仍 pending；本批依指定23條範圍保留，不自行擴充。','',
         '來源 docs/references/gcb-rhel9-v1.2.docx 與原 XLSX 當前版本逐條完整方法、expected 核對，排除歷史修改表。',
         'DOCX SHA256：`'+DOCX_HASH+'`；XLSX SHA256：`'+XLSX_HASH+'`。','',
         '## 逐條來源對照','',
         '| TWGCB / SCA | 標題 / expected | XLSX sheet / row | DOCX configuration_method 全文 | 實作與待批 |',
         '| --- | --- | --- | --- | --- |']
    for n in sorted(ADDED):
        r=sources()[n]
        assert entries[n]['docx_cells'][-2]==r['configuration_method']
        keys=[]
        if n<=125:
            from linuxgcb.argv import w_strtok
            import ast
            for target,_ in rules()[n]:
                call=next(x for x in ast.walk(ast.parse(w_strtok(target[2:])[2])) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='check')
                keys.append(ast.literal_eval(call.args[1]))
        cells=[r['gcb_id']+' / '+str(900000+n),r['title']+' / '+r['expected'],r['sheet']+' / '+str(r['row']),r['configuration_method'],('設定檔鍵：'+', '.join(keys)+'。' if keys else '')+caveat(n)]
        out.append('| '+' | '.join(c.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('|','&#124;').replace('\n','<br>') for c in cells)+' |')
    out += ['', '## 來源解讀待批清單','',
        '- 0109–0125：來源均寫入 /etc/sysctl.conf 或 /etc/sysctl.d；沒有明寫 /proc/sys 讀取。因此採設定檔值，all/default 分開精確對應，IPv4/IPv6 雙鍵逐條 all 聚合。sysctl -w 與 route.flush 是來源修復，不執行也不據此添加即時檢查。設定檔輸出原始數字，expected 僅由規則 ^0$ 或 ^1$ 判定。排除 #、; 註解，允許兩側空白；鍵全字匹配，不接受 all/default、鍵尾綴或多餘值。缺鍵、無法讀取與衝突值不提交輸出。',
        '- 0119/0120/0121/0123：來源還要求清理 /usr/lib/sysctl.d 與 /run/sysctl.d 衝突，故也讀取這兩個目錄。所有同鍵宣告須一致，並未模擬 sysctl 覆寫優先序；遮蔽檔、同值重複、inline 註解與正規化語意待批。0121 sed 包含重複 net.ipv4 的來源筆誤，保留全文；檢查依來源 sysctl -w 及 printf 一致的 net.ipv4.conf.all.rp_filter。',
        '- 0126–0129：沿用來源 install MODULE /bin/true 與 blacklist MODULE，精確分詞、可跨檔、拒絕額外 install 參數與衝突宣告。缺模組不豁免；開機、實際載入與 modprobe 優先序仍待 RHEL9 真機。',
        '- 0130：不改用題述示例 cfg80211/rfkill。來源優先 nmcli radio all off，候選使用同工具唯讀 nmcli -t -f WIFI,WWAN radio all，兩欄必須 disabled，LC_ALL=C。nmcli 已安裝但執行失敗即停止，不降級到 fallback。未安裝才依 /sys/class/net/*/wireless、device/driver/module 連結取實際模組，查 install/blacklist；首個缺失停止。無 wireless 對象不提交 PASS，適用性仍待批；來源 xargs -0 與 find 輸出分隔矛盾不照搬，改由唯讀路徑 API 對應同一資料。硬體 blocked、軟體 disabled、無硬體的語意與安裝判斷 PATH 需核准。',
        '- 0131：選擇來源 ip link（/usr/sbin/ip link），不使用 ifconfig，不執行 ip link set。對完整 stdout 不分大小寫找 promisc，等同來源 grep -i promisc 的候選判定；至少有一筆合法介面標頭才可提交 PASS。包含 promiscuity 0 亦會被來源字面篩選攔下，未自行修正成其他判定，待批。',
        '- 命令只呼叫一次，不使用 shell；timeout=8 秒，stderr、非零、空輸出與例外均無成功輸出。掃描首個違規即返回。內嵌 python3 -c 僅三個 argv，w_strtok 雙引號 roundtrip，命令無箭頭字串；單一 PASS commit。靜態解析仍受候選引擎 argv/緩衝/PCRE2 與主機 namespace 限制，未宣稱真機符合。','',
        '## 驗證與交付','',
        '重建：python3 -m scripts.p2b9_review；python3 -m linuxgcb build；python3 -m linuxgcb validate；python3 -m unittest discover -s tests -v。',
        'tests/test_p2b9.py 使用隔離設定樹與 mock subprocess，包含逐條來源、鍵名/值/註解/衝突、模組、無線兩分支、命令錯誤與逾時、單一 PASS 與 argv、282 個完整 checks 相對起點 04a49c0 保持原樣（rules diff=0）。既有 tests/fixtures、來源與證據檔未改。歷史測試只調整現行總數及新增ID集合排除。',
        '驗證結果：python3 -m unittest discover -s tests -v 共120項全過；build/validate 為305候選；既有282個完整 checks 不變，rules diff=0；git diff --check 通過。完整輸出見 docs/P2B9_TEST_OUTPUT.txt。',
        '全程 offline development only，無 SSH、生產 API、sudo、服務變更、網路請求或秘密讀取。.git 由環境明列唯讀；依任務例外保留工作目錄變更，不繞過限制提交。','']
    (ROOT/'docs/P2B9_REVIEW.md').write_text('\n'.join(out))


if __name__=='__main__':main()
