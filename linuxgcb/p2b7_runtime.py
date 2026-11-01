"""Read-only source predicates. ROOT is only for isolated offline tests."""
import glob
import os
import re
import shlex
import stat
import subprocess
import time
ROOT = ''


def path(p):
    return ROOT + p


def read(p):
    with open(path(p), encoding='utf-8') as f:
        return f.read()


def files(pattern):
    return sorted(p[len(ROOT):] if ROOT else p for p in glob.iglob(path(pattern)))


def lines(p):
    return [s.split('#', 1)[0].strip() for s in read(p).splitlines() if s.split('#', 1)[0].strip()]


def values(paths, key):
    out = []
    for p in paths:
        for s in lines(p):
            m = re.fullmatch(re.escape(key) + r'\s*=\s*(.*?)\s*', s)
            if m:
                out.append(m[1])
    return out


def setting(paths, key, expected):
    v = values(paths, key)
    return bool(v) and all(x == expected for x in v)


def meta(p, mode=None, uid=None, gid=None):
    s = os.stat(path(p))
    return (mode is None or stat.S_IMODE(s.st_mode) & ~mode == 0) and (uid is None or s.st_uid == uid) and (gid is None or s.st_gid == gid)


def records(p, size):
    rows = [s.split(':') for s in read(p).splitlines() if s]
    if not rows or any(len(s) != size or not s[0] for s in rows):
        raise ValueError('invalid account database')
    return rows


def scan_argv(n, mount=None):
    commands = ['/bin','/sbin','/usr/bin','/usr/sbin','/usr/local/bin','/usr/local/sbin']
    libraries = ['/lib','/lib64','/usr/lib','/usr/lib64']
    roots = [mount] if n <= 65 else commands if n <= 68 else libraries
    predicates = {
        61:['-type','f','-perm','-0002'], 62:['-nouser'],63:['-nogroup'],
        64:['-type','d','-perm','-0002','-uid','+999'],65:['-type','d','-perm','-0002','-gid','+999'],
        66:['-perm','/0022'],67:['!','-user','root'],
        68:['!','-group','root','!','-group','tty','!','-group','slocate','!','-group','lock'],
        69:['-perm','/0022','-type','f'],70:['!','-user','root'],71:['!','-group','root']}
    return ['/usr/bin/find'] + ([] if n <= 65 else ['-L']) + [path(p) for p in roots] + ['-xdev','(','-path',path('/proc'),'-o','-path',path('/sys'),'-o','-path',path('/dev'),'-o','-path',path('/run'),')','-prune','-o','('] + predicates[n] + [')','-print','-quit']


def scan(n):
    # Source partitions are read from mountinfo; pseudo/network filesystems excluded.
    if n <= 65:
        local = {'ext2','ext3','ext4','xfs','btrfs','vfat','f2fs','jfs','reiserfs'}
        roots = []
        for s in read('/proc/self/mountinfo').splitlines():
            left, right = s.split(' - ', 1)
            if right.split()[0] in local:
                mount = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1],8)), left.split()[4])
                if not any(mount == p or mount.startswith(p+'/') for p in ('/proc','/sys','/dev','/run')):
                    roots.append(mount)
        if not roots:
            return False
    else:
        roots = [None]
    deadline = time.monotonic() + 24
    for mount in dict.fromkeys(roots):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        result = subprocess.run(scan_argv(n,mount), capture_output=True, text=True, timeout=remaining)
        if result.returncode != 0 or result.stdout or result.stderr:
            return False
    return True


def root_path():
    # Do not execute shell startup files. Expand only literal PATH assignments.
    current = None
    for p in ['/etc/profile','/root/.bash_profile','/root/.bashrc']:
        if not os.path.exists(path(p)):
            continue
        for s in lines(p):
            m = re.fullmatch(r'(?:export\s+)?PATH\s*=\s*(.*?)(?:;\s*export\s+PATH)?',s)
            if not m:
                continue
            v = shlex.split(m[1])
            if len(v) != 1:
                raise ValueError('ambiguous PATH')
            v = v[0]
            if '$PATH' in v or '${PATH}' in v:
                if current is None:
                    raise ValueError('unresolved PATH')
                v = re.sub(r'\$\{PATH\}|\$PATH(?![A-Za-z0-9_])',lambda m: current,v)
            if any(c in v for c in '$`;\\'):
                raise ValueError('dynamic PATH')
            current = v
    if current is None:
        raise ValueError('missing PATH')
    return current.split(':')


def check(n):
    if n == 32:
        required = {'gpgcheck','localpkg_gpgcheck'}
        for p in ['/etc/yum.conf','/etc/dnf/dnf.conf'] + files('/etc/yum.repos.d/*'):
            section = None
            seen = {}
            content = lines(p)
            if p.startswith('/etc/yum.repos.d/') and not any(s.startswith('[') and s.endswith(']') for s in content):
                continue
            for s in content:
                if s.startswith('[') and s.endswith(']'):
                    section = s[1:-1]
                    seen.setdefault(section,set())
                for key in required:
                    m = re.fullmatch(key+r'\s*=\s*(.*?)\s*',s)
                    if m and (p.startswith('/etc/yum.repos.d/') or section == 'main'):
                        if section is None or int(m[1]) != 1:
                            return False
                        seen[section].add(key)
            if p.startswith('/etc/yum.repos.d/'):
                if any(v != required for v in seen.values()):
                    return False
            elif seen.get('main') != required:
                return False
        return True
    if n in (34,35):
        found = False
        for p in ['/etc/sudoers'] + files('/etc/sudoers.d/*'):
            for s in lines(p):
                if not re.match(r'^Defaults\s+',s):
                    continue
                for token in re.split(r',\s*',re.sub(r'^Defaults\s+','',s)):
                    if n == 34 and token == '!use_pty':
                        return False
                    if n == 34 and token == 'use_pty':
                        found = True
                    if n == 35 and re.match(r'^logfile\s*=',token):
                        v = shlex.split(token.split('=',1)[1].strip())
                        if len(v) != 1 or not v[0].startswith('/'):
                            return False
                        found = True
        return found
    if n == 36:
        r = subprocess.run(['/usr/bin/rpm','-q','aide'],capture_output=True,text=True,timeout=5)
        if r.returncode not in (0,1):
            raise ValueError('rpm error')
        return r.returncode == 0 and bool(r.stdout.strip())
    if n == 37:
        # Root crontab is the actual source; daily directory is a task-requested alternative.
        p = '/var/spool/cron/root'
        if os.path.exists(path(p)) and any(re.fullmatch(r'(?:[0-5]?[0-9])\s+(?:[01]?[0-9]|2[0-3])\s+\*\s+\*\s+\*\s+/usr/sbin/aide\s+--check',s) for s in lines(p)):
            return True
        for p in files('/etc/cron.daily/*'):
            if os.path.isfile(path(p)) and os.stat(path(p)).st_mode & 0o111:
                if any(re.fullmatch(r'/usr/sbin/aide\s+--check',s) for s in lines(p)):
                    return True
        return False
    if n in (38,39):
        efi = [s.split() for s in lines('/etc/fstab') if len(s.split()) >= 4 and s.split()[1] == '/boot/efi']
        if efi:
            opts = efi[-1][3].split(',')
            return all(k in opts for k in ('uid=0','gid=0')) if n == 38 else 'fmask=0177' in opts
        ps = ['/boot/grub2/grub.cfg','/boot/grub2/grubenv']
        if os.path.exists(path('/boot/grub2/user.cfg')):
            ps.append('/boot/grub2/user.cfg')
        return all(meta(p,uid=0,gid=0) if n == 38 else meta(p,mode=0o600) for p in ps)
    if n == 40:
        return bool(values(['/boot/grub2/user.cfg'],'GRUB2_PASSWORD')) and all(re.fullmatch(r'grub\.pbkdf2\.sha512\.[1-9][0-9]*\.[0-9A-Fa-f]+\.[0-9A-Fa-f]+',v) for v in values(['/boot/grub2/user.cfg'],'GRUB2_PASSWORD'))
    if n == 41:
        return all(setting(['/usr/lib/systemd/system/'+s+'.service'],'ExecStart','-/usr/lib/systemd/systemd-sulogin-shell '+s) for s in ('rescue','emergency'))
    if n in (42,43,307):
        ps = (['/etc/sysctl.conf'] if os.path.exists(path('/etc/sysctl.conf')) else []) + files('/etc/sysctl.d/*.conf')
        key, val = {42:('fs.suid_dumpable',0),43:('kernel.randomize_va_space',2),307:('kernel.yama.ptrace_scope',1)}[n]
        v = values(ps,key)
        ok = bool(v) and all(int(x) == val for x in v)
        if n != 42:
            return ok
        limits = (['/etc/security/limits.conf'] if os.path.exists(path('/etc/security/limits.conf')) else []) + files('/etc/security/limits.d/*.conf')
        core = [s.split() for p in limits for s in lines(p) if re.match(r'^\*\s+hard\s+core\s+',s)]
        return ok and setting(ps,'kernel.core_pattern','|/bin/false') and bool(core) and all(len(s)==4 and int(s[3])==0 for s in core)
    if n == 44:
        v = lines('/etc/crypto-policies/config')
        return bool(v) and all(s.upper() in ('FUTURE','FIPS') for s in v)
    if 61 <= n <= 71:
        return scan(n)
    if n == 72:
        return all(s[1] != '' for s in records('/etc/shadow',9))
    if n in (73,74):
        ps = root_path()
        if any(not p.startswith('/') or '..' in p.split('/') or p == '.' for p in ps):
            return False
        return True if n == 73 else all(os.path.isdir(path(p)) and meta(p,mode=0o7755) for p in ps)
    if n in (75,76,77):
        p = {75:'/etc/passwd',76:'/etc/shadow',77:'/etc/group'}[n]
        return not any(s.startswith('+:') for s in read(p).splitlines())
    if n == 78:
        return [s[0] for s in records('/etc/passwd',7) if int(s[2]) == 0] == ['root']
    if 79 <= n <= 85:
        users = records('/etc/passwd',7)
        for u in users:
            excluded = r'^(root|halt|sync|shutdown)' if n >= 83 else r'^(halt|sync|shutdown)'
            if re.match(excluded,u[0]) or u[6].endswith(('/nologin','/false')):
                continue
            home = u[5]
            if not home.startswith('/') or not os.path.isdir(path(home)):
                return False
            if n == 79 and not meta(home,mode=0o700): return False
            if n == 80 and not meta(home,uid=int(u[2])): return False
            if n == 81 and not meta(home,gid=int(u[3])): return False
            if n == 82:
                for p in files(home.rstrip('/')+'/.[A-Za-z0-9]*'):
                    if not os.path.islink(path(p)) and os.path.isfile(path(p)) and os.stat(path(p)).st_mode & 0o022:
                        return False
            if n >= 83:
                p = home.rstrip('/') + '/' + {83:'.forward',84:'.netrc',85:'.rhosts'}[n]
                if not os.path.islink(path(p)) and os.path.isfile(path(p)):
                    return False
        return True
    if n == 86:
        groups = {int(s[2]) for s in records('/etc/group',4)}
        return all(int(s[3]) in groups for s in records('/etc/passwd',7))
    if n in (87,88,89,90):
        p, size, col = {87:('/etc/passwd',7,2),88:('/etc/group',4,2),89:('/etc/passwd',7,0),90:('/etc/group',4,0)}[n]
        v = [int(s[col]) if col == 2 else s[col] for s in records(p,size)]
        return len(v) == len(set(v))
    if n == 91:
        groups = [s for s in records('/etc/group',4) if s[0] == 'shadow']
        return len(groups)==1 and groups[0][3]=='' and all(int(s[3]) != int(groups[0][2]) for s in records('/etc/passwd',7))
    if n in (303,304):
        for p in ('/etc/security/opasswd','/etc/security/opasswd.old'):
            try:
                ok = meta(p,uid=0,gid=0) if n == 303 else meta(p,mode=0o644)
            except FileNotFoundError:
                continue
            if not ok:
                return False
        return True
    if n == 305:
        return not any(s.endswith('/nologin') for s in lines('/etc/shells'))
    if n == 306:
        v = values(['/etc/sysconfig/chronyd'],'OPTIONS')
        if not v: return False
        for s in v:
            outer = shlex.split(s)
            if len(outer) != 1: return False
            args = shlex.split(outer[0])
            if '-uroot' in args: return False
            for i, arg in enumerate(args):
                if arg == '-u' and (i+1 == len(args) or args[i+1] == 'root'): return False
                if arg == '-F' and (i+1 == len(args) or args[i+1] != '2'): return False
            if not any(args[i:i+2] == ['-F','2'] for i in range(len(args))): return False
        return True
    raise ValueError('unknown candidate')
