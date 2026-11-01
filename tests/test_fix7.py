from linuxgcb.batch9 import ADDED as BATCH9
from linuxgcb.batch10 import ADDED as BATCH10
"""Synthetic R18 regressions; execute emitted candidates on isolated trees."""
import json
import subprocess
import unittest
from linuxgcb.catalog import ROOT
import test_p2b8 as p2b8

BASELINE = '971fbc51601a08352ee80aadb15a23a68e4aab78'
AFFECTED = {8,9,13,14,15,16,23,24,25,73,74,91}


class Fix7Tests(unittest.TestCase):
    setUp = p2b8.P2B8Tests.setUp
    put = p2b8.P2B8Tests.put
    output = p2b8.P2B8Tests.output

    def tree(self):
        self.info = ('1 0 253:0 / / rw - xfs /dev/mapper/root rw\n'
                     '2 1 253:1 / /var rw - xfs /dev/mapper/var rw\n'
                     '3 1 253:2 / /home rw - xfs /dev/mapper/home rw\n'
                     '4 1 0:40 / /proc/sys/fs/binfmt_misc rw - autofs systemd-1 rw\n'
                     '5 4 0:41 / /proc/sys/fs/binfmt_misc rw - binfmt_misc binfmt_misc rw\n')
        self.put('/proc/self/mountinfo', self.info)
        self.put('/proc/mounts', '/dev/mapper/root / xfs rw 0 0\n'
                 '/dev/mapper/var /var xfs rw 0 0\n'
                 '/dev/mapper/home /home xfs rw 0 0\n'
                 'tmpfs /dev/shm tmpfs rw,nodev,nosuid 0 0\n')
        self.put('/etc/login.defs', 'UID_MIN 1000\n')
        self.put('/etc/passwd', 'alice:x:1000:1000::/home:/bin/bash\n')

    def test_r18_independent_lvs_and_real_missing_options(self):
        self.tree()
        for n in (8,15): self.assertEqual(self.output(n), 'PASS\n', n)
        for n in (9,13,14,16,19,23,24,25): self.assertEqual(self.output(n), '', n)
        self.put('/proc/mounts', '/dev/mapper/home /home xfs rw,nodev,nosuid,noexec 0 0\n')
        self.assertEqual(self.output(16), 'PASS\n')
        self.put('/proc/self/mountinfo', self.info.replace('/home rw -', '/home rw,nodev,nosuid,noexec -'))
        for n in (23,24,25): self.assertEqual(self.output(n), 'PASS\n', n)

    def test_related_stacks_fail_in_either_order_and_with_component_boundaries(self):
        for n,path in ((8,'/var'),(15,'/home'),(23,'/home'),(24,'/home'),(25,'/home')):
            for duplicate in (path, '/', path+'/nested'):
                for reverse in (False,True):
                    self.tree()
                    lines=self.info.splitlines()
                    record=f'9 1 253:9 / {duplicate} rw - xfs /dev/other rw'
                    if duplicate.endswith('/nested'):
                        lines.append(record)
                    lines.append(record)
                    self.put('/proc/self/mountinfo', '\n'.join(reversed(lines) if reverse else lines))
                    self.assertEqual(self.output(n), '', (n,duplicate,reverse))
        self.tree()
        self.put('/proc/self/mountinfo', self.info+'6 1 253:3 / /var/tmp rw - xfs /dev/tmp rw\n'
                 '7 1 253:4 / /var/tmp rw - xfs /dev/other rw\n')
        self.assertEqual(self.output(9), '')
        self.assertEqual(self.output(8), '')
        self.assertEqual(self.output(15), 'PASS\n')
        self.tree()
        self.put('/proc/self/mountinfo', self.info+'6 1 253:3 / /variable rw - xfs /dev/a rw\n'
                 '7 1 253:4 / /variable rw - xfs /dev/b rw\n')
        self.assertEqual(self.output(8), 'PASS\n')

    def test_partition_predicates_and_parse_errors_still_fail(self):
        for n,path in ((8,'/var'),(15,'/home')):
            for dev,root in (('253:0','/'),('253:9','/subdir'),('0:90','/')):
                self.tree()
                lines=[line for line in self.info.splitlines() if line.split()[4]!=path]
                lines.append(f'9 1 {dev} {root} {path} rw - xfs /dev/x rw')
                self.put('/proc/self/mountinfo','\n'.join(lines))
                self.assertEqual(self.output(n),'',(n,dev,root))
            for text in ('bad record', self.info.replace('1 0 253:0 / / rw - xfs /dev/mapper/root rw\n','')):
                self.put('/proc/self/mountinfo',text)
                self.assertEqual(self.output(n),'')

    def test_exact_nine_rules_and_protected_artifacts(self):
        old={}; new={}
        for p in (ROOT/'policies').glob('*.yml'):
            prior=json.loads(subprocess.check_output(['git','show',BASELINE+':policies/'+p.name],cwd=ROOT))
            current=json.loads(p.read_text())
            self.assertEqual(prior['policy'],current['policy'])
            old.update({c['id']:c for c in prior['checks']})
            new.update({c['id']:c for c in current['checks']})
        self.assertEqual(len(new),307)
        self.assertEqual({n-900000 for n in old if old[n]!=new[n]},AFFECTED | {32,282,283})
        for n in old: self.assertEqual(dict(new[n],rules=old[n]['rules']),old[n])
        for name in ('data/coverage_manifest.json','data/scope_registry.json'):
            prior=json.loads(subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT))
            current=json.loads((ROOT/name).read_text())
            if isinstance(prior,list):
                self.assertEqual([r for r in prior if r['sca_id']-900000 not in (BATCH9 | BATCH10)],[r for r in current if r['sca_id']-900000 not in (BATCH9 | BATCH10)])
            else:
                self.assertEqual(prior['reviewed'],[r for r in current['reviewed'] if r['sca_id']-900000 not in (BATCH9 | BATCH10)])
                for key,value in prior['counts'].items():
                    delta={'implemented':25,'added':25,'remaining':-25,'partial':25,'reviewed':25,'execution_blocked':25}.get(key,0)
                    self.assertEqual(current['counts'][key],value+delta)
        self.assertEqual(subprocess.check_output(['git','diff','21e56dbc1040ce26defdb972bf7e12a37de382d2','--name-only','--','tests/fixtures','docs/references','tests/fix5_baseline.json','docs/*TEST_OUTPUT*'],cwd=ROOT,text=True),'')
