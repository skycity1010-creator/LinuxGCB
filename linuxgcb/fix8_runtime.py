"""0244: absent or disabled services must also be inactive."""
def disabled_service(service):
    result = subprocess.run(['/usr/bin/systemctl', 'is-enabled', service],
                            capture_output=True, text=True, timeout=8,
                            env=dict(os.environ, LC_ALL='C'))
    value, error = result.stdout.strip(), result.stderr.strip()
    if not error and (value, result.returncode) in {('disabled', 1), ('masked', 1)}:
        return True
    if result.returncode not in (1, 4):
        return False
    if not error and value == 'not-found':
        return True
    diagnostic = ('Failed to get unit file state for ' + service +
                  '.service: No such file or directory')
    return not value and error == diagnostic


def check(n):
    if n != 244:
        return False
    for service in ('iptables', 'ip6tables'):
        if not disabled_service(service):
            return False
        if not observe(['/usr/bin/systemctl', 'is-active', service], {('inactive', 3)}):
            return False
    return True
