"""P2B8 source-bound offline candidates, direct w_strtok Python argv."""
import inspect
import hashlib
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from functools import lru_cache
from pathlib import Path
from . import p2b8_runtime
from .argv import quote_argument
ADDED = set(range(1,30)) | {31} | set(range(285,301))
from .p2b8_runtime import MODULES


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
        raise ValueError('incomplete P2B8 source set')
    return out


def script(n):
    return inspect.getsource(p2b8_runtime) + '\ntry:\n    ok = check(' + str(n) + ")\nexcept (OSError, ValueError, IndexError, KeyError, subprocess.SubprocessError):\n    ok = False\nif ok is None:\n    print('REVIEW')\nelif ok:\n    print('PASS')\n"


@lru_cache(maxsize=1)
def rules():
    return {n:[('c:/usr/bin/python3 -c ' + quote_argument(script(n)), '^PASS$|^REVIEW$')] for n in sorted(ADDED)}


def caveat(n):
    if n in MODULES:
        note = '精確 install 模組 /bin/true 與 blacklist 模組；不以模組不存在豁免；載入狀態與重新開機待真機。'
    elif n in (8,9,13,14,15):
        note = 'mountinfo 確認掛載點、裝置號不同於根與其他祖先、root=/，來源獨立裝置；bind/subpath 不算。'
    elif n == 29:
        note = '來源 df --local -P 逐本機磁區，find -xdev -type d -perm -0002 ! -perm -1000 -print -quit；24秒整體預算。'
    elif 20 <= n <= 22:
        note = '由 sysfs 裝置 removable 與父裝置辨識可攜式掛載；無對象或裝置無法分類輸出 REVIEW，並非符合或違規；USB 固定式及非 block 可攜式辨識待批。'
    elif 23 <= n <= 25:
        note = '來源 passwd UID>=1000 且非 nobody，只查家目錄本身獨立掛載；無對象輸出 REVIEW；以即時值取代來源 fstab 按任務要求，待批。'
    elif 26 <= n <= 28:
        note = '來源條件式 NFS；查即時 nfs/nfs4 掛載選項，無對象輸出 REVIEW；fstab 尚未掛載項之適用性另審。'
    else:
        note = '讀 /proc/mounts 精確掛載點、類型或完整 option token；缺掛載失敗；持久設定及生效差異待真機。'
    return note + ' P2B8 UNVALIDATED；human_review_pending；execution_review=blocked；REVIEW 在輸出匹配層為 raw passed，但 coverage partial 且 blocked，必須人工判定適用性，不是已驗證 PASS。'
