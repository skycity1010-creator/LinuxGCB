"""Offline predicates against isolated trees; never read host configuration."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from linuxgcb import batch6
from linuxgcb import p2b6_runtime as rt
from linuxgcb.argv import w_strtok


class P2B6Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.old = rt.ROOT
        rt.ROOT = self.tmp.name
        self.addCleanup(setattr, rt, 'ROOT', self.old)

    def put(self, path, text):
        dest = Path(self.tmp.name + path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)

    def test_scope_source_and_argv(self):
        self.assertEqual(len(batch6.ADDED), 42)
        for n, rules in batch6.rules().items():
            self.assertEqual(batch6.sources()[n]['category'], '帳號與存取控制')
            argv = w_strtok(rules[0][0][2:])
            self.assertEqual(argv[:2], ['/usr/bin/python3', '-c'])
            self.assertEqual(argv[2], batch6.script(n))
            self.assertEqual(argv[2].count("print('PASS')"), 1)
            compile(argv[2], '<candidate>', 'exec')

    def test_numeric_boundaries_and_comments(self):
        cases = {206:('retry',1,3),208:('minlen',12,None),209:('minclass',4,4),
                 210:('dcredit',None,-1),211:('ucredit',None,-1),212:('lcredit',None,-1),213:('ocredit',None,-1),
                 214:('difok',3,None),215:('maxclassrepeat',1,4),216:('maxrepeat',1,3),217:('dictcheck',1,1),311:('maxsequence',1,3)}
        self.put('/etc/login.defs','PASS_MIN_LEN 12\n')
        for n,(key,low,high) in cases.items():
            good = low if low is not None else high
            path='/etc/security/pwquality.conf'
            for text, expected in [(f'  {key} = {good}  \n',True),(f'# {key}={good}\n',False),(f'{key}_wrong={good}\n',False)]:
                self.put(path,text)
                self.assertEqual(rt.check(n),expected,(n,text))
            for bad in ([low-1] if low is not None else []) + ([high+1] if high is not None else []):
                self.put(path,f'{key}={bad}\n')
                self.assertFalse(rt.check(n),n)

    def test_source_defaults(self):
        cases={218:('/etc/security/faillock.conf','deny = 5','deny = 0'),219:('/etc/security/faillock.conf','unlock_time=900','unlock_time=899'),
               223:('/etc/login.defs','PASS_MIN_DAYS 1','PASS_MIN_DAYS 0'),224:('/etc/login.defs','PASS_WARN_AGE 14','PASS_WARN_AGE 13'),
               225:('/etc/login.defs','PASS_MAX_DAYS 90','PASS_MAX_DAYS 91'),226:('/etc/default/useradd','INACTIVE=30','INACTIVE=0'),
               227:('/etc/login.defs','FAIL_DELAY 4','FAIL_DELAY 3'),228:('/etc/login.defs','CREATE_HOME yes','CREATE_HOME no'),
               240:('/etc/login.defs','UMASK 027','UMASK 022'),310:('/etc/security/faillock.conf','even_deny_root\nroot_unlock_time=60','even_deny_root\nroot_unlock_time=59')}
        for n,(path,good,bad) in cases.items():
            self.put(path,good);self.assertTrue(rt.check(n),n)
            self.put(path,bad);self.assertFalse(rt.check(n),n)
            self.put(path,'# '+good.replace('\n','\n# '));self.assertFalse(rt.check(n),n)

    def test_pam_and_symlink(self):
        good='password requisite pam_pwquality.so local_users_only enforce_for_root\nauth sufficient pam_unix.so\naccount required pam_unix.so\npassword sufficient pam_unix.so sha512 shadow use_authtok\nsession required pam_unix.so\npassword required pam_pwhistory.so remember=3\n'
        self.put('/etc/pam.d/system-auth',good)
        self.put('/etc/authselect/password-auth',good)
        Path(self.tmp.name+'/etc/pam.d/password-auth').symlink_to('../authselect/password-auth')
        for n in (207,220,312,313,314): self.assertTrue(rt.check(n),n)
        self.put('/etc/pam.d/system-auth',good.replace('pam_unix.so','pam_unix.so nullok'))
        self.assertFalse(rt.check(312))
        self.put('/etc/pam.d/system-auth',good.replace('remember=3','remember=2'))
        self.assertFalse(rt.check(220))
        self.put('/etc/libuser.conf','crypt_style = sha512')
        self.put('/etc/login.defs','ENCRYPT_METHOD SHA512')
        self.assertTrue(rt.check(222))
        self.put('/etc/pam.d/postlogin','session required pam_lastlog.so showfailed')
        self.assertTrue(rt.check(221))
        self.put('/etc/pam.d/su','auth required pam_wheel.so use_uid')
        self.put('/etc/group','wheel:x:10:root,user1')
        self.assertTrue(rt.check(241))

    def test_desktop_and_account_and_shell(self):
        self.put('/etc/dconf/db/local.d/00-screensaver','[org/gnome/desktop/screensaver]\nlock-enabled=true\n[org/gnome/desktop/session]\nidle-delay=uint32 900')
        for n in (232,233):self.assertTrue(rt.check(n))
        self.put('/etc/dconf/db/local.d/00-screensaver','[wrong]\nlock-enabled=true\nidle-delay=uint32 900')
        for n in (232,233):self.assertFalse(rt.check(n))
        self.put('/etc/dconf/db/local.d/locks/session','\n'.join('/org/gnome/desktop/'+s for s in ('session/idle-delay','screensaver/lock-enabled','screensaver/lock-delay','lockdown/disable-lock-screen')))
        self.assertTrue(rt.check(237))
        self.put('/etc/gdm/custom.conf','[daemon]\nAutomaticLoginEnable=false')
        self.assertTrue(rt.check(234))
        self.put('/etc/login.defs','UID_MIN 1000')
        self.put('/etc/passwd','root:x:0:0:root:/root:/bin/bash\ndaemon:x:2:2::/:/sbin/nologin')
        with patch.object(rt.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'daemon LK 2026-01-01','')):
            self.assertTrue(rt.check(235));self.assertTrue(rt.check(238))
        for p in ('/etc/bashrc','/etc/profile','/root/.bashrc','/root/.bash_profile'):
            self.put(p,'umask 027\nreadonly TMOUT=900 ; export TMOUT')
        for n in (236,239,309):self.assertTrue(rt.check(n))
        self.put('/etc/bashrc','umask 022\nTMOUT=0')
        for n in (236,239):self.assertFalse(rt.check(n))
        self.put('/etc/security/limits.conf','* hard maxlogins 10')
        self.assertTrue(rt.check(230))
        self.put('/etc/security/limits.conf','* hard maxlogins 11')
        self.assertFalse(rt.check(230))
        self.put('/etc/sudoers','# NOPASSWD\nroot ALL=(ALL) ALL')
        self.assertTrue(rt.check(229))
        self.put('/etc/sudoers','root ALL=(ALL) NOPASSWD: ALL')
        self.assertFalse(rt.check(229))

    def test_rpm_three_states(self):
        for rc,expect in ((0,True),(1,False)):
            with patch.object(rt.subprocess,'run',return_value=subprocess.CompletedProcess([],rc,'kbd-1' if rc==0 else 'not installed','')) as run:
                self.assertEqual(rt.check(231),expect)
                self.assertEqual(run.call_args.args[0],['/usr/bin/rpm','-q','kbd'])
        with patch.object(rt.subprocess,'run',return_value=subprocess.CompletedProcess([],2,'kbd-1','')):
            with self.assertRaises(ValueError):rt.check(231)

    def test_missing_never_commits(self):
        for n in sorted(batch6.ADDED):
            script=batch6.script(n).replace("ROOT = ''",'ROOT = '+repr(self.tmp.name),1)
            # Mock subprocess so no host package query is performed.
            namespace={}
            with patch('subprocess.run',side_effect=OSError('offline')),contextlib.redirect_stdout(io.StringIO()) as out:
                exec(script,namespace)
            self.assertEqual(out.getvalue(),'',n)

    def test_original_146_rules_unchanged(self):
        root=Path(__file__).resolve().parents[1]
        baseline={}
        current={}
        for p in sorted((root/'policies').glob('*.yml')):
            old=json.loads(subprocess.check_output(['git','show','d2bd3ae:policies/'+p.name],cwd=root))
            baseline.update({c['id']:c['rules'] for c in old['checks']})
            current.update({c['id']:c['rules'] for c in json.loads(p.read_text())['checks']})
        self.assertEqual(len(baseline),146)
        self.assertEqual(len(current),236)
        self.assertEqual(baseline,{n:current[n] for n in baseline})
