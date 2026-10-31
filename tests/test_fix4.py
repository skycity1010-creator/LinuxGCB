from linuxgcb.batch8 import ADDED as BATCH8
from linuxgcb.batch7 import ADDED as BATCH7
"""FIX4 offline regressions using only synthetic file trees."""
from linuxgcb.batch6 import ADDED as BATCH6
import copy
import json
import unittest
import test_p2b3 as p2b3
from linuxgcb.catalog import ROOT, digest
from linuxgcb.policy import parse_rule, simulate

CHANGED = {900143, 900144, 900176}


class Fix4Tests(unittest.TestCase):
    tree = p2b3.P2B3Tests.tree
    run_tree = p2b3.P2B3Tests.run_tree

    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT/'tests/fixtures/p2b3/cases.json').read_text())
        cls.checks = {c['id']: c for p in (ROOT/'policies').glob('*.yml')
                      for c in json.loads(p.read_text())['checks']}

    def assert_result(self, n, data, want):
        output = self.run_tree(n, data)
        self.assertEqual(output, 'PASS\n' if want == 'PASS' else '')
        check = self.checks[900000+n]
        target, _ = parse_rule(check['rules'][0])
        self.assertEqual(simulate(check, {target: dict(stdout=output)}), want)

    def test_exact_three_rules_changed_and_protected_evidence(self):
        before = json.loads((ROOT/'tests/fixtures/fix4_baseline.json').read_text())
        old = {c['id']: c for c in before['checks']}
        self.assertEqual(len(old), 146)
        self.assertEqual(set(old), set(self.checks) - {900000+n for n in BATCH6 | BATCH7 | BATCH8})
        self.assertEqual({n for n in old if old[n]['rules'] != self.checks[n]['rules']}, CHANGED | {900188})
        for n in old.keys() - CHANGED - {900188}:
            self.assertEqual(old[n], self.checks[n])
        for name, sha in before['protected_hashes'].items():
            self.assertEqual(digest(ROOT/name), sha, name)

    def test_imuxsock_and_omfile_matrix(self):
        module = 'module(load="imuxsock" SysSock.Use="off" FileCreateMode="0644")\n'
        cases = [
            (module + '$FileCreateMode 0640\n', 'PASS'),
            (module, 'FAIL'),
            (module + '$FileCreateMode 0640\naction(type="omfile" fileCreateMode="0666")', 'FAIL'),
            ('action(type="omfile" fileCreateMode="0640")', 'PASS'),
            ('action(type="omfwd" fileCreateMode="0640")', 'FAIL'),
            ('module(load="omfile" fileCreateMode="0640")', 'FAIL'),
            ('module(load="imuxsock" action(foo) omfile FileCreateMode="0666")\n$FileCreateMode 0640', 'PASS'),
            (module + '$FileCreateMode 9999', 'FAIL'),
        ]
        for text, want in cases:
            with self.subTest(text=text):
                data = self.tree(176)
                data['files']['/etc/rsyslog.conf'] = text
                self.assert_result(176, data, want)

    def test_existing_tools_keep_mode_and_owner_requirements(self):
        for n in (143, 144):
            all_tools = self.tree(n)
            self.assertEqual(len(all_tools['files']), 9)
            seven = copy.deepcopy(all_tools)
            for path in ('/sbin/audisp-remote', '/sbin/audisp-syslog'):
                for field in ('files', 'modes', 'owners'):
                    del seven[field][path]
            self.assertEqual(len(seven['files']), 7)
            for base in (all_tools, seven):
                with self.subTest(n=n, count=len(base['files'])):
                    self.assert_result(n, base, 'PASS')
                    for path in base['files']:
                        bad = copy.deepcopy(base)
                        if n == 143:
                            bad['modes'][path] = 0o755
                            self.assert_result(n, bad, 'FAIL')
                        else:
                            for owner in ([1001, 0], [0, 1001]):
                                bad['owners'][path] = owner
                                self.assert_result(n, bad, 'FAIL')
                    denied = copy.deepcopy(base)
                    denied['stat_error'] = '/sbin/auditctl'
                    self.assert_result(n, denied, 'FAIL')
