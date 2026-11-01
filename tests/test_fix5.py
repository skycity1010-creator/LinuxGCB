from linuxgcb.batch9 import ADDED as BATCH9
from linuxgcb.batch10 import ADDED as BATCH10
from linuxgcb.batch8 import ADDED as BATCH8
from linuxgcb.batch7 import ADDED as BATCH7
"""FIX5: offline scope protection and synthetic rpm exit/output regression."""
import json
import hashlib
import shlex
import subprocess
import unittest

from linuxgcb.batch6 import ADDED as BATCH6
from linuxgcb.argv import w_strtok
from linuxgcb.catalog import ROOT, digest
from linuxgcb.policy import parse_rule, simulate

DISPLAY=('description','rationale','remediation')
def nod(d): return {k:v for k,v in d.items() if k not in DISPLAY}


class Fix5Tests(unittest.TestCase):
    def test_only_900188_rules_changed_and_evidence_preserved(self):
        before = json.loads((ROOT/'tests/fix5_baseline.json').read_text())
        old = {c['id']: c for c in before['checks']}
        current = {c['id']: c for p in (ROOT/'policies').glob('*.yml')
                   for c in json.loads(p.read_text())['checks']}
        self.assertEqual(len(current), 307)
        current = {n:c for n,c in current.items() if n in old}
        self.assertEqual(old.keys(), current.keys())
        changed = {n for n in old if old[n]['rules'] != current[n]['rules']}
        # FIX5: 900188 rpm tri-state. FIX11: 900282/900283 find pseudo-FS prune (flake fix).
        self.assertEqual(changed, {900188, 900282, 900283})
        for n in old:
            actual = dict(current[n])
            if n in changed:
                actual['rules'] = old[n]['rules']
            self.assertEqual(nod(actual), nod(old[n]))
        for name, sha in before['protected_hashes'].items():
            if name in ('data/scope_registry.json', 'data/coverage_manifest.json'):
                original = subprocess.check_output(['git', 'show', 'd2bd3ae:'+name], cwd=ROOT)
                self.assertEqual(hashlib.sha256(original).hexdigest(), sha, name)
                prior = json.loads(original)
                now = json.loads((ROOT/name).read_text())
                if name.endswith('scope_registry.json'):
                    self.assertEqual([r for r in prior if r['sca_id']-900000 not in BATCH6 | BATCH7 | BATCH8 | (BATCH9 | BATCH10)],
                                     [r for r in now if r['sca_id']-900000 not in BATCH6 | BATCH7 | BATCH8 | (BATCH9 | BATCH10)])
                else:
                    self.assertEqual(prior['reviewed'], [r for r in now['reviewed'] if r['sca_id']-900000 not in BATCH6 | BATCH7 | BATCH8 | (BATCH9 | BATCH10)])
            else:
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
