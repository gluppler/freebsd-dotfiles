#!/usr/bin/env python3
"""Run the transaction guard against real pkg and disposable signed packages.

Set PKG to a pkg 2.8.4 executable. All databases, payloads and repositories live
under a temporary directory; this does not use the host's installed packages.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PKG = Path(os.environ.get('PKG', ROOT/'.build/pkg-check/pkg-2.8.4/src/pkg')).resolve()


class Transactions(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PKG.is_file(), 'Set PKG to the real pkg executable; see docs/VALIDATION.md')
        self.directory = tempfile.TemporaryDirectory(prefix='nostromo-pkg-')
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name).resolve()
        for name in ('db','cache','repo','repos','receipt','payload'):
            (self.path/name).mkdir()
        self.env = {**os.environ, 'INSTALL_AS_USER':'yes', 'LC_ALL':'C',
                    'PKG_TEST':str(PKG), 'PKG_WORK':str(self.path)}
        config = {'PKG_DBDIR':str(self.path/'db'), 'PKG_CACHEDIR':str(self.path/'cache'),
                  'REPOS_DIR':[str(self.path/'repos')], 'ABI':'FreeBSD:15:amd64', 'OSVERSION':1501000,
                  'COMPRESSION_FORMAT':'txz',
                  'SYSLOG':False, 'REPO_AUTOUPDATE':False, 'PKG_ENABLE_PLUGINS':False,
                  'ASSUME_ALWAYS_YES':False, 'DEFAULT_ALWAYS_YES':False,
                  'AUTOREMOVE':False, 'HANDLE_RC_SCRIPTS':False}
        (self.path/'pkg.conf').write_text(json.dumps(config))
        subprocess.run(['openssl','genpkey','-algorithm','RSA','-pkeyopt','rsa_keygen_bits:2048',
                        '-out',str(self.path/'signing.pem')],check=True,capture_output=True)
        subprocess.run(['openssl','pkey','-in',str(self.path/'signing.pem'),'-pubout',
                        '-out',str(self.path/'public.pem')],check=True,capture_output=True)
        (self.path/'repos/local.conf').write_text(json.dumps({'NostromoTransaction':{
            'url':(self.path/'repo').as_uri(), 'signature_type':'pubkey',
            'pubkey':str(self.path/'public.pem'), 'enabled':True}}))
        source = (ROOT/'scripts/packages.sh').read_text()
        self.guard = 'transact() {' + source.split('transact() {',1)[1].split('\nupstream_for()',1)[0]
        self.self_upgrade = source.split('# Review that step separately',1)[1].split('\n',1)[1].split(
            'if [ "$action" = reinstall ]; then',1)[0]
        self.identity_check = "pkgtool query -a '%n|%v|%o|%q|%a' >\"$receipt/after\"\n" + source.split(
            "pkgtool query -a '%n|%v|%o|%q|%a' >\"$receipt/after\"\n",1)[1].split('\nif [ "$action" = update ]',1)[0]
        # From the request list through the final transaction choice.
        self.request = '# pkg refuses a request' + source.split('# pkg refuses a request',1)[1].split(
            '    transact install "$@"\nfi\n',1)[0] + '    transact install "$@"\nfi\n'

    def pkg(self, *args, check=True):
        result = subprocess.run([str(PKG),'-C',str(self.path/'pkg.conf'),*args],env=self.env,
                                text=True,capture_output=True,timeout=30)
        if check:
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return result

    def package(self, name, version='1', *, deps=(), file=None, noarch=False, annotations=None):
        # A dependency name records version 1; a mapping names the version.
        deps = deps if isinstance(deps, dict) else dict.fromkeys(deps, '1')
        manifest = {'name':name, 'version':version, 'origin':'misc/'+name,
                    'comment':'Disposable transaction fixture', 'desc':'Test fixture',
                    'arch':'FreeBSD:15:amd64', 'maintainer':'test@example.invalid',
                    'www':'https://example.invalid', 'prefix':str(self.path/'payload'),
                    'deps':{dep:{'origin':'misc/'+dep,'version':v} for dep, v in deps.items()}}
        if noarch:
            # The quarterly catalogue spells architecture-independent packages this way.
            manifest.update({'abi':'FreeBSD:15:*', 'arch':'freebsd:15:*'})
        if file:
            (self.path/'payload'/file).write_text(name+'\n')
            manifest['files']={str(self.path/'payload'/file):''}
        if annotations:
            manifest['annotations']=annotations
        path = self.path/(name+'.json')
        path.write_text(json.dumps(manifest))
        for previous in (self.path/'repo').glob(name+'-*.pkg'):
            previous.unlink()
        self.pkg('create','-M',str(path),'-o',str(self.path/'repo'))

    def publish(self):
        self.pkg('repo',str(self.path/'repo'),'rsa:'+str(self.path/'signing.pem'))
        self.pkg('update','-f')
        # Initialize the disposable database. On the laptop, pkg bootstrap has
        # already created it before the transaction helper is installed.
        self.pkg('rquery','-a','%n')

    def transact(self, operation='install', *args, action='install', before=''):
        script = '''set -eu
receipt=$PKG_WORK/receipt
temp=$PKG_WORK
localpkg() { "$PKG_TEST" -C "$PKG_WORK/pkg.conf" "$@"; }
action=$1
shift
''' + self.guard + '\n' + before + 'transact "$@"\n'
        return subprocess.run(['sh','-c',script,'--',action,operation,*args],env=self.env,
                              text=True,capture_output=True,timeout=30)

    def records(self):
        # Fixture archives are name-version.pkg; skip pkg repo's catalogue files.
        return ''.join(self.pkg('query','-F',str(archive),'P|%n|%v|%o|%q|%#d').stdout
                       for archive in sorted((self.path/'repo').glob('*-*.pkg')))

    def stale_pkg(self):
        # Installed pkg is older than the copy in the transaction repository.
        self.package('pkg')
        self.publish()
        self.pkg('install','-U','-y','-r','NostromoTransaction','pkg')
        self.package('pkg','2')
        self.package('application')
        self.publish()
        # The restart re-executes pkg by name. With none on PATH, the forked
        # worker runs this binary again, consuming stdin as the native restart does.
        self.env['PATH'] = '/usr/bin:/bin'

    def test_install_leaf_dependencies_and_repeat(self):
        names = ['libedit','pkgconf','indexinfo','mpdecimal','expat']
        for name in names:
            self.package(name)
        self.publish()
        self.assertEqual(self.pkg('-v').stdout.strip(),'2.8.4')
        unsupported = self.pkg('install','--no-remove',names[0],check=False)
        self.assertNotEqual(unsupported.returncode,0)
        self.assertIn('unrecognized option',unsupported.stderr)
        for _ in range(2):
            result = self.transact('install',*names)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(set(self.pkg('query','-a','%n').stdout.splitlines()),set(names))
        self.pkg('check','-d','-n','-a')

    def test_preview_reinstall_and_upgrade(self):
        self.package('sample')
        self.publish()
        preview = self.transact('install','sample',action='preview')
        self.assertEqual(preview.returncode,0,preview.stdout+preview.stderr)
        self.assertEqual(self.pkg('query','-a','%n').stdout,'')
        for args in [('sample',),('-f','sample')]:
            result = self.transact('install',*args)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.package('sample','2')
        self.publish()
        upgraded = self.transact('upgrade','sample',action='update')
        self.assertEqual(upgraded.returncode,0,upgraded.stdout+upgraded.stderr)
        self.assertEqual(self.pkg('query','%v','sample').stdout.strip(),'2')
        self.assertEqual(self.transact('upgrade','sample',action='update').returncode,0)

    def test_existing_automatic_dependencies(self):
        self.package('dependency')
        self.package('application',deps=['dependency'])
        self.publish()
        self.pkg('install','-U','-y','-r','NostromoTransaction','application')
        result = self.transact('install','dependency')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(self.pkg('query','%v','dependency').stdout.strip(),'1')

    def test_file_conflict_cannot_receive_a_second_approval(self):
        self.package('incumbent',file='shared')
        self.publish()
        self.pkg('install','-U','-y','-r','NostromoTransaction','incumbent')
        self.package('replacement',file='shared')
        self.publish()
        # Restore the installed payload after creating the conflicting archive.
        (self.path/'payload/shared').write_text('incumbent\n')
        result = self.transact('install','replacement')
        self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('conflict',(result.stdout+result.stderr).lower())
        self.assertEqual(self.pkg('query','-a','%n').stdout.strip(),'incumbent')
        self.assertEqual((self.path/'payload/shared').read_text(),'incumbent\n')
        retry = self.transact('install','replacement')
        self.assertNotEqual(retry.returncode,0,retry.stdout+retry.stderr)
        self.assertEqual(self.pkg('query','-a','%n').stdout.strip(),'incumbent')

    def test_removal_plan_from_real_pkg_is_rejected(self):
        self.package('incumbent')
        self.publish()
        self.pkg('install','-U','-y','-r','NostromoTransaction','incumbent')
        plan=self.pkg('delete','-n','-y','incumbent').stdout
        (self.path/'removal-plan').write_text(plan)
        # Feed the real deletion summary into the same guard. An apply call
        # would exit 99, so the assertion requires rejection during review.
        script='''set -eu
receipt=$PKG_WORK/receipt; temp=$PKG_WORK; action=install
localpkg() {
    case " $* " in *' -n '*) cat "$PKG_WORK/removal-plan" ;; *) exit 99 ;; esac
}
'''+self.guard+'\ntransact install incumbent\n'
        result=subprocess.run(['sh','-c',script],env=self.env,text=True,capture_output=True)
        self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('Package removal proposed',result.stderr)
        self.assertEqual(self.pkg('query','-a','%n').stdout.strip(),'incumbent')

    def test_architecture_independent_archive_passes_the_audit(self):
        self.package('font',noarch=True)
        self.publish()
        records = self.records()
        self.assertEqual(records,'P|font|1|misc/font|FreeBSD:15:*|0\n')
        (self.path/'allowed').write_text('font|misc/font|*|stock\n')
        (self.path/'records').write_text(records)
        audit = subprocess.run(['awk','-v','build=0','-v','recipe=','-f',str(ROOT/'scripts/package-policy.awk'),
                                str(self.path/'allowed'),str(self.path/'records')],text=True,capture_output=True)
        self.assertEqual(audit.returncode,0,audit.stderr)
        result = self.transact('install','font')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(self.pkg('query','%q','font').stdout.strip(),'FreeBSD:15:*')

    def test_identity_check_accepts_an_older_dependency_pkg_keeps(self):
        self.package('dependency')
        self.package('application',deps=['dependency'])
        self.publish()
        self.pkg('install','-U','-y','-r','NostromoTransaction','application')
        self.package('dependency','2')
        self.package('consumer',deps={'dependency':'2'})
        self.publish()
        result = self.transact('install','consumer')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        # The solver keeps the installed dependency rather than upgrading it.
        self.assertEqual(self.pkg('query','%v','dependency').stdout.strip(),'1')
        (self.path/'records').write_text(self.records())
        script = '''set -eu
temp=$PKG_WORK; receipt=$PKG_WORK/receipt
pkgtool() { "$PKG_TEST" -C "$PKG_WORK/pkg.conf" "$@"; }
''' + self.identity_check
        check = subprocess.run(['sh','-c',script],env=self.env,text=True,capture_output=True)
        self.assertEqual(check.returncode,0,check.stderr)

    def test_pkg_restart_cannot_reuse_the_single_approval(self):
        self.stale_pkg()
        result = self.transact('install','application')
        self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('New version of pkg detected',result.stdout)
        self.assertEqual(self.pkg('query','%v','pkg').stdout.strip(),'2')
        self.assertNotEqual(self.pkg('info','-e','application',check=False).returncode,0)

    def test_pkg_upgrades_itself_in_a_separate_reviewed_transaction(self):
        self.stale_pkg()
        (self.path/'records').write_text(self.records())
        result = self.transact('install','application',before=self.self_upgrade)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(self.pkg('query','%v','pkg').stdout.strip(),'2')
        self.assertEqual(self.pkg('query','%v','application').stdout.strip(),'1')
        plans = (self.path/'receipt/plan').read_text()
        self.assertEqual(plans.count('Installed packages to be UPGRADED:'),1)
        self.assertEqual(plans.count('New packages to be INSTALLED:'),1)

    def test_requests_keep_installed_locked_variants(self):
        # Later dependency lists and the desktop list name variants that earlier
        # stages installed and locked. Naming one to pkg stopped the native run.
        self.package('libxml2',annotations={'nostromo_recipe':'abc'})
        self.package('application',deps=['libxml2'])
        self.package('curl')
        self.package('gmake')
        self.publish()
        self.pkg('install','-U','-y','-r','NostromoTransaction','libxml2','application','curl')
        self.pkg('lock','-y','libxml2')
        plain = self.transact('install','gmake','libxml2')
        self.assertNotEqual(plain.returncode,0)
        self.assertIn('libxml2-1 is locked and may not be modified',plain.stdout+plain.stderr)
        (self.path/'policy').mkdir()
        (self.path/'policy/packages.local').write_text(
            '# name|origin|version\nlibxml2|misc/libxml2|1\ncurl|misc/curl|1\n')
        (self.path/'records').write_text('')
        script = '''set -eu
receipt=$PKG_WORK/receipt; temp=$PKG_WORK; policy=$PKG_WORK/policy; recipe=abc; relock=; action=$1
pkgtool() { "$PKG_TEST" -C "$PKG_WORK/pkg.conf" "$@"; }
localpkg() { pkgtool "$@"; }
validate() { :; }
known_recipe() { [ "$1" = "$recipe" ]; }
''' + self.guard + '\n' + self.request + "echo 'Post-transaction checks.'\n"

        def request(action, *names):
            (self.path/'request').write_text(''.join(name+'\n' for name in names))
            return subprocess.run(['sh','-c',script,'--',action],env=self.env,text=True,
                                  capture_output=True,timeout=60)

        kept = 'Keeping the installed, locked libxml2 variant.'
        result = request('install','gmake','libxml2')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn(kept,result.stdout)
        self.assertEqual(self.pkg('query','%v','gmake').stdout.strip(),'1')
        # A request of kept variants alone leaves pkg out. Install still runs the
        # post-transaction checks; a preview stops before them.
        for action in ('install','preview'):
            result = request(action,'libxml2')
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn(kept,result.stdout)
            self.assertNotIn('Proceed with this action',result.stdout)
            self.assertEqual('Post-transaction checks.' in result.stdout,action=='install')
        self.package('application','2',deps=['libxml2'])
        self.package('curl','2')
        self.publish()
        # Updates name every installed package. Stock packages and an unlocked
        # variant, such as a stock bootstrap copy, still upgrade.
        result = request('update','application','curl','gmake','libxml2')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertNotIn('locked curl',result.stdout)
        self.assertEqual(self.pkg('query','%v','application').stdout.strip(),'2')
        self.assertEqual(self.pkg('query','%v','curl').stdout.strip(),'2')
        self.assertEqual(self.pkg('query','%v|%k','libxml2').stdout.strip(),'1|1')
        # Reinstall still names its variant: the helper unlocks it first.
        result = request('reinstall','libxml2')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertNotIn(kept,result.stdout)
        self.assertIn('Installed packages to be REINSTALLED:',result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
