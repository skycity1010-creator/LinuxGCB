import copy
import unittest
from datetime import datetime, timezone, timedelta
from linuxgcb.collector import Collector, CollectionError

NOW=datetime(2026,10,30,tzinfo=timezone.utc)


class Fake:
    def __init__(self):
        self.summary=dict(policy_id='p',hash_file='abc',total_checks=3,
                          start_scan='2026-10-29T00:00:00Z',end_scan='2026-10-29T00:01:00Z')
        self.checks=[dict(id=n,result='passed') for n in range(3)]
        self.calls=[]
        self.mode='ok'
    def get(self,path,params):
        self.calls.append((path,params.copy()))
        checks='/checks/' in path
        offset=params['offset']
        if self.mode=='failure' and checks and offset:
            raise OSError('SYNTHETIC timeout')
        items=self.checks if checks else [copy.deepcopy(self.summary)]
        if self.mode=='changing' and not checks and len(self.calls)>1:
            items[0]['end_scan']='2026-10-29T00:02:00Z'
        total=len(items)
        batch=copy.deepcopy(items[offset:offset+params['limit']])
        if checks and offset:
            if self.mode=='mismatch': total+=1
            if self.mode=='short': batch=[]
            if self.mode=='duplicate': batch=[self.checks[0]]
        data=dict(affected_items=batch,total_affected_items=total,total_failed_items=0)
        if self.mode=='partial': data['total_failed_items']=1
        return dict(error=0,data=data)


class CollectorTests(unittest.TestCase):
    def collect(self,f,now=NOW):
        return Collector(f,page_size=2).collect('SYNTHETIC','p','abc',now=now)

    def test_pages_and_idempotence(self):
        f=Fake();a=self.collect(f);b=self.collect(f,now=NOW+timedelta(minutes=1))
        self.assertEqual(len(a['checks']),3)
        self.assertTrue(a['complete'])
        self.assertEqual(a['snapshot_id'],b['snapshot_id'])
        self.assertEqual([p['offset'] for path,p in f.calls[:4]],[0,0,2,0])
        self.assertEqual(len(a['raw_pages']['checks']),2)

    def test_stale_preserved(self):
        result=self.collect(Fake(),NOW+timedelta(days=2))
        self.assertTrue(result['stale'])
        self.assertEqual(result['checks'][0]['result'],'passed')

    def test_reject_incomplete_and_changing(self):
        for mode in ('failure','mismatch','short','duplicate','partial','changing'):
            with self.subTest(mode=mode):
                f=Fake();f.mode=mode
                with self.assertRaises(CollectionError):self.collect(f)

    def test_summary_invalid(self):
        for key,value in [('hash_file','wrong'),('total_checks',4),('end_scan','2027-01-01T00:00:00Z'),
                          ('start_scan','2026-10-29T01:00:00Z'),('end_scan','2026-10-29 00:01:00')]:
            with self.subTest(key=key,value=value):
                f=Fake();f.summary[key]=value
                with self.assertRaises(CollectionError):self.collect(f)

    def test_bound_and_missing_policy(self):
        with self.assertRaises(CollectionError):Collector(Fake(),page_size=1,max_pages=1).collect('SYNTHETIC','p','abc',now=NOW)
        with self.assertRaises(CollectionError):Collector(Fake()).collect('SYNTHETIC','missing','abc',now=NOW)

    def test_order_independent_key(self):
        f=Fake();first=self.collect(f);f.checks.reverse()
        self.assertEqual(first['snapshot_id'],self.collect(f)['snapshot_id'])
