"""P2B7 source-bound offline candidates, direct w_strtok Python argv."""
import inspect
import hashlib
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from functools import lru_cache
from pathlib import Path
from . import p2b7_runtime
from .argv import quote_argument
from . import fix9_runtime
ADDED = {32} | set(range(34,45)) | set(range(61,92)) | set(range(303,308))


@lru_cache(maxsize=1)
def sources():
    from scripts.inventory import extract
    root = Path(__file__).resolve().parents[1]
    docx = root/'docs/references/gcb-rhel9-v1.2.docx'
    if hashlib.sha256(docx.read_bytes()).hexdigest() != '986effd9501b1fd97776129c6691cf8fc98246bd04514347322f3337508e0e5b':
        raise ValueError('GCB v1.2 reference hash changed')
    ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    xml = ET.fromstring(ZipFile(docx).read('word/document.xml'))
    tables = [['\n'.join(''.join(t.text or '' for t in p.findall('.//w:t',ns))
              for p in cell.findall('.//w:p',ns)) for cell in tr.findall('w:tc',ns)]
              for tr in xml.findall('.//w:tr',ns)]
    out = {}
    for r in extract(next(root.glob('*.xlsx'))):
        n = int(r['gcb_id'][-4:])
        if n not in ADDED:
            continue
        matches = [c for c in tables if r['gcb_id'] in c and c[-1] == r['expected'] and c[-2] == r['configuration_method']]
        if not matches or any(c[-2:] != matches[0][-2:] for c in matches):
            raise ValueError('GCB DOCX/XLSX source mismatch: '+r['gcb_id'])
        out[n] = dict(r, configuration_method=matches[0][-2])
    if set(out) != ADDED:
        raise ValueError('incomplete P2B7 source set')
    return out


def script(n):
    source = inspect.getsource(p2b7_runtime)
    # Preserve byte-identical embedded scripts outside the FIX6 ID family.
    if n not in set(range(79,86)) | {303,304}:
        source = source.replace("u[6].endswith(('/nologin','/false'))", "u[6] in ('/sbin/nologin','/bin/false')")
        source = source.replace("        for p in ('/etc/security/opasswd','/etc/security/opasswd.old'):\n            try:\n                ok = meta(p,uid=0,gid=0) if n == 303 else meta(p,mode=0o644)\n            except FileNotFoundError:\n                continue\n            if not ok:\n                return False\n        return True", "        return all(meta(p,uid=0,gid=0) if n == 303 else meta(p,mode=0o644) for p in ('/etc/security/opasswd','/etc/security/opasswd.old'))")
    if n in {73,74,91}:
        source += '\n' + inspect.getsource(fix9_runtime.root_paths)
        source += '\n' + inspect.getsource(fix9_runtime.fix9_check)
        source += '\ncheck = fix9_check\n'
    return source + '\ntry:\n    ok = check(' + str(n) + ")\nexcept (OSError, ValueError, IndexError, KeyError, subprocess.SubprocessError):\n    ok = False\nif ok:\n    print('PASS')\n"


@lru_cache(maxsize=1)
def rules():
    return {n:[('c:/usr/bin/python3 -c ' + quote_argument(script(n)), '^PASS$')] for n in sorted(ADDED)}


def mechanism(n):
    return '逐條來源唯讀 predicate；直接 python3 -c argv；單一 PASS commit'


def caveat(n):
    notes = {
        32:'main 與 repo 檔同查 gpgcheck/localpkg_gpgcheck=1；各repo section皆需雙key；繼承與生效待批。',
        34:'只接受未限定 Defaults use_pty；限定使用者/主機、include、續行與覆寫待審。',
        35:'logfile 要求非空絕對路徑；來源 /var/log/sudo.log 僅範例；複雜 sudoers 語意待審。',
        36:'定向 rpm -q aide 三態；初始化資料庫動作未執行，資料庫生效另審。',
        37:'來源 root crontab 每天5點；expected 每天允許合法固定分時；依任務另接受 cron.daily 可執行檔明確 /usr/sbin/aide --check。排程替代需批。',
        38:'來源 BIOS grub.cfg/grubenv/選用user.cfg；UEFI fstab uid=0,gid=0；未自行增加 loader/entries。',
        39:'來源 BIOS 600 位元子集；UEFI fmask=0177；未自行增加 loader/entries。',
        40:'靜態確認 grub2-setpassword 產生之 user.cfg PBKDF2 宣告；grub.cfg 載入與重建效果留真機。',
        41:'來源 rescue/emergency.service ExecStart 精確比對；systemd drop-in 實際生效留真機。',
        42:'同查 suid_dumpable=0、core_pattern=|/bin/false 與 * hard core 0；條件性 coredump Storage/ProcessSizeMax/mask、即時值與載入效力待人工證據。',
        43:'持久設定 randomize_va_space 精確2；即時值待真機。',
        44:'來源明列 /etc/crypto-policies/config FUTURE/FIPS；未改查 CURRENT.pol；生效/重開機待真機。',
        68:'來源 find 允許 root/tty/slocate/lock，但 expected 寫 root；依方法保留四群組，待批。',
        72:'shadow 只判空欄；!/* 為非空鎖定；不輸出帳號/雜湊。',
        73:'來源 echo $PATH；離線靜態讀 /etc/profile、/root/.bash_profile、.bashrc 的 literal PATH，受限展開 $PATH；拒絕動態語法；登入環境與其他載入來源待批。',
        74:'沿用0073靜態PATH子集，逐目錄確認存在且無022寫入位元；登入有效環境待批。',
        79:'依來源互動帳號集合，排除 halt/sync/shutdown 名稱前綴與 nologin/false；700位元子集，家目錄不限/home。',
        80:'依來源 passwd 家目錄與 UID；跟隨stat symlink；缺目錄失敗。',
        81:'依來源 passwd 家目錄與主要GID；缺目錄失敗。',
        82:'依來源只查家目錄一層 .[A-Za-z0-9]* 普通檔、排除symlink、禁022；找到即返回。',
        83:'依來源排除root/halt/sync/shutdown前綴，只禁非symlink普通.forward；未擴張成含root，待批。',
        84:'依來源排除root/halt/sync/shutdown前綴，只禁非symlink普通.netrc；未讀檔案內容，待批。',
        85:'依來源排除root/halt/sync/shutdown前綴，只禁非symlink普通.rhosts，待批。',
        86:'passwd 所有主要GID需存在於本機group；NSS遠端群組不推測。',
        87:'UID以整數唯一性判定。',88:'GID以整數唯一性判定。',
        91:'要求shadow群組存在、補充成員空且無passwd主要GID引用；缺群組保守失敗，待批。',
        303:'來源無缺檔豁免；opasswd與.old都必須存在且root:root，不讀內容。',
        304:'來源無缺檔豁免；兩檔都必須存在且644位元子集。',
        305:'排除註解與前後空白後禁止/nologin結尾。',
        306:'來源OPTIONS含-F 2且不得-u root；服務執行身分/重啟生效留真機。',
        307:'來源ptrace_scope精確1，未自行放寬2/3；即時值待真機。',
    }.get(n,'依來源本機帳號檔唯讀解析。')
    if 61 <= n <= 71:
        notes += 'find -xdev、pseudo prune、-print -quit；0061–65依mountinfo逐本機磁區，0066–71固定來源目錄；24秒整體子程序預算，錯誤/逾時無PASS。分區範圍/白名單待真機。'
    return notes + 'P2B7 UNVALIDATED；human_review_pending；execution_review=blocked；來源文字靜態唯讀子集，生效狀態/角色/覆寫需真機；缺失與錯誤無 PASS。'
