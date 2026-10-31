"""REAL EVIDENCE agent010 R2；變異僅為記憶體中 test-only 負面測試。"""
import copy
import csv
import json
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from linuxgcb.catalog import ROOT, digest
from linuxgcb.snapshot import convert, LABEL
from linuxgcb.report import normalize, render

FIXTURE = ROOT/'tests/fixtures/realhost_r2.json'
FAIL_IDS = {900192,900194,900196,900198,900200,900202,900269}
NOW = datetime(2026,10,31,6,tzinfo=timezone.utc)


class SnapshotTests(unittest.TestCase):
    def test_real_evidence_roundtrip(self):
        original = json.loads(FIXTURE.read_text())
        s = convert(FIXTURE)
        self.assertFalse(s['synthetic'])
        self.assertEqual(s['label'], LABEL)
        self.assertEqual(s['manager_dump_sha256'], digest(FIXTURE))
        host = s['hosts'][0]
        self.assertIsNone(host['scanned_at'])
        self.assertEqual(len(s['warnings']),3)
        self.assertEqual(Counter(c['result'] for c in host['checks']), {'passed':46,'failed':7})
        for c in host['checks']:
            self.assertEqual({k:v for k,v in c.items() if k!='policy_id'}, next(x for x in original[c['policy_id']]['checks'] if x['id']==c['id']))
        with tempfile.TemporaryDirectory() as d:
            summary=render(s,d,NOW)
            self.assertEqual(summary['counts']['FAIL'],7)
            self.assertEqual(summary['verified_decided'],0)
            self.assertIsNone(summary['pass_rate'])
            self.assertEqual(summary['completeness'],0)
            with (Path(d)/'report.csv').open(encoding='utf-8-sig',newline='') as f:
                failures=[r for r in csv.DictReader(f) if r['state']=='FAIL']
            self.assertEqual({int(r['sca_id']) for r in failures},FAIL_IDS)
            page=(Path(d)/'report.html').read_text()
            for r in failures:
                self.assertIn(r['gcb_id'],page)
                self.assertTrue(r['title'])
                self.assertTrue(r['command'])
                self.assertEqual(r['remediation_status'],'政策未提供 remediation')
            self.assertIn(LABEL,page)
    def test_scan_info_time_and_invalid_results(self):
        dump=json.loads(FIXTURE.read_text())
        info={pid:{'end_scan':'2026-10-31T12:03:00+08:00'} for pid in dump}
        s=convert(FIXTURE,info)
        self.assertEqual(s['hosts'][0]['scanned_at'],'2026-10-31T04:03:00+00:00')
        self.assertFalse(s['warnings'])
        for result in ('invalid','error','unexpected'):
            modified=copy.deepcopy(s)
            c=modified['hosts'][0]['checks'][0]
            c.update(result=result,reason='test-only raw reason')
            row=next(r for r in normalize(modified,NOW) if r['sca_id']==c['id'])
            self.assertEqual(row['state'],'ERROR')
            self.assertEqual(row['raw_result'],result)
            self.assertEqual(row['raw_reason'],'test-only raw reason')
    def test_invalid_time_rejected(self):
        pid=next(iter(json.loads(FIXTURE.read_text())))
        with self.assertRaises(ValueError):
            convert(FIXTURE,{pid:{'end_scan':'2026-10-31T12:03:00'}})
