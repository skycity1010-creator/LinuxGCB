"""FIX9 emitted commands run only against temporary synthetic filesystems."""
import contextlib
import io
import json
import os
import subprocess
import unittest
from linuxgcb import batch7, batch8
from linuxgcb.argv import w_strtok
from linuxgcb.catalog import ROOT
import test_p2b8 as p2b8

BASELINE = '3fb7feaf51722dc03caf88ea4d7a2c28d96a1930'
AFFECTED = {900023,900024,900025,900073,900074,900091}


class Fix9Tests(unittest.TestCase):
    setUp = p2b8.P2B8Tests.setUp
    put = p2b8.P2B8Tests.put

    def output(self, n):
        batch = batch8 if n < 30 else batch7
        argv = w_strtok(batch.rules()[n][0][0][2:])
        self.assertEqual(argv[:2], ['/usr/bin/python3','-c'])
        self.assertEqual(len(argv), 3)
        self.assertNotIn('->', argv[2])
        self.assertEqual(argv[2].count("print('PASS')"), 1)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            exec(argv[2].replace("ROOT = ''", 'ROOT = '+repr(self.tmp.name), 1), {})
        return out.getvalue()

    def homes(self, options='rw'):
        self.put('/etc/login.defs', 'UID_MIN 1000\n')
        self.put('/etc/passwd', 'alice:x:1000:1000::/home/alice:/bin/bash\n')
        self.info = ('1 0 253:0 / / rw - xfs /dev/mapper/root rw\n'
                     f'2 1 253:1 / /home {options} - xfs /dev/mapper/home rw\n')
        self.put('/proc/self/mountinfo', self.info)

    def test_lv_longest_prefix_and_root_skip(self):
        self.homes()
        for n in (23,24,25): self.assertEqual(self.output(n), '')
        self.homes('rw,nodev,nosuid,noexec')
        for n in (23,24,25): self.assertEqual(self.output(n), 'PASS\n')
        self.put('/etc/passwd', 'alice:x:1000:1000::/home2/alice:/bin/bash\n')
        for n in (23,24,25): self.assertEqual(self.output(n), 'PASS\n')
        self.put('/etc/login.defs', 'UID_MIN 2000\n')
        self.put('/etc/passwd', 'alice:x:1000:1000::/home/alice:/bin/bash\n')
        for n in (23,24,25): self.assertEqual(self.output(n), 'PASS\n')

    def test_duplicate_last_pseudo_and_nested_mount(self):
        self.homes()
        self.put('/proc/self/mountinfo', self.info+'3 1 253:2 / /home rw,nodev,nosuid,noexec - xfs /dev/mapper/last rw\n')
        for n in (23,24,25): self.assertEqual(self.output(n), 'PASS\n')
        self.put('/proc/self/mountinfo', self.info+'3 1 0:4 / /home/alice rw - proc proc rw\n')
        for n in (23,24,25): self.assertEqual(self.output(n), 'PASS\n')
        self.put('/proc/self/mountinfo', self.info+'3 1 253:2 / /home/alice rw,nodev - xfs /dev/mapper/nested rw\n')
        self.assertEqual(self.output(23), 'PASS\n')
        self.assertEqual(self.output(24), '')

    def test_path_expansion_all_assignments_and_missing_directories(self):
        self.put('/root/.bashrc', 'PATH="$HOME/bin:${HOME}/sbin:$PATH:${PATH}"\n')
        self.assertEqual(self.output(73), 'PASS\n')
        self.assertEqual(self.output(74), 'PASS\n')
        for value in ('.:/bin','..:/bin','relative:/bin',':/bin','/bin:', '/bin::/sbin',''):
            self.put('/etc/profile.d/test.sh', 'PATH="'+value+'"\n')
            self.assertEqual(self.output(73), '', value)
        self.put('/etc/profile.d/test.sh', 'PATH="/missing"\n')
        self.put('/root/bin/file', '')
        os.chmod(self.tmp.name+'/root/bin', 0o755)
        self.assertEqual(self.output(74), 'PASS\n')
        for mode in (0o775,0o757):
            os.chmod(self.tmp.name+'/root/bin', mode)
            self.assertEqual(self.output(74), '')

    def test_shadow_absent_empty_members_and_primary_gid(self):
        self.put('/etc/group', 'root:x:0:\n')
        self.assertEqual(self.output(91), 'PASS\n')
        self.put('/etc/passwd', 'alice:x:1000:1000::/home/alice:/bin/bash\n')
        self.put('/etc/group', 'shadow:x:42:\n')
        self.assertEqual(self.output(91), 'PASS\n')
        self.put('/etc/group', 'shadow:x:42:alice\n')
        self.assertEqual(self.output(91), '')
        self.put('/etc/group', 'shadow:x:1000:\n')
        self.assertEqual(self.output(91), '')

    def test_exact_six_rules_and_protected_artifacts(self):
        old, new = {}, {}
        for p in (ROOT/'policies').glob('*.yml'):
            prior = json.loads(subprocess.check_output(['git','show',BASELINE+':policies/'+p.name],cwd=ROOT))
            current = json.loads(p.read_text())
            self.assertEqual(prior['policy'], current['policy'])
            self.assertEqual(prior['requirements'], current['requirements'])
            old.update({c['id']:c for c in prior['checks']})
            new.update({c['id']:c for c in current['checks']})
        self.assertEqual(len(new),307)
        self.assertEqual(set(old),set(new))
        self.assertEqual({n for n in old if old[n] != new[n]}, AFFECTED | {900032,900282,900283})
        for n in old: self.assertEqual(dict(new[n],rules=old[n]['rules']),old[n])
        protected = ['data/coverage_manifest.json','data/scope_registry.json','data/controls.json','data/inventory.json','docs/references','tests/fixtures','tests/fix5_baseline.json','docs/*TEST_OUTPUT*']
        self.assertEqual(subprocess.check_output(['git','diff',BASELINE,'--name-only','--',*protected],cwd=ROOT,text=True),'')
