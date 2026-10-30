import json
import unittest
from pathlib import Path
from linuxgcb.catalog import ROOT, registry, digest, XLSX_HASH
from linuxgcb.policy import validate, simulate, definitions
from linuxgcb.batch1 import FILES, ADDED
from linuxgcb.coverage import manifest
from scripts.inventory import extract


class CatalogTests(unittest.TestCase):
    def test_scope_and_source_unchanged(self):
        rows = registry()
        self.assertEqual((len(rows), sum(r['included'] for r in rows)), (314,307))
        self.assertEqual(len({r['sca_id'] for r in rows}),314)
        self.assertEqual(len({r['gcb_id'] for r in rows}),314)
        self.assertEqual({r['source_sheet'] for r in rows if not r['included']}, {'Nftables防火牆'})
        self.assertTrue(next(r for r in rows if r['sca_id']==900245)['included'])
        self.assertFalse(any(r['gcb_id'].endswith('-0180') for r in rows))
        self.assertEqual(digest(next(ROOT.glob('*.xlsx'))), XLSX_HASH)
        self.assertEqual(rows,json.loads((ROOT/'data/scope_registry.json').read_text()))

    def test_raw_controls_unchanged(self):
        self.assertEqual(extract(next(ROOT.glob('*.xlsx'))),json.loads((ROOT/'data/controls.json').read_text()))

    def test_traceability(self):
        source = {r['gcb_id']:r for r in extract(next(ROOT.glob('*.xlsx')))}
        for r in registry():
            self.assertEqual(r['source_row'],source[r['gcb_id']]['row'])
            self.assertEqual(r['expected'],source[r['gcb_id']]['expected'])
            self.assertEqual(r['review_status'],'human_review_pending')

    def test_structural(self):
        self.assertEqual(validate(),len(definitions()))

    def test_all_positive_negative_missing_error(self):
        fixtures=json.loads((ROOT/'tests/fixtures/rule_outputs.json').read_text())
        self.assertEqual(fixtures['label'],'SYNTHETIC TEST ONLY')
        checked = set()
        for p in (ROOT/'policies').glob('*.yml'):
            for c in json.loads(p.read_text())['checks']:
                checked.add(str(c['id']))
                for name, state in [('positive','PASS'),('negative','FAIL'),('missing','UNRESOLVED'),('empty','FAIL'),('error','UNRESOLVED'),('nonzero_matching','PASS')]:
                    with self.subTest(id=c['id'],case=name):
                        self.assertEqual(simulate(c,fixtures['checks'][str(c['id'])][name]),state)
        self.assertEqual(checked,set(fixtures['checks']))

    def test_permission_bit_subset_and_special_bits(self):
        c=next(c for c in json.loads((ROOT/'policies/linuxgcb_base.yml').read_text())['checks'] if c['id']==900046)
        target=c['rules'][0].split(' -> ')[0]
        for mode in range(0o10000):
            expected='PASS' if mode & ~0o644 == 0 else 'FAIL'
            self.assertEqual(simulate(c,{target:dict(stdout=format(mode,'o'),exit_code=0)}),expected)

    def test_exit_code_does_not_override_matching_output(self):
        c=next(c for c in json.loads((ROOT/'policies/linuxgcb_base.yml').read_text())['checks'] if c['id']==900045)
        target=c['rules'][0].split(' -> ')[0]
        self.assertEqual(simulate(c,{target:dict(stdout='0:0',exit_code=1)}),'PASS')

    def test_batch_manifest_reconciles_and_docx(self):
        m=manifest();rows=registry()
        self.assertEqual({e['sca_id'] for e in m['added']},{900000+n for n in ADDED})
        self.assertEqual(m['counts']['implemented'],len(definitions()))
        self.assertEqual(m['counts']['remaining'],307-len(definitions()))
        self.assertEqual(m['counts']['full']+m['counts']['partial'],len(definitions()))
        self.assertEqual(m['counts']['partial'],4)
        for e in m['added']:
            self.assertTrue(all(e['expected'] == c[-1] for c in e['docx_all_cells']))
            self.assertTrue(all(e['gcb_id'] in c for c in e['docx_all_cells']))
            n=e['sca_id']-900000
            method=e['docx_cells'][-2]
            if n in FILES:
                self.assertIn(FILES[n][0],method)

    def test_all_mode_masks_exhaustive(self):
        from linuxgcb.batch1 import mode_pattern
        import re
        masks={v for _,kind,v in FILES.values() if kind=='mode'}
        for mask in masks:
            pattern=re.compile(mode_pattern(mask))
            for value in range(0o10000):
                self.assertEqual(bool(pattern.search(format(value,'o'))),value & ~mask == 0)

    def test_batch_edges_use_emitted_rules(self):
        import copy
        checks={c['id']:c for p in (ROOT/'policies').glob('*.yml') for c in json.loads(p.read_text())['checks']}
        fixtures=json.loads((ROOT/'tests/fixtures/rule_outputs.json').read_text())['checks']
        for n in sorted(ADDED):
            check=checks[900000+n];base=fixtures[str(900000+n)]['positive']
            # 每個子規則必須獨立參與 all；非第一個錯誤亦不可被第一個 PASS 掩蓋。
            for target in base:
                obs=copy.deepcopy(base);obs[target]['stdout']='WRONG'
                self.assertEqual(simulate(check,obs),'FAIL')
                obs=copy.deepcopy(base);obs[target]['stdout']+='\nWRONG'
                self.assertEqual(simulate(check,obs),'PASS') # SCA 逐行存在匹配，不是整個輸出相等
            if n in FILES:
                path,kind,value=FILES[n];type_target='c:/usr/bin/stat -c %F '+path
                obs=copy.deepcopy(base);obs[type_target]['stdout']='symbolic link'
                self.assertEqual(simulate(check,obs),'FAIL')
                if kind=='owner':
                    target='c:/usr/bin/stat -c %U:%G '+path
                    for owner in ('root:shadow','root:wheel','nobody:root','root:UNKNOWN'):
                        obs=copy.deepcopy(base);obs[target]['stdout']=owner
                        self.assertEqual(simulate(check,obs),'PASS' if owner=='root:shadow' and 'shadow' in value else 'FAIL')
                if base[type_target]['stdout']=='regular file':
                    obs=copy.deepcopy(base);obs[type_target]['stdout']='regular empty file'
                    self.assertEqual(simulate(check,obs),'PASS')
            from linuxgcb.batch1 import SERVICES,PACKAGES
            if n in SERVICES:
                target=next(t for t in base if 'UnitFileState' in t)
                for value in ('enabled-runtime','static','alias','not-found'):
                    obs=copy.deepcopy(base);obs[target]['stdout']='UnitFileState='+value
                    self.assertEqual(simulate(check,obs),'FAIL')
                obs=copy.deepcopy(base)
                target=next(t for t in base if 'LoadState' in t);obs[target]['stdout']='LoadState=not-found'
                self.assertEqual(simulate(check,obs),'FAIL')
            if n in PACKAGES:
                obs=copy.deepcopy(base);target=next(iter(base));obs[target]['stdout']='package missing is not installed'
                obs[target]['exit_code']=1
                self.assertEqual(simulate(check,obs),'FAIL')

    def test_documented_file_and_all_semantics(self):
        check=dict(condition='all',rules=['f:/SYNTHETIC -> r:^ID=rhel$'])
        self.assertEqual(simulate(check,{'f:/SYNTHETIC':dict(exists=False)}),'NOT_APPLICABLE')
        self.assertEqual(simulate(check,{'f:/SYNTHETIC':dict(stdout='')}),'FAIL')
        self.assertEqual(simulate(check,{'f:/SYNTHETIC':dict(error='permission denied')}),'UNRESOLVED')
        check['rules'].append('c:/SYNTHETIC -> r:^good$')
        self.assertEqual(simulate(check,{'f:/SYNTHETIC':dict(exists=False),'c:/SYNTHETIC':dict(stdout='bad')}),'FAIL')
        self.assertEqual(simulate(check,{'f:/SYNTHETIC':dict(exists=False),'c:/SYNTHETIC':dict(stdout='good')}),'NOT_APPLICABLE')
        self.assertEqual(simulate(check,{'c:/SYNTHETIC':dict(stdout='bad')}),'FAIL')
