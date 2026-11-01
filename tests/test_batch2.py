from linuxgcb.batch9 import ADDED as BATCH9
from linuxgcb.batch10 import ADDED as BATCH10
from linuxgcb.batch8 import ADDED as BATCH8
from linuxgcb.batch7 import ADDED as BATCH7
from linuxgcb.batch6 import ADDED as BATCH6
"""BATCH2 synthetic contract/guard tests. Never execute any policy command.

The only subprocesses run shell builtins with authored printf/exit data, after
replacing the entire inventory command in the emitted shell script.
"""
import copy
import hashlib
import json
import re
import shlex
import subprocess
import unittest

from linuxgcb.argv import w_strtok
from linuxgcb.batch3 import ADDED as BATCH3
from linuxgcb.batch2 import ABSENT_PACKAGES, ADDED, CATEGORIES, MARKER, specs, guarded, expected
from linuxgcb.catalog import ROOT, registry
from linuxgcb.policy import emit_rule, parse_rule, simulate
from scripts.batch2_fixtures import generated


class Batch2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checks={c['id']:c for p in (ROOT/'policies').glob('*.yml') for c in json.loads(p.read_text())['checks']}
        cls.fixtures=json.loads((ROOT/'tests/fixtures/rule_outputs.json').read_text())['checks']
        cls.fixtures['900188'] = generated()['900188']  # FIX5 in-memory overlay; historical file stays intact.
        # FIX11 in-memory overlay: 282/283 find hardened with pseudo-FS prune.
        for k in ('900282','900283'):
            cls.fixtures[k] = generated()[k]
        cls.baseline=json.loads((ROOT/'tests/fixtures/batch2_baseline.json').read_text())

    def check(self,n): return self.checks[900000+n]
    def positive(self,n): return copy.deepcopy(self.fixtures[str(900000+n)]['positive'])

    def test_registry_exact_remaining_categories_and_baseline(self):
        before={c['id'] for c in self.baseline['checks']}
        rows=registry()
        wanted={r['sca_id'] for r in rows if r['category'] in CATEGORIES and r['sca_id'] not in before}
        self.assertEqual(wanted,{900000+n for n in ADDED})
        self.assertEqual(len(ADDED),44)
        self.assertEqual(len(self.checks),307)
        self.assertFalse(any(r['coverage']=='unimplemented' for r in rows if r['category'] in CATEGORIES))
        self.assertEqual({c['id']:c for c in self.baseline['checks']}, {n:self.checks[n] for n in before})
        for filename,digest in self.baseline['hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT/filename).read_bytes()).hexdigest(),digest)
        for row in rows:
            if row['sca_id'] not in before and row['category'] not in CATEGORIES and row['sca_id']-900000 not in BATCH3 | BATCH6 | BATCH7 | BATCH8 | (BATCH9 | BATCH10):
                self.assertNotEqual(row['implementation'],'candidate')
        # Existing synthetic fixtures are also preserved field for field.
        for key,digest in self.baseline['legacy_fixture_hashes'].items():
            self.assertEqual(hashlib.sha256(json.dumps(self.fixtures[key],sort_keys=True,ensure_ascii=False).encode()).hexdigest(),digest)

    def test_generated_fixtures_and_every_predicate_counterexample(self):
        self.assertEqual(generated(),{str(900000+n):self.fixtures[str(900000+n)] for n in ADDED})
        for n in sorted(ADDED):
            cases=self.fixtures[str(900000+n)]
            check=self.check(n)
            self.assertEqual(check['regex_type'],'pcre2')
            self.assertEqual(check['compliance'],[{'twgcb':['TWGCB-01-012-'+format(n,'04d')]}])
            for name,want in [('positive','PASS'),('negative','FAIL'),('missing','UNRESOLVED'),('empty','FAIL'),('error','UNRESOLVED'),('nonzero_matching','PASS')]:
                with self.subTest(n=n,case=name): self.assertEqual(simulate(check,cases[name]),want)
            for case in cases['predicate_negatives']:
                with self.subTest(n=n,rule=case['rule']):
                    self.assertIn(case['rule'],check['rules'])
                    self.assertEqual(simulate(check,case['observations']),'FAIL')
            self.assertIn('UNVALIDATED', next(json.loads(p.read_text())['policy']['name'] for p in (ROOT/'policies').glob('*.yml') if any(c['id']==check['id'] for c in json.loads(p.read_text())['checks'])))
            for target in cases['positive']:
                no_marker=self.positive(n)
                no_marker[target]['stdout']=no_marker[target]['stdout'].replace('ABSENT' if n in ABSENT_PACKAGES else MARKER,'')
                self.assertNotEqual(simulate(check,no_marker),'PASS')
                for variant in (None,dict(error='permission denied')):
                    obs=self.positive(n)
                    if variant is None: del obs[target]
                    else: obs[target]=variant
                    with self.subTest(n=n,target=target,variant=variant):
                        self.assertNotEqual(simulate(check,obs),'PASS')

    def test_emitted_guard_with_fake_commands_only(self):
        for n,items in specs().items():
            if n in ABSENT_PACKAGES: continue  # Dedicated FIX3 tri-state tests.
            for command,pattern,good,bad in items:
                target=guarded(command)
                # Obtain the actual emitted wrapper then replace its full inner
                # inventory command with a shell containing only printf/exit.
                self.assertIn(target,{parse_rule(rule)[0] for rule in self.check(n)['rules']})
                argv=w_strtok(target[2:])
                self.assertEqual(argv[:2],['/bin/sh','-c'])
                prefix='out=$('+command+')'
                self.assertTrue(argv[2].startswith(prefix))
                for code in (0,1,2,126,127):
                    payload=good+'\n'+MARKER+'\n'  # Even matching stdout cannot escape a failed command.
                    fake='/bin/sh -c '+shlex.quote('printf "%s" '+shlex.quote(payload)+'; exit '+str(code))
                    script='out=$('+fake+')'+argv[2][len(prefix):]
                    completed=subprocess.run(['/bin/sh','-c',script],text=True,capture_output=True,timeout=5)
                    self.assertEqual(completed.returncode,code)
                    self.assertEqual(completed.stdout,payload+MARKER+'\n' if code==0 else '')
                    if code:
                        obs=self.positive(n)
                        obs[target]=dict(stdout=completed.stdout,exit_code=completed.returncode)
                        self.assertNotEqual(simulate(self.check(n),obs),'PASS')

    def test_negation_is_rule_level_not_existential_line_negation(self):
        for n,items in specs().items():
            if n in ABSENT_PACKAGES: continue  # Dedicated FIX3 tri-state tests.
            for command,pattern,good,bad in items:
                if not pattern.startswith('!'): continue
                rule=emit_rule(guarded(command),pattern)
                self.assertTrue(rule.startswith('not c:'))
                self.assertNotIn('!r:',rule)
                obs=self.positive(n)
                # A compliant unrelated line cannot hide a prohibited member.
                obs[guarded(command)]['stdout']='unrelated\n'+bad+'\n'+MARKER
                self.assertEqual(simulate(self.check(n),obs),'FAIL')

    def test_default_protocol_and_compression(self):
        for text,want in [('port 22','PASS'),('protocol 2','PASS'),('protocol 1','FAIL'),('protocol 2,1','FAIL')]:
            obs=self.positive(255);target=next(iter(obs));obs[target]['stdout']=text+'\n'+MARKER
            self.assertEqual(simulate(self.check(255),obs),want)
        for value,want in [('yes','PASS'),('delayed','PASS'),('no','PASS'),('invalid','FAIL')]:
            obs=self.positive(279);target=next(iter(obs));obs[target]['stdout']='compression '+value+'\n'+MARKER
            self.assertEqual(simulate(self.check(279),obs),want)
        for n in (255,279): self.assertIn('RHEL9 OpenSSH 8.0+',self.check(n)['description'])

    def test_numeric_boundaries_and_crypto_components(self):
        for n,key,maximum in ((266,'maxauthtries',4),(272,'clientaliveinterval',600),(273,'logingracetime',60),(277,'maxsessions',4)):
            for value in (-1,0,1,maximum,maximum+1,99999):
                obs=self.positive(n);target=next(iter(obs))
                obs[target]['stdout']=re.sub(key+r' [0-9]+',key+' '+str(value),obs[target]['stdout'])
                self.assertEqual(simulate(self.check(n),obs),'PASS' if 1<=value<=maximum else 'FAIL')
        for key,bad in [('ciphers','aes128-cbc'),('macs','hmac-md5'),('kexalgorithms','diffie-hellman-group1-sha1')]:
            obs=self.positive(263);target=next(iter(obs))
            obs[target]['stdout']=re.sub('^'+key+r' .*$',key+' '+bad,obs[target]['stdout'],flags=re.M)
            self.assertEqual(simulate(self.check(263),obs),'FAIL')

    def test_key_sets_reject_empty_and_any_bad_member(self):
        for n in (259,260,261,262):
            check=self.check(n);obs=self.positive(n);target=next(iter(obs))
            obs[target]['stdout']=MARKER
            self.assertEqual(simulate(check,obs),'FAIL')
            bad=specs()[n][0][-1]
            obs=self.positive(n);obs[target]['stdout']+='\n'+bad
            self.assertEqual(simulate(check,obs),'FAIL')
        for n,mask in ((204,0o600),(260,0o640),(262,0o644)):
            rule=next(r for r in self.check(n)['rules'] if not r.startswith('not ') and 'stat -c %a' in r)
            _,pattern=parse_rule(rule)
            for value in range(0o10000):
                self.assertEqual(bool(pattern.fullmatch(format(value,'o'))),value & ~mask==0)

    def test_current_docx_amendment_and_concrete_values(self):
        manifest=json.loads((ROOT/'data/coverage_manifest.json').read_text())
        row=next(r for r in manifest['reviewed'] if r['sca_id']==900272)
        self.assertTrue(all('ClientAliveCountMax 1' in c[-2] for c in row['docx_all_cells']))
        self.assertTrue(any('ClientAliveCountMax 0' in c[-2] for c in row['docx_historical_cells']))
        source={r['gcb_id']:r for r in json.loads((ROOT/'data/controls.json').read_text())}
        for n in ADDED:
            value=expected(source['TWGCB-01-012-'+format(n,'04d')])
            self.assertTrue(self.check(n)['description'].startswith('合規值: '+value+' ｜ '))
        self.assertIn('待確認（來源未提供單一基準值）',self.check(258)['description'])

    def test_allowlist_rejects_altered_shell_and_negation(self):
        target=next(iter(self.positive(255)))
        for rule in ('not c:/SYNTHETIC -> r:^bad$',target.replace('/usr/sbin/sshd','/tmp/evil')+' -> r:^good$'):
            with self.assertRaises(ValueError): parse_rule(rule)
