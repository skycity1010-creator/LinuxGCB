"""Read-only source predicates; embedded directly in python3 argv."""
import glob
import os
import re
import subprocess
ROOT = ''


def read(path):
    with open(ROOT + path, encoding='utf-8') as stream:
        return stream.read()


def lines(path):
    return [s.split('#', 1)[0].strip() for s in read(path).splitlines()
            if s.split('#', 1)[0].strip()]


def paths(pattern):
    return sorted(p[len(ROOT):] for p in glob.glob(ROOT + pattern))


def value(path, key, equal=True, section=None):
    found = None
    current = None
    for line in lines(path):
        if line.startswith('['):
            current = line
        elif section is None or current == '[' + section + ']':
            m = re.fullmatch(re.escape(key) + (r'\s*=\s*(.*?)' if equal else r'\s+(.*?)'), line)
            if m:
                found = m[1].strip()
    return found


def number(path, key, low=None, high=None, equal=True, section=None):
    v = value(path, key, equal, section)
    return (v is not None and re.fullmatch(r'-?\d+', v) is not None
            and (low is None or int(v) >= low) and (high is None or int(v) <= high))


def pam(path, kind, control, module, options=()):
    matches = []
    for line in lines(path):
        tokens = line.split()
        if len(tokens) >= 3 and tokens[0] == kind and tokens[1] in control and tokens[2] == module:
            matches.append(tokens[3:])
    return bool(matches) and all(all(option in opts for option in options) for opts in matches)


def stacks(kind, control, module, options=()):
    return all(pam('/etc/pam.d/' + name, kind, control, module, options)
               for name in ('system-auth', 'password-auth'))


def history():
    candidates = [s.split() for s in lines('/etc/pam.d/system-auth')]
    options = [t[3:] for t in candidates if len(t) >= 3 and t[0] == 'password'
               and t[1] in ('required', 'requisite') and t[2] == 'pam_pwhistory.so']
    return bool(options) and all(any(re.fullmatch(r'remember=\d+', x) and int(x.split('=')[1]) >= 3 for x in opts) for opts in options)


def sudo():
    names = ['/etc/sudoers'] + paths('/etc/sudoers.d/*')
    for path in names:
        for raw in read(path).splitlines():
            if re.match(r'\s*(?:#|@)include', raw) and not re.fullmatch(r'\s*(?:#|@)includedir\s+/etc/sudoers.d\s*', raw):
                return False
        if any(re.search(r'\bNOPASSWD\b|!authenticate\b', s, re.I) for s in lines(path)):
            return False
    return True


def maxlogins():
    entries = [s.split() for p in ['/etc/security/limits.conf'] + paths('/etc/security/limits.d/*.conf') for s in lines(p)]
    settings = [t for t in entries if len(t) == 4 and t[2] == 'maxlogins']
    return (any(t[:3] == ['*', 'hard', 'maxlogins'] for t in settings)
            and all(t[3].isdigit() and 0 < int(t[3]) <= 10 for t in settings))


def accounts():
    threshold = value('/etc/login.defs', 'UID_MIN', False)
    if threshold is None or not threshold.isdigit():
        return False
    users = [s.split(':') for s in lines('/etc/passwd')]
    for t in users:
        if len(t) != 7 or not t[2].isdigit():
            return False
        if t[0] != 'root' and not t[0].startswith('+') and int(t[2]) < int(threshold):
            if t[0] not in ('sync', 'shutdown', 'halt') and t[6] not in ('/sbin/nologin', '/usr/sbin/nologin', '/bin/false'):
                return False
            result = subprocess.run(['/usr/bin/passwd', '-S', t[0]], capture_output=True, text=True)
            if result.returncode or len(result.stdout.split()) < 2 or result.stdout.split()[1] not in ('L', 'LK'):
                return False
    return bool(users)


def shell_setting(names, key):
    values = []
    for path in names:
        for line in lines(path):
            if key == 'umask':
                m = re.fullmatch(r'umask\s+([0-7]{3,4})\s*;?', line)
                if m:
                    values.append(int(m[1], 8) & 0o027 == 0o027)
            else:
                m = re.fullmatch(r'(?:readonly\s+)?TMOUT\s*=\s*(\d+)\s*(?:;\s*export\s+TMOUT\s*)?', line)
                if m:
                    values.append(0 < int(m[1]) <= 900)
    return bool(values) and all(values)


def check(n):
    pw = '/etc/security/pwquality.conf'
    login = '/etc/login.defs'
    numeric = {206:(pw,'retry',1,3,True),208:(pw,'minlen',12,None,True),209:(pw,'minclass',4,4,True),
        210:(pw,'dcredit',None,-1,True),211:(pw,'ucredit',None,-1,True),212:(pw,'lcredit',None,-1,True),213:(pw,'ocredit',None,-1,True),
        214:(pw,'difok',3,None,True),215:(pw,'maxclassrepeat',1,4,True),216:(pw,'maxrepeat',1,3,True),217:(pw,'dictcheck',1,1,True),
        218:('/etc/security/faillock.conf','deny',1,5,True),219:('/etc/security/faillock.conf','unlock_time',900,None,True),
        223:(login,'PASS_MIN_DAYS',1,None,False),224:(login,'PASS_WARN_AGE',14,None,False),225:(login,'PASS_MAX_DAYS',1,90,False),
        226:('/etc/default/useradd','INACTIVE',1,30,True),227:(login,'FAIL_DELAY',4,None,False),311:(pw,'maxsequence',1,3,True)}
    if n in numeric:
        ok = number(*numeric[n])
        return ok and (n != 208 or number(login,'PASS_MIN_LEN',12,None,False))
    if n == 207: return stacks('password',('requisite',),'pam_pwquality.so',('enforce_for_root',))
    if n == 220: return history()
    if n == 221: return lines('/etc/pam.d/postlogin')[0] == 'session required pam_lastlog.so showfailed'
    if n == 222: return value('/etc/libuser.conf','crypt_style') == 'sha512' and value(login,'ENCRYPT_METHOD',False) == 'SHA512' and stacks('password',('sufficient',),'pam_unix.so',('sha512',))
    if n == 228: return value(login,'CREATE_HOME',False) == 'yes'
    if n == 229: return sudo()
    if n == 230: return maxlogins()
    if n == 231:
        result = subprocess.run(['/usr/bin/rpm','-q','kbd'], capture_output=True, text=True)
        if result.returncode not in (0,1): raise ValueError('rpm query error')
        return result.returncode == 0 and bool(result.stdout.strip())
    if n == 232: return value('/etc/dconf/db/local.d/00-screensaver','lock-enabled',section='org/gnome/desktop/screensaver') == 'true'
    if n == 233:
        v = value('/etc/dconf/db/local.d/00-screensaver','idle-delay',section='org/gnome/desktop/session')
        return v is not None and re.fullmatch(r'uint32\s+\d+',v) is not None and 0 < int(v.split()[1]) <= 900
    if n == 234: return value('/etc/gdm/custom.conf','AutomaticLoginEnable',section='daemon') == 'false'
    if n == 235: return accounts()
    if n == 236: return shell_setting(['/etc/bashrc'],'TMOUT') and shell_setting(['/etc/profile'] + paths('/etc/profile.d/*.sh'),'TMOUT')
    if n == 237: return all('/org/gnome/desktop/' + s in lines('/etc/dconf/db/local.d/locks/session') for s in ('session/idle-delay','screensaver/lock-enabled','screensaver/lock-delay','lockdown/disable-lock-screen'))
    if n == 238:
        roots = [s.split(':') for s in lines('/etc/passwd') if s.split(':')[0] == 'root']
        return len(roots) == 1 and len(roots[0]) == 7 and roots[0][3] == '0'
    if n == 239: return shell_setting(['/etc/bashrc'],'umask') and shell_setting(['/etc/profile'] + paths('/etc/profile.d/*.sh'),'umask')
    if n == 240:
        v = value(login,'UMASK',False)
        return v is not None and re.fullmatch(r'[0-7]{3,4}',v) is not None and int(v,8) & 0o027 == 0o027
    if n == 241: return pam('/etc/pam.d/su','auth',('required',),'pam_wheel.so',('use_uid',)) and any(len(t)==4 and t[0]=='wheel' and 'root' in t[3].split(',') for t in (s.split(':') for s in lines('/etc/group')))
    if n == 309: return shell_setting(['/root/.bashrc'],'umask') and shell_setting(['/root/.bash_profile'],'umask')
    if n == 310: return 'even_deny_root' in lines('/etc/security/faillock.conf') and number('/etc/security/faillock.conf','root_unlock_time',60)
    if n == 312: return stacks('auth',('sufficient',),'pam_unix.so') and all('nullok' not in s.split()[3:] for name in ('system-auth','password-auth') for s in lines('/etc/pam.d/'+name) if 'pam_unix.so' in s.split())
    if n == 313: return stacks('password',('requisite',),'pam_pwquality.so',('local_users_only',))
    if n == 314: return all(stacks(kind,(control,),'pam_unix.so',opts) for kind,control,opts in (('auth','sufficient',()),('account','required',()),('password','sufficient',('sha512','shadow','use_authtok')),('session','required',())))
    raise ValueError(n)
