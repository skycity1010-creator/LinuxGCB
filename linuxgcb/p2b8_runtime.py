"""Read-only source predicates; ROOT is used only by isolated tests."""
import glob
import os
import re
import subprocess
import time
ROOT = ''
MODULES = dict(zip([1,2,3,31]+list(range(285,301)),
    ['cramfs','squashfs','udf','usb-storage','freevxfs','hfs','hfsplus','jffs2','afs','ceph','cifs','exfat','ext','fat','fscache','fuse','gfs2','nfs_common','nfsd','smbfs_common']))
FIXED = {5:('/tmp','nodev'),6:('/tmp','nosuid'),7:('/tmp','noexec'),10:('/var/tmp','nodev'),11:('/var/tmp','nosuid'),12:('/var/tmp','noexec'),16:('/home','nodev'),17:('/dev/shm','nodev'),18:('/dev/shm','nosuid'),19:('/dev/shm','noexec')}
PARTITIONS = {8:'/var',9:'/var/tmp',13:'/var/log',14:'/var/log/audit',15:'/home'}


def read(path):
    with open(ROOT+path, encoding='utf-8') as f:
        return f.read()


def unescape(s):
    return re.sub(r'\\([0-7]{3})',lambda m:chr(int(m[1],8)),s)


def mounts():
    out = []
    for line in read('/proc/mounts').splitlines():
        if not line.strip() or line.lstrip().startswith('#'): continue
        f = line.split()
        if len(f) != 6: raise ValueError('mount record')
        out.append((unescape(f[0]),unescape(f[1]),f[2],set(f[3].split(','))))
    if not out: raise ValueError('empty mount table')
    return out


def mountinfo():
    out = {}
    for line in read('/proc/self/mountinfo').splitlines():
        a,b = line.split(' - ',1)
        f = a.split(); tail = b.split()
        if len(f)<6 or len(tail)<3: raise ValueError('mountinfo record')
        path=unescape(f[4])
        if path in out: raise ValueError('stacked mount requires review')
        out[path]=(f[2],unescape(f[3]),tail[0])
    if '/' not in out: raise ValueError('no root')
    return out


def independent(path, info):
    if path not in info or info[path][1] != '/' or info[path][0].startswith('0:'): return False
    return all(info[path][0]!=v[0] for p,v in info.items() if p!=path and (p=='/' or path.startswith(p.rstrip('/')+'/')))


def removable(source):
    # Resolve kernel block class symlinks, then examine partition and disk ancestors.
    if not source.startswith('/dev/'): return None
    name=os.path.basename(os.path.realpath(ROOT+source))
    base=ROOT+'/sys/class/block/'+name
    if not os.path.exists(base): return None
    base=os.path.realpath(base)
    boundary=os.path.realpath(ROOT+'/sys')
    while base.startswith(boundary+'/'):
        p=base+'/removable'
        if os.path.isfile(p):
            with open(p) as f: value=f.read().strip()
            if value not in ('0','1'): raise ValueError('removable flag')
            return value=='1'
        base=os.path.dirname(base)
    return None


def scan_argv(path):
    return ['/usr/bin/find',path,'-xdev','-type','d','-perm','-0002','!','-perm','-1000','-print','-quit']


def check(n):
    if n in MODULES:
        module=MODULES[n]; install=[]; blacklist=False
        for path in sorted(glob.glob(ROOT+'/etc/modprobe.d/*.conf')):
            with open(path) as f:
                for line in f:
                    fields=line.split('#',1)[0].strip().split()
                    if len(fields)>=2 and fields[1]==module:
                        if fields[0]=='install': install.append(fields[2:])
                        if fields==['blacklist',module]: blacklist=True
        return bool(install) and all(x==['/bin/true'] for x in install) and blacklist
    if n==29:
        end=time.monotonic()+24
        df=subprocess.run(['/usr/bin/df','--local','-P'],capture_output=True,text=True,timeout= max(.01,end-time.monotonic()))
        if df.returncode or df.stderr: return False
        lines=df.stdout.splitlines()[1:]
        if not lines: return False
        for line in lines:
            if time.monotonic() >= end: raise ValueError('scan budget exhausted')
            f=line.split()
            if len(f)!=6: raise ValueError('df record')
            result=subprocess.run(scan_argv(unescape(f[5])),capture_output=True,text=True,timeout=max(.01,end-time.monotonic()))
            if result.returncode or result.stdout or result.stderr: return False
        return True
    ms=mounts()
    if n==4:
        selected=[m for m in ms if m[1]=='/tmp']
        return len(selected)==1 and selected[0][2]=='tmpfs'
    if n in PARTITIONS: return independent(PARTITIONS[n],mountinfo())
    if n in FIXED:
        path,opt=FIXED[n]; selected=[m for m in ms if m[1]==path]
        return len(selected)==1 and opt in selected[0][3]
    opt=('nodev','nosuid','noexec')[(n-20)%3]
    if 20<=n<=22:
        selected=[]; unknown=False
        for m in ms:
            if m[0].startswith('/dev/'):
                r=removable(m[0])
                if r is None: unknown=True
                if r: selected.append(m)
        if any(opt not in m[3] for m in selected): return False
        if unknown or not selected: return None
    elif 23<=n<=25:
        info=mountinfo(); homes=set()
        for line in read('/etc/passwd').splitlines():
            if not line.strip() or line.lstrip().startswith('#'): continue
            f=line.split(':')
            if len(f)!=7: raise ValueError('passwd record')
            if int(f[2])>=1000 and f[0]!='nobody': homes.add(f[5])
        selected=[m for m in ms if m[1] in homes and independent(m[1],info)]
    elif 26<=n<=28:
        selected=[m for m in ms if m[2] in ('nfs','nfs4')]
    else: raise ValueError('unknown rule')
    if not selected: return None
    return all(opt in m[3] for m in selected)
