"""Read-only observations; no shell or service mutations."""
import os
import re
import subprocess


def observe(argv, states):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=8,
                            env=dict(os.environ, LC_ALL='C'))
    value = result.stdout.strip()
    return not result.stderr and (value, result.returncode) in states


def check(n):
    if n == 244:
        for service in ('iptables', 'ip6tables'):
            if not observe(['/usr/bin/systemctl', 'is-enabled', service], {('masked', 1)}):
                return False
            if not observe(['/usr/bin/systemctl', 'is-active', service], {('inactive', 3)}):
                return False
        return True
    if n == 246:
        result = subprocess.run(['/usr/bin/firewall-cmd', '--get-default-zone'],
                                capture_output=True, text=True, timeout=8,
                                env=dict(os.environ, LC_ALL='C'))
        return (result.returncode == 0 and not result.stderr and
                re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_-]*', result.stdout.strip()) is not None)
    return False
