"""P2B8 predicates run on synthetic trees and mocked subprocesses only."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from linuxgcb import batch8 as b, p2b8_runtime as rt
from linuxgcb.argv import w_strtok
from linuxgcb.catalog import ROOT
from linuxgcb.coverage import manifest


class P2B8Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        old=rt.ROOT; rt.ROOT=self.tmp.name; self.addCleanup(setattr,rt,'ROOT',old)

    def put(self,path,text):
        p=Path(self.tmp.name+path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)

    def tree(self):
        self.put('/etc/modprobe.d/local.conf','\n'.join('install '+m+' /bin/true\nblacklist '+m for m in rt.MODULES.values()))
        paths=['/','/tmp','/var','/var/tmp','/var/log','/var/log/audit','/home','/dev/shm','/media/disk','/home/alice','/mnt/nfs']
        self.put('/proc/mounts','\n'.join(f'/dev/d{i} {p} '+('tmpfs' if p in ('/tmp','/dev/shm') else 'nfs4' if p=='/mnt/nfs' else 'xfs')+' rw,nodev,nosuid,noexec 0 0' for i,p in enumerate(paths)))
        self.put('/proc/self/mountinfo','\n'.join(f'{i+1} 0 8:{i} / {p} rw,nodev,nosuid,noexec - xfs /dev/d{i} rw' for i,p in enumerate(paths)))
        for i in range(11): self.put('/sys/class/block/d'+str(i)+'/removable','1')
        self.put('/etc/login.defs','UID_MIN 1000\n')
        self.put('/etc/passwd','alice:x:1000:1000::/home/alice:/bin/bash\nnobody:x:65534:65534::/nonexistent:/sbin/nologin')

    def output(self,n):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            exec(b.script(n).replace("ROOT = ''",'ROOT = '+repr(self.tmp.name),1),{})
        return out.getvalue()

    def test_all_sources_argv_and_single_commit(self):
        self.assertEqual(len(b.ADDED),46);self.assertEqual(len(rt.MODULES),20)
        self.assertEqual(manifest()['counts']['implemented'],307)
        self.tree()
        def run(argv,**kwargs):
            return subprocess.CompletedProcess(argv,0,'Filesystem 1024-blocks Used Available Capacity Mounted on\n/dev/d0 10 1 9 10% /\n' if argv[0].endswith('/df') else '','')
        with patch.object(rt.subprocess,'run',side_effect=run):
            for n in sorted(b.ADDED):
                self.assertEqual(b.sources()[n]['category'],'磁碟與檔案系統')
                argv=w_strtok(b.rules()[n][0][0][2:]); self.assertEqual(argv[:2],['/usr/bin/python3','-c']);self.assertEqual(len(argv),3)
                self.assertEqual(argv[2],b.script(n));self.assertNotIn('->',argv[2]);self.assertEqual(argv[2].count("print('PASS')"),1)
                compile(argv[2],'<candidate>','exec')
                self.assertEqual(self.output(n),'PASS\n',n)

    def test_module_exact_values_comments_missing_conflicts(self):
        for n,module in rt.MODULES.items():
            for text,expected in [('',False),('# install '+module+' /bin/true\n# blacklist '+module,False),(' install '+module+' /bin/true  # ok\n blacklist '+module+' ',True),('install '+module+'suffix /bin/true\nblacklist '+module,False),('install '+module+' /bin/false\nblacklist '+module,False),('install '+module+' /bin/true extra\nblacklist '+module,False)]:
                self.put('/etc/modprobe.d/test.conf',text);self.assertEqual(rt.check(n),expected,(n,text))
        self.put('/etc/modprobe.d/test.conf','install cramfs /bin/true\nblacklist cramfs')
        self.put('/etc/modprobe.d/other.conf','install cramfs /bin/false')
        self.assertFalse(rt.check(1))

    def test_mount_tokens_missing_comments_and_bind(self):
        self.tree()
        for n,(path,opt) in rt.FIXED.items():
            self.put('/proc/mounts',f'# /dev/x {path} xfs rw,{opt} 0 0\n/dev/x / xfs rw 0 0')
            self.assertFalse(rt.check(n))
            self.put('/proc/mounts',f'/dev/x {path} xfs rw,{opt}_bad 0 0')
            self.assertFalse(rt.check(n))
            self.put('/proc/mounts',f'/dev/x {path} xfs rw,{opt} 0 0');self.assertTrue(rt.check(n))
        self.tree()
        for n,path in rt.PARTITIONS.items():
            for dev,root in [('8:0','/'),('8:90','/subdir'),('0:90','/')]:
                self.put('/proc/self/mountinfo',f'1 0 8:0 / / rw - xfs /dev/root rw\n2 1 {dev} {root} {path} rw - xfs /dev/x rw')
                self.assertFalse(rt.check(n),(n,dev,root))
        self.put('/proc/mounts','/dev/x /tmp xfs rw 0 0');self.assertFalse(rt.check(4))

    def test_conditional_review_and_option_fail(self):
        self.tree()
        self.put('/proc/mounts','/dev/root / xfs rw 0 0')
        with patch.object(rt,'removable',return_value=False):
            for n in range(20,29):self.assertIsNone(rt.check(n),n)
        for n in range(20,29):self.assertEqual(self.output(n),'PASS\n' if n in (23,24,25) else 'REVIEW\n',n)
        self.tree()
        self.put('/proc/mounts','/dev/usb /media/x xfs rw 0 0\nhost:/export /mnt/nfs nfs rw 0 0\n/dev/d9 /home/alice xfs rw 0 0')
        with patch.object(rt,'removable',return_value=True):
            for n in range(20,29):self.assertFalse(rt.check(n),n)

    def test_sysfs_partition_parent(self):
        self.put('/sys/class/block/sdb/sdb1/partition','1')
        self.put('/sys/class/block/sdb/removable','1\n')
        base=Path(self.tmp.name+'/sys/class/block');(base/'sdb1').symlink_to(base/'sdb/sdb1')
        self.assertTrue(rt.removable('/dev/sdb1'))
        self.put('/sys/class/block/sdb/removable','0');self.assertFalse(rt.removable('/dev/sdb1'))
        self.assertIsNone(rt.removable('/dev/missing'))

    def test_scan_fail_fast_errors_timeout(self):
        argv=rt.scan_argv('/');self.assertIn('-xdev',argv);self.assertEqual(argv[-2:],['-print','-quit'])
        df=subprocess.CompletedProcess([],0,'header\n/dev/a 10 1 9 10% /\n/dev/b 10 1 9 10% /home\n','')
        for code,out,err in [(0,'/bad\n',''),(1,'',''),(0,'','denied')]:
            with patch.object(rt.subprocess,'run',side_effect=[df,subprocess.CompletedProcess([],code,out,err)]) as run:
                self.assertFalse(rt.check(29));self.assertEqual(run.call_count,2)
        with patch.object(rt.subprocess,'run',side_effect=subprocess.TimeoutExpired('find',24)):
            self.assertEqual(self.output(29),'')
        for n in b.ADDED:
            with patch('builtins.open',side_effect=PermissionError),patch('glob.glob',side_effect=PermissionError),patch('subprocess.run',side_effect=OSError):
                self.assertEqual(self.output(n),'',n)

    def test_original_236_rules_and_protected_artifacts(self):
        count=0
        for p in (ROOT/'policies').glob('*.yml'):
            old=json.loads(subprocess.check_output(['git','show','d5e32f0:policies/'+p.name],cwd=ROOT))
            new={c['id']:c for c in json.loads(p.read_text())['checks']}
            for c in old['checks']:self.assertEqual(c,dict(new[c['id']],rules=c['rules']) if c['id'] in {900023,900024,900025,900073,900074,900091} else new[c['id']]);count+=1
        self.assertEqual(count,236)
        self.assertEqual(subprocess.check_output(['git','diff','--name-only','21e56dbc1040ce26defdb972bf7e12a37de382d2','--','tests/fixtures','tests/fix5_baseline.json','docs/*TEST_OUTPUT*'],cwd=ROOT,text=True),'')
