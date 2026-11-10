#!/usr/bin/env python3
"""Exercise the reader with local files and stand-ins for FreeBSD tools."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
READER = ROOT / 'home/.local/bin/nostromo-docs'


class Reader(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='docs test ')
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name)
        binary = self.path/'bin'
        binary.mkdir()
        self.env = {**os.environ, 'TEST_ROOT':str(self.path), 'TMPDIR':str(self.path),
                    'PATH':str(binary)+os.pathsep+os.environ['PATH'],
                    'NOSTROMO_DOCS_ROOT':str(ROOT/'docs/reference')}
        self.env['NOSTROMO_CPPREFERENCE_ROOT']=str(self.path/'cppreference')
        stub = binary/'stub'
        stub.write_text(f'#!{sys.executable}\n' + '''import json, os, sys, time
from pathlib import Path
p=Path(os.environ['TEST_ROOT']); name=Path(sys.argv[0]).name; args=sys.argv[1:]
with (p/'calls').open('a') as log:
    log.write(json.dumps([name,args,{k:os.environ.get(k) for k in
        ('GOTOOLCHAIN','GOPROXY','GOSUMDB','QT_QPA_PLATFORM','MANPATH')}])+'\\n')
if name=='go':
    assert os.environ['GOTOOLCHAIN']=='local' and os.environ['GOPROXY']=='off'
    assert os.environ['GOSUMDB']=='off'
    if args[0]=='env': print(p/'go root')
    elif args[0]=='list': print(p)
    else: print('func Printf(format string, a ...any) (n int, err error)')
elif name=='pkg':
    if args[-1]=='python-doc-html':
        for topic in ('reference','tutorial','library','c-api','extending','howto','using','whatsnew'):
            print(p/'python library'/topic/'index.html')
    elif args[-1]=='en-freebsd-doc': print(p/'freebsd/en/books/handbook/index.html')
    else: print(p/'python library/library/pathlib.txt')
elif name=='nostromo-tool': print(os.environ.get('TEST_LLVM_MC','/usr/local/llvm21/bin/llvm-mc'))
elif name=='rustc': print(p/'rust root')
elif name=='less': print(Path(args[-1]).read_text(),end='')
elif name=='lowdown': print(Path(args[-1]).read_text(),end='')
elif name=='tput': print('80')
elif name in ('nostromo-picker','fzf'):
    choices=sys.stdin.read()
    if name=='nostromo-picker' and args[-1]=='DOCS' and os.environ.get('NOSTROMO_DOCS_PREVIEW'):
        Path(os.environ['NOSTROMO_DOCS_PREVIEW']).write_text('DOCS > \\n'+choices)
    queue=p/'choices'; lines=queue.read_text().splitlines()
    if not lines: raise SystemExit(1)
    print(lines[0]); queue.write_text('\\n'.join(lines[1:])+'\\n' if lines[1:] else '')
elif name=='foot': time.sleep(0.4)
''')
        stub.chmod(0o755)
        for name in ('go','pkg','rustc','less','lowdown','tput','nostromo-picker',
                     'fzf','foot','qutebrowser','man','notify-send','nostromo-tool'):
            (binary/name).symlink_to(stub)

    def read(self, *args):
        return subprocess.run(['sh',str(READER),*args], env=self.env,
                              capture_output=True, text=True, timeout=4)

    def calls(self):
        return [json.loads(line) for line in (self.path/'calls').read_text().splitlines()]

    def test_queries_remain_literal_and_cannot_become_commands(self):
        for action, topic in [('c','malloc'),('cpp','std::vector'),('man','pf.conf')]:
            self.assertEqual(self.read(action,topic).returncode, 0)
            self.assertEqual(self.calls()[-1][1], [topic] if action=='man' else ['3',topic])
        before = self.calls()
        for topic in ('-Psh','../secrets','/etc/passwd','a;touch bad','$(id)','a\nb'):
            self.assertEqual(self.read('c',topic).returncode, 2)
        self.assertEqual(self.calls(), before)

    def test_go_reader_is_offline_and_cleans_its_pager_file(self):
        result = self.read('go','fmt.Printf')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('func Printf', result.stdout)
        self.assertEqual(self.calls()[0][1], ['doc','-all','fmt.Printf'])
        self.assertEqual(list(self.path.glob('nostromo-docs.*')), [])

    def test_python_reader_uses_the_installed_text_file(self):
        file = self.path/'python library/library/pathlib.txt'
        file.parent.mkdir(parents=True)
        file.write_text('Path example:\n    Path("src").is_dir()\n')
        result = self.read('python','pathlib')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, file.read_text())
        self.assertEqual([row[0] for row in self.calls()], ['pkg','less'])
        self.assertNotEqual(self.read('python','missing').returncode, 0)

    def test_local_book_url_encodes_spaces_and_stays_on_wayland(self):
        book = self.path/'rust root/share/doc/rust/html/std/index.html'
        book.parent.mkdir(parents=True)
        book.write_text('<pre>fn example() {}</pre>')
        result = self.read('rust','std')
        self.assertEqual(result.returncode, 0, result.stderr)
        name, args, env = self.calls()[-1]
        self.assertEqual(name, 'qutebrowser')
        from urllib.parse import unquote
        self.assertEqual(unquote(args[-1]), 'file://'+str(book))
        self.assertNotIn(' ', args[-1])
        self.assertEqual(env['QT_QPA_PLATFORM'], 'wayland')

    def test_examples_keep_code_and_never_run_it(self):
        result = self.read('examples','assembly')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('    addu $v0, $a0, $a1', result.stdout)
        self.assertEqual([row[0] for row in self.calls()], ['tput','lowdown','less'])
        self.assertIn('--term-no-colour', self.calls()[1][1])

    def test_full_language_books_are_local_and_escape_urls(self):
        from urllib.parse import unquote
        for args, relative in [(('language','c'),'cppreference/en/c.html'),
                               (('language','cpp'),'cppreference/en/cpp.html'),
                               (('go-language',),'go root/doc/go_spec.html'),
                               (('python-book','reference'),'python library/reference/index.html')]:
            file=self.path/relative;file.parent.mkdir(parents=True,exist_ok=True);file.write_text('<pre>example</pre>')
            result=self.read(*args)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(unquote(self.calls()[-1][1][-1]),'file://'+str(file))
        for args in [('language','../secret'),('python-book','unknown'),('rust','../std')]:
            self.assertEqual(self.read(*args).returncode,2)

    def test_llvm_manual_uses_the_ports_versioned_name(self):
        # FreeBSD's llvm21 port installs llvm-mc.1 as /usr/local/share/man/man1/llvm-mc21.1.gz.
        for tool, manual in [('/usr/local/llvm21/bin/llvm-mc', 'llvm-mc21'), ('/opt/llvm/bin/llvm-mc', 'llvm-mc')]:
            self.env['TEST_LLVM_MC'] = tool
            result = self.read('llvm')
            self.assertEqual(result.returncode, 0, result.stderr)
            name, args, env = self.calls()[-1]
            self.assertEqual((name, args), ('man', [manual]))
            self.assertTrue(env['MANPATH'].startswith(tool[:-len('/bin/llvm-mc')] + '/share/man:'), env['MANPATH'])

    def test_check_finds_every_local_reference(self):
        files = ['cppreference/en/c.html', 'cppreference/en/cpp.html', 'go root/doc/go_spec.html',
                 'python library/library/pathlib.txt', 'freebsd/en/books/handbook/index.html',
                 *(f'python library/{topic}/index.html' for topic in
                   ('reference','tutorial','library','c-api','extending','howto','using','whatsnew')),
                 *(f'rust root/share/doc/rust/html/{topic}/index.html' for topic in
                   ('book','std','reference','rust-by-example','embedded-book'))]
        for relative in files:
            file = self.path/relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('reference')
        result = self.read('--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(['man', ['-w', 'llvm-mc21']], [row[:2] for row in self.calls()])
        (self.path/'go root/doc/go_spec.html').unlink()
        self.assertNotEqual(self.read('--check').returncode, 0)

    def test_menu_cancellation_and_separate_document_window(self):
        (self.path/'choices').write_text('')
        self.assertEqual(self.read('menu').returncode, 0)
        self.assertFalse(any(row[0]=='foot' for row in self.calls()))
        (self.path/'choices').write_text('EXAMPLE TEMPLATES\nassembly\n')
        result = self.read('menu')
        self.assertEqual(result.returncode, 0, result.stderr)
        # Wait for the detached stand-in before TemporaryDirectory cleans up.
        for _ in range(30):
            if any(row[0]=='foot' for row in self.calls()): break
            time.sleep(.02)
        foot = next(row for row in self.calls() if row[0]=='foot')
        self.assertEqual(foot[1], ['-e',str(READER),'--hold','examples','assembly'])
        time.sleep(.45)


if __name__ == '__main__':
    unittest.main(verbosity=2)
