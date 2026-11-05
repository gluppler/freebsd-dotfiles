#!/usr/bin/env python3
"""Compile the independent examples using installed host tools, without downloads."""
from pathlib import Path
import ast
import os
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def blocks(topic, language):
    return re.findall(r'```'+language+r'\n(.*?)\n```',
                      (ROOT/'docs/reference'/f'{topic}.md').read_text(), re.S)


with tempfile.TemporaryDirectory(prefix='nostromo-examples-') as directory:
    work = Path(directory)
    env = {**os.environ, 'GOTOOLCHAIN':'local', 'GOPROXY':'off', 'GOSUMDB':'off',
           'GOCACHE':str(work/'go-cache'), 'GOMODCACHE':str(work/'go-modules')}

    def run(args, **kwargs):
        subprocess.run(args, cwd=work, env=env, check=True, **kwargs)

    for code in blocks('c','c'):
        run(['cc','-std=c11','-Wall','-Wextra','-Werror','-x','c','-fsyntax-only','-'],
            input=code, text=True)
    (work/'example.cpp').write_text(blocks('cpp','cpp')[0])
    run(['c++','-std=c++20','-Wall','-Wextra','-Werror','example.cpp','-o','cpp-example'])
    run([str(work/'cpp-example')])
    (work/'example.rs').write_text(blocks('rust','rust')[0])
    run(['rustc','--edition=2021','-Dwarnings','example.rs','-o','rust-example'])
    run([str(work/'rust-example')])
    (work/'go.mod').write_text('module example.org/greeting\n\ngo 1.22\n')
    for name, code in zip(('greet.go','example_test.go'), blocks('go','go')):
        (work/name).write_text(code)
    run(['go','test','greet.go','example_test.go'])
    ast.parse(blocks('python','python')[0])
    run(['sh','-n'], input=blocks('shell','sh')[0], text=True)
    (work/'example.lua').write_text(blocks('vis','lua')[0])
    run(['luac','-p','example.lua'])
    triples = ('x86_64-unknown-freebsd','thumbv6m-none-eabi',
               'aarch64-none-elf','mipsel-none-elf')
    targets = subprocess.check_output(['clang','--print-targets'], text=True)
    for triple, code in zip(triples, blocks('assembly','asm')):
        (work/'example.s').write_text(code)
        if triple.startswith('mips') and 'mips' not in targets:
            print('MIPS assembly: host Clang has no MIPS backend; native LLVM check pending.')
            continue
        run(['clang','--target='+triple,'-c','example.s','-o','example.o'])
    print('Host C/C++/Rust/Go, Python/shell/Lua syntax and available assembly examples passed.')
    print('Zephyr example requires the selected native board devicetree and build.')
