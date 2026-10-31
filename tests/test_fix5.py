"""FIX5: offline scope protection and synthetic rpm exit/output regression."""
import json
import shlex
import subprocess
import unittest

from linuxgcb.argv import w_strtok
from linuxgcb.catalog import ROOT, digest
from linuxgcb.policy import parse_rule, simulate


class Fix5Tests(unittest.TestCase):
    def test_only_900188_rules_changed_and_evidence_preserved(self):
        before = json.loads((ROOT/'tests/fix5_baseline.json').read_text())
        old = {c['id']: c for c in before['checks']}
        current = {c['id']: c for p in (ROOT/'policies').glob('*.yml')
                   for c in json.loads(p.read_text())['checks']}
        self.assertEqual(len(current), 146)
        self.assertEqual(old.keys(), current.keys())
        self.assertEqual({n for n in old if old[n]['rules'] != current[n]['rules']}, {900188})
        for n in old:
            actual = dict(current[n])
            if n == 900188:
                actual['rules'] = old[n]['rules']
            self.assertEqual(actual, old[n])
        for name, sha in before['protected_hashes'].items():
            self.assertEqual(digest(ROOT/name), sha, name)
        for p in (ROOT/'policies').glob('*.yml'):
            self.assertIn('UNVALIDATED', json.loads(p.read_text())['policy']['name'])

    def test_exact_tristate_argv_and_buffered_large_output(self):
        check = next(c for c in json.loads((ROOT/'policies/linuxgcb_base.yml').read_text())['checks']
                     if c['id'] == 900188)
        body = ('out=$(rpm -q setroubleshoot 2>/dev/null); rc=$?; case $rc in '
                '0) echo INSTALLED;; 1) echo ABSENT;; *) exit $rc;; esac')
        self.assertEqual(check['rules'], ['c:/bin/sh -c "'+body+'" -> r:^ABSENT$'])
        target, _ = parse_rule(check['rules'][0])
        self.assertEqual(w_strtok(target[2:]), ['/bin/sh', '-c', body])
        prefix = 'out=$(rpm -q setroubleshoot 2>/dev/null)'
        # Replace the complete rpm query; execute only synthetic printf/exit.
        for rc in (0, 1, 2, 3, 126, 127):
            with self.subTest(rc=rc):
                payload = 'ABSENT\n'*500+'LINUXGCB_COMMAND_OK\n'
                fake = 'printf %s '+shlex.quote(payload)+'; exit '+str(rc)
                result = subprocess.run(['/bin/sh', '-c', 'out=$('+fake+')'+body[len(prefix):]],
                                        capture_output=True, text=True, timeout=5)
                expected = 'INSTALLED\n' if rc == 0 else 'ABSENT\n' if rc == 1 else ''
                self.assertEqual(result.stdout, expected)
                self.assertEqual(result.returncode, 0 if rc in (0, 1) else rc)
                self.assertEqual(simulate(check, {target: dict(stdout=result.stdout, exit_code=result.returncode)}),
                                 'PASS' if rc == 1 else 'FAIL')
