"""P2B9 source-bound offline candidates, direct w_strtok Python argv."""
import inspect
import hashlib
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from functools import lru_cache
from pathlib import Path
from . import p2b9_runtime
from .argv import quote_argument
ADDED = set(range(109,132))
import re


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
        raise ValueError('incomplete P2B9 source set')
    return out


def script(n, key=None):
    runtime = inspect.getsource(p2b9_runtime)
    return runtime + '\ntry:\n    value = check(' + repr(n) + ', ' + repr(key) + ")\nexcept (OSError, ValueError, UnicodeError, subprocess.SubprocessError):\n    value = None\nif value is not None:\n    print('PASS') if value == 'PASS' else print(value)\n"


@lru_cache(maxsize=1)
def rules():
    out = {}
    for n, row in sources().items():
        keys = list(dict.fromkeys(re.findall(r'(?m)^net[.][a-zA-Z0-9_.]+(?=\s*=)', row['configuration_method'])))
        if n in (119,120,121,123):
            keys = list(dict.fromkeys(re.findall(r'sysctl -w (net[.][a-zA-Z0-9_.]+)=', row['configuration_method'])))
            keys = [k for k in keys if not k.endswith('.route.flush')]
        if n <= 125 and not keys:
            raise ValueError('missing source key')
        out[n] = [('c:/usr/bin/python3 -c '+quote_argument(script(n,k)), '^'+row['expected']+'$') for k in keys] if n <= 125 else [('c:/usr/bin/python3 -c '+quote_argument(script(n)), '^PASS$')]
    return out


def caveat(n):
    if n <= 125:
        note = '逐一精確來源 key，查 /etc/sysctl.conf 與 /etc/sysctl.d/*.conf，所有有效宣告須一致；數值於規則層等值判定。不讀 /proc/sys；sysctl -w 與 route.flush 為來源修復步驟，不執行。'
        if n in (119,120,121,123):
            note += '來源清理命令另含 /usr/lib/sysctl.d 與 /run/sysctl.d，故同時查這兩處有無衝突；不模擬載入優先序。'
    elif n <= 129:
        note = '精確 install 模組 /bin/true 與 blacklist 模組；不豁免不存在模組；重新開機及載入狀態待真機。'
    elif n == 130:
        note = '若 nmcli 存在，以 nmcli -t -f WIFI,WWAN radio all 唯讀查軟體 WIFI 與 WWAN 均 disabled；否則以 sysfs wireless 找 module 並檢查來源 install/blacklist。無無線對象不提交 PASS，適用性待批。'
    else:
        note = '依來源用 ip link 唯讀輸出，任一行不分大小寫含 promisc 即失敗；空輸出、缺介面、stderr、非零或逾時不提交 PASS；不執行來源 ip link set。'
    return note + ' P2B9 UNVALIDATED；human_review_pending；execution_review=blocked；來源與引擎語意待批。'
