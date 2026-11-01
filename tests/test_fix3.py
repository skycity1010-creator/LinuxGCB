"""Offline FIX3 regressions; execute only synthetic shell builtins."""
import json
import shlex
import subprocess
import unittest
from unittest.mock import patch

from linuxgcb.argv import w_strtok
from linuxgcb.batch2 import ABSENT_PACKAGES, MARKER, guarded
from linuxgcb.catalog import ROOT, digest
from linuxgcb.policy import parse_rule, simulate

CHANGED = {900000+n for n in ABSENT_PACKAGES if n != 188} | {900205}


class Fix3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checks = {c['id']: c for p in (ROOT/'policies').glob('*.yml')
                      for c in json.loads(p.read_text())['checks']}
        cls.before = json.loads((ROOT/'tests/fixtures/fix3_baseline.json').read_text())

    def test_exact_seven_rules_changed_and_ninety_checks_untouched(self):
        before = {c['id']: c for c in self.before['checks']}
        self.assertEqual(len(before), 97)
        self.assertTrue(before.keys() <= self.checks.keys())
        self.assertEqual({n for n in before if before[n]['rules'] != self.checks[n]['rules']}, CHANGED | {900188,900282,900283})
        for n, check in before.items():
            actual = dict(self.checks[n])
            if n in CHANGED | {900188,900282,900283}:
                actual['rules'] = check['rules']
            self.assertEqual(actual, check)
        for name, sha in self.before['protected_hashes'].items():
            self.assertEqual(digest(ROOT/name), sha, name)

    def test_engine_output_boundary_and_old_marker_failure(self):
        # Preserve the historical 900188 guard solely in the test allowlist.
        from linuxgcb.policy import batch2_emitted
        legacy = next(c for c in self.before['checks'] if c['id'] == 900188)
        allowlist = batch2_emitted() | set(legacy['rules'])
        patcher = patch('linuxgcb.policy.batch2_emitted', return_value=allowlist)
        patcher.start()
        self.addCleanup(patcher.stop)
        old = next(c for c in self.before['checks'] if c['id'] == 900188)
        target = parse_rule(old['rules'][0])[0]
        for count, want in ((255, 'PASS'), (256, 'FAIL'), (500, 'FAIL')):
            output = '\n'.join(['bash']*count+[MARKER])
            self.assertEqual(simulate(old, {target:dict(stdout=output)}), want)
        # Historical rules are test-only allowlisted to exercise the real matcher.
        historical = [c for c in self.before['checks'] if c['id'] in CHANGED-{900205}]
        with patch('linuxgcb.policy.batch2_emitted', return_value={r for c in historical for r in c['rules']}):
            for check in historical:
                target = parse_rule(check['rules'][0])[0]
                self.assertEqual(simulate(check, {target:dict(stdout='bash\n'*500+MARKER)}), 'FAIL')
        for n in ABSENT_PACKAGES:
            check = self.checks[900000+n]
            self.assertEqual(len(check['rules']), 1)
            target, _ = parse_rule(check['rules'][0])
            self.assertEqual(simulate(check, {target:dict(stdout='ABSENT\n')}), 'PASS')
        # Negated predicates also see only the first 256 lines.
        target = parse_rule(old['rules'][0])[0]
        self.assertEqual(simulate(old, {target:dict(stdout=MARKER+'\n'+'bash\n'*255+'setroubleshoot')}), 'PASS')

    def test_each_package_tristate_and_argv_without_running_rpm(self):
        for n, package in ABSENT_PACKAGES.items():
            check = self.checks[900000+n]
            target, _ = parse_rule(check['rules'][0])
            argv = w_strtok(target[2:])
            self.assertEqual(argv[:2], ['/bin/sh', '-c'])
            self.assertEqual(len(argv), 3)
            prefix = 'out=$(rpm -q '+package+' 2>/dev/null)'
            self.assertTrue(argv[2].startswith(prefix))
            for rc in (0, 1, 2, 3, 126, 127):
                # Malicious-looking matching data must never escape buffering.
                fake = 'printf %s '+shlex.quote('ABSENT\n'+MARKER+'\n'*500)+'; exit '+str(rc)
                script = 'out=$('+fake+')'+argv[2][len(prefix):]
                result = subprocess.run(['/bin/sh','-c',script], capture_output=True, text=True, timeout=5)
                expected = 'INSTALLED\n' if rc == 0 else 'ABSENT\n' if rc == 1 else ''
                self.assertEqual(result.stdout, expected)
                self.assertEqual(result.returncode, 0 if rc in (0,1) else rc)
                self.assertEqual(simulate(check, {target:dict(stdout=result.stdout)}), 'PASS' if rc == 1 else 'FAIL')

    def test_cron_legacy_and_action_and_rejections(self):
        check = self.checks[900205]
        target, _ = parse_rule(check['rules'][0])
        for line in ('cron.* /var/log/cron', 'cron.* action(type="omfile" file="/var/log/cron")',
                     '\tcron.*\taction(type="omfile"\tfile="/var/log/cron") '):
            self.assertEqual(simulate(check, {target:dict(stdout=line+'\n'+MARKER)}), 'PASS', line)
        for line in ('#cron.* /var/log/cron', 'cron.none /var/log/cron',
                     'cron.* action(type="omfwd" file="/var/log/cron")',
                     'cron.* action(type="omfile" file="/var/log/other")',
                     'cron.* action(type="omfile" file="/var/log/cron")junk'):
            self.assertEqual(simulate(check, {target:dict(stdout=line+'\n'+MARKER)}), 'FAIL', line)
        self.assertEqual(simulate(check, {target:dict(stdout='cron.* /var/log/cron')}), 'FAIL')
