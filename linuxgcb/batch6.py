"""P2B6 source-bound offline candidates, direct w_strtok Python argv."""
import inspect
import json
from functools import lru_cache
from pathlib import Path
from . import p2b6_runtime
from .argv import quote_argument
ADDED = set(range(206,242)) | set(range(309,315))


@lru_cache(maxsize=1)
def sources():
    from scripts.inventory import extract
    root = Path(__file__).resolve().parents[1]
    return {int(r['gcb_id'][-4:]):r for r in extract(next(root.glob('*.xlsx'))) if int(r['gcb_id'][-4:]) in ADDED}


def script(n):
    return inspect.getsource(p2b6_runtime) + '\ntry:\n    ok = check(' + str(n) + ")\nexcept (OSError, ValueError, IndexError, KeyError):\n    ok = False\nif ok:\n    print('PASS')\n"


@lru_cache(maxsize=1)
def rules():
    return {n:[('c:/usr/bin/python3 -c ' + quote_argument(script(n)), '^PASS$')] for n in sorted(ADDED)}


def mechanism(n):
    return '逐條來源唯讀 predicate；直接 python3 -c argv；單一 PASS commit'


def caveat(n):
    extra = {
        206:'來源 Retry 大寫解讀為 libpwquality retry 小寫；待批。',
        208:'同時要求來源 PASS_MIN_LEN 與 minlen；RHEL9 PASS_MIN_LEN 效力待審。',
        220:'來源腳本與文字模組混用；採 pam_pwhistory remember>=3，單查 system-auth；待批。',
        223:'只檢查預設值；既有帳號 chage 效果待人工證據，不讀 shadow。',
        224:'只檢查預設值；既有帳號 chage 效果待人工證據，不讀 shadow。',
        225:'只檢查預設值；既有帳號 chage 效果待人工證據，不讀 shadow。',
        226:'useradd -D -f 對應 /etc/default/useradd INACTIVE；既有帳號待人工證據。',
        227:'依來源 login.defs FAIL_DELAY>=4，未替換成 PAM delay。',
        228:'依來源 login.defs CREATE_HOME，未改查 /etc/default/useradd。',
        231:'rpm -q kbd：0 installed、1 absent、其他錯誤無 PASS；不用 rpm -qa。',
        235:'依來源 UID_MIN（非 SYS_UID_MAX）；root/+ 排除，shell 另排除 sync/shutdown/halt；passwd -S 唯讀確認 L/LK。不讀 shadow。',
        236:'同時要求 bashrc 與 profile/profile.d；保守靜態宣告子集，條件分支/載入順序與 readonly/export 效力待審。',
        239:'同時要求 bashrc 與 profile/profile.d；umask 位元包含027，含007因不符合來源027不接受；shell 分支待審。',
        241:'確認 wheel 包含 root；其他允許成員名單需人工核准。',
        309:'依來源同時檢查 /root/.bash_profile 與 /root/.bashrc，缺檔失敗。',
        312:'檢查渲染堆疊 pam_unix 無 nullok；authselect feature 狀態及 apply-changes 待真機。',
    }.get(n,'')
    if n in (232,233,237): extra += '只讀來源 dconf 系統來源檔；缺檔無 PASS；dconf update 編譯資料庫、profile/locks 載入與桌面有效值待真機。'
    if n in (207,220,222,312,313,314): extra += '讀 /etc/pam.d 渲染堆疊並跟隨 symlink；authselect custom profile 與執行中效力待真機。'
    return extra + 'P2B6 UNVALIDATED；human_review_pending；execution_review=blocked；唯讀 Python 標準庫，錯誤/缺失無成功輸出；w_strtok/PCRE2/timeout 待真機。'
