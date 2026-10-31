"""P2B3 test-only trees. Never execute endpoint commands or read host configs."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from linuxgcb.argv import w_strtok
from linuxgcb.batch3 import ADDED, AUDIT, PACKAGES, audit_lines, rules, script
from linuxgcb.catalog import ROOT, digest, registry
from linuxgcb.policy import parse_rule, simulate, validate
from scripts.p2b3_fixtures import inputs, outputs


class P2B3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'tests/fixtures/p2b3/cases.json').read_text())
        cls.checks={c['id']:c for p in (ROOT/'policies').glob('*.yml') for c in json.loads(p.read_text())['checks']}

    def tree(self,n): return copy.deepcopy(self.data['inputs'][str(900000+n)]['positive'])

    def run_tree(self,n,data,fail_read=False):
        """Execute actual embedded script against temp files and mocked systemctl/RPM.

        stat uid/gid are test data because this test must not chown or use sudo.
        All paths inside the emitted program are redirected to the test-only tree.
        """
        self.assertNotEqual(n,92)
        with tempfile.TemporaryDirectory(prefix='p2b3-test-only-', dir=ROOT) as folder:
            for name,content in data['files'].items():
                path=Path(folder+name);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
            for name,mode in data['modes'].items():
                path=Path(folder+name)
                if not path.exists(): path.mkdir(parents=True)
                if path.is_file(): path.chmod(mode)
            real_stat=os.stat
            def fake_stat(path,*args,**kwargs):
                if data.get('stat_error') and os.fspath(path) == folder + data['stat_error']:
                    raise PermissionError('test-only stat denied')
                info=real_stat(path,*args,**kwargs)
                name=os.fspath(path)
                owner=data['owners'].get(name[len(folder):]) if isinstance(name,str) and name.startswith(folder) else None
                fields=list(info)
                if owner: fields[4:6]=owner
                relative=name[len(folder):] if isinstance(name,str) and name.startswith(folder) else None
                if relative in data['modes']: fields[0]=stat.S_IFMT(info.st_mode) | data['modes'][relative]
                return os.stat_result(fields)
            def fake_command(argv,**kwargs):
                cmd=data['commands']
                if argv[0]=='/bin/sh' and 'rpm -q ' in argv[2]:
                    rc=cmd.get('rpm',127)
                    return subprocess.CompletedProcess(argv,0 if rc in (0,1) else rc,
                                                       'INSTALLED\n' if rc==0 else 'ABSENT\n' if rc==1 else '', '')
                self.assertEqual(argv[:2],['/usr/bin/systemctl','show'])
                self.assertTrue(argv[2].endswith(('.service','.socket')))
                self.assertTrue(all(x.startswith('--property=') for x in argv[3:]))
                cmd={**cmd, **cmd.get('units',{}).get(argv[2],{})}
                return subprocess.CompletedProcess(argv,cmd.get('systemctl_error',0),
                    'LoadState='+cmd.get('load','')+'\nActiveState='+cmd.get('active','')+'\nUnitFileState='+cmd.get('unit','')+'\n','')
            program=script(n).replace("ROOT = ''",'ROOT = '+repr(folder),1)
            # Check the exact shell and Python argument round trip before execution.
            argv=w_strtok(rules()[n][0][0][2:]);self.assertEqual(argv[:2],['/bin/sh','-c'])
            self.assertEqual(shlex.split(argv[2]),['/usr/bin/python3','-c',script(n)])
            capture=io.StringIO()
            with patch('os.stat',side_effect=fake_stat),patch('subprocess.run',side_effect=fake_command),contextlib.redirect_stdout(capture):
                if fail_read:
                    with patch('builtins.open',side_effect=PermissionError('test-only denied')): exec(compile(program,'<test-only emitted script>','exec'),{})
                else: exec(compile(program,'<test-only emitted script>','exec'),{})
            return capture.getvalue()

    def test_scope_baseline_sources_and_status(self):
        before=json.loads((ROOT/'tests/fixtures/p2b3/baseline.json').read_text())
        self.assertEqual(len(before['checks']),97)
        for c in before['checks']: self.assertEqual(self.checks[c['id']],c)
        for name,sha in before['protected_hashes'].items(): self.assertEqual(digest(ROOT/name),sha,name)
        self.assertEqual(len(ADDED),49);self.assertEqual(len(self.checks),146);self.assertEqual(validate(),146)
        rows=registry();self.assertEqual((len(rows),sum(r['included'] for r in rows)),(314,307))
        self.assertEqual({r['sca_id'] for r in rows if r['implementation']=='candidate'}-{c['id'] for c in before['checks']},{900000+n for n in ADDED})
        for row in rows:
            if row['sca_id']-900000 in ADDED:
                self.assertEqual(row['review_status'],'human_review_pending')
                self.assertEqual(row['execution_review'],'blocked');self.assertEqual(row['live_validation'],'UNVALIDATED')
        manifest=json.loads((ROOT/'data/coverage_manifest.json').read_text())
        self.assertEqual(manifest['counts']['implemented'],146)
        for row in manifest['reviewed']:
            if row['sca_id']-900000 in ADDED:
                self.assertIn('tests/test_p2b3.py',row['tests'])
                self.assertIn('UNVALIDATED',row['caveats'])

    def test_all_49_fixture_output_matrix(self):
        self.assertEqual(self.data['label'],'SYNTHETIC TEST ONLY')
        self.assertEqual(self.data['inputs'],inputs());self.assertEqual(self.data['checks'],outputs())
        for n in sorted(ADDED):
            check=self.checks[900000+n];cases=self.data['checks'][str(900000+n)]
            for case,obs in cases.items():
                want='PASS' if case in ('positive','nonzero_matching') else 'UNRESOLVED' if case in ('missing','error') else 'FAIL'
                with self.subTest(n=n,case=case): self.assertEqual(simulate(check,obs),want)
            # All programs emit at most one result. 256-line truncation cannot hide a bad member.
            for obs in cases['positive'].values(): self.assertLessEqual(len(obs['stdout'].splitlines()),1)
            for rule in check['rules']: parse_rule(rule)

    def test_real_parsers_positive_negative_missing_empty_error(self):
        for n in sorted(ADDED-{92}):
            cases=self.data['inputs'][str(900000+n)]
            for name,want in (('positive','PASS\n'),('negative','')):
                with self.subTest(n=n,case=name): self.assertEqual(self.run_tree(n,cases[name]),want)
            for name in ('missing','empty','error'):
                data=self.tree(n)
                if name=='missing': data['files']={};data['modes']={};data['commands']={}
                elif name=='empty': data['files']={p:'' for p in data['files']};data['commands']={}
                else: data['commands']={'rpm':2,'systemctl_error':1}
                # Metadata-only checks need an explicit stat error, rather than empty file data.
                if n in (143,144) and name=='empty': data['files']={};data['modes']={}
                if n in (143,144) and name=='error': data['stat_error']='/sbin/auditctl'
                with self.subTest(n=n,case=name): self.assertEqual(self.run_tree(n,data,fail_read=name=='error' and n not in (95,96,99,100,143,144)), 'PASS\n' if n in (143,144) and name in ('missing','empty') else '')

    def test_every_audit_predicate_comments_tokens_boundaries_uid_min(self):
        for n in sorted(AUDIT):
            data=self.tree(n);path='/etc/audit/rules.d/audit.rules';lines=audit_lines(n)
            self.assertTrue(lines)
            for line in lines:
                for changed in ('# '+line, line+'-suffix',line.replace('-k ', '-k WRONG-',1).replace('key=execpriv','key=WRONG')):
                    variant=copy.deepcopy(data);variant['files'][path]=variant['files'][path].replace(line+'\n',changed+'\n')
                    with self.subTest(n=n,line=line,changed=changed): self.assertEqual(self.run_tree(n,variant),'')
            if 'auid>=1000' in data['files'][path]:
                data['files']['/etc/login.defs']='UID_MIN 500\n# UID_MIN 1000\nUID_MIN 2000\n'
                self.assertEqual(self.run_tree(n,data),'')
                data['files'][path]=data['files'][path].replace('auid>=1000','auid>=2000')
                self.assertEqual(self.run_tree(n,data),'PASS\n')
        data=self.tree(148);data['files']['/etc/audit/rules.d/audit.rules']='-w /etc/sudoers.d/ -p wa -k scope\n'
        self.assertEqual(self.run_tree(148,data),'')
        # A missing rule beyond 256 lines must still cause failure; required late rules still count.
        for n in (148,154,172):
            data=self.tree(n);path='/etc/audit/rules.d/audit.rules';data['files'][path]='# padding\n'*600+data['files'][path]
            self.assertEqual(self.run_tree(n,data),'PASS\n')
            data['files'][path]+='\n# unrelated trailing content'
            data['files'][path]=data['files'][path].replace(audit_lines(n)[-1],'# removed')
            self.assertEqual(self.run_tree(n,data),'')

    def test_effective_values_and_permission_masks(self):
        for n,key,good,bad in ((146,'max_log_file','32','31'),(147,'max_log_file_action','keep_logs','rotate')):
            for tail,want in ((bad,''),(good,'PASS\n')):
                data=self.tree(n);data['files']['/etc/audit/auditd.conf']=key+' = '+good+'\n# '+key+' = '+bad+'\n'+key+' = '+tail+'\n'
                self.assertEqual(self.run_tree(n,data),want)
        for value in ('0','31','32','33','999999','32x','-32'):
            data=self.tree(146);data['files']['/etc/audit/auditd.conf']='max_log_file='+value+'\n'
            self.assertEqual(self.run_tree(146,data),'PASS\n' if value.isdigit() and int(value)>=32 else '')
        for n,path,mask in ((138,'/var/log/audit/audit.log',0o600),(140,'/var/log/audit',0o700),(143,'/sbin/auditd',0o750),(308,'/var/log/rsyslog',0o750)):
            for mode in (0,0o400,mask,0o777,0o1750,0o2640,0o4750):
                data=self.tree(n);data['modes'][path]=mode
                self.assertEqual(self.run_tree(n,data),'PASS\n' if mode & ~mask==0 else '',(n,mode))
        data=self.tree(138);data['files']['/etc/audit/auditd.conf']+='log_file=/missing\n'
        self.assertEqual(self.run_tree(138,data),'')

    def test_journal_dropins_sections_defaults_and_errors(self):
        for n,key,good,bad in ((181,'Compress','yes','no'),(182,'Storage','persistent','volatile')):
            for content,want in (('#'+key+'='+good,''),('[Other]\n'+key+'='+good,''),('[Journal]\n'+key+'='+good,'PASS\n'),('[Journal]\n'+key+'='+good+'\n'+key+'='+bad,'')):
                data=self.tree(n);data['files']['/etc/systemd/journald.conf']=content
                self.assertEqual(self.run_tree(n,data),want)
            data=self.tree(n);data['files']['/usr/lib/systemd/journald.conf.d/10-site.conf']='[Journal]\n'+key+'='+bad
            self.assertEqual(self.run_tree(n,data),'')
            data['files']['/etc/systemd/journald.conf.d/10-site.conf']='[Journal]\n'+key+'='+good
            self.assertEqual(self.run_tree(n,data),'PASS\n')
            data['files']['/run/systemd/journald.conf.d/99-local.conf']='[Journal]\n'+key+'='+bad
            self.assertEqual(self.run_tree(n,data),'')

    def test_services_and_rpm_errors_and_v3(self):
        for n in (95,96,99,100):
            for load,unit,active,want in (('loaded','masked','inactive',True),('loaded','disabled','inactive',True),('not-found','','inactive',True),('loaded','enabled','inactive',False),('masked','masked','active',False),('','','',False)):
                data=self.tree(n);data['commands'].update(load=load,unit=unit,active=active)
                self.assertEqual(self.run_tree(n,data),'PASS\n' if want else '')
            data=self.tree(n);data['commands']['systemctl_error']=1
            self.assertEqual(self.run_tree(n,data),'')
        data=self.tree(95);data['commands']['units']={'avahi-daemon.socket':{'active':'active'}}
        self.assertEqual(self.run_tree(95,data),'')
        for n in (96,99,100):
            for rc,want in ((1,'PASS\n'),(2,''),(3,''),(126,''),(127,'')):
                data=self.tree(n);data['commands']['rpm']=rc
                self.assertEqual(self.run_tree(n,data),want)
        for n in (96,99,100):
            data=self.tree(n);data['commands'].update(rpm=1,active='active',unit='enabled')
            self.assertEqual(self.run_tree(n,data),'')
        data=self.tree(96);data['commands'].update(active='active',unit='enabled');data['files']['/etc/snmp/snmpd.conf']='rouser test_only_user priv\n'
        self.assertEqual(self.run_tree(96,data),'PASS\n')
        for line in ('rocommunity public','com2sec user default public','rouser insecure noauth','includeFile /test-only','rwuser writable priv'):
            bad=copy.deepcopy(data);bad['files']['/etc/snmp/snmpd.conf']+=line+'\n'
            self.assertEqual(self.run_tree(96,bad),'')
        # Execute the exact FIX3 shell, replacing only rpm with an inert printf/exit.
        targets=[w_strtok(rules()[92][0][0][2:])[2]]
        from linuxgcb import p2b3_runtime
        for package in ('net-snmp','vsftpd','ypserv'):
            targets.append('out=$(rpm -q '+package+' 2>/dev/null); rc=$?; case $rc in 0) echo INSTALLED;; 1) echo ABSENT;; *) exit $rc;; esac')
        self.assertIn('case $rc in 0) echo INSTALLED;; 1) echo ABSENT;;',__import__('inspect').getsource(p2b3_runtime.package_state))
        for body in targets:
            for rc in (0,1,2,3,126,127):
                start=body.index('rpm -q ');end=body.index(' 2>/dev/null',start)
                fake="printf 'ABSENT\\nPASS\\n'; exit "+str(rc)
                result=subprocess.run(['/bin/sh','-c',body[:start]+fake+body[end:]],capture_output=True,text=True,timeout=5)
                self.assertEqual(result.stdout,'INSTALLED\n' if rc==0 else 'ABSENT\n' if rc==1 else '')
                self.assertEqual(result.returncode,0 if rc in (0,1) else rc)

    def test_rsyslog_new_old_syntax_and_logrotate(self):
        for line in ('auth.*,authpriv.* ,daemon.* /var/log/secure', 'auth.*;authpriv.*;daemon.* action(type="omfile" file="/var/log/secure")', 'auth.* /var/log/secure\nauthpriv.* /var/log/secure\ndaemon.* /var/log/secure'):
            data=self.tree(177);data['files']['/etc/rsyslog.conf']=line
            self.assertEqual(self.run_tree(177,data),'PASS\n')
            for bad in ('#'+line,line.replace('omfile','omfwd'),line.replace('/var/log/secure','/var/log/secure.other'),line.replace('daemon.*','daemon.none')):
                if bad==line: continue
                data['files']['/etc/rsyslog.conf']=bad
                self.assertEqual(self.run_tree(177,data),'')
        for line,want in (('$FileCreateMode 0600','PASS\n'),('$FileCreateMode 0644',''),('$FileCreateMode 0640\naction(type="omfile" file="/var/log/test" fileCreateMode="0666")',''),('$FileCreateMode 0640\n$FileCreateMode 9999','')):
            data=self.tree(176);data['files']['/etc/rsyslog.conf']=line
            self.assertEqual(self.run_tree(176,data),want)
        for token in ('weekly','rotate 4','compress','missingok','notifempty','postrotate','endscript'):
            data=self.tree(308);path='/etc/logrotate.d/rsyslog';data['files'][path]=data['files'][path].replace(token,'# removed '+token)
            self.assertEqual(self.run_tree(308,data),'')

    def test_dynamic_privileged_sudo_and_immutable(self):
        data=self.tree(158);data['files']['/opt/new-privileged']='test-only';data['modes']['/opt/new-privileged']=0o2750
        self.assertEqual(self.run_tree(158,data),'')
        data['files']['/etc/audit/rules.d/privileged.rules']+='-a always,exit -F path=/opt/new-privileged -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged\n'
        self.assertEqual(self.run_tree(158,data),'PASS\n')
        for n,path in ((158,'/etc/audit/rules.d/privileged.rules'),(161,'/etc/audit/rules.d/actions.rules'),(173,'/etc/audit/rules.d/99-finalize.rules'),(145,'/etc/aide.conf')):
            data=self.tree(n);data['files'][path]='\n'.join('# '+line for line in data['files'][path].splitlines())
            self.assertEqual(self.run_tree(n,data),'')
        data=self.tree(161);data['files']['/etc/sudoers']='Defaults logfile="/var/log/other-sudo.log"\n'
        self.assertEqual(self.run_tree(161,data),'')
        data=self.tree(173);data['files']={'/etc/audit/rules.d/2-early.rules':'-e 1\n', '/etc/audit/rules.d/10-final.rules':'-e 2\n--loginuid-immutable\n'}
        self.assertEqual(self.run_tree(173,data),'PASS\n')
        data=self.tree(173);data['files']['/etc/audit/rules.d/zz-override.rules']='-e 1\n'
        self.assertEqual(self.run_tree(173,data),'')

    def test_actual_shell_quoting_runs_only_redirected_audit_program(self):
        # Validate both parsing layers in a real shell using an inert isolated file.
        with tempfile.TemporaryDirectory(prefix='p2b3-test-only-shell-', dir=ROOT) as folder:
            path=Path(folder+'/etc/audit/rules.d/audit.rules');path.parent.mkdir(parents=True)
            path.write_text('\n'.join(audit_lines(148)))
            target=rules()[148][0][0];argv=w_strtok(target[2:])
            command=argv[2].replace('/usr/bin/python3',shlex.quote(sys.executable),1)
            command=command.replace(shlex.quote(script(148)),shlex.quote(script(148).replace("ROOT = ''",'ROOT = '+repr(folder),1)))
            result=subprocess.run(argv[:2]+[command],capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,0);self.assertEqual(result.stdout,'PASS\n');self.assertEqual(result.stderr,'')
