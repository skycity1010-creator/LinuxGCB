"""Offline R21 regressions using the emitted 900244 candidate."""
import json
import subprocess
import unittest
from linuxgcb.catalog import ROOT
import test_p2b10 as p2b10

DISPLAY=('description','rationale','remediation')
def nod(d): return {k:v for k,v in d.items() if k not in DISPLAY}

BASELINE = '7a8a3dbaccffe64ae4c99dc186d28a7de3da316f'


class Fix8Tests(unittest.TestCase):
    output = p2b10.P2B10Tests.output
    cp = p2b10.P2B10Tests.cp
    good = p2b10.P2B10Tests.good

    def test_disabled_masked_and_missing_require_inactive_for_both_services(self):
        for pos, service in ((0, 'iptables'), (2, 'ip6tables')):
            for state in (self.cp('disabled', 1), self.cp('masked', 1),
                          self.cp('not-found', 4), self.cp('not-found', 1),
                          self.cp('', 1, 'Failed to get unit file state for '+service+'.service: No such file or directory\n')):
                results = self.good()
                results[pos] = state
                self.assertEqual(self.output(244, results)[0], 'PASS\n')
                for active in (self.cp('active', 0), self.cp('inactive', 0), self.cp('failed', 3)):
                    results[pos+1] = active
                    self.assertEqual(self.output(244, results)[0], '')
        results = [self.cp('not-found', 4), self.cp('inactive', 3)] * 2
        self.assertEqual(self.output(244, results)[0], 'PASS\n')

    def test_enabled_and_unrecognized_errors_fail_closed(self):
        for pos in (0, 2):
            for state in (self.cp('enabled', 0), self.cp('not-found', 0),
                          self.cp('not-found', 127), self.cp('', 1, 'Permission denied'),
                          self.cp('disabled', 1, 'warning'),
                          self.cp('', 1, 'Failed to get unit file state: Permission denied'),
                          self.cp('', 1, 'No such file or directory'),
                          FileNotFoundError(), PermissionError(), subprocess.TimeoutExpired('mock', 8)):
                results = self.good()
                results[pos] = state
                self.assertEqual(self.output(244, results)[0], '')

    def test_only_900244_rules_change_and_protected_files_unchanged(self):
        old, new = {}, {}
        for path in (ROOT/'policies').glob('*.yml'):
            prior = json.loads(subprocess.check_output(['git', 'show', BASELINE+':policies/'+path.name], cwd=ROOT))
            current = json.loads(path.read_text())
            self.assertEqual(prior['policy'], current['policy'])
            self.assertEqual(prior['requirements'], current['requirements'])
            old.update({c['id']: c for c in prior['checks']})
            new.update({c['id']: c for c in current['checks']})
        self.assertEqual(len(new), 307)
        self.assertEqual(set(old), set(new))
        self.assertEqual({n for n in old if nod(old[n]) != nod(new[n])}, {900032,900244,900023,900024,900025,900073,900074,900091,900282,900283})
        self.assertEqual(nod(dict(new[900244], rules=old[900244]['rules'])), nod(old[900244]))
        protected = ['data/coverage_manifest.json', 'data/scope_registry.json', 'data/controls.json',
                     'docs/references', 'tests/fixtures', 'tests/fix5_baseline.json', 'docs/*TEST_OUTPUT*']
        self.assertEqual(subprocess.check_output(['git', 'diff', BASELINE, '--name-only', '--', *protected], cwd=ROOT, text=True), '')
