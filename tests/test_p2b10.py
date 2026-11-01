"""Synthetic source, argv, subprocess and unchanged baseline checks."""
import contextlib
import io
import json
import subprocess
import unittest
from unittest.mock import patch
from linuxgcb import batch10 as b
from linuxgcb.argv import w_strtok
from linuxgcb.catalog import ROOT
from linuxgcb.coverage import manifest
from linuxgcb.policy import simulate


class P2B10Tests(unittest.TestCase):
    def output(self, n, results):
        with patch('subprocess.run', side_effect=results) as run, contextlib.redirect_stdout(io.StringIO()) as out:
            exec(w_strtok(b.rules()[n][0][0][2:])[2], {})
        for call in run.call_args_list:
            self.assertNotIn('shell', call.kwargs)
            self.assertEqual(call.kwargs['timeout'], 8)
            self.assertEqual(call.kwargs['env']['LC_ALL'], 'C')
        return out.getvalue(), run

    def cp(self, value, rc=0, err=''):
        return subprocess.CompletedProcess([], rc, value, err)

    def good(self):
        return [self.cp('masked\n',1), self.cp('inactive\n',3)] * 2

    def test_source_and_argv(self):
        self.assertEqual(set(b.sources()), {244,246})
        self.assertIn('#systemctl --now mask ip6tables', b.sources()[244]['configuration_method'])
        self.assertIn('--set-default-zone=public', b.sources()[246]['configuration_method'])
        checks={c['id']:c for c in json.loads((ROOT/'policies/linuxgcb_firewalld.yml').read_text())['checks']}
        for n in b.ADDED:
            target, pattern=b.rules()[n][0]
            argv=w_strtok(target[2:])
            self.assertEqual(argv[:2], ['/usr/bin/python3','-c'])
            self.assertEqual(len(argv),3)
            self.assertEqual(argv[2], b.script(n))
            self.assertNotIn('->', argv[2])
            self.assertEqual(argv[2].count("print('PASS')"),1)
            for value, want in [('PASS\n','PASS'), ('','FAIL')]:
                self.assertEqual(simulate(checks[900000+n], {target:dict(stdout=value)}),want)
        counts=manifest()['counts']
        self.assertEqual((counts['implemented'],counts['remaining'],counts['included'],counts['excluded']), (307,0,307,7))

    def test_both_services_and_status_rc(self):
        out, run=self.output(244,self.good())
        self.assertEqual(out,'PASS\n')
        self.assertEqual([c.args[0] for c in run.call_args_list], [
            ['/usr/bin/systemctl', action, service]
            for service in ('iptables','ip6tables') for action in ('is-enabled','is-active')])
        for pos in range(4):
            for value,rc in [('disabled',1),('enabled',0),('active',0),('failed',3),('not-found',4),('',1),('masked',0),('inactive',0),('masked\ninactive',1)]:
                if pos % 2 == 0 and (value, rc) in {('disabled', 1), ('not-found', 4)}:
                    continue  # FIX8: disabled/absent plus inactive is compliant.
                results=self.good();results[pos]=self.cp(value,rc)
                self.assertEqual(self.output(244,results)[0],'',(pos,value,rc))

    def test_zone_including_public(self):
        for value in ['public\n','drop\n','trusted\n','custom-zone_1\n']:
            out,run=self.output(246,[self.cp(value)])
            self.assertEqual(out,'PASS\n')
            self.assertEqual(run.call_args.args[0], ['/usr/bin/firewall-cmd','--get-default-zone'])
        for value in ['', ' \n', 'public\ndrop\n', 'Error: denied', 'not running']:
            self.assertEqual(self.output(246,[self.cp(value)])[0],'')

    def test_errors_are_mocked_and_never_commit(self):
        for n in b.ADDED:
            for error in [PermissionError(), FileNotFoundError(), UnicodeError(), ValueError(), subprocess.TimeoutExpired('mock',8), subprocess.SubprocessError()]:
                self.assertEqual(self.output(n,[error])[0],'')
            for pos in range(4 if n==244 else 1):
                for result in [self.cp('masked',1,'denied'), self.cp('public',1),self.cp('',0)]:
                    results=self.good() if n==244 else [self.cp('public')]
                    results[pos]=result
                    self.assertEqual(self.output(n,results)[0],'')

    def test_original_305_checks_unchanged(self):
        count=0
        for p in (ROOT/'policies').glob('*.yml'):
            old=json.loads(subprocess.check_output(['git','show','21e56dbc1040ce26defdb972bf7e12a37de382d2:policies/'+p.name],cwd=ROOT))
            new=json.loads(p.read_text())
            self.assertEqual(old['policy'],new['policy'])
            self.assertEqual(old['requirements'],new['requirements'])
            current={c['id']:c for c in new['checks']}
            for c in old['checks']:
                self.assertEqual(c,current[c['id']]); count+=1
        self.assertEqual(count,305)
        self.assertEqual(subprocess.check_output(['git','diff','--name-only','HEAD','--','tests/fixtures','tests/fix5_baseline.json','docs/*TEST_OUTPUT*'],cwd=ROOT,text=True),'')
