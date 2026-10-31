"""Author P2B3 test-only input trees and output-model cases; never run host checks."""
import copy
import json
from linuxgcb.catalog import ROOT
from linuxgcb.batch3 import ADDED, AUDIT, audit_lines, rules


def inputs():
    result={}
    for n in sorted(ADDED):
        files={}; modes={}; owners={}; commands={}
        if n in AUDIT:
            files['/etc/audit/rules.d/audit.rules']='\n'.join(audit_lines(n))+'\n'
            files['/etc/login.defs']='UID_MIN 1000\n'
        elif n==92: commands={'rpm':1}
        elif n==93: files['/etc/chrony.conf']='server ntp.example.test iburst\n'
        elif n in (95,96,99,100):
            commands={'rpm':0,'load':'loaded','active':'inactive','unit':'masked'}
        elif n in (134,135): files['/etc/default/grub']='GRUB_CMDLINE_LINUX="audit=1 audit_backlog_limit=8192"\n'
        elif n==136: files['/etc/aliases']='postmaster: root\n'
        elif n in (137,138,139,140):
            files['/etc/audit/auditd.conf']='log_file = /var/log/audit/audit.log\n'
            files['/var/log/audit/audit.log']='test-only audit content\n'
            modes={'/var/log/audit':0o700,'/var/log/audit/audit.log':0o600}
            owners={'/var/log/audit': [0,0], '/var/log/audit/audit.log':[0,0]}
        elif n in (143,144):
            for name in ('auditctl','aureport','ausearch','autrace','auditd','audisp-remote','audisp-syslog','augenrules','rsyslogd'):
                path='/sbin/'+name;files[path]='test-only inert tool';modes[path]=0o750;owners[path]=[0,0]
        elif n==145:
            files['/etc/aide.conf']='\n'.join('/usr/sbin/'+name+' p+i+n+u+g+s+b+acl+xattrs+sha512' for name in ('auditctl','auditd','ausearch','aureport','autrace','audisp-remote','audisp-syslog','augenrules'))+'\n'
        elif n==146: files['/etc/audit/auditd.conf']='max_log_file = 32\n'
        elif n==147: files['/etc/audit/auditd.conf']='max_log_file_action = keep_logs\n'
        elif n==158:
            files={'/proc/self/mountinfo':'1 0 0:1 / / rw - ext4 /dev/test rw\n','/etc/login.defs':'UID_MIN 1000\n','/usr/bin/test-privileged':'test-only inert executable',
                   '/etc/audit/rules.d/privileged.rules':'-a always,exit -F path=/usr/bin/test-privileged -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged\n'}
            modes['/usr/bin/test-privileged']=0o4750
        elif n==161:
            files={'/etc/sudoers':'Defaults logfile="/var/log/site-sudo.log"\n','/etc/audit/rules.d/actions.rules':'-w /var/log/site-sudo.log -p wa -k actions\n'}
        elif n==173: files['/etc/audit/rules.d/99-finalize.rules']='-e 2\n--loginuid-immutable\n'
        elif n==176: files['/etc/rsyslog.conf']='$FileCreateMode 0640\n'
        elif n==177: files['/etc/rsyslog.conf']='auth.*,authpriv.* ,daemon.* /var/log/secure\n'
        elif n in (181,182): files['/etc/systemd/journald.conf']='[Journal]\nCompress=yes\nStorage=persistent\n'
        elif n==308:
            files['/etc/logrotate.d/rsyslog']='/var/log/rsyslog/*.log {\n weekly\n rotate 4\n compress\n missingok\n notifempty\n postrotate /usr/bin/systemctl reload rsyslog.service >/dev/null || true\n endscript\n}\n'
            modes['/var/log/rsyslog']=0o750
        good=dict(files=files,modes=modes,owners=owners,commands=commands)
        bad=copy.deepcopy(good)
        if n==92: bad['commands']['rpm']=0
        elif n in (95,96,99,100): bad['commands']['active']='active';bad['commands']['unit']='enabled'
        elif n in (137,139):
            path='/var/log/audit/audit.log' if n==137 else '/var/log/audit';bad['owners'][path]=[1001,0]
        elif n in (138,140): bad['modes']['/var/log/audit/audit.log' if n==138 else '/var/log/audit']=0o777
        elif n in (143,144):
            if n==143: bad['modes']['/sbin/auditd']=0o777
            else: bad['owners']['/sbin/auditd']=[0,1001]
        else:
            path=next(p for p in files if p not in ('/etc/login.defs','/proc/self/mountinfo','/usr/bin/test-privileged'))
            bad['files'][path]='# test-only removed required configuration\n'
        result[str(900000+n)]={'positive':good,'negative':bad}
    return result


def outputs():
    result={}
    for n,items in rules().items():
        target=items[0][0];ok='ABSENT\n' if n==92 else 'PASS\n'
        cases={'positive':{target:dict(stdout=ok,exit_code=0)},
               'negative':{target:dict(stdout='INSTALLED\n' if n==92 else '',exit_code=0)},
               'missing':{},'empty':{target:dict(stdout='',exit_code=0)},
               'error':{target:dict(error='test-only permission/command error')},
               'nonzero_matching':{target:dict(stdout=ok,exit_code=2)}}
        if n in AUDIT | {158,161,173,145}: cases['commented']={target:dict(stdout='',exit_code=0)}
        if n in (92,96,99,100): cases['rpm_other_error']={target:dict(stdout='',exit_code=2)}
        result[str(900000+n)]=cases
    return result


def main():
    path=ROOT/'tests/fixtures/p2b3/cases.json'
    path.write_text(json.dumps(dict(label='SYNTHETIC TEST ONLY',inputs=inputs(),checks=outputs()),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__': main()
