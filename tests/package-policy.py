#!/usr/bin/env python3
"""Fail-closed package graph checks; no package manager or root privileges."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Policy(unittest.TestCase):
    def check_graph(self, policy, records, *, build=0):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "allowed").write_text(policy)
            (directory / "records").write_text(records)
            return subprocess.run(
                ["awk", "-v", "recipe=abc123", "-v", f"build={build}", "-f",
                 str(ROOT / "scripts/package-policy.awk"), str(directory / "allowed"),
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

    def test_archive_queries_handle_empty_dependency_lists_without_hiding_errors(self):
        source = (ROOT / 'scripts/packages.sh').read_text()
        identity = 'identity() {' + source.split('identity() {', 1)[1].split('\nif [ "$action" = finish-bootstrap', 1)[0]
        upstream = 'upstream_for() {' + source.split('upstream_for() {',1)[1].split('\nrecipe=',1)[0]
        resolve = source.split('cp "$temp/request" "$temp/queue"', 1)[1].split('# Protect shared-library', 1)[0]
        names = ['libedit', 'pkgconf', 'indexinfo', 'mpdecimal', 'expat']
        origins = ['devel/libedit', 'devel/pkgconf', 'print/indexinfo', 'math/mpdecimal', 'textproc/expat2']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'scripts').mkdir()
            (path/'scripts/package-policy.awk').write_bytes((ROOT/'scripts/package-policy.awk').read_bytes())
            (path/'packages.allowed').write_text('build-tool|devel/build-tool|*|stock\ndrm-612-kmod|graphics/drm-612-kmod|*|stock\n' + ''.join(
                f'{name}|{origin}|*|stock\n' for name, origin in zip(names, origins)))
            records = {'build-tool': {'origin': 'devel/build-tool', 'deps': names},
                       'drm-612-kmod': {'origin': 'graphics/drm-612-kmod', 'deps': []}}
            records.update({name: {'origin': origin, 'deps': []} for name, origin in zip(names, origins)})
            (path/'packages.json').write_text(json.dumps(records))
            stub = path/'pkg'
            stub.write_text(f'#!{sys.executable}\n' + '''
import json, os, sys
from pathlib import Path
root = Path(os.environ['TEST_ROOT']); args = sys.argv[1:]
packages = json.loads((root/'packages.json').read_text())
fault = os.environ['TEST_FAULT']
if args[0] in ('fetch','rquery'):
    expected = 'NostromoKmods' if args[-1].startswith('drm-612-kmod') else 'NostromoUpstream'
    assert args[args.index('-r')+1] == expected, args
if args[0] == 'fetch':
    dest = Path(args[args.index('-o')+1]); dest.mkdir(exist_ok=True)
    (dest/(args[-1]+'.pkg')).write_text(args[-1][:-2]); sys.exit(0)
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
temp=$TEST_ROOT; policy=$TEST_ROOT; build=1; recipe=abc123
pkgtool() { "$TEST_ROOT/pkg" "$@"; }
remote() { pkgtool "$@"; }
validate() { case $1 in '' | [!A-Za-z0-9]* | *[!A-Za-z0-9_+.-]*) exit 2 ;; esac; }
''' + upstream + '\n' + identity + '\ncp "$temp/request" "$temp/queue"\n' + resolve
            for fault, status in [('',0), ('old-pkg',0), ('missing-edge',1),
                                  ('partial',1), ('wrong-origin',1), ('query',42), ('annotation-query',43)]:
                with self.subTest(fault=fault):
                    (path/'repo').mkdir(exist_ok=True)
                    (path/'request').write_text('build-tool\ndrm-612-kmod\n')
                    result = subprocess.run(['sh','-c',script], capture_output=True, text=True,
                        env={**os.environ, 'TEST_ROOT':directory, 'TEST_FAULT':fault})
                    self.assertEqual(result.returncode, status, result.stderr)
                    if status==0:
                        self.assertEqual(set((path/'seen').read_text().splitlines()), {'build-tool','drm-612-kmod',*names})
                        self.assertNotIn('|||', (path/'records').read_text())

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
        source = (ROOT/'scripts/packages.sh').read_text()
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

    def test_catalog_uses_release_modules_and_ordinary_application_versions(self):
        source = (ROOT/'scripts/packages.sh').read_text()
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
        result = self.check_graph((ROOT / "packages.allowed").read_text(), graph)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_local_manifest_matches_the_policy(self):
        allowed = {r[0]: r for line in (ROOT / "packages.allowed").read_text().splitlines()
                   if line and not line.startswith("#") for r in [line.split("|")]}
        seen = set()
        for line in (ROOT / "packages.local").read_text().splitlines():
            if not line or line.startswith("#"):
                continue
            row = line.split("|")
            self.assertEqual(len(row), 3, line)
            name, origin, version = row
            self.assertNotIn(name, seen)
            seen.add(name)
            self.assertEqual(allowed[name], [name, origin, version, "local"])
        self.assertEqual(seen, {name for name, row in allowed.items() if row[3] == "local"})

    def test_bootstrap_cleanup_preserves_user_roots_locks_and_consumers(self):
        source = (ROOT / 'scripts/packages.sh').read_text()
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
                'gcc': ['1','0','0','0','base/gcc'],
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
        source = (ROOT / 'scripts/packages.sh').read_text()
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
        source = (ROOT / 'scripts/packages.sh').read_text()
        branch = source.split('if [ "$action" = update ]; then\n',1)[1].split('\nelse printf',1)[0]
        with tempfile.TemporaryDirectory() as directory:
            script = '''set -eu
store=$TEST_ROOT
temp=$TEST_ROOT
pkgtool() { printf '%s\n' 'FreeBSD-runtime|base/FreeBSD-runtime' 'foot|x11/foot' 'git-lite|devel/git@lite'; }
''' + branch + '\ncat "$temp/request"\n'
            result = subprocess.run(['sh','-c',script], env={**os.environ,'TEST_ROOT':directory},
                                    capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.splitlines(), ['foot','git-lite'])

    def test_remove_rejects_consumers_locks_base_and_local_library_providers(self):
        source = (ROOT / 'scripts/packages.sh').read_text()
        branch = source.split('if [ "$action" = remove ] || [ "$action" = remove-check ]; then\n', 1)[1]
        branch = branch.split('\nif [ "$action" = update ]; then', 1)[0]
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
if true; then
''' + branch
            for name, origin, locked, vital, consumers, library, okay in [
                ('leaf','misc/leaf',0,0,0,'',True),
                ('leaf','misc/leaf',0,0,1,'',False),
                ('leaf','misc/leaf',1,0,0,'',False),
                ('leaf','misc/leaf',0,1,0,'',False),
                ('leaf','base/runtime',0,0,0,'',False),
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

    def test_upgrade_dispatches_through_the_transaction_guard(self):
        source = (ROOT / 'scripts/packages.sh').read_text()
        branch = source.split('elif [ "$action" = update ]; then\n', 1)[1].split('\nelse\n', 1)[0]
        for status in (0, 1):
            result = subprocess.run(['sh','-c', '''set -eu
transact() { printf '%s\n' "$*"; return "$TEST_STATUS"; }
set -- pkg app library
''' + branch], capture_output=True, text=True, env={**os.environ,'TEST_STATUS':str(status)})
            self.assertEqual(result.returncode, status)
            self.assertEqual(result.stdout.splitlines(), ['upgrade pkg app library'])

    def test_pkg_upgrades_itself_before_the_requested_transaction(self):
        source = (ROOT / 'scripts/packages.sh').read_text()
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
        source = (ROOT / 'scripts/packages.sh').read_text()
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
        source = (ROOT / 'scripts/packages.sh').read_text()
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
            for path in (repo/'scripts', repo/'src/ports', tools):
                path.mkdir(parents=True)
            source = (ROOT/'scripts/ports-variants.sh').read_text()
            native = 'PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin:/usr/local/sbin\n'
            self.assertIn(native, source)
            (repo/'scripts/ports-variants.sh').write_text(source.replace(native, f'PATH={tools}:/bin:/usr/bin\n'))
            (repo/'ports.lock').write_text('92ed857ab5f20e13114a4c01193751e7f0866a36\n')
            (repo/'scripts/fetch-source.sh').write_text(
                'mkdir -p "$2/devel/app"\nprintf "PORTNAME=app\\n" >"$2/devel/app/Makefile"\n'
                'printf x >>"$(dirname "$0")/../fetches"\n')
            (repo/'scripts/recipe-hash.sh').write_text('cat "$(dirname "$0")/../recipe"\n')
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
                (repo/'src/ports/app.patch').write_text('--- a/devel/app/Makefile\n+++ b/devel/app/Makefile\n'
                                                        f'@@ -1 +1,2 @@\n PORTNAME=app\n+OPTIONS_UNSET={option}\n')

            def run(*args):
                result = subprocess.run(['sh', str(repo/'scripts/ports-variants.sh'), *args],
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
