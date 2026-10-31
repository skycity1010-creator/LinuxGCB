"""FIX2 regression: execute only synthetic printf/exit, never inventory commands."""
import json
import shlex
import subprocess
import unittest

from linuxgcb.argv import quote_argument, w_strtok
from linuxgcb.batch2 import ADDED, MARKER, guarded, specs
from linuxgcb.catalog import ROOT
from linuxgcb.policy import simulate


class Fix2Tests(unittest.TestCase):
    def test_tokenizer_contract(self):
        self.assertEqual(w_strtok('a "b c" d\\ e'), ['a', 'b c', 'd e'])
        self.assertEqual(w_strtok("a 'b c'"), ['a', "'b", "c'"])
        self.assertEqual(w_strtok(r'a "b\"c\\d"'), ['a', 'b"c\\d'])
        for value in ('', 'a b', "'%s\\n'", '$out; "x"'):
            self.assertEqual(w_strtok(quote_argument(value)), [value])

    def test_all_44_old_commands_fail_and_new_preserve_semantics(self):
        checks = {c['id']: c for p in (ROOT/'policies').glob('*.yml')
                  for c in json.loads(p.read_text())['checks']}
        seen = set()
        for n, items in specs().items():
            check = checks[900000+n]
            for command, pattern, good, bad in items:
                old_script = ('out=$('+command+'); rc=$?; if [ "$rc" -eq 0 ]; then '
                              'printf "%s\\n" "$out" "'+MARKER+'"; else exit "$rc"; fi')
                old_argv = w_strtok('/bin/sh -c '+shlex.quote(old_script))
                self.assertGreater(len(old_argv), 3)
                # -n parses without running any source command, even if a regression
                # unexpectedly makes the old script syntactically valid.
                old = subprocess.run([old_argv[0], '-n', *old_argv[1:]],
                                     capture_output=True, text=True, timeout=5)
                self.assertNotEqual(old.returncode, 0)
                empty = {r.split(' -> ', 1)[0].removeprefix('not '):
                         dict(stdout=old.stdout, exit_code=old.returncode) for r in check['rules']}
                self.assertEqual(simulate(check, empty), 'FAIL')
                argv = w_strtok(guarded(command)[2:])
                self.assertEqual(len(argv), 3)
                self.assertEqual(argv[:2], ['/bin/sh', '-c'])
                self.assertTrue(argv[2].startswith('out=$('+command+');'))
                # Compare shell semantics independently to the former intended script.
                for payload in (good, bad):
                    fake = 'printf %s '+shlex.quote(payload)
                    prefix = 'out=$('+command+')'
                    outputs = []
                    for script in (old_script, argv[2]):
                        result = subprocess.run(['/bin/sh', '-c', 'out=$('+fake+')'+script[len(prefix):]],
                                                capture_output=True, text=True, timeout=5)
                        outputs.append((result.returncode, result.stdout))
                    self.assertEqual(outputs[0], outputs[1])
                seen.add(n)
        self.assertEqual(seen, ADDED)
