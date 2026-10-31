"""P2B7 isolated source predicates; no host configuration or scans are executed."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from linuxgcb import batch7, p2b7_runtime as rt
from linuxgcb.argv import w_strtok
from linuxgcb.catalog import ROOT
from linuxgcb.coverage import manifest


class P2B7Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        old = rt.ROOT
        rt.ROOT = self.tmp.name
        self.addCleanup(setattr, rt, 'ROOT', old)

    def put(self, p, text='', mode=None):
        dest = Path(self.tmp.name+p)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
        if mode is not None: dest.chmod(mode)
        return dest

    def tree(self):
        self.put('/etc/yum.conf','[main]\ngpgcheck=1\nlocalpkg_gpgcheck=1')
        self.put('/etc/dnf/dnf.conf','[main]\ngpgcheck=1\nlocalpkg_gpgcheck=1')
        self.put('/etc/yum.repos.d/local.repo','[local]\ngpgcheck=1\nlocalpkg_gpgcheck=1')
        self.put('/etc/sudoers','Defaults use_pty, logfile="/var/log/sudo.log"')
        self.put('/etc/cron.daily/aidecheck','#!/bin/bash\n/usr/sbin/aide --check',0o700)
        self.put('/etc/fstab','')
        self.put('/boot/grub2/grub.cfg','',0o600)
        self.put('/boot/grub2/grubenv','',0o600)
        self.put('/boot/grub2/user.cfg','GRUB2_PASSWORD=grub.pbkdf2.sha512.10000.ABC.DEF',0o600)
        for name in ('rescue','emergency'):
            self.put('/usr/lib/systemd/system/'+name+'.service','[Service]\nExecStart=-/usr/lib/systemd/systemd-sulogin-shell '+name)
        self.put('/etc/sysctl.conf','fs.suid_dumpable = 0\nkernel.core_pattern = |/bin/false\nkernel.randomize_va_space=2\nkernel.yama.ptrace_scope=1')
        self.put('/etc/security/limits.conf','* hard core 0')
        self.put('/etc/crypto-policies/config','FUTURE # comment')
        self.put('/proc/self/mountinfo','1 0 8:1 / / rw - xfs /dev/test rw')
        self.put('/etc/passwd','root:x:0:0::/root:/bin/bash\nuser:x:1000:1000::/home/user:/bin/bash')
        self.put('/etc/shadow','root:!:1:0:99999:7:::\nuser:!:1:0:99999:7:::')
        self.put('/etc/group','root:x:0:\nuser:x:1000:\nshadow:x:42:')
        self.put('/etc/profile','PATH="/usr/bin:/usr/sbin"\nexport PATH')
        Path(self.tmp.name+'/usr/bin').mkdir(parents=True,exist_ok=True)
        Path(self.tmp.name+'/usr/sbin').mkdir(parents=True,exist_ok=True)
        Path(self.tmp.name+'/usr/bin').chmod(0o755)
        Path(self.tmp.name+'/usr/sbin').chmod(0o755)
        Path(self.tmp.name+'/root').mkdir(exist_ok=True)
        Path(self.tmp.name+'/root').chmod(0o700)
        Path(self.tmp.name+'/home/user').mkdir(parents=True,exist_ok=True)
        Path(self.tmp.name+'/home/user').chmod(0o700)
        self.put('/etc/security/opasswd','',0o644)
        self.put('/etc/security/opasswd.old','',0o644)
        self.put('/etc/shells','/bin/bash\n# /sbin/nologin')
        self.put('/etc/sysconfig/chronyd','OPTIONS="-F 2"')

    def owner_stat(self, p, *args, **kwargs):
        st = list(self.real_stat(p,*args,**kwargs))
        user = str(p).startswith(self.tmp.name+'/home/user')
        st[4] = st[5] = 1000 if user else 0
        return os.stat_result(st)

    def test_scope_source_argv_and_no_secret_output(self):
        self.assertEqual(len(batch7.ADDED),48)
        m = manifest()
        self.assertEqual((m['counts']['included'],m['counts']['excluded'],m['counts']['implemented']),(307,7,305))
        for n, rules in batch7.rules().items():
            self.assertEqual(batch7.sources()[n]['category'],'系統設定與維護')
            argv = w_strtok(rules[0][0][2:])
            self.assertEqual(argv[:2],['/usr/bin/python3','-c'])
            self.assertEqual(len(argv),3)
            self.assertEqual(argv[2],batch7.script(n))
            self.assertNotIn('->',argv[2])
            self.assertEqual(argv[2].count("print('PASS')"),1)
            compile(argv[2],'<candidate>','exec')

    def test_all_48_positive_and_single_commit(self):
        self.tree()
        self.real_stat = os.stat
        with patch.object(rt.os,'stat',side_effect=self.owner_stat), patch.object(rt.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'','')) as run:
            for n in sorted(batch7.ADDED):
                if n == 36: run.return_value = subprocess.CompletedProcess([],0,'aide-test','')
                else: run.return_value = subprocess.CompletedProcess([],0,'','')
                program = batch7.script(n).replace("ROOT = ''",'ROOT = '+repr(self.tmp.name),1)
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    exec(program,{})
                self.assertEqual(out.getvalue(),'PASS\n',n)

    def test_all_missing_and_errors_never_commit(self):
        for n in batch7.ADDED:
            program = batch7.script(n).replace("ROOT = ''",'ROOT = '+repr(self.tmp.name),1)
            with patch('subprocess.run',side_effect=OSError('offline')),contextlib.redirect_stdout(io.StringIO()) as out:
                exec(program,{})
            self.assertEqual(out.getvalue(),'PASS\n' if n in (303,304) else '',n)
        self.tree()
        for n in batch7.ADDED:
            with patch('builtins.open',side_effect=PermissionError),patch.object(rt.os,'stat',side_effect=PermissionError),patch('subprocess.run',side_effect=subprocess.TimeoutExpired('offline',1)),contextlib.redirect_stdout(io.StringIO()) as out:
                exec(batch7.script(n).replace("ROOT = ''",'ROOT = '+repr(self.tmp.name),1),{})
            self.assertEqual(out.getvalue(),'',n)

    def test_sysctl_numeric_boundary_comments_and_prefix(self):
        for n,key,good in [(42,'fs.suid_dumpable',0),(43,'kernel.randomize_va_space',2),(307,'kernel.yama.ptrace_scope',1)]:
            self.put('/etc/security/limits.conf','* hard core 0')
            extra='\nkernel.core_pattern=|/bin/false' if n==42 else ''
            for text, expected in [(f' {key} = {good}  ',True),(f'# {key}={good}',False),(f'{key}_bad={good}',False),(f'{key}={good+1}',False),(f'{key}={good-1}',False)]:
                self.put('/etc/sysctl.conf',text+extra)
                self.assertEqual(rt.check(n),expected,(n,text))
        self.put('/etc/sysctl.conf','fs.suid_dumpable=0\nkernel.core_pattern=|/bin/false')
        self.put('/etc/security/limits.conf','* hard core 1')
        self.assertFalse(rt.check(42))
        self.put('/etc/sysctl.d/99-local.conf','fs.suid_dumpable=1')
        self.put('/etc/security/limits.conf','* hard core 0')
        self.assertFalse(rt.check(42))

    def test_rpm_three_states(self):
        for code, output, expected in [(0,'aide-1',True),(1,'not installed',False),(0,'',False)]:
            with patch.object(rt.subprocess,'run',return_value=subprocess.CompletedProcess([],code,output,'')) as run:
                self.assertEqual(rt.check(36),expected)
                self.assertEqual(run.call_args.args[0],['/usr/bin/rpm','-q','aide'])
        with patch.object(rt.subprocess,'run',return_value=subprocess.CompletedProcess([],2,'aide-1','')):
            with self.assertRaises(ValueError): rt.check(36)

    def test_find_fail_fast_scope_and_error(self):
        self.tree()
        self.put('/proc/self/mountinfo','1 0 8:1 / / rw - xfs /dev/test rw\n2 0 8:2 / /home rw - ext4 /dev/test2 rw\n3 0 0:1 / /proc rw - proc proc rw')
        for n in range(61,72):
            argv=rt.scan_argv(n,'/')
            self.assertIn('-xdev',argv)
            self.assertEqual(argv[-2:],['-print','-quit'])
            self.assertIn('-prune',argv)
            self.assertNotIn('-exec',argv)
            if n >= 66: self.assertNotIn(self.tmp.name+'/',argv)
            with patch.object(rt.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'/violation\n','')) as run:
                self.assertFalse(rt.check(n))
                self.assertEqual(run.call_count,1)
                self.assertLessEqual(run.call_args.kwargs['timeout'],24)
            for code,out,err in [(0,'','denied'),(1,'',''),(0,'violation','')]:
                with patch.object(rt.subprocess,'run',return_value=subprocess.CompletedProcess([],code,out,err)):
                    self.assertFalse(rt.check(n))
        with patch.object(rt.subprocess,'run',side_effect=subprocess.TimeoutExpired('find',24)), contextlib.redirect_stdout(io.StringIO()) as out:
            exec(batch7.script(61).replace("ROOT = ''",'ROOT = '+repr(self.tmp.name),1),{})
        self.assertEqual(out.getvalue(),'')

    def test_accounts_negative_and_lock(self):
        self.tree()
        self.put('/etc/shadow','root::1:0:99:7:::')
        self.assertFalse(rt.check(72))
        for field in ('!','!!','*','!locked'):
            self.put('/etc/shadow',f'root:{field}:1:0:99:7:::')
            self.assertTrue(rt.check(72))
        for n,p in [(75,'passwd'),(76,'shadow'),(77,'group')]:
            self.put('/etc/'+p,'+:\n')
            self.assertFalse(rt.check(n))
        self.tree()
        for n,p,line in [(78,'passwd','evil:x:0:0::/root:/bin/bash'),(87,'passwd','other:x:1000:1000::/home/other:/bin/bash'),(88,'group','other:x:1000:'),(89,'passwd','user:x:1001:1000::/home/user:/bin/bash'),(90,'group','user:x:1001:')]:
            self.tree()
            self.put('/etc/'+p,rt.read('/etc/'+p)+'\n'+line)
            self.assertFalse(rt.check(n),n)
        self.tree()
        self.put('/etc/group','root:x:0:\nshadow:x:42:')
        self.assertFalse(rt.check(86))
        self.put('/etc/group','root:x:0:\nuser:x:1000:\nshadow:x:42:user')
        self.assertFalse(rt.check(91))
        self.put('/etc/group','root:x:0:\nuser:x:1000:\nshadow:x:42:')
        self.put('/etc/passwd','root:x:0:0::/root:/bin/bash\nuser:x:1000:42::/home/user:/bin/bash')
        self.assertFalse(rt.check(91))

    def test_home_fail_fast_and_source_exclusions(self):
        self.tree()
        Path(self.tmp.name+'/home/user').chmod(0o750)
        self.assertFalse(rt.check(79))
        self.real_stat=os.stat
        with patch.object(rt.os,'stat',side_effect=self.owner_stat):
            self.assertTrue(rt.check(80)); self.assertTrue(rt.check(81))
        self.put('/home/user/.bashrc','',0o662)
        self.assertFalse(rt.check(82))
        for n,name in [(83,'.forward'),(84,'.netrc'),(85,'.rhosts')]:
            p=self.put('/home/user/'+name)
            self.assertFalse(rt.check(n))
            p.unlink()
            self.put('/root/'+name)
            self.assertTrue(rt.check(n)) # Source explicitly excludes root.
        Path(self.tmp.name+'/home/user/.bashrc').unlink()
        Path(self.tmp.name+'/home/user').rmdir()
        for n in range(79,86): self.assertFalse(rt.check(n),n)

    def test_path_static_subset_and_permissions(self):
        self.tree()
        for v in ('/bin::/sbin','.:/bin','../bin:/bin','bin:/bin','/bin/../sbin'):
            self.put('/etc/profile','PATH="'+v+'"')
            self.assertFalse(rt.check(73),v)
        self.put('/etc/profile','PATH="/usr/bin:/usr/sbin"')
        self.put('/root/.bashrc','PATH="$PATH:/root"')
        self.assertTrue(rt.check(73));self.assertTrue(rt.check(74))
        Path(self.tmp.name+'/usr/bin').chmod(0o775)
        self.assertFalse(rt.check(74))
        self.put('/root/.bashrc','PATH="$PATH_SUFFIX"')
        with self.assertRaises(ValueError): rt.check(73)
        self.put('/root/.bashrc','PATH="$(bad)"')
        with self.assertRaises(ValueError): rt.check(73)

    def test_source_config_negatives_and_opasswd_missing(self):
        self.tree()
        for n,p,bad in [(32,'/etc/dnf/dnf.conf','[other]\ngpgcheck=1\nlocalpkg_gpgcheck=1'),(34,'/etc/sudoers','# Defaults use_pty'),(35,'/etc/sudoers','Defaults logfile_bad="/log"'),(37,'/etc/cron.daily/aidecheck','# /usr/sbin/aide --check'),(40,'/boot/grub2/user.cfg','GRUB2_PASSWORD='),(41,'/usr/lib/systemd/system/rescue.service','ExecStart=/bin/bash'),(44,'/etc/crypto-policies/config','DEFAULT'),(305,'/etc/shells','/sbin/nologin'),(306,'/etc/sysconfig/chronyd','OPTIONS="-F 2 -u root"')]:
            self.put(p,bad)
            self.assertFalse(rt.check(n),n)
            self.tree()
        self.put('/var/spool/cron/root','0 5 * * * /usr/sbin/aide --check')
        Path(self.tmp.name+'/etc/cron.daily/aidecheck').unlink()
        self.assertTrue(rt.check(37))
        self.put('/var/spool/cron/root','0 25 * * * /usr/sbin/aide --check')
        self.assertFalse(rt.check(37))
        Path(self.tmp.name+'/etc/security/opasswd.old').unlink()
        self.real_stat = os.stat
        for n in (303,304):
            with patch.object(rt.os,'stat',side_effect=self.owner_stat), contextlib.redirect_stdout(io.StringIO()) as out:
                exec(batch7.script(n).replace("ROOT = ''",'ROOT = '+repr(self.tmp.name),1),{})
            self.assertEqual(out.getvalue(),'PASS\n')

    def test_chrony_options_conflicting_and_repeated(self):
        for options in ('-F 2 -F 0','-F 2 -u chrony -u root','-F 2 -uroot','-F 2 -u','-F 2 -F'):
            self.put('/etc/sysconfig/chronyd','OPTIONS="'+options+'"')
            self.assertFalse(rt.check(306),options)

    def test_repo_sections_and_owner_metadata(self):
        self.tree()
        self.put('/etc/yum.repos.d/local.repo','[first]\ngpgcheck=1\nlocalpkg_gpgcheck=1\n[second]\ngpgcheck=0\nlocalpkg_gpgcheck=1')
        self.assertFalse(rt.check(32))
        self.put('/etc/yum.repos.d/local.repo','[first]\ngpgcheck=1\nlocalpkg_gpgcheck=1\n[second]\ngpgcheck=1')
        self.assertFalse(rt.check(32))
        self.real_stat=os.stat
        with patch.object(rt.os,'stat',side_effect=self.owner_stat):
            self.assertTrue(rt.check(38));self.assertTrue(rt.check(303))
        with patch.object(rt.os,'stat',return_value=os.stat_result((0o100600,0,0,1,1234,1234,0,0,0,0))):
            self.assertFalse(rt.check(38));self.assertFalse(rt.check(303))
            self.assertFalse(rt.check(80));self.assertFalse(rt.check(81))

    def test_boot_branches_and_mode_bits(self):
        self.tree()
        self.put('/etc/fstab','UUID=example /boot/efi vfat uid=0,gid=0,fmask=0177 0 2')
        self.assertTrue(rt.check(38));self.assertTrue(rt.check(39))
        self.put('/etc/fstab','UUID=example /boot/efi vfat uid=0,gid=1,fmask=0077 0 2')
        self.assertFalse(rt.check(38));self.assertFalse(rt.check(39))
        self.put('/etc/fstab','')
        self.assertTrue(rt.check(39))
        Path(self.tmp.name+'/boot/grub2/grub.cfg').chmod(0o640)
        self.assertFalse(rt.check(39))
        for mode,expected in [(0o644,True),(0o600,True),(0o664,False),(0o1644,False)]:
            self.put('/etc/security/opasswd','',mode)
            self.assertEqual(rt.check(304),expected)

    def test_original_188_rules_and_evidence_unchanged(self):
        old={};new={}
        for p in sorted((ROOT/'policies').glob('*.yml')):
            old.update({c['id']:c for c in json.loads(subprocess.check_output(['git','show','6788fdc:policies/'+p.name],cwd=ROOT))['checks']})
            new.update({c['id']:c for c in json.loads(p.read_text())['checks']})
        self.assertEqual(len(old),188);self.assertEqual(len(new),305)
        self.assertEqual(old,{n:new[n] for n in old})
        names=subprocess.check_output(['git','diff','--name-only','971fbc51601a08352ee80aadb15a23a68e4aab78','--','tests/fixtures','tests/fix5_baseline.json','docs/*TEST_OUTPUT*','docs/P2B6_REVIEW.md'],cwd=ROOT,text=True)
        self.assertEqual(names,'')
