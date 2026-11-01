"""Commander 2026-11-01 overrides, embedded only in six FIX9 rules."""


def home_options(n):
    info = {}
    pseudo = {'proc','sysfs','devtmpfs','devpts','tmpfs','cgroup','cgroup2',
              'securityfs','debugfs','tracefs','configfs','pstore','mqueue',
              'hugetlbfs','autofs','binfmt_misc','fusectl','rpc_pipefs'}
    for line in read('/proc/self/mountinfo').splitlines():
        left, right = line.split(' - ', 1)
        f = left.split(); tail = right.split()
        if len(f) < 6 or len(tail) < 3:
            raise ValueError('mountinfo record')
        info[unescape(f[4])] = (tail[0], set(f[5].split(',')))
    if '/' not in info:
        raise ValueError('no root')
    minimum = 1000
    for line in read('/etc/login.defs').splitlines():
        f = line.split('#', 1)[0].split()
        if f and f[0] == 'UID_MIN':
            if len(f) != 2: raise ValueError('UID_MIN')
            minimum = int(f[1])
    opt = ('nodev','nosuid','noexec')[n-23]
    for line in read('/etc/passwd').splitlines():
        if not line.strip() or line.lstrip().startswith('#'): continue
        f = line.split(':')
        if len(f) != 7: raise ValueError('passwd record')
        if int(f[2]) < minimum or f[0] == 'nobody': continue
        home = f[5]
        if not home.startswith('/'): raise ValueError('home path')
        home = os.path.normpath(home)
        mount = max((p for p in info if p == '/' or home == p or
                     home.startswith(p.rstrip('/')+'/')), key=len)
        kind, options = info[mount]
        if mount != '/' and kind not in pseudo and opt not in options:
            return False
    return True


def root_paths():
    default = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
    result = []
    for p in ['/etc/profile'] + files('/etc/profile.d/*.sh') + ['/root/.bash_profile','/root/.bashrc']:
        if not os.path.exists(path(p)): continue
        for s in lines(p):
            m = re.fullmatch(r'(?:export\s+)?PATH\s*=\s*(.*?)(?:;\s*export\s+PATH)?', s)
            if not m: continue
            words = shlex.split(m[1])
            if len(words) > 1: raise ValueError('ambiguous PATH')
            value = words[0] if words else ''
            value = re.sub(r'\$\{(HOME|PATH)\}|\$(HOME|PATH)(?![A-Za-z0-9_])',
                           lambda m: '/root' if (m[1] or m[2]) == 'HOME' else default, value)
            # Function-local templates (e.g. pathmunge's PATH=$PATH:$1) are not
            # literal PATH values; positional parameters never reach root's PATH.
            if re.search(r'\$\{?\d', value): continue
            if any(c in value for c in '$`;\\'): raise ValueError('dynamic PATH')
            result.extend(value.split(':'))
    if not result: raise ValueError('missing PATH')
    return result


def fix9_check(n):
    if n in (23,24,25): return home_options(n)
    if n in (73,74):
        ps = root_paths()
        if n == 73:
            return all(p.startswith('/') and p not in ('.','..') for p in ps)
        for p in ps:
            try:
                status = os.stat(path(p))
            except FileNotFoundError:
                continue
            if stat.S_ISDIR(status.st_mode) and status.st_mode & 0o022:
                return False
        return True
    groups = [s for s in records('/etc/group',4) if s[0] == 'shadow']
    if not groups: return True
    return len(groups) == 1 and groups[0][3] == '' and all(int(s[3]) != int(groups[0][2]) for s in records('/etc/passwd',7))
