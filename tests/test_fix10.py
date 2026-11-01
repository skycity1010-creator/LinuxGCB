"""FIX10 uses only temporary files and the emitted read-only command."""
import contextlib
import io
import json
import subprocess
import unittest
from pathlib import Path
from linuxgcb import batch7
from linuxgcb.argv import w_strtok
from linuxgcb.catalog import ROOT
import test_p2b7 as p2b7

DISPLAY=('description','rationale','remediation')
def nod(d): return {k:v for k,v in d.items() if k not in DISPLAY}

BASELINE = '12851d61d23b8a7bbf413e01dd6db0abc5c420aa'
GOOD = '[main]\ngpgcheck=1\nlocalpkg_gpgcheck=1\n'


class Fix10Tests(unittest.TestCase):
    setUp = p2b7.P2B7Tests.setUp
    put = p2b7.P2B7Tests.put

    def output(self):
        command = batch7.rules()[32][0][0][2:]
        self.assertTrue(command.startswith('/usr/bin/python3 -c "'))
        argv = w_strtok(command)
        self.assertEqual(len(argv), 3)
        self.assertNotIn('->', argv[2])
        self.assertEqual(argv[2].count("print('PASS')"), 1)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            exec(argv[2].replace("ROOT = ''", 'ROOT = '+repr(self.tmp.name), 1), {})
        return out.getvalue()

    def main(self):
        self.put('/etc/dnf/dnf.conf', GOOD)
        self.put('/etc/yum.conf').unlink()
        (Path(self.tmp.name)/'etc/yum.conf').symlink_to('dnf/dnf.conf')

    def test_comment_only_repo_and_template_apply_restore(self):
        self.main()
        self.put('/etc/yum.repos.d/redhat.repo', '# subscription-manager generated\n\n; no sections\n')
        self.assertEqual(self.output(), 'PASS\n')
        self.put('/etc/yum.repos.d/no-section.repo', 'gpgcheck=0\n')
        self.assertEqual(self.output(), 'PASS\n')
        self.put('/etc/dnf/dnf.conf', '[main]\ngpgcheck=1\n')
        self.assertEqual(self.output(), '')
        template = self.put('/etc/yum.repos.d/gcb-gpgcheck.repo', (ROOT/'templates/gcb-gpgcheck.repo').read_text())
        self.assertEqual(self.output(), '')
        self.put('/etc/dnf/dnf.conf', GOOD)
        self.assertEqual(self.output(), 'PASS\n')
        template.unlink()
        self.put('/etc/dnf/dnf.conf', '[main]\ngpgcheck=1\n')
        self.assertEqual(self.output(), '')

    def test_every_repo_section_requires_both_keys(self):
        self.main()
        self.put('/etc/yum.repos.d/redhat.repo', '# no sections\n')
        for section in ('[bad]\n', '[bad]\ngpgcheck=1\n', '[bad]\nlocalpkg_gpgcheck=1\n', '[bad]\ngpgcheck=0\nlocalpkg_gpgcheck=1\n'):
            self.put('/etc/yum.repos.d/test.repo', '[good]\ngpgcheck=1\nlocalpkg_gpgcheck=1\n'+section)
            self.assertEqual(self.output(), '', section)

    def test_main_still_requires_both_keys_and_section(self):
        for path in ('/etc/yum.conf', '/etc/dnf/dnf.conf'):
            for bad in ('# empty\n', '[main]\ngpgcheck=1\n', '[main]\nlocalpkg_gpgcheck=1\n', '[main]\ngpgcheck=1\nlocalpkg_gpgcheck=0\n'):
                self.put('/etc/yum.conf', GOOD)
                self.put('/etc/dnf/dnf.conf', GOOD)
                self.put(path, bad)
                self.assertEqual(self.output(), '', (path, bad))

    def test_only_900032_and_protected_artifacts(self):
        old, new = {}, {}
        for path in (ROOT/'policies').glob('*.yml'):
            prior = json.loads(subprocess.check_output(['git','show',BASELINE+':policies/'+path.name], cwd=ROOT))
            current = json.loads(path.read_text())
            self.assertEqual((lambda d:{k:v for k,v in d['policy'].items() if k not in ('name','description')})(prior), (lambda d:{k:v for k,v in d['policy'].items() if k not in ('name','description')})(current))  # FIX13 VERIFIED rename
            self.assertEqual(prior['requirements'], current['requirements'])
            old.update({c['id']:c for c in prior['checks']})
            new.update({c['id']:c for c in current['checks']})
        self.assertEqual(len(new), 307)
        self.assertEqual(old.keys(), new.keys())
        self.assertEqual({n for n in old if old[n]['rules'] != new[n]['rules']}, {900032,900282,900283})
        for n in old:
            self.assertEqual(nod(dict(new[n], rules=old[n]['rules'])), nod(old[n]))
        protected = ['data/controls.json','data/inventory.json','docs/references','tests/fixtures','tests/fix5_baseline.json','docs/*TEST_OUTPUT*','*.xlsx','*.docx']  # FIX13: registry/manifest 治理欄位刻意更新，移出 protected
        self.assertEqual(subprocess.check_output(['git','diff',BASELINE,'--name-only','--',*protected], cwd=ROOT, text=True), '')
