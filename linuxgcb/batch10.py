"""P2B10 source-bound offline candidates, direct w_strtok Python argv."""
import inspect
import hashlib
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from functools import lru_cache
from pathlib import Path
from . import p2b10_runtime, fix8_runtime
from .argv import quote_argument
ADDED = {244, 246}


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
        raise ValueError('incomplete P2B10 source set')
    return out


def script(n):
    runtime = inspect.getsource(p2b10_runtime)
    if n == 244:
        runtime += '\n' + inspect.getsource(fix8_runtime)
    return runtime + '\ntry:\n    ok = check(' + repr(n) + ")\nexcept (OSError, ValueError, UnicodeError, subprocess.SubprocessError):\n    ok = False\nif ok:\n    print('PASS')\n"


@lru_cache(maxsize=1)
def rules():
    sources()
    return {n: [('c:/usr/bin/python3 -c '+quote_argument(script(n)), '^PASS$')] for n in sorted(ADDED)}


def caveat(n):
    note = ('來源 --now mask 涵蓋 iptables 與 ip6tables；唯讀 is-enabled 須 masked/rc1，is-active 須 inactive/rc3；disabled 不等同遮蔽，缺服務不豁免。' if n == 244 else
            '以 --get-default-zone 唯讀對應來源設定區域；有效非空區域名稱即可，public 為來源允許範例；不推論是否曾人工設定。')
    return note + ' P2B10 UNVALIDATED；human_review_pending；execution_review=blocked；來源與引擎語意待批。'
