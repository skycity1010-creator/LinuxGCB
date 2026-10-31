"""P2B9 offline synthetic configuration and command-output checks."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from linuxgcb import batch9 as b, p2b9_runtime as rt
from linuxgcb.argv import w_strtok
from linuxgcb.catalog import ROOT
from linuxgcb.policy import simulate


class P2B9Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        old=rt.ROOT;rt.ROOT=self.tmp.name;self.addCleanup(setattr,rt,'ROOT',old)

    def put(self,path,text):
        p=Path(self.tmp.name+path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)

    def output(self,n,key=None):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            exec(b.script(n,key).replace("ROOT = ''",'ROOT = '+repr(self.tmp.name),1),{})
        return out.getvalue()

    def test_sources_argv_and_rule_values(self):
        self.assertEqual(set(b.sources()),set(range(109,132)))
        checks={c['id']:c for p in (ROOT/'policies').glob('*.yml') for c in json.loads(p.read_text())['checks']}
        for n,rules in b.rules().items():
            self.assertEqual(b.sources()[n]['category'],'網路設定')
            for target,pattern in rules:
                argv=w_strtok(target[2:]);self.assertEqual(argv[:2],['/usr/bin/python3','-c']);self.assertEqual(len(argv),3)
                self.assertNotIn('->',argv[2]);self.assertEqual(argv[2].count("print('PASS')"),1);compile(argv[2],'<candidate>','exec')
                if n<=125:
                    self.assertEqual(pattern,'^'+b.sources()[n]['expected']+'$')
            if n<=125:
                observations={target:dict(stdout=b.sources()[n]['expected']+'\n') for target,_ in rules}
                self.assertEqual(simulate(checks[900000+n],observations),'PASS')
                observations[rules[-1][0]]['stdout']='2\n'
                self.assertEqual(simulate(checks[900000+n],observations),'FAIL')

    def test_sysctl_exact_comments_spaces_conflicts_missing(self):
        for n,rules in b.rules().items():
            if n>125:continue
            for target,_ in rules:
                # Recover exact key argument from the generated script's check call.
                import ast
                tree=ast.parse(w_strtok(target[2:])[2])
                call=next(x for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='check')
                key=ast.literal_eval(call.args[1]);value=b.sources()[n]['expected']
                for text,want in [('',None),('# '+key+' = '+value,None),(key+'suffix = '+value,None),(key.replace('.all.','.default.')+' = '+value,None) if '.all.' in key else ('; '+key+' = '+value,None),('  '+key+'  =  '+value+'  # ok',value),(key+' = '+value+'\n'+key+' = 2',None),(key+' = 1 extra',None)]:
                    self.put('/etc/sysctl.d/test.conf',text);self.assertEqual(rt.check(n,key),want,(n,text))
                self.put('/etc/sysctl.d/test.conf',key+' = '+value)
                self.assertEqual(self.output(n,key),value+'\n')
        self.put('/usr/lib/sysctl.d/vendor.conf','net.ipv4.conf.all.rp_filter = 0')
        self.put('/etc/sysctl.d/test.conf','net.ipv4.conf.all.rp_filter = 1')
        self.assertIsNone(rt.check(121,'net.ipv4.conf.all.rp_filter'))

    def test_modules_exact_and_conflicting(self):
        for n,m in rt.MODULES.items():
            for text,want in [('',None),('# install '+m+' /bin/true\nblacklist '+m,None),('install '+m+'suffix /bin/true\nblacklist '+m,None),('install '+m+' /bin/false\nblacklist '+m,None),(' install '+m+' /bin/true # yes\n blacklist '+m+' ', 'PASS'),('install '+m+' /bin/true extra\nblacklist '+m,None)]:
                self.put('/etc/modprobe.d/test.conf',text);self.assertEqual(rt.check(n),want)
        self.put('/etc/modprobe.d/test.conf','install tipc /bin/true\nblacklist tipc')
        self.put('/etc/modprobe.d/conflict.conf','install tipc /bin/false')
        self.assertIsNone(rt.check(129))

    def test_commands_errors_and_wireless_fallback(self):
        for n,out in [(130,'disabled:disabled\n'),(131,'1: lo: <LOOPBACK,UP> mtu 65536\n')]:
            for code,err,want in [(0,'','PASS'),(1,'',None),(0,'denied',None)]:
                with patch.object(rt.shutil,'which',return_value='/usr/bin/nmcli'),patch.object(rt.subprocess,'run',return_value=subprocess.CompletedProcess([],code,out,err)) as run:
                    
                    if code or err:
                        with self.assertRaises(ValueError):rt.check(n)
                    else:
                        self.assertEqual(rt.check(n),want)
                    self.assertEqual(run.call_count,1)
                    self.assertEqual(run.call_args.args[0],['/usr/bin/nmcli','-t','-f','WIFI,WWAN','radio','all'] if n==130 else ['/usr/sbin/ip','link'])
            with patch('shutil.which',return_value='/usr/bin/nmcli'),patch('subprocess.run',side_effect=subprocess.TimeoutExpired('cmd',8)):
                self.assertEqual(self.output(n),'')
        for out in ['', 'garbage', '1: eth0: <UP,PROMISC> mtu 1500\n', '1: eth0: <UP> promiscuity 1\n']:
            with patch.object(rt.subprocess,'run',return_value=subprocess.CompletedProcess([],0,out,'')):
                if out:
                    self.assertIsNone(rt.check(131))
                else:
                    with self.assertRaises(ValueError):rt.check(131)
        with patch.object(rt.shutil,'which',return_value=None):
            self.assertIsNone(rt.check(130))
            self.put('/sys/class/net/wlan0/wireless/placeholder','')
            module=Path(self.tmp.name+'/sys/module/testwifi');module.mkdir(parents=True)
            link=Path(self.tmp.name+'/sys/class/net/wlan0/device/driver/module');link.parent.mkdir(parents=True);link.symlink_to(module)
            self.assertIsNone(rt.check(130))
            self.put('/etc/modprobe.d/wifi.conf','install testwifi /bin/true\nblacklist testwifi')
            self.assertEqual(rt.check(130),'PASS')
        for n in b.ADDED:
            with patch('builtins.open',side_effect=PermissionError),patch('glob.glob',side_effect=PermissionError),patch('shutil.which',return_value=None),patch('subprocess.run',side_effect=PermissionError):
                self.assertEqual(self.output(n,'net.ipv4.test'),'')

    def test_original_282_checks_unchanged(self):
        count=0
        for p in (ROOT/'policies').glob('*.yml'):
            old=json.loads(subprocess.check_output(['git','show','04a49c0:policies/'+p.name],cwd=ROOT))
            new={c['id']:c for c in json.loads(p.read_text())['checks']}
            self.assertEqual(old['policy'],json.loads(p.read_text())['policy'])
            for c in old['checks']:self.assertEqual(c,new[c['id']]);count+=1
        self.assertEqual(count,282)
        self.assertEqual(subprocess.check_output(['git','diff','--name-only','HEAD','--','tests/fixtures','tests/fix5_baseline.json','docs/*TEST_OUTPUT*'],cwd=ROOT,text=True),'')
