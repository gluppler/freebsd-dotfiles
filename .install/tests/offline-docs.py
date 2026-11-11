#!/usr/bin/env python3
"""Exercise the reader with local files and stand-ins for FreeBSD tools."""
from pathlib import Path
from xml.etree import ElementTree
import hashlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
READER = ROOT / 'bin/nostromo-docs'
CATALOGUE = re.search(r"catalogue\(\) \{\n    cat <<'EOF'\n(.*?)\nEOF\n", READER.read_text(), re.S)[1].splitlines()
PYTHON_BOOKS = ('reference','tutorial','library','c-api','extending','howto','using','faq','whatsnew')


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
        self.env['NOSTROMO_LIBRARY_ROOT']=str(self.path/'library')
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
    elif args==['help']:
        print('Go is a tool for managing Go source code.\\n\\nThe commands are:\\n\\n'
              '\\tbug         start a bug report\\n\\tbuild       compile packages and dependencies\\n\\n'
              'Use "go help <command>" for more information about a command.\\n\\n'
              'Additional help topics:\\n\\n\\tbuildconstraint build constraints\\n'
              '\\tenvironment     environment variables\\n')
    elif args[0]=='help': print('usage: go '+args[1])
    else: print('func Printf(format string, a ...any) (n int, err error)')
elif name=='pkg':
    if args[1]=='%n %v': print('\\n'.join(package+' 1.0' for package in args[2:]))
    elif args[-1]=='python-doc-html':
        for topic in ('reference','tutorial','library','c-api','extending','howto','using','faq','whatsnew'):
            print(p/'python library'/topic/'index.html')
    elif args[-1]=='lua54': print(p/'lua54/lua/manual.html')
    elif args[-1]=='en-freebsd-doc': print(p/'freebsd/en/books/handbook/index.html')
    else: print(p/'python library/library/pathlib.txt')
elif name=='nostromo-tool': print(os.environ.get('TEST_LLVM_MC','/usr/local/llvm21/bin/llvm-mc'))
elif name=='rustc': print(p/'rust root')
elif name=='less': print(Path(args[-1]).read_text(),end='')
elif name=='lowdown': print(Path(args[-1]).read_text(),end='')
elif name=='tput': print('80')
elif name in ('nostromo-picker','fzf'):
    choices=sys.stdin.read()
    with (p/'offered').open('a') as log: log.write(json.dumps([args[-1],choices.splitlines()])+'\\n')
    if name=='nostromo-picker' and args[-1]=='DOCS' and os.environ.get('NOSTROMO_DOCS_PREVIEW'):
        Path(os.environ['NOSTROMO_DOCS_PREVIEW']).write_text('DOCS > \\n'+choices)
    queue=p/'choices'; lines=queue.read_text().splitlines()
    if not lines: raise SystemExit(1)
    print(lines[0]); queue.write_text('\\n'.join(lines[1:])+'\\n' if lines[1:] else '')
elif name=='foot': time.sleep(0.4)
''')
        stub.chmod(0o755)
        for name in ('go','pkg','rustc','less','lowdown','tput','nostromo-picker','fzf','foot',
                     'qutebrowser','zathura','man','notify-send','nostromo-tool','clang'):
            (binary/name).symlink_to(stub)

    def read(self, *args):
        return subprocess.run(['sh',str(READER),*args], env=self.env,
                              capture_output=True, text=True, timeout=4)

    def calls(self):
        return [json.loads(line) for line in (self.path/'calls').read_text().splitlines()]

    def offered(self):
        return [json.loads(line) for line in (self.path/'offered').read_text().splitlines()]

    def write(self, relative, text='reference'):
        file = self.path/relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)
        return file

    def detached(self, name):
        # The menu opens the reference from a detached shell; let it finish before cleanup.
        for _ in range(100):
            found = [row for row in self.calls() if row[0]==name] if (self.path/'calls').exists() else []
            if found:
                time.sleep(.45 if name=='foot' else .1)
                return found[-1]
            time.sleep(.02)
        self.fail(f'{name} was not started')

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
        file = self.write('python library/library/pathlib.txt', 'Path example:\n    Path("src").is_dir()\n')
        result = self.read('python','pathlib')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, file.read_text())
        self.assertEqual([row[0] for row in self.calls()], ['pkg','less'])
        self.assertNotEqual(self.read('python','missing').returncode, 0)

    def test_local_book_url_encodes_spaces_and_stays_on_wayland(self):
        book = self.write('rust root/share/doc/rust/html/std/index.html', '<pre>fn example() {}</pre>')
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
        self.assertEqual(list(self.path.glob('nostromo-docs.*')), [])

    def test_markdown_keeps_text_and_code_without_its_markup(self):
        self.write('library/notes/page.md', '\n'.join([
            '---', 'layout: post', 'title: "Part 1 - Setting up"', '---',
            '<a name="top"></a>Intro <b>bold</b>, <code>x</code>, <img src="t.png" alt="tree"> and std::vector<int> v;<br>',
            'The last `nop` fills <i>the</i> slot. `<span>kept</span>` stays.',
            'before <!-- one', 'two --> after',
            '    <div>indented code</div>',
            '```cpp', 'template <typename T> <div>fenced</div>', '```',
            '{% include image.html url="assets/images/tree.png" description="B-tree layout" %}',
            '{% raw %}{{ text }}{% endraw %} x<sup>2</sup>', '']))
        result = self.read('library','notes/page.md')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            '# Part 1 - Setting up', '',
            'Intro **bold**, `x`, [image: tree] and std::vector<int> v; ',
            'The last `nop` fills *the* slot. `<span>kept</span>` stays.',
            'before ', ' after',
            '    <div>indented code</div>',
            '```cpp', 'template <typename T> <div>fenced</div>', '```',
            '[image: B-tree layout]',
            '{{ text }} x^2'])
        self.assertEqual([row[0] for row in self.calls()], ['tput','lowdown','less'])
        self.assertEqual(list(self.path.glob('nostromo-docs.*')), [])

    def test_mkdocs_notes_tabs_and_directives_read_as_text(self):
        self.write('library/badge/page.md', '\n'.join([
            '!!! tip "Power first"', '    Budget the **current**.', '', '    Then pick a regulator.',
            'Next paragraph.', '',
            '??? warning', '    Hot.', '',
            '=== "Linux"', '', '    ```sh', '    mpremote ls', '', '    mpremote cp', '    ```', '',
            '{%', '   include-markdown "../index.md"', '%}after',
            '![Badge](badge.png){: style="width:400px;" } shown.',
            '    !!! note "indented, so code"', '']))
        result = self.read('library','badge/page.md')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            '> **Power first**', '> Budget the **current**.', '>', '> Then pick a regulator.', '',
            'Next paragraph.', '',
            '> **Warning**', '> Hot.', '',
            '**Linux**', '', '', '```sh', 'mpremote ls', '', 'mpremote cp', '```', '',
            '', 'after',
            '![Badge](badge.png) shown.',
            '    !!! note "indented, so code"'])
        self.assertEqual([row[0] for row in self.calls()], ['tput','lowdown','less'])

    def test_electronics_guide_opens_each_chapter_by_its_title(self):
        from urllib.parse import unquote
        guide = ROOT/'docs/electronics'
        titles = [re.search(r'<title>([^<]+)</title>', page.read_text())[1] for page in sorted(guide.glob('*.html'))]
        self.assertEqual((titles[0], len(titles)), ('Electronics guide', len(set(titles))))
        result = self.read('electronics')
        self.assertEqual(result.returncode, 0, result.stderr)
        name, args, env = self.calls()[-1]
        self.assertEqual((name, unquote(args[-1]), env['QT_QPA_PLATFORM']),
                         ('qutebrowser', 'file://'+str(guide/'00-contents.html'), 'wayland'))
        before = self.calls()
        for topic in ('../electronics/02-dc','02-dc.html','missing','01-symbols/x','-x'):
            self.assertEqual(self.read('electronics',topic).returncode, 2, topic)
        self.assertEqual(self.calls(), before)
        (self.path/'calls').unlink()
        (self.path/'choices').write_text('ELECTRONICS GUIDE\nBadges and projects\n')
        self.assertEqual(self.read('menu').returncode, 0)
        self.assertEqual(unquote(self.detached('qutebrowser')[1][-1]), 'file://'+str(guide/'11-badges.html'))
        self.assertEqual(self.offered()[-1], ['ELECTRONICS GUIDE', titles])
        self.assertFalse(any(row[0]=='foot' for row in self.calls()))

    def test_library_documents_open_in_the_reader_that_suits_them(self):
        from urllib.parse import unquote
        pdf = self.write('library/c-standard.pdf', '%PDF-1.7')
        page = self.write('library/posix/index.html', '<p>POSIX</p>')
        text = self.write('library/what-happens-when/README.rst', 'What happens when...\n')
        for topic in ('c-standard.pdf','posix/index.html','what-happens-when/README.rst'):
            result = self.read('library',topic)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([row[:2] for row in self.calls()][0], ['zathura',['--',str(pdf)]])
        self.assertEqual(self.calls()[1][0], 'qutebrowser')
        self.assertEqual(unquote(self.calls()[1][1][-1]), 'file://'+str(page))
        self.assertEqual(self.calls()[2][:2], ['less',['-iMRS','--',str(text)]])
        before = self.calls()
        for topic in ('../c-standard.pdf','/etc/passwd','-x.pdf','posix/../../x'):
            self.assertEqual(self.read('library',topic).returncode, 2)
        result = self.read('library','missing.pdf')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Missing local document', result.stderr)
        self.assertEqual(self.calls(), before)

    def test_library_chapters_have_titles_in_reading_order(self):
        self.write('library/http3/SUMMARY.md',
                   '* [English](en/README.md)\n  * [Why](en/why.md)\n  * [Alpha](en/alpha.md)\n')
        for name, text in [('README.md','# HTTP/3 explained\n'),('alpha.md','<!-- x -->\n# Alpha\n'),
                           ('why.md','```\n# not a title\n```\n## Why QUIC\n'),
                           ('zeta.md','---\ntitle: Zeta\n---\n'),('again.md','Why QUIC\n========\n')]:
            self.write(f'library/http3/en/{name}', text)
        (self.path/'choices').write_text('SYSTEMS LIBRARY\nHTTP/3 explained\nWhy QUIC (2)\n')
        result = self.read('menu')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.detached('foot')[1], ['-e',str(READER),'--hold','library','http3/en/again.md'])
        systems = [title for entry, title, _ in (row.split('|') for row in CATALOGUE) if entry=='SYSTEMS LIBRARY']
        self.assertEqual(self.offered()[1], ['SYSTEMS LIBRARY', systems])
        self.assertEqual(self.offered()[2], ['HTTP/3 explained',
                         ['HTTP/3 explained','Why QUIC','Alpha','Why QUIC (2)','Zeta']])

    def test_single_document_entries_open_directly_in_their_own_window(self):
        pdf = self.write('library/c-standard.pdf', '%PDF-1.7')
        (self.path/'choices').write_text('C STANDARD\n')
        result = self.read('menu')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.detached('zathura')[1], ['--',str(pdf)])
        self.assertEqual([prompt for prompt, _ in self.offered()], ['DOCS'])
        self.assertFalse(any(row[0]=='foot' for row in self.calls()))

    def test_go_language_documents_and_command_help_are_local(self):
        from urllib.parse import unquote
        spec = self.write('go root/doc/go_spec.html', '<pre>spec</pre>')
        self.write('go root/doc/godebug.md', '# Go, Backwards Compatibility, and GODEBUG\n')
        result = self.read('go-language')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(unquote(self.calls()[-1][1][-1]), 'file://'+str(spec))
        result = self.read('go-language','godebug')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('# Go, Backwards Compatibility, and GODEBUG', result.stdout)
        result = self.read('go-help','buildconstraint')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'usage: go buildconstraint\n')
        for args in [('go-language','tutorial'),('go-help','nonexistent'),('go-help','../build')]:
            self.assertEqual(self.read(*args).returncode, 2)
        (self.path/'choices').write_text('GO COMMAND\nenvironment\n')
        self.assertEqual(self.read('menu').returncode, 0)
        self.assertEqual(self.detached('foot')[1], ['-e',str(READER),'--hold','go-help','environment'])
        self.assertEqual(self.offered()[-1][1], ['bug','build','buildconstraint','environment'])

    def test_go_by_example_shows_each_program_then_how_it_runs(self):
        self.write('library/go-by-example/examples.txt', "Hello World\nExec'ing Processes\nTesting and Benchmarking\n")
        self.write('library/go-by-example/examples/hello-world/hello-world.go', 'package main\n')
        self.write('library/go-by-example/examples/hello-world/hello-world.sh', '$ go run hello-world.go\nhello world\n')
        self.write('library/go-by-example/examples/execing-processes/execing-processes.go', 'package main\n')
        result = self.read('go-by-example','hello-world')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '// hello-world.go\n\npackage main\n\n'
                         '# Running it: hello-world.sh\n\n$ go run hello-world.go\nhello world\n\n')
        for topic, code in [('Hello',2),('../x',2),('testing-and-benchmarking',1)]:
            self.assertEqual(self.read('go-by-example',topic).returncode, code, topic)
        (self.path/'choices').write_text("GO BY EXAMPLE\nExec'ing Processes\n")
        self.assertEqual(self.read('menu').returncode, 0)
        self.assertEqual(self.detached('foot')[1], ['-e',str(READER),'--hold','go-by-example','execing-processes'])
        self.assertEqual(self.offered()[-1][1], ['Hello World',"Exec'ing Processes",'Testing and Benchmarking'])

    def test_secret_knowledge_chapters_come_from_the_committed_extract(self):
        chapters = sorted(p.stem for p in (ROOT/'docs/secret-knowledge').glob('*.md') if p.name!='LICENSE.md')
        self.assertEqual(chapters, ['howtos','lists','one-liners','services','shell-tricks','tools'])
        result = self.read('knowledge','one-liners')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[0], '# Shell one-liners')
        for topic in ('LICENSE','missing','../reference/c'):
            self.assertEqual(self.read('knowledge',topic).returncode, 2, topic)
        (self.path/'choices').write_text('SECRET KNOWLEDGE\ntools\n')
        self.assertEqual(self.read('menu').returncode, 0)
        self.assertEqual(self.detached('foot')[1], ['-e',str(READER),'--hold','knowledge','tools'])
        self.assertEqual(self.offered()[-1][1], chapters)

    def test_saved_manuals_keep_their_names_and_open_in_the_pdf_reader(self):
        (self.path/'data/reference').mkdir(parents=True)
        self.env['NOSTROMO_DOCS_ROOT'] = str(self.path/'data/reference')
        (self.path/'choices').write_text('SAVED MANUALS\n')
        self.assertEqual(self.read('menu').returncode, 0)
        name, args, _ = self.calls()[-1]
        self.assertEqual(name, 'notify-send')
        self.assertIn(str(self.path/'data/manuals'), args[-1])
        manual = self.write('data/manuals/ThinkPad T14 Gen 2 (Intel) user guide.pdf', '%PDF-1.7')
        self.write('data/manuals/notes.txt', 'not a manual')
        (self.path/'choices').write_text(f'SAVED MANUALS\n{manual.name}\n')
        self.assertEqual(self.read('menu').returncode, 0)
        self.assertEqual(self.detached('zathura')[1], ['--',str(manual)])
        self.assertEqual(self.offered()[-1][1], [manual.name])
        for topic, code in [('../secret.pdf',2),('-x.pdf',2),('.hidden.pdf',2),('notes.txt',2),('missing.pdf',1)]:
            self.assertEqual(self.read('manual',topic).returncode, code, topic)

    def test_cmake_pages_open_through_man(self):
        (self.path/'choices').write_text('CMAKE\ncmake-presets\n')
        self.assertEqual(self.read('menu').returncode, 0)
        self.assertEqual(self.detached('foot')[1], ['-e',str(READER),'--hold','man','cmake-presets'])
        offered = self.offered()[-1][1]
        self.assertEqual(offered[:3], ['cmake','ctest','cpack'])
        self.assertIn('cmake-generator-expressions', offered)
        self.assertEqual(len(offered), len(set(offered)))

    def test_versions_name_every_pinned_reference(self):
        self.write('library/.posix.sha256', '11c7ee3e98febe3d58d03a02885d0fab9a3564d06a9b02742d9d138ae341a957\n')
        result = self.read('versions')
        self.assertEqual(result.returncode, 0, result.stderr)
        for text in ('(C23) working draft N3220','C++23 working draft N4950','POSIX.1-2024','Arm ABI: 2026Q3',
                     'Library posix: archive sha256 11c7ee3e98fe','cmake-man 1.0','lua54 1.0'):
            self.assertIn(text, result.stdout)

    def test_every_menu_entry_has_an_action(self):
        text = READER.read_text()
        entries = re.findall(r"'([^']+)'", re.search(r"choice=\$\(printf '%s\\n' (.*?)\|\s*choose DOCS\)", text, re.S)[1])
        branch = text[text.index('    case $choice in\n'):text.index('    *) exit 0 ;;\n    esac')]
        branch = re.sub(r'\\\n\s*', ' ', branch)
        labels = {label.strip().strip("'") for pattern in re.findall(r"^    ([^ \n][^\n]*?)\)[ \n]", branch, re.M)
                  for label in pattern.split('|')}
        self.assertEqual(len(entries), len(set(entries)))
        self.assertEqual(set(entries), labels)

    def test_full_language_books_are_local_and_escape_urls(self):
        from urllib.parse import unquote
        for args, relative in [(('language','c'),'cppreference/en/c.html'),
                               (('language','cpp'),'cppreference/en/cpp.html'),
                               (('go-language',),'go root/doc/go_spec.html'),
                               (('go-language','memory-model'),'go root/doc/go_mem.html'),
                               (('lua',),'lua54/lua/manual.html'),
                               (('python-book','reference'),'python library/reference/index.html'),
                               (('python-book','faq'),'python library/faq/index.html')]:
            file = self.write(relative, '<pre>example</pre>')
            result = self.read(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(unquote(self.calls()[-1][1][-1]), 'file://'+str(file))
        for args in [('language','../secret'),('python-book','unknown'),('rust','../std'),('lua','extra')]:
            self.assertEqual(self.read(*args).returncode, 2)

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
        files = ['cppreference/en/c.html', 'cppreference/en/cpp.html', 'python library/library/pathlib.txt',
                 'freebsd/en/books/handbook/index.html', 'lua54/lua/manual.html',
                 *(f'go root/doc/{name}' for name in ('go_spec.html','go_mem.html','asm.html','godebug.md')),
                 *(f'python library/{topic}/index.html' for topic in PYTHON_BOOKS),
                 *(f'rust root/share/doc/rust/html/{topic}/index.html' for topic in
                   ('book','std','reference','rust-by-example','embedded-book')),
                 *('library/'+row.split('|')[2].replace('*','x') for row in CATALOGUE),
                 'library/go-by-example/examples/hello-world/hello-world.go']
        for relative in files:
            self.write(relative)
        self.write('library/go-by-example/examples.txt', 'Hello World\n')
        result = self.read('--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        checked = [row[:2] for row in self.calls()]
        for manual in ('llvm-mc21','abduco','cmake-presets','cpack-generators'):
            self.assertIn(['man', ['-w', manual]], checked)
        self.assertIn(['go', ['help']], checked)
        for relative, message in [('go root/doc/go_mem.html', ''),
                                  ('lua54/lua/manual.html', 'Missing local document from lua54'),
                                  ('library/http3/en/x.md', 'Missing library document: http3/en/*.md'),
                                  ('library/aapcs64.pdf', 'Missing library document: aapcs64.pdf'),
                                  ('library/go-by-example/examples/hello-world/hello-world.go',
                                   'Missing Go by Example entry: hello-world')]:
            file = self.path/relative
            shutil.rmtree(file.parent) if file.name=='hello-world.go' else file.unlink()
            result = self.read('--check')
            self.assertNotEqual(result.returncode, 0, relative)
            self.assertIn(message, result.stderr)
            self.write(relative)
        # The electronics guide is installed beside the examples, as the Secret Knowledge chapters are.
        data = self.path/'data'
        for name in ('reference','secret-knowledge'):
            shutil.copytree(ROOT/'docs'/name, data/name)
        self.env['NOSTROMO_DOCS_ROOT'] = str(data/'reference')
        result = self.read('--check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'Missing electronics guide: {data}/electronics', result.stderr)
        shutil.copytree(ROOT/'docs/electronics', data/'electronics')
        result = self.read('--check')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_menu_cancellation_and_separate_document_window(self):
        (self.path/'choices').write_text('')
        self.assertEqual(self.read('menu').returncode, 0)
        self.assertFalse(any(row[0]=='foot' for row in self.calls()))
        (self.path/'choices').write_text('EXAMPLE TEMPLATES\nassembly\n')
        result = self.read('menu')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.detached('foot')[1], ['-e',str(READER),'--hold','examples','assembly'])


class Library(unittest.TestCase):
    """docs-library.sh with the real fetch-source.sh and stand-ins for fetch, sha256 and uname."""
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='library test ')
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name).resolve()
        self.repo, tools, self.served = self.path/'repo', self.path/'bin', self.path/'served'
        for path in (self.repo/'.install/scripts', tools, self.served):
            path.mkdir(parents=True)
        source = (ROOT/'.install/scripts/docs-library.sh').read_text()
        native = 'export PATH=/usr/local/bin:/usr/local/sbin:/bin:/usr/bin:/sbin:/usr/sbin\n'
        self.assertIn(native, source)
        (self.repo/'.install/scripts/docs-library.sh').write_text(source.replace(native, f'export PATH="{tools}:/bin:/usr/bin"\n'))
        shutil.copyfile(ROOT/'.install/scripts/fetch-source.sh', self.repo/'.install/scripts/fetch-source.sh')
        shutil.copyfile(ROOT/'.install/intermediates.crt', self.repo/'.install/intermediates.crt')
        (tools/'uname').write_text('#!/bin/sh\necho FreeBSD\n')
        (tools/'sha256').write_text(f'#!{sys.executable} -I\nimport hashlib, sys\n'
                                    'print(hashlib.sha256(open(sys.argv[-1], "rb").read()).hexdigest())\n')
        (tools/'fetch').write_text(f'#!{sys.executable} -I\n' + f'''import os, shutil, sys
args = sys.argv[1:]
with open({str(self.path/'fetches')!r}, 'a') as log: log.write(args[-1] + '\\n')
with open({str(self.path/'trust')!r}, 'a') as log:
    log.write(os.environ.get('SSL_CA_CERT_FILE', '-') + ' ' + os.environ.get('SSL_CA_CERT_PATH', '-') + '\\n')
shutil.copyfile({str(self.served)!r} + '/' + args[-1].rsplit('/', 1)[1], args[args.index('-o') + 1])
''')
        for tool in ('uname','sha256','fetch'):
            (tools/tool).chmod(0o755)
        self.env = {**os.environ, 'PATH':f'{tools}{os.pathsep}{os.environ["PATH"]}', 'TMPDIR':str(self.path)}
        self.library = self.repo/'.build/docs/library'

    def archive(self, name, root, members):
        """Serve a .tar.gz whose members are text, ('link', target) or 'fifo'."""
        with tarfile.open(self.served/name, 'w:gz') as tar:
            directory = tarfile.TarInfo(root)
            directory.type, directory.mode = tarfile.DIRTYPE, 0o755
            tar.addfile(directory)
            for relative, value in members.items():
                info = tarfile.TarInfo(f'{root}/{relative}')
                if isinstance(value, tuple):
                    info.type, info.linkname = tarfile.SYMTYPE, value[1]
                    tar.addfile(info)
                elif value == 'fifo':
                    info.type = tarfile.FIFOTYPE
                    tar.addfile(info)
                else:
                    data = value.encode()
                    info.size, info.mode = len(data), 0o644
                    tar.addfile(info, io.BytesIO(data))
        return hashlib.sha256((self.served/name).read_bytes()).hexdigest()

    def serve(self, name, data):
        (self.served/name).write_bytes(data)
        return hashlib.sha256(data).hexdigest()

    def pin(self, *records):
        (self.repo/'.install/sources.lock').write_text('# name|archive root|sha256|URL\n'
            'ports|ports-0|' + '0'*64 + '|https://example.org/ports.tar.gz\n' +
            ''.join('|'.join(record) + '\n' for record in records))

    def install(self):
        (self.path/'fetches').unlink(missing_ok=True)
        return subprocess.run(['sh', str(self.repo/'.install/scripts/docs-library.sh')], env=self.env,
                              capture_output=True, text=True, timeout=60)

    def fetches(self):
        file = self.path/'fetches'
        return file.read_text().splitlines() if file.exists() else []

    def snapshot(self):
        return {str(path.relative_to(self.library)): os.readlink(path) if path.is_symlink() else
                path.read_bytes() if path.is_file() else 'directory' for path in self.library.rglob('*')}

    def leftovers(self):
        # Only fetch-source.sh makes the downloads directory.
        downloads = self.repo/'.build/downloads'
        return (sorted(path.name for path in (self.repo/'.build/docs').iterdir()),
                list(downloads.iterdir()) if downloads.exists() else [], list(self.path.glob('nostromo-source.*')))

    def test_library_keeps_checked_documents_once_and_follows_its_pins(self):
        book = self.archive('book-1.tar.gz', 'book-1', {'README.md':'# Book\n', 'en/part1.md':'# One\n',
                            'en/link.md':('link','part1.md'), 'en/up':('link','..')})
        pdf = self.serve('standard.pdf', b'%PDF-1.7 one')
        self.pin(('doc-book','book-1',book,'https://example.org/book-1.tar.gz'),
                 ('doc-standard','standard.pdf',pdf,'https://example.org/standard.pdf'))
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.fetches(), ['https://example.org/book-1.tar.gz','https://example.org/standard.pdf'])
        # Both downloads, the archive through fetch-source.sh, add the pinned intermediates to the base roots.
        self.assertEqual((self.path/'trust').read_text().splitlines(), [f'{self.repo}/.install/intermediates.crt /etc/ssl/certs'] * 2)
        self.assertEqual((self.library/'book/en/link.md').read_text(), '# One\n')
        self.assertEqual((self.library/'.book.sha256').read_text(), book+'\n')
        self.assertEqual((self.library/'standard.pdf').read_bytes(), b'%PDF-1.7 one')
        # Only the checked documents stay: no archive, workspace or extraction directory.
        self.assertEqual(self.leftovers(), (['library'], [], []))
        result = self.install()
        self.assertEqual((result.returncode, self.fetches()), (0, []), result.stderr)
        (self.library/'standard.pdf').write_bytes(b'%PDF-1.7 edited')
        result = self.install()
        self.assertEqual((result.returncode, self.fetches()), (0, ['https://example.org/standard.pdf']), result.stderr)
        self.assertEqual((self.library/'standard.pdf').read_bytes(), b'%PDF-1.7 one')
        # A new pin replaces the whole tree, and items that are no longer pinned go.
        newer = self.archive('book-2.tar.gz', 'book-2', {'README.md':'# Book, second edition\n'})
        self.pin(('doc-book','book-2',newer,'https://example.org/book-2.tar.gz'))
        (self.library/'stale').mkdir()
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.fetches(), ['https://example.org/book-2.tar.gz'])
        self.assertEqual(self.snapshot(), {'.book.sha256':(newer+'\n').encode(), 'book':'directory',
                                           'book/README.md':b'# Book, second edition\n'})
        self.assertEqual(result.stdout.count('Removed an unpinned library item'), 2)
        self.assertEqual(self.leftovers(), (['library'], [], []))

    def test_unsafe_trees_and_bad_downloads_leave_the_library_as_it_was(self):
        book = self.archive('book-1.tar.gz', 'book-1', {'README.md':'# Book\n'})
        pdf = self.serve('standard.pdf', b'%PDF-1.7 one')
        pinned = [('doc-book','book-1',book,'https://example.org/book-1.tar.gz'),
                  ('doc-standard','standard.pdf',pdf,'https://example.org/standard.pdf')]
        self.pin(*pinned)
        self.assertEqual(self.install().returncode, 0)
        before = self.snapshot()
        (self.path/'outside').mkdir()
        for members in ({'escape':('link',str(self.path/'outside'))}, {'escape':('link','../../../../../outside')},
                        {'dangling':('link','missing')}, {'pipe':'fifo'}):
            digest = self.archive('other-1.tar.gz', 'other-1', {'README.md':'other\n', **members})
            self.pin(*pinned, ('doc-other','other-1',digest,'https://example.org/other-1.tar.gz'))
            result = self.install()
            self.assertEqual(result.returncode, 1, members)
            self.assertIn('Unsafe link or special file in doc-other.', result.stderr)
            self.assertEqual(self.snapshot(), before)
            self.assertEqual(self.leftovers(), (['library'], [], []))
        # A download that differs from its pin replaces nothing.
        self.pin(*pinned)
        self.serve('standard.pdf', b'%PDF-1.7 changed upstream')
        (self.library/'standard.pdf').write_bytes(b'%PDF-1.7 edited')
        result = self.install()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Checksum mismatch: doc-standard', result.stderr)
        self.assertEqual((self.library/'standard.pdf').read_bytes(), b'%PDF-1.7 edited')
        # Malformed records stop before anything is downloaded or removed.
        for record in (('doc-Book','book-1',book,'https://example.org/book-1.tar.gz'),
                       ('doc-book','book-1',book[:-1],'https://example.org/book-1.tar.gz'),
                       ('doc-book','book-1',book,'http://example.org/book-1.tar.gz')):
            self.pin(record)
            result = self.install()
            self.assertEqual((result.returncode, self.fetches()), (1, []), record)
            self.assertTrue((self.library/'standard.pdf').exists())

    def test_one_directory_of_a_larger_archive_is_all_that_is_kept(self):
        # Nothing else is extracted, so a member tar would refuse elsewhere in the archive stops nothing.
        program = self.archive('program-1.tar.gz', 'program-1', {
            'README.md':'# Program\n', 'src/main.c':'int main(void) { return 0; }\n',
            'src/' + '../' * 7 + 'elsewhere':'never extracted\n',
            'docs/manual/index.html':'<p>Manual</p>\n', 'docs/manual/part/one.html':'<p>One</p>\n',
            'docs/manual/start.html':('link','index.html')})
        self.pin(('doc-manual','program-1/docs/manual',program,'https://example.org/program-1.tar.gz'))
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.path.rglob('elsewhere')), [])
        self.assertEqual(self.fetches(), ['https://example.org/program-1.tar.gz'])
        self.assertEqual(self.snapshot(), {'.manual.sha256':(program+'\n').encode(), 'manual':'directory',
                                           'manual/index.html':b'<p>Manual</p>\n', 'manual/part':'directory',
                                           'manual/part/one.html':b'<p>One</p>\n', 'manual/start.html':'index.html'})
        self.assertEqual(self.leftovers(), (['library'], [], []))
        result = self.install()
        self.assertEqual((result.returncode, self.fetches()), (0, []), result.stderr)
        newer = self.archive('program-2.tar.gz', 'program-2', {'docs/manual/index.html':'<p>Second</p>\n'})
        self.pin(('doc-manual','program-2/docs/manual',newer,'https://example.org/program-2.tar.gz'))
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.snapshot(), {'.manual.sha256':(newer+'\n').encode(), 'manual':'directory',
                                           'manual/index.html':b'<p>Second</p>\n'})
        self.assertEqual(self.leftovers(), (['library'], [], []))

    def test_unsafe_or_missing_directories_leave_the_library_as_it_was(self):
        program = self.archive('program-1.tar.gz', 'program-1', {'docs/manual/index.html':'<p>Manual</p>\n'})
        pinned = ('doc-manual','program-1/docs/manual',program,'https://example.org/program-1.tar.gz')
        self.pin(pinned)
        self.assertEqual(self.install().returncode, 0)
        before = self.snapshot()
        (self.path/'outside').mkdir()
        unsafe = 'Unsafe link or special file in doc-other.'
        for root, members, message in [
                ('other-1/docs/other', {'docs/other/escape':('link',str(self.path/'outside'))}, unsafe),
                ('other-1/docs/other', {'docs/other/up':('link','..')}, unsafe),
                ('other-1/docs/other', {'docs/other/pipe':'fifo'}, unsafe),
                # A member that climbs out of its directory; eight levels up from where it
                # would extract is this test's own temporary root, never anywhere else.
                ('other-1/docs/other', {'docs/other/' + '../' * 8 + 'escaped':'escaped\n'}, ''),
                ('other-1/docs/missing', {}, ''),
                ('other-1/docs/other/index.html', {}, '')]:
            digest = self.archive('other-1.tar.gz', 'other-1', {'docs/other/index.html':'<p>Other</p>\n', **members})
            self.pin(pinned, ('doc-other',root,digest,'https://example.org/other-1.tar.gz'))
            result = self.install()
            self.assertEqual(result.returncode, 1, (root, members, result.stderr))
            self.assertIn(message, result.stderr)
            self.assertEqual(self.snapshot(), before)
            self.assertEqual(self.leftovers(), (['library'], [], []))
        self.assertEqual(list(self.path.rglob('escaped')), [])
        # A directory named outside its archive is refused before anything is downloaded.
        for root in ('/program-1/docs/manual', '-program-1/docs', 'program-1/../program-1/docs/manual'):
            self.pin(pinned, ('doc-other',root,program,'https://example.org/program-1.tar.gz'))
            result = self.install()
            self.assertEqual((result.returncode, self.fetches()), (1, []), root)
            self.assertEqual(self.snapshot(), before)
        self.pin(('doc-manual','program-1/docs/manual',hashlib.sha256(b'other').hexdigest(),
                  'https://example.org/program-1.tar.gz'))
        result = self.install()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Checksum mismatch: doc-manual', result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.leftovers(), (['library'], [], []))


# Where the electronics guide's figures draw. Text classes: font size, and advance per
# character in ems (Azeret Mono, or Michroma for headings).
NUMBER = r'-?(?:\d+\.?\d*|\.\d+)'
FONTS = {'s':(11, .65), 'b':(15, .65), 'mark':(14, .65), 'head':(10.5, 1.08)}


def compose(a, b):
    """The matrix (a, b, c, d, e, f) that applies b, then a."""
    return (a[0]*b[0] + a[2]*b[1], a[1]*b[0] + a[3]*b[1], a[0]*b[2] + a[2]*b[3], a[1]*b[2] + a[3]*b[3],
            a[0]*b[4] + a[2]*b[5] + a[4], a[1]*b[4] + a[3]*b[5] + a[5])


def transform(text):
    """An SVG or CSS transform list, in px and degrees, as a matrix."""
    matrix = (1, 0, 0, 1, 0, 0)
    for name, args in re.findall(r'(\w+)\(([^)]*)\)', text):
        values = [float(value) for value in re.findall(NUMBER, args)]
        x, y, turn = values[0], values[-1], math.radians(values[0])
        matrix = compose(matrix, {
            'translate':(1, 0, 0, 1, x, values[1] if len(values) > 1 else 0),
            'translateX':(1, 0, 0, 1, x, 0), 'translateY':(1, 0, 0, 1, 0, y),
            'scale':(x, 0, 0, y, 0, 0), 'scaleX':(x, 0, 0, 1, 0, 0), 'scaleY':(1, 0, 0, y, 0, 0),
            'rotate':(math.cos(turn), math.sin(turn), -math.sin(turn), math.cos(turn), 0, 0)}[name])
    return matrix


def moving(svg):
    """{class: {keyframe: matrix}} for each class its CSS moves; a fixed transform is keyframe None."""
    css = ''.join(style.text or '' for style in svg.iter('style'))
    frames = {name: {stop: transform(value) for stop, value in re.findall(r'([\d.]+)%\{[^}]*?transform:([^;}]*)', body)}
              for name, body in re.findall(r'@keyframes ([\w-]+)\{((?:[^{}]*\{[^}]*\})*)\}', css)}
    out = {}
    for name, body in re.findall(r'\.([\w-]+)\{([^}]*)\}', css):
        animation, fixed = re.search(r'animation:([\w-]+)', body), re.search(r'transform:([^;}]*)', body)
        # Bars and gauges scale within their own box, which is checked as drawn.
        if 'transform-box' in body:
            continue
        if animation and frames.get(animation[1]):
            out[name] = frames[animation[1]]
        elif fixed:
            out[name] = {None: transform(fixed[1])}
    return out


def path_points(d):
    """The end of each segment of a path."""
    tokens = re.findall(r'[A-Za-z]|' + NUMBER, d)
    counts = {'M':2, 'L':2, 'H':1, 'V':1, 'A':7, 'Q':4, 'C':6, 'S':4, 'T':2}
    points, x, y, start, command, i = [], 0.0, 0.0, (0.0, 0.0), 'M', 0
    while i < len(tokens):
        if tokens[i].isalpha():
            command, i = tokens[i], i + 1
            if command in 'Zz':
                x, y = start
                continue
        upper, relative = command.upper(), command.islower()
        values = [float(value) for value in tokens[i:i + counts[upper]]]
        i += counts[upper]
        if upper == 'H':
            x = values[0] + (x if relative else 0)
        elif upper == 'V':
            y = values[0] + (y if relative else 0)
        else:
            x, y = values[-2] + (x if relative else 0), values[-1] + (y if relative else 0)
        points.append((x, y))
        if upper == 'M':
            start, command = (x, y), 'l' if relative else 'L'
    return points


def corners(node):
    """What one node draws, as points in its own coordinates; text by its estimated width."""
    get = lambda name: float(node.get(name, 0))
    if node.tag == 'path':
        return path_points(node.get('d', ''))
    if node.tag == 'rect':
        box = (get('x'), get('y'), get('x') + get('width'), get('y') + get('height'))
    elif node.tag == 'circle':
        box = (get('cx') - get('r'), get('cy') - get('r'), get('cx') + get('r'), get('cy') + get('r'))
    elif node.tag == 'text':
        size, advance = next((FONTS[name] for name in node.get('class', '').split() if name in FONTS), (13, .65))
        width = len(''.join(node.itertext())) * advance * size
        left = get('x') - {'end':width, 'middle':width / 2}.get(node.get('text-anchor'), 0)
        box = (left, get('y') - .72 * size, left + width, get('y') + .22 * size)
    else:
        return []
    return [(box[0], box[1]), (box[2], box[1]), (box[0], box[3]), (box[2], box[3])]


def combine(outer, inner):
    """Matrices by keyframe, outer then inner. A fixed transform, keyframe None, holds at every
    keyframe; animations with different keyframes are tried in every pair."""
    keys = (set(outer) | set(inner)) - {None} or {None}
    if all(None in side or keys <= set(side) for side in (outer, inner)):
        return {key: compose(outer.get(key, outer.get(None)), inner.get(key, inner.get(None))) for key in keys}
    return {(a, b): compose(m, t) for a, m in outer.items() for b, t in inner.items()}


def drawn(node, matrices, moved, out):
    """Every point a node and its children draw, at each keyframe that moves them."""
    own = next((moved[name] for name in node.get('class', '').split() if name in moved), None)
    # A CSS transform replaces the transform attribute.
    if own:
        matrices = combine(matrices, own)
    elif node.get('transform'):
        matrices = combine(matrices, {None:transform(node.get('transform'))})
    if node.get('clip-path'):
        return
    for m in matrices.values():
        out.extend((m[0]*x + m[2]*y + m[4], m[1]*x + m[3]*y + m[5], node) for x, y in corners(node))
    if node.tag != 'text':
        for child in node:
            drawn(child, matrices, moved, out)


class Guide(unittest.TestCase):
    """The electronics guide: built from .install/electronics, self-contained, and drawn inside its figures."""
    def setUp(self):
        self.pages = {page.name: ElementTree.fromstring(page.read_text(encoding='utf-8').removeprefix('<!DOCTYPE html>\n'))
                      for page in sorted((ROOT/'docs/electronics').glob('*.html'))}

    def test_pages_are_built_from_their_source(self):
        result = subprocess.run([sys.executable, str(ROOT/'.install/electronics/build.py'), '--check'],
                                capture_output=True, text=True, timeout=300)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_pages_stand_alone_and_every_link_lands(self):
        ids = {}
        for name, root in self.pages.items():
            found = [node.get('id') for node in root.iter() if node.get('id')]
            self.assertEqual(len(found), len(set(found)), name)
            ids[name] = set(found)
        self.assertIn('00-contents.html', ids)
        for name, root in self.pages.items():
            policy = root.find("head/meta[@http-equiv='Content-Security-Policy']").get('content')
            self.assertTrue(policy.startswith("default-src 'none';"), name)
            for node in root.iter():
                self.assertNotIn(node.tag, ('script','iframe','object','embed','img','link','base'), name)
                self.assertEqual([key for key in node.attrib if key.startswith('on') or key == 'src'], [], name)
                if 'href' in node.attrib:
                    page, _, fragment = node.get('href').partition('#')
                    self.assertIn(page or name, ids, f'{name}: {node.get("href")}')
                    self.assertIn(fragment or None, {None, *ids[page or name]}, f'{name}: {node.get("href")}')

    def test_every_figure_is_titled_and_drawn_inside_its_frame(self):
        for name, root in self.pages.items():
            for svg in root.iter('svg'):
                title = svg.find('title')
                self.assertEqual((svg.get('role'), svg.get('aria-labelledby')), ('img', title.get('id')), name)
                self.assertTrue(title.text.strip(), name)
                left, top, width, height = (float(value) for value in svg.get('viewBox').split())
                points, moved = [], moving(svg)
                for child in svg:
                    drawn(child, {None:(1, 0, 0, 1, 0, 0)}, moved, points)
                # The page shows what overflows (figure svg { overflow: visible }), over the text around it.
                outside = {(node.tag, ''.join(node.itertext()) or node.get('d', '')[:40]) for x, y, node in points
                           if not (left - 2 <= x <= left + width + 2 and top - 2 <= y <= top + height + 2)}
                self.assertEqual(outside, set(), f'{name}: {title.text}')

    def test_formula_sheet_links_every_named_equation(self):
        named = {(name, node.get('id')) for name, root in self.pages.items() for node in root.iter()
                 if node.get('id', '').startswith('eq-')}
        listed = {tuple(node.get('href').split('#')) for node in self.pages['12-formulas.html'].iter('a')
                  if '#eq-' in node.get('href', '')}
        self.assertEqual(listed, named)
        self.assertGreater(len(named), 100)


if __name__ == '__main__':
    unittest.main(verbosity=2)
