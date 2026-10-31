from linuxgcb.batch7 import ADDED as BATCH7
from linuxgcb.batch6 import ADDED as BATCH6
"""EXP-1；所有變異皆為記憶體內 test-only，不改寫真實 fixture。"""
import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from linuxgcb.catalog import ROOT
from linuxgcb.batch3 import ADDED as BATCH3
from linuxgcb.batch2 import ADDED as BATCH2
from linuxgcb.expected import UNKNOWN, parse_description, source_expected
from linuxgcb.report import normalize, render
from linuxgcb.snapshot import convert


class ExpectedTests(unittest.TestCase):
    def test_all_53_source_values_and_q1_preserved(self):
        source = {r['gcb_id']: r for r in json.loads((ROOT/'data/controls.json').read_text())}
        checks = [c for p in (ROOT/'policies').glob('*.yml') for c in json.loads(p.read_text())['checks']]
        checks = [c for c in checks if c['id']-900000 not in BATCH2 | BATCH3 | BATCH6 | BATCH7]
        self.assertEqual(len(checks), 53)
        for c in checks:
            gid = c['compliance'][0]['twgcb'][0]
            self.assertTrue(c['description'].startswith('合規值: '))
            self.assertIn(' ｜ Q1 執行審查 ', c['description'])
            self.assertEqual(parse_description(c['description']), source_expected(source[gid]))
            self.assertNotEqual(parse_description(c['description']), UNKNOWN)
        by = {c['id']: parse_description(c['description']) for c in checks}
        self.assertEqual(by[900242], 'firewalld 已安裝')
        self.assertEqual(by[900245], 'nftables masked+inactive')
        self.assertEqual(by[900132], 'audit audit-libs 已安裝')
        self.assertEqual(by[900047], 'root:root或root:shadow')

    def test_parser_and_missing_source(self):
        self.assertEqual(parse_description('合規值: 000 ｜ Q1 review'), '000')
        self.assertEqual(parse_description('合規值: no'), 'no')
        for text in (None, '', 'Q1 old', ' 合規值: 0', '合規值:  ｜ Q1 old'):
            self.assertEqual(parse_description(text), '')
        self.assertEqual(source_expected({'gcb_id':'unknown', 'expected':None}), UNKNOWN)
        self.assertEqual(source_expected({'gcb_id':'unknown', 'expected':'安裝'}), UNKNOWN)

    def test_real_r2_r3_expected_in_snapshot_csv_html(self):
        for filename in ('realhost_r2.json', 'realhost_r3.json'):
            path = ROOT/'tests/fixtures'/filename
            before = path.read_bytes()
            snapshot = convert(path)
            self.assertTrue(all(c['expected'] for c in snapshot['hosts'][0]['checks']))
            with tempfile.TemporaryDirectory() as d:
                render(snapshot, d, datetime(2026,10,31,23,tzinfo=timezone.utc))
                with (Path(d)/'report.csv').open(encoding='utf-8-sig', newline='') as f:
                    observed = [r for r in csv.DictReader(f) if r['raw_result']]
                self.assertEqual(len(observed), 53)
                self.assertTrue(all(r['expected'] for r in observed))
                self.assertTrue(all('raw_prefix_missing' in r['expected_status'] for r in observed))
                self.assertIn('<th>expected</th>', (Path(d)/'report.html').read_text())
            self.assertEqual(path.read_bytes(), before)

    def test_raw_description_precedes_policy_and_missing_is_marked(self):
        snapshot = convert(ROOT/'tests/fixtures/realhost_r2.json')
        c = snapshot['hosts'][0]['checks'][0]
        c['description'] = '合規值: test-only 基準 ｜ Q1 test-only'
        rows = normalize(snapshot, datetime(2026,10,31,23,tzinfo=timezone.utc))
        row = next(r for r in rows if r['sca_id']==c['id'])
        self.assertEqual(row['expected'], 'test-only 基準')
        self.assertEqual(row['expected_status'], 'raw_description')
        missing = next(r for r in rows if r['policy_id'] is None)
        self.assertEqual(missing['expected'], '')
        self.assertEqual(missing['expected_status'], 'prefix_missing')
