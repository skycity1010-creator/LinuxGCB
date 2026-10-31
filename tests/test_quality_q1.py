from linuxgcb.batch7 import ADDED as BATCH7
from linuxgcb.batch6 import ADDED as BATCH6
"""SYNTHETIC Q1 回歸；不執行任何政策命令。"""
import copy
import json
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from linuxgcb.catalog import ROOT, registry
from linuxgcb.batch3 import ADDED as BATCH3
from linuxgcb.batch2 import ADDED as BATCH2
from linuxgcb.policy import simulate, definitions
from linuxgcb.report import normalize, metrics, render

NOW = datetime(2026,10,30,tzinfo=timezone.utc)

class QualityQ1Tests(unittest.TestCase):
    def check(self, n):
        return dict(condition='all', regex_type='pcre2',
                    rules=[a+' -> r:'+b for a,b in definitions()[n]])

    def snapshot(self):
        snapshot=json.loads((ROOT/'tests/fixtures/snapshot.json').read_text())
        # Test-only hash binding; historical observations remain unchanged on disk.
        snapshot['policy_hashes']=json.loads((ROOT/'data/policy_hashes.json').read_text())
        return snapshot

    def test_reject_unsupported_conditions_even_when_matching(self):
        for condition in ('any','none','ALL',''):
            with self.subTest(condition=condition), self.assertRaises(ValueError):
                simulate(dict(condition=condition,rules=['c:/SYNTHETIC -> r:^good$']), {})

    def test_reject_unsupported_rule_and_regex_syntax(self):
        for rule in ('p:daemon -> r:^good$', 'c:/SYNTHETIC -> r:^good$ && r:bad',
                     'c:/SYNTHETIC -> r:^(?=good)good$', 'c:/SYNTHETIC -> r:^\\w+$',
                     'c:/SYNTHETIC -> r:^good.$|bad', 'c:/SYNTHETIC -> n:(\\d+) compare == 1'):
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                simulate(dict(condition='all',rules=[rule]), {})
        for check in (dict(condition='all',rules=[]),dict(condition='all',regex_type='osregex',rules=['c:/SYNTHETIC -> r:^good$'])):
            with self.assertRaises(ValueError): simulate(check,{})

    def test_stat_uses_numeric_directory_type_only(self):
        from linuxgcb.batch1 import FILES
        for n,(path,_,_) in FILES.items():
            rules=self.check(n)['rules']
            self.assertFalse(any('%F' in r for r in rules))
            directory=n in (179,193,194,195,196,197,198,199,200,201,202)
            self.assertEqual(any('%f ' in r for r in rules),directory)
            # regular 是舊版額外要求；來源沒有明文限定，不能默默加嚴。
            self.assertFalse(any('regular' in r for r in rules))

    def test_numeric_type_locale_and_all_file_types(self):
        # locale 為具名合成情境，未宣稱本機安裝這些 locale。
        for locale in ('C','zh_TW.UTF-8','de_DE.UTF-8'):
            for kind in (stat.S_IFDIR,stat.S_IFREG,stat.S_IFLNK,stat.S_IFIFO,stat.S_IFSOCK,stat.S_IFCHR,stat.S_IFBLK):
                for mode in (0,0o700,0o755,0o7777):
                    obs={'c:/usr/bin/stat -c %U:%G /var/log':dict(stdout='root:root'),
                         'c:/usr/bin/stat -c %f /var/log':dict(stdout=format(kind|mode,'x'))}
                    with self.subTest(locale=locale,kind=kind,mode=mode):
                        self.assertEqual(simulate(self.check(179),obs),'PASS' if kind==stat.S_IFDIR else 'FAIL')

    def test_stderr_exit_and_multiline_are_not_runtime_protection(self):
        check=dict(condition='all',rules=['c:/SYNTHETIC -> r:^good$'])
        for code in (0,1,127):
            self.assertEqual(simulate(check,{'c:/SYNTHETIC':dict(stdout='bad\ngood\nbad',stderr='SYNTHETIC error',exit_code=code)}),'PASS')
        for stdout in ('','bad','good bad','good\rbad'):
            self.assertEqual(simulate(check,{'c:/SYNTHETIC':dict(stdout=stdout,stderr='good',exit_code=1)}),'FAIL')
        self.assertEqual(simulate(check,{}),'UNRESOLVED')
        self.assertEqual(simulate(check,{'c:/SYNTHETIC':dict(error='SYNTHETIC unknown execution')}),'UNRESOLVED')

    def test_all_aggregates_error_na_and_failure(self):
        check=dict(condition='all',rules=['c:/A -> r:^good$','c:/B -> r:^good$'])
        for second,want in ((dict(stdout='bad'),'FAIL'),(dict(stdout='good'),'UNRESOLVED'),(dict(engine_result='NOT_APPLICABLE'),'UNRESOLVED')):
            self.assertEqual(simulate(check,{'c:/B':second}),want)
        self.assertEqual(simulate(check,{'c:/A':dict(stdout='good'),'c:/B':dict(engine_result='NOT_APPLICABLE')}),'NOT_APPLICABLE')

    def test_review_reconciles_exact_existing_ids(self):
        rows=[r for r in registry() if r['implementation']=='candidate']
        self.assertEqual({r['sca_id'] for r in rows},{900000+n for n in definitions()})
        rows=[r for r in rows if r['sca_id']-900000 not in BATCH2 | BATCH3 | BATCH6 | BATCH7]
        self.assertEqual(len(rows),53)
        self.assertTrue(all(r['execution_review']=='blocked' for r in rows))
        self.assertTrue(all('Q1-01' in r['issue_ids'] for r in rows))
        self.assertEqual(sum(r['coverage']=='full' for r in rows),0)

    def test_all_raw_pass_never_becomes_verified_compliance(self):
        snapshot=self.snapshot()
        snapshot['hosts'][0]['checks']=[dict(id=900000+n,result='passed') for n in definitions()]
        rows=normalize(snapshot,NOW);summary=metrics(rows)
        self.assertEqual(summary['counts'].get('PASS',0),0)
        self.assertEqual(summary['completeness'],0)
        self.assertEqual(summary['raw_observed'],len(definitions()))
        self.assertFalse(any(r['verified_compliance'] for r in rows))
        self.assertEqual(sum(r['state']=='NOT_SCANNED' for r in rows if r['raw_result'] is not None),0)

    def test_missing_backup_and_service_are_pending_errors_are_errors(self):
        for n in (53,54,55,56,57,58,59,60,30,94,97,98,245):
            for evidence,want in (('missing','MANUAL_PENDING'),('absence_unverified','MANUAL_PENDING'),('symlink_unresolved','MANUAL_PENDING'),('tool_error','ERROR'),('permission_error','ERROR'),('timeout','ERROR')):
                snapshot=self.snapshot();snapshot['hosts'][0]['checks']=[dict(id=900000+n,result='failed',evidence_status=evidence,reason='SYNTHETIC metadata only')]
                row=next(r for r in normalize(snapshot,NOW) if r['sca_id']==900000+n)
                self.assertEqual((row['state'],row['raw_result']),(want,'failed'))
                self.assertFalse(row['verified_compliance'])

    def test_synthetic_report_end_to_end_no_complete_elevation(self):
        snapshot=self.snapshot()
        with tempfile.TemporaryDirectory() as directory:
            summary=render(snapshot,directory,NOW)
            self.assertEqual(summary['raw_observed'],6)
            self.assertEqual(summary['verified_decided'],0)
            self.assertEqual(summary['completeness'],0)
            self.assertEqual(json.loads((Path(directory)/'snapshot.json').read_text()),snapshot)
            self.assertIn('verified_compliance',(Path(directory)/'report.csv').read_text(encoding='utf-8-sig'))

    def test_all_service_states_preserve_raw_distinctions(self):
        from linuxgcb.batch1 import SERVICES, DISABLED_SERVICES
        fixtures=json.loads((ROOT/'tests/fixtures/rule_outputs.json').read_text())['checks']
        for n in set(SERVICES)|{243,245}:
            base=fixtures[str(900000+n)]['positive']
            # FIX-1 停用組的完整狀態矩陣移至 test_fix1；此處保留啟用組。
            states = {'LoadState':['not-found','error','bad-setting'],
                                'ActiveState':['active','inactive','failed','activating'],
                                'UnitFileState':['enabled','disabled','masked','masked-runtime','enabled-runtime','static','alias','indirect']}
            for prop,values in ({} if n in DISABLED_SERVICES else states).items():
                target=next(k for k in base if '--property='+prop in k)
                expected=base[target]['stdout']
                for value in values:
                    obs=copy.deepcopy(base);obs[target]['stdout']=prop+'='+value
                    self.assertEqual(simulate(self.check(n),obs),'PASS' if obs[target]['stdout']==expected else 'FAIL')
            # 查詢 .service 沒有 socket、alias 與原子快照證據；不得計完整符合。
            snapshot=self.snapshot();snapshot['hosts'][0]['checks']=[dict(id=900000+n,result='passed')]
            row=next(r for r in normalize(snapshot,NOW) if r['sca_id']==900000+n)
            self.assertEqual(row['state'],'MANUAL_PENDING')
