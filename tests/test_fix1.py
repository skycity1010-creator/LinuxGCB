"""SYNTHETIC TEST ONLY: output fixtures; never execute policy commands."""
import copy
import itertools
import json
import unittest

from linuxgcb.batch1 import DISABLED_SERVICES
from linuxgcb.catalog import ROOT
from linuxgcb.policy import simulate


class Fix1Tests(unittest.TestCase):
    def setUp(self):
        self.checks = {c['id']: c for p in (ROOT/'policies').glob('*.yml')
                       for c in json.loads(p.read_text())['checks']}
        self.fixtures = json.loads((ROOT/'tests/fixtures/rule_outputs.json').read_text())

    def test_named_service_cases_use_emitted_all_rules(self):
        self.assertEqual(self.fixtures['label'], 'SYNTHETIC TEST ONLY')
        for n in DISABLED_SERVICES:
            check = self.checks[900000+n]
            self.assertEqual(check['condition'], 'all')
            cases = self.fixtures['checks'][str(900000+n)]
            for name, want in [('not_found', 'PASS'), ('installed_enabled', 'FAIL'),
                               ('installed_disabled_inactive', 'PASS'),
                               ('installed_masked', 'PASS'), ('empty', 'FAIL'),
                               ('error', 'UNRESOLVED'), ('missing', 'UNRESOLVED')]:
                with self.subTest(id=check['id'], case=name):
                    self.assertEqual(simulate(check, cases[name]), want)

    def test_every_service_state_and_samba_member(self):
        # Mutate each Samba member separately: smb PASS cannot hide unsafe nmb.
        for n, units in DISABLED_SERVICES.items():
            check = self.checks[900000+n]
            base = self.fixtures['checks'][str(900000+n)]['positive']
            for unit in units:
                cmd = 'c:/usr/bin/systemctl show '+unit+'.service'
                for load, state, active in itertools.product(
                    ('loaded', 'masked', 'error', 'bad-setting'),
                    ('disabled', 'masked', 'enabled', 'enabled-runtime',
                     'static', 'alias', 'indirect', 'masked-runtime', ''),
                    ('inactive', 'active', 'failed', 'activating', 'deactivating')):
                    obs = copy.deepcopy(base)
                    obs[cmd+' --property=LoadState']['stdout'] = 'LoadState='+load
                    obs[cmd+' --property=ActiveState']['stdout'] = 'ActiveState='+active
                    obs[cmd+' --property=LoadState --property=UnitFileState']['stdout'] = (
                        'LoadState='+load+'\nUnitFileState='+state)
                    want = ('PASS' if load in ('loaded', 'masked') and
                            state in ('disabled', 'masked') and active == 'inactive' else 'FAIL')
                    with self.subTest(id=check['id'], unit=unit, load=load, state=state, active=active):
                        self.assertEqual(simulate(check, obs), want)
                for active in ('inactive', 'active', 'failed', 'activating'):
                    obs = copy.deepcopy(base)
                    obs[cmd+' --property=LoadState']['stdout'] = 'LoadState=not-found'
                    obs[cmd+' --property=ActiveState']['stdout'] = 'ActiveState='+active
                    # Missing properties may be omitted by systemctl show.
                    for suffix in ('', '\nUnitFileState='):
                        obs[cmd+' --property=LoadState --property=UnitFileState']['stdout'] = 'LoadState=not-found'+suffix
                        self.assertEqual(simulate(check, obs), 'PASS' if active == 'inactive' else 'FAIL')

    def test_absence_requires_explicit_stdout_and_errors_stay_unresolved(self):
        for n in DISABLED_SERVICES:
            check = self.checks[900000+n]
            cases = self.fixtures['checks'][str(900000+n)]
            for key in cases['positive']:
                obs = copy.deepcopy(cases['positive'])
                obs[key] = dict(stdout='', stderr='No such unit / LoadState=not-found', exit_code=1)
                self.assertEqual(simulate(check, obs), 'FAIL')
                obs[key] = dict(error='SYNTHETIC permission/DBus/timeout')
                self.assertEqual(simulate(check, obs), 'UNRESOLVED')

    def test_required_services_still_require_enabled_active(self):
        # The shared helper must not relax auditd, rsyslog or firewalld.
        for n in (133, 175, 243):
            check = self.checks[900000+n]
            base = self.fixtures['checks'][str(900000+n)]['positive']
            self.assertEqual(simulate(check, base), 'PASS')
            for prop, value in [('LoadState', 'not-found'), ('ActiveState', 'inactive'),
                                ('UnitFileState', 'disabled')]:
                obs = copy.deepcopy(base)
                key = next(k for k in obs if k.endswith('--property='+prop))
                obs[key]['stdout'] = prop+'='+value
                self.assertEqual(simulate(check, obs), 'FAIL')
