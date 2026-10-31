"""Read-only routines embedded in P2B3 commands; no endpoint helper installation.

Build imports this module but never invokes its readers. Tests redirect ROOT to
an isolated test-only tree before executing any reader.
"""
import glob
import os
import re
import stat
import subprocess

ROOT = ''


def read(path):
    with open(ROOT + path, encoding='utf-8') as stream:
        return stream.read()


def files(pattern):
    parent = os.path.dirname(ROOT + pattern)
    try:
        os.stat(parent)
    except FileNotFoundError:
        return []
    with os.scandir(parent) as entries:
        list(entries)
    return sorted(p[len(ROOT):] for p in glob.glob(ROOT + pattern))


def active(text):
    return [line.strip() for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith(('#', ';'))]


def setting(text, key, section=None):
    value = None
    current = None
    for line in active(text):
        if line.startswith('['):
            current = line
        elif '=' in line and (section is None or current == '[' + section + ']'):
            name, content = line.split('=', 1)
            if name.strip().lower() == key.lower():
                value = content.split('#', 1)[0].strip()
    return value


def metadata(path, mask=None, directory=False):
    info = os.stat(ROOT + path)
    if directory and not stat.S_ISDIR(info.st_mode):
        return False
    return ((info.st_uid == 0 and info.st_gid == 0) if mask is None
            else stat.S_IMODE(info.st_mode) & ~mask == 0)


def audit_matches(path, required):
    lines = active(read(path))
    for item in required:
        pattern = r'\s*' + r'\s+'.join(re.escape(t) for t in item.split()) + r'\s*'
        if not any(re.fullmatch(pattern, line) for line in lines):
            return False
    return True


def uid_min():
    values = [line.split()[1] for line in active(read('/etc/login.defs'))
              if line.split()[0] == 'UID_MIN']
    if not values or not values[-1].isdigit():
        raise ValueError('UID_MIN unresolved')
    return str(int(values[-1]))


def audit_rules(required):
    if any('auid>=1000' in line for line in required):
        required = [line.replace('auid>=1000', 'auid>=' + uid_min()) for line in required]
    return audit_matches('/etc/audit/rules.d/audit.rules', required)


def log_metadata(mask=None, directory=False):
    path = setting(read('/etc/audit/auditd.conf'), 'log_file')
    if not path or not path.startswith('/'):
        return False
    if directory:
        path = os.path.dirname(path)
    return metadata(path, mask, directory)


def service(unit):
    result = subprocess.run(['/usr/bin/systemctl', 'show', unit,
                             '--property=LoadState', '--property=ActiveState',
                             '--property=UnitFileState'], capture_output=True, text=True)
    if result.returncode:
        raise ValueError('systemctl failed')
    props = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    # Source asks to disable; explicit not-found + inactive is also disabled.
    return (props.get('ActiveState') == 'inactive' and
            (props.get('LoadState') == 'not-found' or
             (props.get('LoadState') in ('loaded', 'masked') and
              props.get('UnitFileState') in ('disabled', 'masked'))))


def package_state(package):
    command = 'out=$(rpm -q ' + package + ' 2>/dev/null); rc=$?; case $rc in 0) echo INSTALLED;; 1) echo ABSENT;; *) exit $rc;; esac'
    result = subprocess.run(['/bin/sh', '-c', command], capture_output=True, text=True)
    if result.returncode or result.stdout.strip() not in ('INSTALLED', 'ABSENT'):
        raise ValueError('rpm failed')
    return result.stdout.strip()


def optional_service(package, unit, snmp=False):
    state = package_state(package)
    if service(unit):
        return True
    if state == 'ABSENT' or not snmp:
        return False
    lines = active(read('/etc/snmp/snmpd.conf'))
    # A conservative, explicit authPriv-only subset of the source's v3 branch.
    forbidden = ('com2sec', 'com2sec6', 'group', 'view', 'access', 'rocommunity',
                 'rwcommunity', 'rocommunity6', 'rwcommunity6', 'includeFile',
                 'includeDir', 'includefile', 'includedir', 'rwuser')
    if any(line.split()[0] in forbidden for line in lines):
        return False
    users = [line for line in lines if line.split()[0] == 'rouser']
    return bool(users) and all(re.fullmatch(r'rouser\s+\S+\s+priv(?:\s+\S+)?', line,
                                          re.I) for line in users)


def rsyslog_text():
    return '\n'.join(read(path) for path in ['/etc/rsyslog.conf'] + files('/etc/rsyslog.d/*.conf'))


def rsyslog_mode():
    text = '\n'.join(active(rsyslog_text()))
    declarations = [line for line in text.splitlines() if re.match(r'^\$FileCreateMode(?:\s|$)', line)]
    if any(not re.fullmatch(r'\$FileCreateMode\s+0?[0-7]{3}\s*', line) for line in declarations):
        return False
    modes = [line.split()[1] for line in declarations]
    overrides = re.findall(r'fileCreateMode\s*=\s*"([^"]*)"', text, re.I)
    return (bool(modes or overrides) and
            all(re.fullmatch(r'0?[0-7]{3}', value) and int(value, 8) & ~0o640 == 0
                for value in modes + overrides))


def rsyslog_rules():
    lines = active(rsyslog_text())
    # Accept source comma notation and conventional semicolon selector separators.
    for facility in ('auth', 'authpriv', 'daemon'):
        selector = r'(?:auth|authpriv|daemon)\.\*'
        selectors = selector + r'(?:\s*[,;]\s*' + selector + r')*'
        destination = r'(?:-?/var/log/secure|action\(\s*type="omfile"\s+file="/var/log/secure"\s*\))'
        if not any(re.fullmatch(selectors + r'\s+' + destination, line) and
                   re.search(r'(?:^|[,;])\s*' + facility + r'\.\*(?:\s*[,;]|\s+)', line)
                   for line in lines):
            return False
    return True


def journal(key, expected):
    # /etc drop-ins take priority over equal basenames in /run and vendor dirs.
    paths = {}
    for folder in ('/usr/lib', '/usr/local/lib', '/run', '/etc'):
        for path in files(folder + '/systemd/journald.conf.d/*.conf'):
            paths[os.path.basename(path)] = path
    text = read('/etc/systemd/journald.conf')
    value = setting(text, key, 'Journal')
    for name in sorted(paths):
        path = paths[name]
        if os.path.islink(ROOT + path) and os.readlink(ROOT + path) == '/dev/null':
            continue
        override = setting(read(path), key, 'Journal')
        if override is not None:
            value = override
    return value == expected


def grub(key, minimum):
    values = {}
    for line in active(read('/etc/default/grub')):
        match = re.fullmatch(r'(GRUB_CMDLINE_LINUX(?:_DEFAULT)?)\s*=\s*([\'"])(.*?)\2', line)
        if match:
            values[match[1]] = match[3].split()
    if 'GRUB_CMDLINE_LINUX' not in values:
        return False
    options = [word.split('=', 1)[1] for word in values['GRUB_CMDLINE_LINUX'] if word.startswith(key + '=')]
    if not options:
        return False
    options += [word.split('=', 1)[1] for word in values.get('GRUB_CMDLINE_LINUX_DEFAULT', []) if word.startswith(key + '=')]
    return all(value.isdigit() and (int(value) == 1 if key == 'audit' else int(value) >= minimum) for value in options)


def sudo_log():
    paths = ['/etc/sudoers'] + files('/etc/sudoers.d/*')
    logs = set()
    for path in paths:
        text = read(path)
        for raw in text.splitlines():
            include = re.match(r'\s*(?:#|@)include(dir)?\s+(.+)', raw)
            if include and not (include[1] == 'dir' and include[2].strip() == '/etc/sudoers.d'):
                return False
        for line in active(text):
            if line.startswith('Defaults'):
                if re.search(r'!logfile\b', line):
                    return False
                values = re.findall(r"\blogfile\s*=\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s,]+))", line)
                for parts in values:
                    value = next(part for part in parts if part)
                    if not value.startswith('/') or any(char.isspace() for char in value):
                        return False
                    logs.add(value)
    return bool(logs) and all(audit_matches('/etc/audit/rules.d/actions.rules',
                                          ['-w ' + path + ' -p wa -k actions']) for path in logs)


def privileged():
    # Traverse each mounted real filesystem separately, preserving find -xdev.
    pseudo = {'proc', 'sysfs', 'devtmpfs', 'devpts', 'cgroup', 'cgroup2', 'securityfs',
              'debugfs', 'tracefs', 'configfs', 'pstore', 'mqueue', 'hugetlbfs',
              'fusectl', 'autofs', 'binfmt_misc', 'rpc_pipefs'}
    mounts = set()
    for line in read('/proc/self/mountinfo').splitlines():
        left, right = line.split(' - ', 1)
        if right.split()[0] not in pseudo:
            mount = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), left.split()[4])
            mounts.add(mount)
    if not mounts:
        return False
    required = set()
    def fail(error):
        raise error
    for mount in sorted(mounts):
        device = os.stat(ROOT + mount).st_dev
        for folder, dirs, names in os.walk(ROOT + mount, onerror=fail, followlinks=False):
            dirs[:] = [name for name in dirs if not os.path.islink(folder + '/' + name)
                       and os.stat(folder + '/' + name).st_dev == device
                       and (folder + '/' + name)[len(ROOT):] not in mounts]
            for name in names:
                path = folder + '/' + name
                info = os.lstat(path)
                if stat.S_ISREG(info.st_mode) and info.st_mode & 0o6000:
                    required.add('-a always,exit -F path=' + path[len(ROOT):] +
                                 ' -F perm=x -F auid>=' + uid_min() +
                                 ' -F auid!=4294967295 -k privileged')
    return audit_matches('/etc/audit/rules.d/privileged.rules', sorted(required))


def immutable():
    paths = sorted(files('/etc/audit/rules.d/*.rules'),
                   key=lambda path: [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', path)])
    lines = [line for path in paths for line in active(read(path))]
    controls = [line for line in lines if re.match(r'-e(?:\s|$)', line)]
    return (bool(controls) and controls[-1] == '-e 2' and
            '--loginuid-immutable' in lines and lines[-1] in ('-e 2', '--loginuid-immutable'))


def logrotate():
    text = '\n'.join(active(read('/etc/logrotate.d/rsyslog')))
    match = re.fullmatch(r'/var/log/rsyslog/\*\.log\s*\{(.*?)\}', text, re.S)
    if not match:
        return False
    lines = active(match[1])
    required = {'weekly', 'rotate 4', 'compress', 'missingok', 'notifempty', 'endscript'}
    return (required.issubset(set(lines)) and
            any(re.fullmatch(r'postrotate\s+/usr/bin/systemctl reload rsyslog.service\s*>/dev/null\s*\|\|\s*true', line)
                for line in lines) and metadata('/var/log/rsyslog', 0o750, True))
