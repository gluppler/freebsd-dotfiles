#!/usr/bin/env python3
"""Fail-closed package graph checks; no package manager or root privileges."""
from pathlib import Path
import hashlib
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
PKG_ALPHABET = "ybndrfg8ejkmcpqxot1uwisza345h769"


def pkg_base32(data):
    """libpkg's pkg_checksum_encode_base32 (pkg 2.8.4), case by case."""
    out, remain = [], -1
    for i, byte in enumerate(data):
        if i % 5 == 0:
            x, remain = byte, byte >> 5
            out.append(PKG_ALPHABET[x & 0x1F])
        elif i % 5 == 1:
            x = remain | byte << 3
            out += [PKG_ALPHABET[x & 0x1F], PKG_ALPHABET[x >> 5 & 0x1F]]
            remain = x >> 10
        elif i % 5 == 2:
            x = remain | byte << 1
            out.append(PKG_ALPHABET[x & 0x1F])
            remain = x >> 5
        elif i % 5 == 3:
            x = remain | byte << 4
            out += [PKG_ALPHABET[x & 0x1F], PKG_ALPHABET[x >> 5 & 0x1F]]
            remain = x >> 10 & 0x3
        else:
            x = remain | byte << 2
            out += [PKG_ALPHABET[x & 0x1F], PKG_ALPHABET[x >> 5 & 0x1F]]
            remain = -1
    if remain >= 0:
        out.append(PKG_ALPHABET[remain])
    return "".join(out)


class Policy(unittest.TestCase):
    def check_graph(self, policy, records, *, build=0):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "allowed").write_text(policy)
            (directory / "records").write_text(records)
            return subprocess.run(
                ["awk", "-v", "recipe=abc123", "-v", f"build={build}", "-f",
                 str(ROOT / ".install/scripts/package-policy.awk"), str(directory / "allowed"),
                 str(directory / "records")], capture_output=True, text=True)

    def test_resolved_graph_and_changed_origin(self):
        policy = "app|editors/app|*|stock\nlib|devel/lib|*|stock\n"
        graph = ("P|app|2|editors/app|FreeBSD:15:amd64|1\n"
                 "D|app|lib|3|devel/lib\nP|lib|3|devel/lib|FreeBSD:15:amd64|0\n")
        self.assertEqual(self.check_graph(policy, graph).returncode, 0)
        for broken in (graph.replace("editors/app", "other/app"),
                       graph.replace("D|app|lib|3|devel/lib\n", ""),
                       graph.replace("P|lib|3|devel/lib|FreeBSD:15:amd64|0\n", ""),
                       graph.replace("P|lib|3|", "P|lib|4|"),
                       graph.replace("FreeBSD:15:amd64", "FreeBSD:14:amd64"),
                       graph + "P|lib|3|devel/lib|FreeBSD:15:amd64|0\n"):
            with self.subTest(graph=broken):
                self.assertNotEqual(self.check_graph(policy, broken).returncode, 0)

    def test_architecture_independent_packages_keep_the_release_check(self):
        policy = "font|x11-fonts/font|*|stock\n"
        for abi, okay in [("FreeBSD:15:*", True), ("freebsd:15:*", True),
                          ("FreeBSD:14:*", False), ("FreeBSD:*", False), ("*", False),
                          ("FreeBSD:15:aarch64", False), ("freebsd:15:*:*", False)]:
            with self.subTest(abi=abi):
                result = self.check_graph(policy, f"P|font|1|x11-fonts/font|{abi}|0\n")
                self.assertEqual(result.returncode == 0, okay, result.stderr)

    def test_local_variant_must_have_matching_recipe(self):
        policy = "wlroots020|x11-toolkits/wlroots020|0.20.2_1|local\n"
        graph = "P|wlroots020|0.20.2_1|x11-toolkits/wlroots020|FreeBSD:15:amd64|0\n"
        self.assertNotEqual(self.check_graph(policy, graph).returncode, 0)
        self.assertEqual(self.check_graph(policy, graph +
            "A|wlroots020|nostromo_recipe|abc123\n").returncode, 0)
        self.assertNotEqual(self.check_graph(policy, graph +
            "A|wlroots020|nostromo_recipe|old-recipe\n").returncode, 0)

    def test_gnu_scope_and_versions_cannot_widen_silently(self):
        policy = "gmake|devel/gmake|4.4.1|gnu-build\n"
        graph = "P|gmake|4.4.1|devel/gmake|FreeBSD:15:amd64|0\n"
        self.assertNotEqual(self.check_graph(policy, graph).returncode, 0)
        self.assertEqual(self.check_graph(policy, graph, build=1).returncode, 0)
        self.assertNotEqual(self.check_graph(policy, graph.replace("4.4.1", "5"), build=1).returncode, 0)
        self.assertNotEqual(self.check_graph(policy.replace("4.4.1", "*"), graph, build=1).returncode, 0)
        self.assertNotEqual(self.check_graph(policy.replace("gnu-build", "stock"), graph).returncode, 0)

    def test_unknown_packages_and_empty_audits_stop(self):
        policy = "app|editors/app|*|stock\n"
        for graph in ("", "P|new|1|editors/new|FreeBSD:15:amd64|0\n", "surprise\n"):
            self.assertNotEqual(self.check_graph(policy, graph).returncode, 0)

    RESOLVER_NAMES = ['libedit', 'pkgconf', 'indexinfo', 'mpdecimal', 'expat']

    def resolver(self, path):
        """The dependency walk of packages.sh, with stand-ins for pkg and openssl."""
        source = (ROOT / '.install/scripts/packages.sh').read_text()
        identity = 'identity() {' + source.split('identity() {', 1)[1].split('\nif [ "$action" = finish-bootstrap', 1)[0]
        upstream = 'upstream_for() {' + source.split('upstream_for() {',1)[1].split('\nrecipe=',1)[0]
        fetching = 'archive_sum() {' + source.split('archive_sum() {', 1)[1].split('\ncp "$temp/request" "$temp/queue"', 1)[0]
        resolve = source.split('cp "$temp/request" "$temp/queue"', 1)[1].split('# Protect shared-library', 1)[0]
        names = self.RESOLVER_NAMES
        origins = ['devel/libedit', 'devel/pkgconf', 'print/indexinfo', 'math/mpdecimal', 'textproc/expat2']
        (path/'scripts').mkdir()
        (path/'scripts/package-policy.awk').write_bytes((ROOT/'.install/scripts/package-policy.awk').read_bytes())
        (path/'packages.allowed').write_text('build-tool|devel/build-tool|*|stock\ndrm-612-kmod|graphics/drm-612-kmod|*|stock\n' + ''.join(
            f'{name}|{origin}|*|stock\n' for name, origin in zip(names, origins)))
        records = {'build-tool': {'origin': 'devel/build-tool', 'deps': names},
                   'drm-612-kmod': {'origin': 'graphics/drm-612-kmod', 'deps': []}}
        records.update({name: {'origin': origin, 'deps': []} for name, origin in zip(names, origins)})
        (path/'packages.json').write_text(json.dumps(records))
        (path/'bin').mkdir()
        # FreeBSD's openssl; the archive checksum test covers the real one.
        (path/'bin/openssl').write_text(f'#!{sys.executable}\nimport hashlib, sys\n'
            'sys.stdout.buffer.write(hashlib.blake2b(open(sys.argv[-1], "rb").read(), digest_size=64).digest())\n')
        (path/'bin/openssl').chmod(0o755)
        stub = path/'pkg'
        stub.write_text(f'#!{sys.executable}\n' + f'PKG_ALPHABET = {PKG_ALPHABET!r}\n' +
                        inspect.getsource(pkg_base32) + '''
import hashlib, json, os, sys
from pathlib import Path
root = Path(os.environ['TEST_ROOT']); args = sys.argv[1:]
packages = json.loads((root/'packages.json').read_text())
fault = os.environ['TEST_FAULT']
with (root/'calls').open('a') as log:
    log.write(json.dumps(args) + '\\n')
if args[0] in ('fetch','rquery','search'):
    expected = 'NostromoKmods' if args[-1].startswith('drm-612-kmod') else 'NostromoUpstream'
    assert args[args.index('-r')+1] == expected, args
if args[0] == 'search':
    name = args[-1]
    # A nested version precedes the top-level fields, as in pkg's own records.
    record = {'name': name, 'deps': {'x': {'origin': 'misc/x', 'version': '9'}}, 'version': '1'}
    if fault != 'no-path':
        record['sum'] = '2$' + pkg_base32(hashlib.blake2b(name.encode(), digest_size=64).digest())
        record['repopath'] = 'All/Hashed/' + name + '-1~2$abcdefgh.pkg'
    print(json.dumps(record, separators=(',', ':'))); sys.exit(0)
if args[0] == 'fetch':
    dest = Path(args[args.index('-o')+1])/'All/Hashed'; dest.mkdir(parents=True, exist_ok=True)
    name = args[-1][:-2]
    (dest/(args[-1]+'~2$abcdefgh.pkg')).write_text(name + ('altered' if fault == 'bad-download' else ''))
    sys.exit(0)
if args[0] == 'rquery': name=args[-1]; fmt=args[-2]
elif args[:2] == ['query','-F']: name=Path(args[2]).read_text(); fmt=args[3]
else: raise SystemExit('unexpected pkg call: '+repr(args))
row=packages[name]; deps=row['deps']
if fault=='query' and fmt.startswith('D|'): sys.exit(42)
if fault=='annotation-query' and fmt.startswith('A|'): sys.exit(43)
if fmt.startswith('P|'):
    count=0 if args[0]=='rquery' else len(deps)
    if fault=='missing-edge' and name=='libedit' and args[0]=='query': count=1
    print(f'P|{name}|1|{row["origin"]}|FreeBSD:15:amd64|{count}')
elif fmt=='%n|%v': print(name+'|1')
elif fmt=='%dn':
    for dep in deps: print(dep)
elif fmt.startswith('D|'):
    for dep in deps:
        origin=packages[dep]['origin']
        if fault=='wrong-origin' and dep=='libedit': origin='other/libedit'
        print(f'D|{name}|{dep}|1|{origin}')
    # pkg 2.8.4 print_query keeps %n when the multiline list is empty.
    if not deps:
        if fault=='partial' and name=='libedit': print('D|libedit||1|')
        elif fault=='old-pkg': pass
        else: print(f'D|{name}|||')
elif fmt.startswith('A|'): print(f'A|{name}||')
else: raise SystemExit('unexpected query format: '+fmt)
''')
        stub.chmod(0o755)
        script = '''set -eu
temp=$TEST_ROOT; policy=$TEST_ROOT; build=1; recipe=abc123; downloads=$TEST_ROOT/downloads
pkgtool() { "$TEST_ROOT/pkg" "$@"; }
remote() { pkgtool "$@"; }
validate() { case $1 in '' | [!A-Za-z0-9]* | *[!A-Za-z0-9_+.-]*) exit 2 ;; esac; }
''' + upstream + '\n' + identity + '\n' + fetching + '\ncp "$temp/request" "$temp/queue"\n' + resolve

        def run(fault=''):
            (path/'repo').mkdir(exist_ok=True)
            (path/'request').write_text('build-tool\ndrm-612-kmod\n')
            (path/'calls').write_text('')
            result = subprocess.run(['sh','-c',script], capture_output=True, text=True,
                env={**os.environ, 'TEST_ROOT':str(path), 'TEST_FAULT':fault,
                     'PATH':f"{path/'bin'}:{os.environ['PATH']}"})
            calls = [json.loads(line) for line in (path/'calls').read_text().splitlines()]
            return result, calls
        return run

    def test_archive_queries_handle_empty_dependency_lists_without_hiding_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            run = self.resolver(path)
            for fault, status in [('',0), ('old-pkg',0), ('no-path',0), ('missing-edge',1),
                                  ('partial',1), ('wrong-origin',1), ('query',42), ('annotation-query',43)]:
                with self.subTest(fault=fault):
                    result, _ = run(fault)
                    self.assertEqual(result.returncode, status, result.stderr)
                    if status==0:
                        self.assertEqual(set((path/'seen').read_text().splitlines()),
                                         {'build-tool','drm-612-kmod',*self.RESOLVER_NAMES})
                        self.assertNotIn('|||', (path/'records').read_text())

    def test_each_archive_is_downloaded_once_and_checked_against_the_catalogue(self):
        # Every install transaction resolved and downloaded its whole closure again,
        # and looked up each new archive by querying every archive fetched so far.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            run = self.resolver(path)
            packages = 2 + len(self.RESOLVER_NAMES)
            hashed = path/'downloads/All/Hashed'

            def counts(calls):
                lookups = [call for call in calls if call[:2] == ['query', '-F'] and call[-1] == '%n|%v']
                return sum(call[0] == 'fetch' for call in calls), len(lookups)

            result, calls = run()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(counts(calls), (packages, packages))
            self.assertEqual(len(list(hashed.iterdir())), packages)
            result, calls = run()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(counts(calls), (0, packages))
            # An altered or replaced kept archive is downloaded again, never reused.
            altered = hashed/'libedit-1~2$abcdefgh.pkg'
            altered.write_text('libedit, altered')
            linked = hashed/'expat-1~2$abcdefgh.pkg'
            linked.unlink()
            linked.symlink_to(path/'packages.json')
            result, calls = run()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(sorted(call[-1] for call in calls if call[0] == 'fetch'), ['expat-1', 'libedit-1'])
            self.assertEqual(altered.read_text(), 'libedit')
            self.assertFalse(linked.is_symlink())
            self.assertEqual((path/'packages.json').read_text()[:1], '{')
            # A download that does not match the catalogue stops the transaction.
            altered.unlink()
            result, _ = run('bad-download')
            self.assertEqual(result.returncode, 1)
            self.assertIn('Checksum mismatch: libedit', result.stderr)

    def test_archive_checksum_matches_libpkg_encoding(self):
        source = (ROOT/'.install/scripts/packages.sh').read_text()
        function = 'archive_sum() {' + source.split('archive_sum() {', 1)[1].split('\n}\n', 1)[0] + '\n}\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'bin').mkdir()
            # This stand-in prints the archive itself as its digest, so every
            # input length reaches the encoder.
            (path/'bin/openssl').write_text(f'#!{sys.executable}\nimport sys\n'
                                            'sys.stdout.buffer.write(open(sys.argv[-1], "rb").read())\n')
            (path/'bin/openssl').chmod(0o755)
            archive = path/'archive'

            def checksum(*, stand_in=True):
                env = {**os.environ}
                if stand_in:
                    env['PATH'] = f"{path/'bin'}:{env['PATH']}"
                result = subprocess.run(['sh', '-c', 'set -eu\n' + function + 'archive_sum "$1"', 'sh', str(archive)],
                                        capture_output=True, text=True, env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout

            for size in [*range(1, 12), 32, 63, 64, 65]:
                with self.subTest(size=size):
                    data = os.urandom(size)
                    archive.write_bytes(data)
                    self.assertEqual(checksum(), '2$' + pkg_base32(data) + '\n')
            supported = subprocess.run(['openssl', 'dgst', '-blake2b512'], input=b'', capture_output=True)
            if supported.returncode == 0:
                data = os.urandom(4096)
                archive.write_bytes(data)
                self.assertEqual(checksum(stand_in=False),
                                 '2$' + pkg_base32(hashlib.blake2b(data, digest_size=64).digest()) + '\n')

    def test_downloads_are_kept_only_during_an_install_run(self):
        source = (ROOT/'.install/scripts/packages.sh').read_text()
        block = 'cache=$store/cache\n' + source.split('cache=$store/cache\n', 1)[1].split('if [ "$action" = catalog ]', 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            store, temp, run = path/'store', path/'temp', path/'run'
            script = ('set -eu\nstore=$STORE; temp=$TEMP\n'
                      'remote() { printf "%s\\n" "$dbdir $*" >>"$TEMP/calls"; [ "$*" != update ] || [ ! -e "$TEMP/fail" ]; }\n'
                      + block.replace('/var/run/', str(run) + '/') + 'printf "%s %s\\n" "$dbdir" "$downloads"\n')

            def helper():
                temp.mkdir(exist_ok=True)
                (temp/'db').mkdir(exist_ok=True)
                shutil.rmtree(temp/'downloads', ignore_errors=True)
                (temp/'calls').write_text('')
                result = subprocess.run(['sh', '-c', script], capture_output=True, text=True,
                                        env={**os.environ, 'STORE': str(store), 'TEMP': str(temp)})
                return result, (temp/'calls').read_text().splitlines()

            (store/'cache/downloads').mkdir(parents=True)
            # Outside an install run, archives from a stopped run are removed.
            result, calls = helper()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.split(), [str(temp/'db'), str(temp/'downloads')])
            self.assertFalse((store/'cache').exists())
            self.assertEqual(calls, [f'{temp}/db update'])
            # A live installer's lock keeps them for its later transactions.
            (run/'nostromo-install.lock').mkdir(parents=True)
            (run/'nostromo-install.lock/pid').write_text(f'{os.getpid()}\n')
            result, calls = helper()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.split(), [str(store/'cache/db'), str(store/'cache/downloads')])
            (store/'cache/db/repo.sqlite').write_text('kept catalogue\n')
            (store/'cache/downloads/kept.pkg').write_text('kept archive\n')
            result, calls = helper()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((store/'cache/downloads/kept.pkg').is_file())
            self.assertEqual(calls, [f'{store}/cache/db update'])
            # A kept catalogue that pkg cannot refresh is downloaded again in full.
            (temp/'fail').write_text('')
            result, calls = helper()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(calls, [f'{store}/cache/db update', f'{store}/cache/db update -f'])
            self.assertFalse((store/'cache/db/repo.sqlite').exists())
            self.assertTrue((store/'cache/downloads/kept.pkg').is_file())
            # A fresh private catalogue has nothing to fall back to.
            (run/'nostromo-install.lock/pid').write_text('not-a-pid\n')
            result, calls = helper()
            self.assertEqual(result.returncode, 1)
            self.assertEqual(calls, [f'{temp}/db update'])

    def test_raw_empty_dependency_rows_reproduce_the_reported_failure(self):
        names = ['libedit', 'pkgconf', 'indexinfo', 'mpdecimal', 'expat']
        policy = ''.join(f'{name}|devel/{name}|*|stock\n' for name in names)
        graph = ''.join(f'P|{name}|1|devel/{name}|FreeBSD:15:amd64|0\nD|{name}|||\n' for name in names)
        result = self.check_graph(policy, graph)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr.count('Unreviewed package:   ()'), 5)
        for name in names:
            self.assertIn('Incomplete dependency list: '+name, result.stderr)
            self.assertIn('Unresolved dependency: '+name+' -> ', result.stderr)

    def test_failed_package_operations_remove_private_downloads_and_release_lock(self):
        source = (ROOT/'.install/scripts/packages.sh').read_text()
        lifecycle = 'lock=/var/run/nostromo-packages.lock\n' + source.split(
            'lock=/var/run/nostromo-packages.lock\n',1)[1].split('recipe=$(cat',1)[0]
        for body, status in [('exit 1',1), ('kill -TERM $$',143)]:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)
                (path/'run').mkdir()
                (path/'tmp').mkdir()
                script = ('set -eu\numask 077\n' + lifecycle +
                          'printf partial > "$temp/repo/download.pkg"\n'+body+'\n')
                script = script.replace('/var/run/',str(path/'run')+'/').replace('/var/tmp/',str(path/'tmp')+'/')
                result = subprocess.run(['sh','-c',script], capture_output=True, text=True)
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertFalse(list((path/'tmp').iterdir()))
                self.assertFalse(list((path/'run').iterdir()))

    def test_lock_from_an_earlier_boot_and_stale_workspaces_are_reclaimed(self):
        source = (ROOT/'.install/scripts/packages.sh').read_text()
        lifecycle = 'lock=/var/run/nostromo-packages.lock\n' + source.split(
            'lock=/var/run/nostromo-packages.lock\n',1)[1].split('recipe=$(cat',1)[0]
        dead = subprocess.Popen(['true'])
        dead.wait()
        later = int(time.time()) + 3600
        for boot, owner, status in [(later, None, 0), (later, dead.pid, 0), (later, os.getpid(), 1), (1, None, 1)]:
            with self.subTest(boot=boot, owner=owner), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)
                lock = path/'run/nostromo-packages.lock'
                lock.mkdir(parents=True)
                if owner: (lock/'pid').write_text(f'{owner}\n')
                stale = path/'tmp/nostromo-packages.AbCd1234'
                (stale/'repo').mkdir(parents=True)
                (stale/'repo/download.pkg').write_text('partial')
                (path/'bin').mkdir()
                # Root ownership is modeled; the boot time comes from the fixture.
                (path/'bin/stat').write_text(f'#!{sys.executable}\n' + '''import os, sys
s=os.stat(sys.argv[-1])
print(sys.argv[-2].replace('%u','0').replace('%B',str(int(getattr(s,'st_birthtime',s.st_mtime)))))
''')
                (path/'bin/sysctl').write_text(f"#!/bin/sh\necho '{{ sec = {boot}, usec = 0 }} Thu Jan  1 00:00:01 1970'\n")
                for stub in ('stat','sysctl'): (path/'bin'/stub).chmod(0o755)
                script = ('set -eu\numask 077\n' + lifecycle + '[ "$(cat "$lock/pid")" = "$$" ]\n')
                script = script.replace('/var/run/',str(path/'run')+'/').replace('/var/tmp/',str(path/'tmp')+'/')
                result = subprocess.run(['sh','-c',script], capture_output=True, text=True,
                                        env={**os.environ, 'PATH':str(path/'bin')+':'+os.environ['PATH']})
                self.assertEqual(result.returncode, status, result.stderr)
                if status:
                    self.assertIn('Another package operation holds', result.stderr)
                    self.assertTrue((stale/'repo/download.pkg').is_file())
                    self.assertTrue(lock.is_dir())
                else:
                    self.assertIn('interrupted before the last boot', result.stderr)
                    self.assertIn('Removed a stale package workspace: '+str(stale), result.stderr)
                    self.assertEqual(result.stdout, '')
                    self.assertFalse(list((path/'tmp').iterdir()))
                    self.assertFalse(list((path/'run').iterdir()))

    def test_only_the_current_transaction_receipt_is_kept(self):
        source = (ROOT/'.install/scripts/packages.sh').read_text()
        block = '# Record exact archive hashes' + source.split('# Record exact archive hashes',1)[1].split(
            'cp "$temp/records"',1)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            store = path/'store'
            for name in ('transaction-20261105-140800-1', 'transaction-20261110-172500-2'):
                (store/name).mkdir(parents=True)
                (store/name/'packages').write_text('earlier\n')
            (store/'local').mkdir()
            (store/'local/python312.pkg').write_text('variant\n')
            (store/'signing.pem').write_text('key\n')
            outside = path/'outside'
            outside.mkdir()
            (outside/'keep').write_text('keep\n')
            (store/'transaction-link').symlink_to(outside)
            script = 'set -eu\nstore=$STORE\n' + block + 'printf %s "$receipt"\n'
            result = subprocess.run(['sh','-c',script], capture_output=True, text=True, env={**os.environ, 'STORE':str(store)})
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = Path(result.stdout)
            self.assertTrue(receipt.is_dir())
            # Imported variants and the signing key are working state, not records.
            self.assertEqual(sorted(p.name for p in store.iterdir()),
                             sorted([receipt.name, 'local', 'signing.pem', 'transaction-link']))
            self.assertEqual((outside/'keep').read_text(), 'keep\n')

    def test_only_an_unreviewed_unused_flavor_of_an_audited_origin_is_replaceable(self):
        # The T14's base setup installed stock git; the desktop list names git-lite.
        source = (ROOT/'.install/scripts/packages.sh').read_text()
        block = '# The base setup may have installed' + source.split('# The base setup may have installed',1)[1].split(
            '# pkg installs its own upgrade first',1)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'packages.allowed').write_text('# name|origin|version|kind\ngit-lite|devel/git|*|stock\n'
                                                 'git-tiny|devel/git|*|stock\nvim|editors/vim|*|stock\n')
            (path/'records').write_text('P|git-lite|2.56.0|devel/git|FreeBSD:15:amd64|4\n'
                                        'P|curl|8.23.0|ftp/curl|FreeBSD:15:amd64|5\n')
            # name|origin|locked|vital|consumers, as pkg query prints them.
            installed = ['git|devel/git|0|0|0', 'git-gui|devel/git|1|0|0', 'git-svn|devel/git|0|0|2',
                         'git-full|devel/git|0|1|0', 'git-tiny|devel/git|0|0|0', 'git-lite|devel/git|0|0|0',
                         'curl-stock|ftp/curl|0|0|0', 'vim-tiny|editors/vim|0|0|0', 'stray|misc/stray|0|0|0']
            script = '''set -eu
policy=$TEST_ROOT; temp=$TEST_ROOT
pkgtool() {
    case $* in
    "query -a %n|%o|%k|%V|%#r") printf '%s\\n' $INSTALLED ;;
    "query %dn git") printf '%s\\n' p5-Error perl5 ;;
    "query %dn curl-stock") printf '%s\\n' libidn2 ;;
    *) return 90 ;;
    esac
}
''' + block
            result = subprocess.run(['sh','-c',script], capture_output=True, text=True,
                                    env={**os.environ, 'TEST_ROOT':str(path), 'INSTALLED':' '.join(installed)})
            self.assertEqual(result.returncode, 0, result.stderr)
            # Locked, vital, used, reviewed or unrelated packages are never candidates.
            self.assertEqual((path/'replaceable').read_text().split(), ['git', 'curl-stock'])
            self.assertEqual((path/'replaced-dependencies').read_text().split(), ['p5-Error', 'perl5', 'libidn2'])

    def test_catalog_uses_release_modules_and_ordinary_application_versions(self):
        source = (ROOT/'.install/scripts/packages.sh').read_text()
        branch = source.split('if [ "$action" = catalog ]; then\n',1)[1].split('\nif [ "$action" = details ]; then',1)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'packages.allowed').write_text('app|misc/app|*|stock\ndrm-612-kmod|graphics/drm-612-kmod|*|stock\n')
            script = '''set -eu
policy=$TEST_ROOT; temp=$TEST_ROOT
remote() {
    case $4 in
    NostromoUpstream) printf '%s\\n' 'app|2|Manual for drm-kmod drivers' 'drm-612-kmod|old-kernel|Module' ;;
    NostromoKmods) printf '%s\\n' 'drm-612-kmod|release-kernel|Module' 'app|wrong-repo|Ignore this duplicate' ;;
    *) return 90 ;;
    esac
}
if true; then
''' + branch
            result = subprocess.run(['sh','-c',script], capture_output=True, text=True,
                                    env={**os.environ,'TEST_ROOT':directory})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), [
                'app\t2\tstock\tManual for drm-kmod drivers',
                'drm-612-kmod\trelease-kernel\tstock\tModule'])

    def test_repository_policy_has_no_unclassified_gnu(self):
        graph = "P|pkg|2|ports-mgmt/pkg|FreeBSD:15:amd64|0\n"
        result = self.check_graph((ROOT / ".install/packages.allowed").read_text(), graph)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_local_manifest_matches_the_policy(self):
        allowed = {r[0]: r for line in (ROOT / ".install/packages.allowed").read_text().splitlines()
                   if line and not line.startswith("#") for r in [line.split("|")]}
        seen = set()
        for line in (ROOT / ".install/packages.local").read_text().splitlines():
            if not line or line.startswith("#"):
                continue
            row = line.split("|")
            self.assertEqual(len(row), 3, line)
            name, origin, version = row
            self.assertNotIn(name, seen)
            seen.add(name)
            self.assertEqual(allowed[name], [name, origin, version, "local"])
        self.assertEqual(seen, {name for name, row in allowed.items() if row[3] == "local"})

    def native_requests(self):
        # The policy rows, then each variant's dependency list as recorded on FreeBSD.
        allowed = {row[0]: row for line in (ROOT/'.install/packages.allowed').read_text().splitlines()
                   if line and not line.startswith('#') for row in [line.split('|')]}
        lists = dict(line.split('|') for line in (ROOT/'.install/tests/variant-deps.txt').read_text().splitlines()
                     if line and not line.startswith('#'))
        inputs = hashlib.sha256(b''.join(path.read_bytes() for path in (
            ROOT/'.install/ports.lock', ROOT/'.install/packages.local', ROOT/'.install/ports/ports.conf',
            *sorted((ROOT/'.install/ports').glob('*.patch'))))).hexdigest()
        self.assertEqual(lists.pop('inputs'), inputs, 'record .install/tests/variant-deps.txt again on FreeBSD')
        return allowed, {name: names.split() for name, names in lists.items()}

    def test_native_dependency_lists_name_reviewed_packages_in_build_order(self):
        # ffmpeg-dependencies stopped on frei0r, the header of a build-only option, and
        # py312-ecdsa needs the framework's wheel tools. No reviewed package depends on them.
        allowed, lists = self.native_requests()
        order = [line.split('|')[0] for line in (ROOT/'.install/packages.local').read_text().splitlines()
                 if line and not line.startswith('#')]
        self.assertEqual(list(lists), order)
        for position, name in enumerate(order):
            for dependency in lists[name]:
                self.assertTrue(dependency in allowed, f'{name} needs the unreviewed {dependency}')
                if allowed[dependency][3] == 'local':
                    # The helper takes a variant only from its own finished build.
                    self.assertLess(order.index(dependency), position, f'{name} needs {dependency} first')

    def test_cached_catalog_closures_of_every_request_are_reviewed(self):
        # Requested packages bring their own dependencies: py312-build needs
        # py312-pyproject-hooks. Reads a catalog cached from the quarterly repository.
        catalog = ROOT/'.build/packagesite.yaml'
        if not catalog.is_file():
            self.skipTest('the quarterly catalog is not cached')
        with catalog.open(encoding='utf-8') as stream:
            packages = {package['name']: package for package in map(json.loads, filter(str.strip, stream))}
        allowed, lists = self.native_requests()
        queue = [(line, '.install/packages.txt') for line in (ROOT/'.install/packages.txt').read_text().splitlines()
                 if line and not line.startswith('#')]
        queue += [('gperf', 'install.sh'), *((name, '.install/packages.local') for name in lists)]
        seen = set()
        while queue:
            name, requester = queue.pop()
            if name in seen:
                continue
            seen.add(name)
            self.assertTrue(name in allowed, f'{requester} needs the unreviewed {name}')
            _, origin, version, kind = allowed[name]
            if kind == 'local':
                # Its archive is built here; the recorded list covers what it links and runs.
                queue.extend((dependency, name) for dependency in lists[name])
                continue
            self.assertEqual(packages[name]['origin'], origin)
            self.assertIn(version, ('*', packages[name]['version']), name)
            queue.extend((dependency, name) for dependency in packages[name].get('deps') or ())

    def test_no_reviewed_stock_package_links_the_wlroots_variant(self):
        # The variant leaves out wlroots' X11 and XWayland functions. The stock cage
        # called them, exited, and SDDM showed a blank console; build such programs here.
        catalog = ROOT/'.build/packagesite.yaml'
        if not catalog.is_file():
            self.skipTest('the quarterly catalog is not cached')
        with catalog.open(encoding='utf-8') as stream:
            packages = {package['name']: package for package in map(json.loads, filter(str.strip, stream))}
        provided = set(packages['wlroots020']['shlibs_provided'])
        self.assertIn('libwlroots-0.20.so', provided)
        allowed, _ = self.native_requests()
        for name, (_, _, _, kind) in allowed.items():
            if kind != 'local':
                self.assertFalse(provided & set(packages.get(name, {}).get('shlibs_required') or ()), name)
        self.assertTrue(provided & set(packages['cage']['shlibs_required']))

    def test_desktop_glyphs_have_a_requested_font(self):
        # fcft (bar, foot, fuzzel), Pango (dunst, gtklock) and Qt fall back through every
        # installed font. Read with fc-query from fonts/ and the FreeBSD 15 quarterly
        # packages on 2026-11-12: the bar's ᛒ was in none until noto-sans-runic. foot
        # draws U+2500-259F itself. The console has its own check in terminal-idle.py.
        covered = {
            'fonts/': '°·é–—“”…›↑●',
            'noto-sans-math': '≋≡▀▄█♪',
            'noto-sans-symbols2': '■▬▰◆◇◷☼♨',
            'noto-sans-runic': 'ᛒ',
            'noto-sans-jp': '文',
        }
        requested = set((ROOT/'.install/packages.txt').read_text().splitlines())
        self.assertLessEqual(set(covered) - {'fonts/'}, requested)
        files = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, check=True).stdout
        for name in files.decode().split('\0'):
            if not name or name.startswith(('.install/', 'docs/', 'art/licenses/')) or 'LICENSE' in name:
                continue
            try:
                text = (ROOT/name).read_text(encoding='utf-8')
            except (UnicodeDecodeError, IsADirectoryError):
                continue
            for glyph in {ch for ch in text if ord(ch) > 0x7e}:
                self.assertTrue(any(glyph in chars for chars in covered.values()),
                                f'{name}: U+{ord(glyph):04X} {glyph} has no verified font')

    def test_bootstrap_cleanup_preserves_user_roots_locks_and_consumers(self):
        source = (ROOT / '.install/scripts/packages.sh').read_text()
        branch = source.split('if [ "$action" = finish-bootstrap ]; then\n', 1)[1].split('\nif [ "$action" = import ]; then', 1)[0]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            (path / 'packages.allowed').write_text('libiconv|converters/libiconv|1.18_1|gnu-runtime\n')
            (path / 'local-libraries').write_text('libgdbm.so.6\n')
            stub = path / 'pkg'
            stub.write_text(f'#!{sys.executable}\n' + '''import json, os, sys
from pathlib import Path
p=Path(os.environ['TEST_ROOT']); state=json.loads((p/'state').read_text()); args=sys.argv[1:]
if args == ['query','-a','%n|%a|%#r|%k|%V|%o']:
    for name, data in state.items(): print('|'.join([name]+data['fields']))
elif args[:2] == ['query','%b']: print(state[args[2]].get('library',''))
elif args[:2] == ['delete','-n']: pass
elif args[:2] == ['delete','-y']:
    name=args[2]; assert state[name]['fields'][:4] == ['1','0','0','0']
    del state[name]
    if name == 'gnutls' and 'nettle' in state: state['nettle']['fields'][1]='0'
    (p/'state').write_text(json.dumps(state))
    with (p/'deleted').open('a') as log: log.write(name+'\\n')
else: raise SystemExit('unexpected pkg call: '+repr(args))
''')
            stub.chmod(0o755)
            states = {
                'gnutls': ['1','0','0','0','security/gnutls'],
                'nettle': ['1','1','0','0','security/nettle'],
                'bash': ['0','0','0','0','shells/bash'],
                'readline': ['1','0','1','0','devel/readline'],
                'libidn': ['1','0','0','1','dns/libidn'],
                'libidn2': ['1','2','0','0','dns/libidn2'],
                'gdbm': ['1','0','0','0','databases/gdbm'],
                'libiconv': ['1','0','0','0','converters/libiconv'],
                'gcc': ['1','0','0','0','base'],
                'unrelated': ['1','0','0','0','misc/unrelated'],
            }
            (path/'state').write_text(json.dumps({name: {'fields': fields, 'library': 'libgdbm.so.6' if name=='gdbm' else ''} for name, fields in states.items()}))
            script = 'set -eu\npolicy=$TEST_ROOT\ntemp=$TEST_ROOT\npkgtool() { "$TEST_ROOT/pkg" "$@"; }\nif true; then\n' + branch
            result = subprocess.run(['sh','-c',script], env={**os.environ,'TEST_ROOT':str(path)}, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0, 'retained GNU roots must require review')
            self.assertEqual((path/'deleted').read_text().splitlines(), ['gnutls','nettle'])
            self.assertEqual(set(json.loads((path/'state').read_text())), set(states)-{'gnutls','nettle'})
            self.assertIn('Retained GNU packages', result.stderr)

    def test_stock_variant_conversion_requires_exact_identity_and_no_lock(self):
        source = (ROOT / '.install/scripts/packages.sh').read_text()
        branch = source.split('if [ "$action" = reinstall ]; then\n',1)[1].split('    transact install -f',1)[0]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            (path/'packages.local').write_text('curl|ftp/curl|8.19.0\n')
            script = '''set -eu
policy=$TEST_ROOT
recipe=current
relock=
known_recipe() { [ "$1" = current ]; }
pkgtool() {
    case "$1:$2" in
        info:-e) return 0 ;;
        'query:%At|%Av') [ -z "$TEST_RECIPE" ] || printf 'nostromo_recipe|%s\n' "$TEST_RECIPE" ;;
        query:%k) printf '%s\n' "$TEST_LOCK" ;;
        'query:%n|%o|%v') printf '%s\n' "$TEST_ID" ;;
        unlock:-y) printf 'unlocked\n' ;;
        *) return 90 ;;
    esac
    return 0
}
set -- curl
''' + branch + '\n'
            for receipt, locked, identity, okay in [
                ('','0','curl|ftp/curl|8.19.0',True),
                ('','1','curl|ftp/curl|8.19.0',False),
                ('','0','curl|ftp/curl|8.18.0',False),
                ('','0','curl|other/curl|8.19.0',False),
                ('unknown','0','curl|ftp/curl|8.19.0',False),
                ('current','1','curl|ftp/curl|8.18.0',True),
            ]:
                result = subprocess.run(['sh','-c',script], env={**os.environ, 'TEST_ROOT':str(path),
                    'TEST_RECIPE':receipt,'TEST_LOCK':locked,'TEST_ID':identity}, capture_output=True, text=True)
                self.assertEqual(result.returncode==0, okay, result.stderr)

    def test_application_update_does_not_request_pkgbase(self):
        source = (ROOT / '.install/scripts/packages.sh').read_text()
        branch = source.split('if [ "$action" = update ]; then\n',1)[1].split('\nelse printf',1)[0]
        with tempfile.TemporaryDirectory() as directory:
            script = '''set -eu
store=$TEST_ROOT
temp=$TEST_ROOT
pkgtool() { printf '%s\n' 'FreeBSD-runtime|base' 'FreeBSD-utilities|base' 'foot|x11/foot' 'git-lite|devel/git@lite'; }
''' + branch + '\ncat "$temp/request"\n'
            result = subprocess.run(['sh','-c',script], env={**os.environ,'TEST_ROOT':directory},
                                    capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.splitlines(), ['foot','git-lite'])

    def removal_section(self):
        # The shared removable check, then the remove and retire branches.
        source = (ROOT / '.install/scripts/packages.sh').read_text()
        validate = 'validate() {' + source.split('validate() {', 1)[1].split('esac }\n', 1)[0] + 'esac }\n'
        section = source.split('# Only a package nothing here needs', 1)[1].split('\nif [ "$action" = update ]; then', 1)[0]
        return validate + '# Only a package nothing here needs' + section + '\n'

    def test_remove_rejects_consumers_locks_base_and_local_library_providers(self):
        branch = self.removal_section()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'packages.txt').write_text('desktop\n')
            (path/'packages.local').write_text('variant|misc/variant|1\n')
            (path/'local-libraries').write_text('liblocal.so.1\n')
            script = '''set -eu
policy=$TEST_ROOT; store=$TEST_ROOT; temp=$TEST_ROOT; action=remove
pkgtool() {
    case "$1:$2" in
    query:-a) case $3 in P*) printf '%s\n' "$TEST_PACKAGE" ;; D*) : ;; esac ;;
    query:%b) printf '%s\n' "$TEST_LIBRARY" ;;
    delete:*) printf 'deleted %s\n' "$2" ;;
    *) exit 90 ;;
    esac
}
set -- "$TEST_NAME"
''' + branch
            for name, origin, locked, vital, consumers, library, okay in [
                ('leaf','misc/leaf',0,0,0,'',True),
                ('leaf','misc/leaf',0,0,1,'',False),
                ('leaf','misc/leaf',1,0,0,'',False),
                ('leaf','misc/leaf',0,1,0,'',False),
                ('leaf','base',0,0,0,'',False),
                ('pkg','ports-mgmt/pkg',0,0,0,'',False),
                ('desktop','x11/desktop',0,0,0,'',False),
                ('leaf','misc/leaf',0,0,0,'liblocal.so.1',False),
            ]:
                with self.subTest(name=name, origin=origin, consumers=consumers):
                    result = subprocess.run(['sh','-c',script], capture_output=True, text=True,
                        env={**os.environ, 'TEST_ROOT':directory, 'TEST_NAME':name,
                             'TEST_PACKAGE':f'P|{name}|{origin}|{locked}|{vital}|{consumers}',
                             'TEST_LIBRARY':library})
                    self.assertEqual(result.returncode == 0, okay, result.stderr)
                    self.assertEqual('deleted' in result.stdout, okay)

    def test_retire_removes_only_unused_packages_from_the_retired_origin(self):
        # The stock cage stayed installed after SDDM stopped using it.
        branch = self.removal_section()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'packages.local').write_text('variant|misc/variant|1\n')
            (path/'local-libraries').write_text('liblocal.so.1\n')
            script = '''set -eu
policy=$TEST_ROOT; store=$TEST_ROOT; temp=$TEST_ROOT; action=retire
pkgtool() {
    case "$1:$2" in
    info:-e) [ "$3" = "$TEST_INSTALLED" ] ;;
    query:%o) printf '%s\\n' "$TEST_ORIGIN" ;;
    query:-a) case $3 in P*) printf '%s\\n' "$TEST_PACKAGE" ;; D*) : ;; esac ;;
    query:%b) printf '%s\\n' "$TEST_LIBRARY" ;;
    delete:-y) printf 'deleted %s\\n' "$3" ;;
    *) exit 90 ;;
    esac
}
''' + branch
            for retired, installed, origin, consumers, library, requested, status, report in [
                ('# note\n\ncage|x11-wm/cage\n', '', 'x11-wm/cage', 0, '', '', 0, ''),
                ('cage|x11-wm/cage\n', 'cage', 'x11-wm/cage', 0, '', '', 0, 'Removed the retired cage package.'),
                ('cage|x11-wm/cage\n', 'cage', 'misc/cage', 0, '', '', 1, 'Review cage'),
                ('cage|x11-wm/cage\n', 'cage', 'x11-wm/cage', 1, '', '', 1, 'Cannot remove'),
                ('cage|x11-wm/cage\n', 'cage', 'x11-wm/cage', 0, 'liblocal.so.1', '', 1, 'locally built program'),
                ('cage|x11-wm/cage\n', 'cage', 'x11-wm/cage', 0, '', 'cage\n', 1, 'Required by the configured'),
                ('-cage|x11-wm/cage\n', '-cage', 'x11-wm/cage', 0, '', '', 2, 'Invalid package name.'),
            ]:
                with self.subTest(retired=retired, origin=origin, consumers=consumers, requested=requested):
                    (path/'packages.retired').write_text(retired)
                    (path/'packages.txt').write_text('desktop\n' + requested)
                    result = subprocess.run(['sh','-c',script], capture_output=True, text=True,
                        env={**os.environ, 'TEST_ROOT':directory, 'TEST_INSTALLED':installed, 'TEST_ORIGIN':origin,
                             'TEST_PACKAGE':f'P|{installed}|{origin}|0|0|{consumers}', 'TEST_LIBRARY':library})
                    self.assertEqual(result.returncode, status, result.stderr)
                    self.assertIn(report, result.stdout + result.stderr)
                    self.assertEqual('deleted' in result.stdout, status == 0 and bool(installed))

    def test_retired_packages_are_no_longer_requested_or_reviewed(self):
        # A retired name that is still requested would stop every installing run.
        retired = [line.split('|') for line in (ROOT/'.install/packages.retired').read_text().splitlines()
                   if line and not line.startswith('#')]
        self.assertTrue(retired)
        requested = {line for line in (ROOT/'.install/packages.txt').read_text().splitlines()
                     if line and not line.startswith('#')}
        listed = {line.split('|')[0] for name in ('packages.allowed', 'packages.local')
                  for line in (ROOT/'.install'/name).read_text().splitlines() if line and not line.startswith('#')}
        for row in retired:
            self.assertEqual(len(row), 2, row)
            self.assertRegex(row[1], r'^[a-z0-9-]+/[A-Za-z0-9_.+-]+$')
            self.assertNotIn(row[0], requested | listed)

    def test_upgrade_dispatches_through_the_transaction_guard(self):
        source = (ROOT / '.install/scripts/packages.sh').read_text()
        branch = source.split('elif [ "$action" = update ]; then\n', 1)[1].split('\nelse\n', 1)[0]
        for status in (0, 1):
            result = subprocess.run(['sh','-c', '''set -eu
transact() { printf '%s\n' "$*"; return "$TEST_STATUS"; }
set -- pkg app library
''' + branch], capture_output=True, text=True, env={**os.environ,'TEST_STATUS':str(status)})
            self.assertEqual(result.returncode, status)
            self.assertEqual(result.stdout.splitlines(), ['upgrade pkg app library'])

    def test_pkg_upgrades_itself_before_the_requested_transaction(self):
        source = (ROOT / '.install/scripts/packages.sh').read_text()
        step = source.split('# Review that step separately', 1)[1].split('\n', 1)[1]
        step = step.split('if [ "$action" = reinstall ]; then', 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            for action, record, expected in [
                ('install', 'P|pkg|2|ports-mgmt/pkg|FreeBSD:15:amd64|0', ['upgrade pkg']),
                ('reinstall', 'P|pkg|2|ports-mgmt/pkg|FreeBSD:15:amd64|0', ['upgrade pkg']),
                ('update', 'P|pkg|2|ports-mgmt/pkg|FreeBSD:15:amd64|0', ['upgrade pkg']),
                ('preview', 'P|pkg|2|ports-mgmt/pkg|FreeBSD:15:amd64|0', []),
                ('install', 'P|pkg-devel|2|ports-mgmt/pkg-devel|FreeBSD:15:amd64|0', []),
                ('install', 'D|cmake-core|pkg|2|ports-mgmt/pkg', []),
            ]:
                with self.subTest(action=action, record=record):
                    (path/'records').write_text(record + '\n')
                    result = subprocess.run(['sh','-c', 'set -eu\ntemp=$TEST_ROOT; action=$TEST_ACTION\n'
                        'transact() { printf "%s\\n" "$*"; }\n' + step], capture_output=True, text=True,
                        env={**os.environ,'TEST_ROOT':directory,'TEST_ACTION':action})
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout.splitlines(), expected)

    def test_installed_identity_reports_each_mismatch(self):
        source = (ROOT / '.install/scripts/packages.sh').read_text()
        marker = "pkgtool query -a '%n|%v|%o|%q|%a' >\"$receipt/after\"\n"
        check = marker + source.split(marker, 1)[1].split('\nif [ "$action" = update ]', 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'records').write_text('P|app|1|misc/app|FreeBSD:15:*|1\nP|lib|2|devel/lib|FreeBSD:15:amd64|0\n')
            for installed, message in [
                # pkg keeps an installed dependency the new package does not need replaced.
                ('app|1|misc/app|FreeBSD:15:*|0\nlib|1|devel/lib|FreeBSD:15:amd64|1\n', None),
                ('app|1|misc/app|FreeBSD:15:*|0\nlib|2|other/lib|FreeBSD:15:amd64|1\n',
                 'Installed origin/ABI differs from the audited package: lib'),
                ('app|1|misc/app|FreeBSD:15:amd64|0\nlib|2|devel/lib|FreeBSD:15:amd64|1\n',
                 'Installed origin/ABI differs from the audited package: app'),
                ('app|1|misc/app|FreeBSD:15:*|0\n', 'Missing transaction package: lib'),
            ]:
                with self.subTest(installed=installed):
                    result = subprocess.run(['sh','-c', 'set -eu\ntemp=$TEST_ROOT; receipt=$TEST_ROOT\n'
                        'pkgtool() { printf "%s" "$TEST_INSTALLED"; }\n' + check], capture_output=True, text=True,
                        env={**os.environ,'TEST_ROOT':directory,'TEST_INSTALLED':installed})
                    self.assertEqual(result.returncode == 0, message is None, result.stderr)
                    if message:
                        self.assertIn(message, result.stderr)

    def test_update_checks_pending_versions_and_preserves_dependency_flags(self):
        source = (ROOT / '.install/scripts/packages.sh').read_text()
        branch = source.split('localpkg check -d -n -a\n', 1)[1]
        branch = 'localpkg check -d -n -a\n' + branch.split('\nwhile IFS=', 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'records').write_text('P|app|2|misc/app|FreeBSD:15:amd64|0\n')
            (path/'before').write_text('app|1|misc/app|FreeBSD:15:amd64|1\n')
            (path/'protected-build').write_text('gmake\n')
            (path/'request').write_text('app\n')
            for pending, automatic, identity, okay in [
                ('',1,'app|2|misc/app|FreeBSD:15:amd64',True),
                ('app-1 <',1,'app|1|misc/app|FreeBSD:15:amd64',False),
                ('',0,'app|2|misc/app|FreeBSD:15:amd64',False),
                ('',1,'app|2|other/app|FreeBSD:15:amd64',False),
                ('',1,'other|2|misc/other|FreeBSD:15:amd64',False),
            ]:
                script = '''set -eu
temp=$TEST_ROOT; receipt=$TEST_ROOT; store=$TEST_ROOT; action=update; build=1
localpkg() {
    case "$*" in
    'check -d -n -a') return 0 ;;
    'version -U -R -r NostromoTransaction -l <') [ -z "$TEST_PENDING" ] || printf '%s\n' "$TEST_PENDING" ;;
    *) return 90 ;;
    esac
    return 0
}
pkgtool() { printf '%s|%s\n' "$TEST_ID" "$TEST_AUTO"; }
''' + branch
                result = subprocess.run(['sh','-c',script], capture_output=True, text=True,
                    env={**os.environ,'TEST_ROOT':directory,'TEST_PENDING':pending,
                         'TEST_AUTO':str(automatic),'TEST_ID':identity})
                self.assertEqual(result.returncode == 0, okay, result.stderr)
                self.assertEqual((path/'protected-build').read_text(), 'gmake\n')

    def test_prepare_replaces_only_an_unedited_ports_tree_from_an_earlier_recipe(self):
        # The script runs unchanged with modeled tools. FreeBSD's NetBSD mtree exits 2
        # for changed content but only reports missing and extra files.
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            repo, tools = base/'repo', base/'bin'
            for path in (repo/'.install/scripts', repo/'.install/ports', tools):
                path.mkdir(parents=True)
            source = (ROOT/'.install/scripts/ports-variants.sh').read_text()
            native = 'PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin:/usr/local/sbin\n'
            self.assertIn(native, source)
            (repo/'.install/scripts/ports-variants.sh').write_text(source.replace(native, f'PATH={tools}:/bin:/usr/bin\n'))
            (repo/'.install/ports.lock').write_text('92ed857ab5f20e13114a4c01193751e7f0866a36\n')
            (repo/'.install/scripts/fetch-source.sh').write_text(
                'mkdir -p "$2/devel/app"\nprintf "PORTNAME=app\\n" >"$2/devel/app/Makefile"\n'
                'printf x >>"$(dirname "$0")/../../fetches"\n')
            (repo/'.install/scripts/recipe-hash.sh').write_text('cat "$(dirname "$0")/../../recipe"\n')
            (tools/'uname').write_text('#!/bin/sh\necho FreeBSD\n')
            (tools/'mtree').write_text(f'#!{sys.executable}\n' + r'''
import hashlib, os, sys
args = sys.argv[1:]
root = args[args.index('-p') + 1]
def walk():
    found = {}
    for directory, dirs, files in os.walk(root):
        for name in dirs + files:
            path = os.path.join(directory, name)
            found[os.path.relpath(path, root)] = 'dir' if os.path.isdir(path) else \
                hashlib.sha256(open(path, 'rb').read()).hexdigest()
    return found
if '-c' in args:
    print('#\t   tree: ' + root)
    for name, value in sorted(walk().items()): print(name + '\t' + value)
    sys.exit()
spec = dict(line.rstrip('\n').split('\t') for line in open(args[args.index('-f') + 1]) if line[0] != '#')
found, status = walk(), 0
for name, value in spec.items():
    if name not in found: print(name + ' missing')
    elif found[name] != value: print(name + ': sha256digest changed'); status = 2
for name in sorted(found.keys() - spec.keys()): print('extra: ' + name)
sys.exit(status)
''')
            for tool in ('uname', 'mtree'):
                (tools/tool).chmod(0o755)
            build, ports = repo/'.build', repo/'.build/ports'
            makefile, cookie = ports/'devel/app/Makefile', build/'ports-work/app/.build_done.app'
            extra, moved = ports/'devel/app/files/patch-local', base/'Makefile'

            def recipe(name, option):
                (repo/'recipe').write_text(name + '\n')
                (repo/'.install/ports/app.patch').write_text('--- a/devel/app/Makefile\n+++ b/devel/app/Makefile\n'
                                                        f'@@ -1 +1,2 @@\n PORTNAME=app\n+OPTIONS_UNSET={option}\n')

            def run(*args):
                result = subprocess.run(['sh', str(repo/'.install/scripts/ports-variants.sh'), *args],
                                        capture_output=True, text=True)
                self.assertEqual([p.name for p in build.iterdir() if p.is_dir() and p.name.startswith('ports.')], [])
                return result

            recipe('one', 'GNU')
            result = run('prepare')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(makefile.read_text(), 'PORTNAME=app\nOPTIONS_UNSET=GNU\n')
            cookie.parent.mkdir(parents=True)
            cookie.touch()
            # A retry under the same recipe keeps the tree and its build work.
            self.assertEqual(run('prepare').returncode, 0)
            self.assertEqual((repo/'fetches').read_text(), 'x')
            self.assertTrue(cookie.exists())
            edits = {
                'extra: devel/app/files': (lambda: (extra.parent.mkdir(), extra.write_text('local\n')),
                                           lambda: shutil.rmtree(extra.parent)),
                'devel/app/Makefile missing': (lambda: makefile.rename(moved), lambda: moved.rename(makefile)),
                'devel/app/Makefile: sha256digest changed': (
                    lambda: makefile.write_text('PORTNAME=edited\n'),
                    lambda: makefile.write_text('PORTNAME=app\nOPTIONS_UNSET=GNU\n')),
            }
            for report, (edit, undo) in edits.items():
                edit()
                for name, option in (('one', 'GNU'), ('two', 'X11')):
                    with self.subTest(report=report, recipe=name):
                        recipe(name, option)
                        result = run('prepare')
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn(report, result.stdout)
                        self.assertIn('has the edits listed above', result.stderr)
                        self.assertTrue(ports.is_dir() and cookie.exists())
                        self.assertEqual((build/'ports.recipe').read_text(), 'one\n')
                undo()
            self.assertEqual((repo/'fetches').read_text(), 'x')
            # Builds never use a stale tree; prepare replaces it with its build work.
            result = run('deps', 'app')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Recipe changed: prepare the ports tree again.', result.stderr)
            result = run('prepare')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('replacing the unedited generated ports tree', result.stdout)
            self.assertIn('Discarding build work', result.stdout)
            self.assertEqual(makefile.read_text(), 'PORTNAME=app\nOPTIONS_UNSET=X11\n')
            self.assertEqual((build/'ports.recipe').read_text(), 'two\n')
            self.assertFalse((build/'ports-work').exists())
            self.assertEqual((repo/'fetches').read_text(), 'xx')
            # An interrupted replacement leaves receipts without a tree.
            shutil.rmtree(ports)
            self.assertEqual(run('prepare').returncode, 0)
            self.assertEqual((repo/'fetches').read_text(), 'xxx')
            # Without its receipt, a tree cannot be shown to be generated, so it stays.
            (build/'ports.mtree').unlink()
            recipe('three', 'NLS')
            result = run('prepare')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Incomplete generated ports tree', result.stderr)
            self.assertEqual(makefile.read_text(), 'PORTNAME=app\nOPTIONS_UNSET=X11\n')

    def test_ports_patches_apply_to_the_pinned_archive_and_keep_search_paths(self):
        # Reads the archive fetch-source.sh caches, after checking it; nothing is downloaded.
        top, expected = next(row[1:3] for row in (line.split('|') for line in
                             (ROOT/'.install/sources.lock').read_text().splitlines()) if row[0] == 'ports')
        archive = ROOT/'.build/downloads/ports.tar.gz'
        if not archive.is_file():
            self.skipTest('the pinned ports archive is not cached')
        with archive.open('rb') as stream:
            self.assertEqual(hashlib.file_digest(stream, 'sha256').hexdigest(), expected)
        patches = sorted((ROOT/'.install/ports').glob('*.patch'))
        ports = sorted({'/'.join(line[6:].split('/')[:2]) for patch in patches
                        for line in patch.read_text().splitlines() if line.startswith('+++ b/')})

        def variables(path):
            # Joined make assignments; option helpers such as NLS_CPPFLAGS stay separate.
            found = {}
            for line in path.read_text().replace('\\\n', ' ').splitlines():
                match = re.match(r'([A-Za-z0-9_]+)\s*[+?:!]?=(.*)', line)
                if match:
                    found.setdefault(match[1], []).extend(match[2].split())
            return found

        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(['tar', '-xzf', str(archive), '-C', directory, f'{top}/Mk/Uses/readline.mk',
                            *(f'{top}/{port}' for port in ports)], check=True)
            pristine, patched = Path(directory)/top, Path(directory)/'patched'
            shutil.copytree(pristine, patched)
            for patch in patches:
                with patch.open() as stream:
                    result = subprocess.run(['patch', '-s', '-F', '0', '-p1'], cwd=patched, stdin=stream,
                                            capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, patch.name + result.stdout + result.stderr)
            # USES=readline also adds LOCALBASE search paths. Python's first native
            # build lost them and could not link the system libmpdec and expat.
            readline = variables(pristine/'Mk/Uses/readline.mk')
            paths = {name: readline[name] for name in ('CPPFLAGS', 'LDFLAGS')}
            self.assertEqual(paths, {'CPPFLAGS': ['-I${LOCALBASE}/include'], 'LDFLAGS': ['-L${LOCALBASE}/lib']})
            outcome = {}
            for port in ports:
                before, after = variables(pristine/port/'Makefile'), variables(patched/port/'Makefile')
                if 'readline' not in before.get('USES', []) or 'readline' in after.get('USES', []):
                    continue
                if not any(name.endswith('LIB_DEPENDS') for name in after):
                    outcome[port] = 'no LOCALBASE libraries'
                elif any(use.startswith('localbase') for use in after['USES']):
                    outcome[port] = 'USES=localbase'
                else:
                    for name, words in paths.items():
                        self.assertLessEqual(set(words), set(after.get(name, [])), f'{port} {name}')
                    outcome[port] = 'own search paths'
            self.assertEqual(outcome, {'lang/python312': 'own search paths', 'multimedia/pipewire': 'USES=localbase',
                                       'textproc/hunspell': 'no LOCALBASE libraries'})

    def test_variant_builds_report_listed_advisories_instead_of_stopping(self):
        # Modeled make refuses a listed port without DISABLE_VULNERABILITIES, as the
        # pinned framework's check-vulnerable does on every build.
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            repo, tools, build = base/'repo', base/'bin', base/'repo/.build'
            for path in (repo/'.install/scripts', build/'ports/devel/app', tools):
                path.mkdir(parents=True)
            source = (ROOT/'.install/scripts/ports-variants.sh').read_text()
            native = 'PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin:/usr/local/sbin\n'
            self.assertIn(native, source)
            (repo/'.install/scripts/ports-variants.sh').write_text(source.replace(native, f'PATH={tools}:/bin:/usr/bin\n'))
            (repo/'.install/scripts/recipe-hash.sh').write_text('echo abc123\n')
            (repo/'.install/ports.lock').write_text('92ed857ab5f20e13114a4c01193751e7f0866a36\n')
            (repo/'.install/packages.local').write_text('app|devel/app|1.0\n')
            (build/'ports.recipe').write_text('abc123\n')
            (build/'ports.mtree').touch()
            advisories = base/'vuln.xml'
            (tools/'uname').write_text('#!/bin/sh\necho FreeBSD\n')
            (tools/'sysctl').write_text('#!/bin/sh\ncase $2 in hw.ncpu) echo 4 ;; *) echo 8589934592 ;; esac\n')
            (tools/'make').write_text(f'#!{sys.executable}\n' + r'''
import os, sys
args = sys.argv[1:]
if '-V' in args:
    print({'PKGNAME': 'app-1.0', 'AUDITFILE': os.environ['TEST_ADVISORIES']}[args[args.index('-V') + 1]])
    sys.exit()
targets = args[next(i for i, arg in enumerate(args) if arg.startswith('PKG_NOTE_')) + 1:]
with open(os.environ['TEST_ROOT'] + '/builds', 'a') as log:
    log.write(' '.join(targets) + '\n')
listed = os.path.isfile(os.environ['TEST_ADVISORIES']) and 'app' in open(os.environ['TEST_ADVISORIES']).read()
if listed and 'DISABLE_VULNERABILITIES=yes' not in targets:
    print('===>  app-1.0 has known vulnerabilities:')
    sys.exit(1)
packages = next(arg for arg in args if arg.startswith('PACKAGES='))[9:] + '/All'
os.makedirs(packages, exist_ok=True)
open(packages + '/app-1.0.pkg', 'w').close()
''')
            (tools/'pkg').write_text(f'#!{sys.executable}\n' + r'''
import os, sys
args = sys.argv[1:]
if args[0] == 'query':
    print('nostromo_recipe|abc123')
    sys.exit()
with open(os.environ['TEST_ROOT'] + '/audits', 'a') as log:
    log.write(' '.join(args[1:]) + '\n')
if 'app' in open(args[2]).read():
    print('app-1.0 is vulnerable:\n  App -- example advisory\n\n1 problem(s) in 1 package(s) found.')
    sys.exit(1)
print('0 problem(s) in 0 package(s) found.')
''')
            for tool in tools.iterdir():
                tool.chmod(0o755)
            package = build/'ports-packages/All/app-1.0.pkg'
            for listing, reported in ((None, False), ('<vuln>other</vuln>\n', False), ('<vuln>app</vuln>\n', True)):
                with self.subTest(listing=listing):
                    if listing is None:
                        advisories.unlink(missing_ok=True)
                    else:
                        advisories.write_text(listing)
                    result = subprocess.run(['sh', str(repo/'.install/scripts/ports-variants.sh'), 'build', 'app'],
                                            capture_output=True, text=True,
                                            env={**os.environ, 'TEST_ROOT': str(base),
                                                 'TEST_ADVISORIES': str(advisories)})
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    # Standard output stays the archive path; reports go to standard error.
                    self.assertEqual(result.stdout, f'{package}\n')
                    self.assertEqual('App -- example advisory' in result.stderr, reported, result.stderr)
                    self.assertEqual('Building app despite the audit report above.' in result.stderr, reported)
            self.assertEqual((base/'builds').read_text().splitlines(),
                             ['DISABLE_VULNERABILITIES=yes checksum stage stage-qa check-plist package'] * 3)
            # pkg audit reads only the framework's advisory file, and only when it exists.
            self.assertEqual((base/'audits').read_text().splitlines(), [f'-f {advisories} app-1.0'] * 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
