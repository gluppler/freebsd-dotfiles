#!/usr/bin/env python3
"""Fail-closed package graph checks; no package manager or root privileges."""
from pathlib import Path
import json
import os
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
        branch = source.split('if [ "$action" = reinstall ]; then\n',1)[1].split('    localpkg install -U -f -n',1)[0]
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

    def test_upgrade_uses_native_upgrade_and_stops_on_failure(self):
        source = (ROOT / 'scripts/packages.sh').read_text()
        branch = source.split('elif [ "$action" = update ]; then\n', 1)[1].split('\nelse\n', 1)[0]
        for status in (0, 1):
            result = subprocess.run(['sh','-c', '''set -eu
localpkg() { printf '%s\n' "$*"; return "$TEST_STATUS"; }
set -- pkg app library
''' + branch], capture_output=True, text=True, env={**os.environ,'TEST_STATUS':str(status)})
            self.assertEqual(result.returncode, status)
            self.assertEqual(result.stdout.splitlines(), [
                'upgrade -U -n --no-remove -r NostromoTransaction pkg app library',
                *(['upgrade -U -y --no-remove -r NostromoTransaction pkg app library'] if status==0 else [])])

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
