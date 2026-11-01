import copy
import csv
import json
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
from linuxgcb.catalog import ROOT
from linuxgcb.report import normalize,metrics,render,safe_cell

NOW=datetime(2026,10,30,tzinfo=timezone.utc)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.fixture=json.loads((ROOT/'tests/fixtures/snapshot.json').read_text())
        # Test-only rebind to the expanded policy; preserve historical fixture bytes.
        self.fixture['policy_hashes']=json.loads((ROOT/'data/policy_hashes.json').read_text())
    def rows(self):return normalize(self.fixture,NOW)
    def test_full_inventory_status_and_denominators(self):
        rows=self.rows();by={r['sca_id']:r for r in rows};m=metrics(rows)
        self.assertEqual(len(rows),314)
        self.assertEqual(m['counts']['EXCLUDED'],7)
        self.assertEqual(m['applicable'],307)
        self.assertEqual(m['counts'].get('PASS',0),0)
        self.assertEqual(m['counts']['FAIL'],1)
        self.assertEqual(by[900243]['state'],'ERROR')
        self.assertEqual(by[900108]['state'],'MANUAL_PENDING')
        self.assertEqual(by[900269]['state'],'MANUAL_PENDING')
        self.assertEqual(by[900270]['state'],'MANUAL_PENDING')
        self.assertTrue(by[900046]['exception_approved'])
        self.assertEqual(by[900046]['state'],'FAIL')
        self.assertEqual(m['completeness'],0.0)
        self.assertEqual(m['pass_rate'],None)
    def test_no_scan_and_stale(self):
        host=self.fixture['hosts'][0];host['checks']=[];host.pop('scanned_at')
        rows=self.rows();self.assertTrue(all(r['stale'] for r in rows))
        self.assertEqual(next(r for r in rows if r['sca_id']==900045)['state'],'NOT_SCANNED')
        host['checks']=[dict(id=900045,result='passed')]
        self.assertEqual(next(r for r in self.rows() if r['sca_id']==900045)['state'],'MANUAL_PENDING')
    def test_zero_denominator(self):
        m=metrics([])
        self.assertIsNone(m['pass_rate']);self.assertIsNone(m['completeness']);self.assertIsNone(m['attainment'])
    def test_approved_na_does_not_hide_failure_or_error(self):
        h=self.fixture['hosts'][0]
        approved=next(iter(h['exceptions'].values()))
        h['not_applicable']={f'TWGCB-01-012-{n:04d}':copy.deepcopy(approved) for n in (45,46,243)}
        by={r['sca_id']:r for r in self.rows()}
        self.assertEqual(by[900045]['state'],'NOT_APPLICABLE')
        self.assertEqual(by[900046]['state'],'FAIL')
        self.assertEqual(by[900243]['state'],'NOT_APPLICABLE')
        h['checks'][3]['execution_error']=True
        self.assertEqual(next(r for r in self.rows() if r['sca_id']==900243)['state'],'ERROR')
        h['not_applicable']['TWGCB-01-012-0045']['expires']='2020-01-01T00:00:00Z'
        self.assertEqual(next(r for r in self.rows() if r['sca_id']==900045)['state'],'MANUAL_PENDING')
    def test_unapproved_profiles_conservative(self):
        self.fixture['hosts'][0]['approved_profiles']=[]
        rows=self.rows();self.assertEqual(metrics(rows)['unresolved'],307)
        self.assertEqual(next(r for r in rows if r['sca_id']==900045)['state'],'MANUAL_PENDING')
    def test_invalid_snapshots_rejected(self):
        mutations=[lambda s:s.update(source_sha256='bad'),lambda s:s.update(policy_hashes={}),
            lambda s:s['hosts'].append(copy.deepcopy(s['hosts'][0])),
            lambda s:s['hosts'][0]['checks'].append(dict(id=123,result='passed')),
            lambda s:s['hosts'][0]['checks'].append(dict(id=900045,result='passed')),
            lambda s:s['hosts'][0]['checks'].append(dict(id=900247,result='passed'))]
        for mutate in mutations:
            s=copy.deepcopy(self.fixture);mutate(s)
            with self.assertRaises(ValueError):normalize(s,NOW)
    def test_html_csv_raw_integrity(self):
        before=copy.deepcopy(self.fixture)
        with tempfile.TemporaryDirectory() as d:
            render(self.fixture,d,NOW)
            page=(Path(d)/'report.html').read_text()
            self.assertNotIn('<script>',page)
            self.assertIn('&lt;script&gt;',page)
            self.assertIn('SYNTHETIC',page)
            with (Path(d)/'report.csv').open(encoding='utf-8-sig',newline='') as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),314)
            bad=next(r for r in rows if r['sca_id']=='900046')
            self.assertTrue(bad['raw_reason'].startswith("'="))
            self.assertEqual(json.loads((Path(d)/'snapshot.json').read_text()),before)
        self.assertEqual(self.fixture,before)
    def test_formula_vectors(self):
        for text in ('=1',' +1','\t@evil','\r-1','\n=1','\ufeff=1','\v=1','\x00@evil','\u2003=1'):
            self.assertTrue(safe_cell(text).startswith("'"))
        self.assertEqual(safe_cell('普通文字'),'普通文字')
    def test_multiple_host_weighted_counts(self):
        other=copy.deepcopy(self.fixture['hosts'][0]);other['agent_id']='SYNTHETIC-002';other['checks']=[]
        self.fixture['hosts'].append(other)
        self.assertEqual(metrics(self.rows())['applicable'],614)
        self.assertEqual(len(self.rows()),628)

    def test_authored_controls_do_not_create_evidence(self):
        from linuxgcb.batch1 import ADDED
        by={r['sca_id']:r for r in self.rows()}
        for n in ADDED:
            self.assertIsNone(by[900000+n]['raw_result'])
            self.assertEqual(by[900000+n]['state'],'MANUAL_PENDING' if n==141 else 'NOT_SCANNED')
        self.fixture['hosts'][0]['checks'].append(dict(id=900141,result='passed'))
        self.assertEqual(next(r for r in self.rows() if r['sca_id']==900141)['state'],'MANUAL_PENDING')
        self.assertEqual(metrics(self.rows())['completeness'],0.0)
