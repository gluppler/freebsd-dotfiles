"""Host checks for target guards and dispatch; never flashes or executes firmware."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class Embedded(unittest.TestCase):
    def test_rust_dispatch_is_project_scoped_and_rejects_unknown_channels(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory); (path/'bin').mkdir();(path/'project/src').mkdir(parents=True)
            tool=path/'bin/rustup'
            tool.write_text('#!/bin/sh\nprintf "%s\\n" "$RUSTUP_HOME" "$CARGO_HOME" "$@"\n')
            tool.chmod(0o755)
            marker=path/'project/.nostromo-rust';marker.write_text('1.98.1\n')
            env={**os.environ,'PATH':str(path/'bin')+':/usr/bin:/bin','XDG_DATA_HOME':str(path/'data')}
            args=['sh',str(ROOT/'home/.local/bin/nostromo-rust'),'tool','cargo','check','--target','thumbv6m-none-eabi']
            result=subprocess.run(args,cwd=path/'project/src',env=env,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stdout.splitlines(),[str(path/'data/nostromo/rustup'),str(path/'data/nostromo/cargo'),
                'run','1.98.1','cargo','check','--target','thumbv6m-none-eabi'])
            marker.write_text('nightly; touch unsafe\n')
            self.assertNotEqual(subprocess.run(args,cwd=path/'project',env=env,capture_output=True).returncode,0)

    def test_zephyr_rejects_wrong_architecture_word_size_and_float_abi(self):
        upstream=ROOT/'.build/upstream/zephyr-4.5.0'
        if not upstream.exists():self.skipTest('pinned Zephyr cache not prepared')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);(path/'resource/lib/baremetal').mkdir(parents=True)
            cases=[('arm','armv7em-none-eabihf',1,0,True),('arm','armv7em-none-eabihf',0,0,False),
                   ('arm64','armv7em-none-eabi',0,1,False),('riscv','riscv32-unknown-elf',0,1,False),
                   ('riscv','riscv64-unknown-elf',0,1,True),('x86','i686-pc-none-elf',0,1,False),
                   ('x86','i686-pc-none-elf',0,0,True)]
            for arch,triple,hard,bits64,expected in cases:
                (path/'profile').write_text('check|'+triple+'|\n')
                script=path/'check.cmake'
                script.write_text(f'''set(ZEPHYR_BASE "{upstream}")
set(NOSTROMO_RUNTIME "{path}")
set(ARCH {arch})
set(CONFIG_LLVM_USE_LLD ON)
set(CONFIG_COMPILER_RT_RTLIB ON)
set(CONFIG_FP_HARDABI {hard})
set(CONFIG_64BIT {bits64})
include("{ROOT}/src/embedded/cmake/toolchain/nostromo-llvm/target.cmake")
if(NOT CMAKE_C_COMPILER_TARGET STREQUAL "{triple}")
  message(FATAL_ERROR "Wrong driver triple")
endif()
''')
                result=subprocess.run(['cmake','-P',str(script)],capture_output=True,text=True)
                self.assertEqual(result.returncode==0,expected,result.stdout+result.stderr)

    def test_built_arm_runtime_links_an_actual_bare_metal_elf(self):
        archive=ROOT/'.build/embedded-test/resource/lib/baremetal/libclang_rt.builtins-armv6m.a'
        linkers=list((Path.home()/'.rustup/toolchains').glob('*/lib/rustlib/aarch64-apple-darwin/bin/rust-lld'))
        if not archive.is_file() or not linkers:self.skipTest('host compiler-rt/linker cache not prepared')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)
            (path/'main.c').write_text('volatile unsigned long long a=123456789123ULL,b=37;\n'
                'void _start(void) { a = a / b; for (;;) {} }\n')
            subprocess.run(['clang','--target=armv6m-none-eabi','-mcpu=cortex-m0','-mthumb','-mfloat-abi=soft',
                '-ffreestanding','-Wall','-Wextra','-Werror','-c',str(path/'main.c'),'-o',str(path/'main.o')],check=True)
            subprocess.run([str(linkers[0]),'-flavor','gnu','-m','armelf','-e','_start','-Ttext=0x08000000',
                str(path/'main.o'),str(archive),'-o',str(path/'firmware.elf')],check=True)
            header=(path/'firmware.elf').read_bytes()
            self.assertEqual(header[:6],b'\x7fELF\x01\x01')
            self.assertEqual(int.from_bytes(header[18:20],'little'),40)

if __name__=='__main__':unittest.main(verbosity=2)
