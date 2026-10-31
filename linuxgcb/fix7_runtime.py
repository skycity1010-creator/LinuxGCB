"""Mountinfo overrides embedded only in the nine FIX7 candidates."""


def mountinfo():
    class MountInfo(dict):
        pass
    out = MountInfo()
    out.duplicates = set()
    for line in read('/proc/self/mountinfo').splitlines():
        a,b = line.split(' - ',1)
        f = a.split(); tail = b.split()
        if len(f)<6 or len(tail)<3: raise ValueError('mountinfo record')
        path=unescape(f[4])
        if path in out: out.duplicates.add(path)
        out[path]=(f[2],unescape(f[3]),tail[0])
    if '/' not in out: raise ValueError('no root')
    return out


def independent(path, info):
    if any(p==path or p=='/' or path.startswith(p.rstrip('/')+'/') or
           p.startswith(path.rstrip('/')+'/') for p in info.duplicates):
        raise ValueError('stacked mount requires review')
    if path not in info or info[path][1] != '/' or info[path][0].startswith('0:'): return False
    return all(info[path][0]!=v[0] for p,v in info.items() if p!=path and (p=='/' or path.startswith(p.rstrip('/')+'/')))
