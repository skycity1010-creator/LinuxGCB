from linuxgcb.batch9 import ADDED as BATCH9
from linuxgcb.batch10 import ADDED as BATCH10
from linuxgcb.batch8 import ADDED as BATCH8
"""FIX6 synthetic R16 regressions; never inspect host account/security files."""
import contextlib
import io
import json
import os
import subprocess
import unittest
from unittest.mock import patch
import test_p2b7 as p2b7
from linuxgcb import batch7, p2b7_runtime as rt
from linuxgcb.catalog import ROOT
GOV=(('live_validation','execution_review','coverage','pending','source_approval','verified_on','verified_by','caveats','review_status'))
strip=lambda rows:[{k:v for k,v in r.items() if k not in GOV} for r in rows]

DISPLAY=('description','rationale','remediation')
def nod(d): return {k:v for k,v in d.items() if k not in DISPLAY}


class Fix6Tests(unittest.TestCase):
    setUp = p2b7.P2B7Tests.setUp
    put = p2b7.P2B7Tests.put
    tree = p2b7.P2B7Tests.tree
    owner_stat = p2b7.P2B7Tests.owner_stat

    def output(self, n):
        program = batch7.script(n).replace("ROOT = ''", 'ROOT = '+repr(self.tmp.name), 1)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            exec(program, {})
        return out.getvalue()

    def test_r16_service_shells_and_root_mode(self):
        self.tree()
        self.real_stat = os.stat
        accounts = rt.read('/etc/passwd')
        for shell in ('/sbin/nologin', '/usr/sbin/nologin', '/bin/false', '/usr/bin/false'):
            self.put('/etc/passwd', accounts+'\ntss:x:59:59::/:'+shell+
                     '\nclevis:x:990:990::/var/cache/clevis:'+shell)
            with patch.object(rt.os, 'stat', side_effect=self.owner_stat):
                for n in range(79,86):
                    self.assertEqual(self.output(n), 'PASS\n', (shell,n))
                os.chmod(self.tmp.name+'/root', 0o550)
                self.assertEqual(self.output(79), '')
                os.chmod(self.tmp.name+'/root', 0o700)
        self.put('/etc/passwd', accounts+'\ninteractive:x:999:999::/missing:/bin/bash')
        for n in range(79,86):
            self.assertEqual(self.output(n), '', n)

    def test_optional_files_modes_owners_and_errors(self):
        self.tree()
        self.real_stat = os.stat
        with patch.object(rt.os, 'stat', side_effect=self.owner_stat):
            os.unlink(self.tmp.name+'/etc/security/opasswd.old')
            for n in (303,304): self.assertEqual(self.output(n), 'PASS\n')
            for mode, want in ((0o600,True),(0o644,True),(0o664,False),(0o755,False),(0o1644,False)):
                os.chmod(self.tmp.name+'/etc/security/opasswd', mode)
                self.assertEqual(self.output(304), 'PASS\n' if want else '')
            os.unlink(self.tmp.name+'/etc/security/opasswd')
            for n in (303,304): self.assertEqual(self.output(n), 'PASS\n')
            self.put('/etc/security/opasswd.old', mode=0o664)
            self.assertEqual(self.output(304), '')
        for uid,gid in ((1,0),(0,1)):
            with patch.object(rt.os, 'stat', return_value=os.stat_result((0o100600,0,0,1,uid,gid,0,0,0,0))):
                self.assertEqual(self.output(303), '')
        with patch.object(rt.os, 'stat', side_effect=PermissionError):
            for n in (303,304): self.assertEqual(self.output(n), '')

    def test_exact_scope_and_metadata(self):
        old = {}; new = {}
        for p in (ROOT/'policies').glob('*.yml'):
            prior = json.loads(subprocess.check_output(['git','show','bc2cfbb:policies/'+p.name],cwd=ROOT))
            now = json.loads(p.read_text())
            self.assertEqual((lambda d:{k:v for k,v in d['policy'].items() if k not in ('name','description')})(prior), (lambda d:{k:v for k,v in d['policy'].items() if k not in ('name','description')})(now))  # FIX13 VERIFIED rename
            old.update({c['id']:c for c in prior['checks']})
            new.update({c['id']:c for c in now['checks']})
        changed = {900000+n for n in range(79,86)} | {900303,900304}
        self.assertEqual(len(new),307)
        self.assertEqual({n for n in old if old[n]['rules'] != new[n]['rules']},changed | {900032,900073,900074,900091,900282,900283})
        for n in old:
            actual = dict(new[n], rules=old[n]['rules'])
            self.assertEqual(nod(actual),nod(old[n]))
        for name in ('data/coverage_manifest.json','data/scope_registry.json'):
            prior = json.loads(subprocess.check_output(['git','show','bc2cfbb:'+name],cwd=ROOT))
            current = json.loads((ROOT/name).read_text())
            if isinstance(prior,list):
                current = [r for r in current if r['sca_id']-900000 not in BATCH8 | (BATCH9 | BATCH10)]
                prior = [r for r in prior if r['sca_id']-900000 not in BATCH8 | (BATCH9 | BATCH10)]
                self.assertEqual(strip(prior),strip(current))  # FIX13 GOV
            else:
                self.assertEqual(strip(prior['reviewed']),strip([r for r in current['reviewed'] if r['sca_id']-900000 not in BATCH8 | (BATCH9 | BATCH10)]))
