"""Read-only P2B9 predicates; isolated tests replace ROOT and subprocess."""
import glob
import os
import re
import shutil
import subprocess
ROOT = ''
MODULES = {126:'dccp',127:'sctp',128:'rds',129:'tipc'}


def read(path):
    with open(ROOT+path, encoding='utf-8') as f:
        return f.read()


def lines(paths):
    for path in paths:
        with open(path, encoding='utf-8') as f:
            for line in f:
                text = re.split(r'[#;]', line, maxsplit=1)[0].strip()
                if text:
                    yield text


def module_ok(module):
    install = False
    blacklist = False
    for text in lines(sorted(glob.glob(ROOT+'/etc/modprobe.d/*.conf'))):
        fields = text.split()
        if len(fields) >= 2 and fields[1] == module:
            if fields[0] == 'install':
                if fields != ['install',module,'/bin/true']:
                    return False
                install = True
            if fields == ['blacklist',module]:
                blacklist = True
    return install and blacklist


def command(argv):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=8, check=False, env=dict(os.environ, LC_ALL='C'))
    if result.returncode or result.stderr or not result.stdout.strip():
        raise ValueError('unreliable command output')
    return result.stdout


def check(n, key=None):
    if n <= 125:
        paths = sorted(glob.glob(ROOT+'/etc/sysctl.d/*.conf'))
        if os.path.lexists(ROOT+'/etc/sysctl.conf'):
            paths.insert(0,ROOT+'/etc/sysctl.conf')
        if n in (119,120,121,123):
            for directory in ('/usr/lib/sysctl.d/','/run/sysctl.d/'):
                paths += sorted(glob.glob(ROOT+directory+'*.conf'))
        value = None
        pattern = re.compile(r'^'+re.escape(key)+r'\s*=\s*(.*?)\s*$')
        for text in lines(paths):
            match = pattern.fullmatch(text)
            if match:
                current = match[1]
                if not re.fullmatch(r'[0-9]+',current) or (value is not None and current != value):
                    return None
                value = current
        return value
    if n in MODULES:
        return 'PASS' if module_ok(MODULES[n]) else None
    if n == 130:
        nmcli = shutil.which('nmcli')
        if nmcli:
            output = command([nmcli,'-t','-f','WIFI,WWAN','radio','all']).strip()
            return 'PASS' if output == 'disabled:disabled' else None
        interfaces = sorted(glob.glob(ROOT+'/sys/class/net/*/wireless'))
        if not interfaces:
            return None
        for wireless in interfaces:
            link = os.path.dirname(wireless)+'/device/driver/module'
            if not os.path.islink(link) or not os.path.isdir(link):
                return None
            module = os.path.basename(os.path.realpath(link))
            if not module_ok(module):
                return None
        return 'PASS'
    if n == 131:
        output = command(['/usr/sbin/ip','link'])
        found = False
        for line in output.splitlines():
            if 'promisc' in line.lower():
                return None
            if re.match(r'^\d+:\s+\S+:\s+<[^>]*>', line):
                found = True
        return 'PASS' if found else None
    raise ValueError('unknown candidate')
