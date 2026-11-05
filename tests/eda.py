"""Run the PCB workflow with inert KiCad commands and disposable projects."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Electronics(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pcb test ')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.bin = self.work/'bin'
        self.bin.mkdir()
        self.env = {**os.environ, 'HOME': str(self.work), 'TEST_ROOT': str(self.work),
                    'PATH': str(self.bin)+os.pathsep+os.environ['PATH']}
        self.project = self.work/'Board $(literal).kicad_pro'
        self.files = [self.project.with_suffix(suffix) for suffix in ('.kicad_pro','.kicad_sch','.kicad_pcb')]
        for path in self.files: path.write_text('saved fixture\n')
        stub = self.bin/'stub'
        stub.write_text(f'#!{sys.executable}\n'+'''
import os,sys,json
from pathlib import Path
root=Path(os.environ['TEST_ROOT']);name=Path(sys.argv[0]).name;args=sys.argv[1:]
with (root/'calls').open('a') as out: out.write(json.dumps([name,args,os.environ.get('GDK_BACKEND'),os.environ.get('INTERACTIVE_HTML_BOM_NO_DISPLAY')])+'\\n')
if name=='realpath': print(Path(args[-1]).resolve())
elif name=='kicad-cli':
    if (root/'fail').exists() and args[:2]==['pcb','drc']:sys.exit(5)
    if '--output' in args:
        out=Path(args[args.index('--output')+1])
        if args[:3] in (['pcb','export','gerbers'],['pcb','export','drill']):out.mkdir(parents=True,exist_ok=True)
        else:out.write_text('fixture output')
    else: print('native help fixture')
elif name=='python3.12':
    assert os.environ['INTERACTIVE_HTML_BOM_NO_DISPLAY']=='1'
    assert '--no-browser' in args and '--name-format' in args
    (Path(args[args.index('--dest-dir')+1])/'ibom.html').write_text('fixture assembly page')
elif name=='uname':print('FreeBSD')
elif name=='id':print('1001')
elif name=='pkg':
    table='sym-lib-table' if args[-1]=='kicad-library-symbols' else 'fp-lib-table'
    print(root/'template'/table)
''')
        stub.chmod(0o755)
        for name in ['realpath','kicad','kicad-cli','python3.12','uname','id','pkg']:
            (self.bin/name).symlink_to(stub)

    def run_workflow(self, action):
        return subprocess.run(['sh',str(ROOT/'home/.local/bin/nostromo-eda'),action,str(self.project)],
                              env=self.env,capture_output=True,text=True,timeout=8)

    def records(self):
        return [json.loads(line) for line in (self.work/'calls').read_text().splitlines()]

    def test_fabrication_has_checks_first_and_never_overwrites_sources(self):
        result=self.run_workflow('manufacture')
        self.assertEqual(result.returncode,0,result.stderr)
        calls=[row for row in self.records() if row[0]=='kicad-cli']
        self.assertEqual([row[1][:2] for row in calls[:2]],[['sch','erc'],['pcb','drc']])
        self.assertTrue(all('--exit-code-violations' in row[1] for row in calls[:2]))
        self.assertIn('--schematic-parity',calls[1][1])
        gerber=calls[2][1]
        self.assertIn('*.Cu,',gerber[gerber.index('--layers')+1])
        self.assertTrue(all(row[2]=='wayland' for row in calls))
        self.assertTrue(all(path.read_text()=='saved fixture\n' for path in self.files))
        self.assertEqual(self.run_workflow('manufacture').returncode,0)
        outputs=list(self.work.glob('pcb-output.*'))
        self.assertEqual(len(outputs),2)
        self.assertTrue(all((path/'ibom.html').is_file() for path in outputs))

    def test_drc_failure_stops_before_exports_and_keeps_report_directory(self):
        (self.work/'fail').touch()
        result=self.run_workflow('manufacture')
        self.assertEqual(result.returncode,5,result.stderr)
        self.assertFalse(any('export' in row[1] or row[0]=='python3.12' for row in self.records()))
        self.assertEqual(len(list(self.work.glob('pcb-output.*'))),1)

    def test_library_setup_preserves_user_table_and_generates_cli_reference(self):
        scripts=self.work/'scripts';scripts.mkdir()
        for name in ['setup-eda.sh','stage-licenses.sh']:shutil.copy2(ROOT/'scripts'/name,scripts/name)
        plugin=self.work/'.build/eda/ibom-d1eb5b79a52a2ddc1ce270b63920346463c19b05'
        (plugin/'InteractiveHtmlBom').mkdir(parents=True)
        (plugin/'InteractiveHtmlBom/generate_interactive_bom.py').write_text('fixture')
        (plugin/'LICENSE').write_text('fixture license')
        config=self.work/'.config/kicad/10.0';config.mkdir(parents=True)
        (config/'sym-lib-table').write_text('personal symbols')
        (self.work/'template').mkdir()
        for name in ['sym-lib-table','fp-lib-table']:(self.work/'template'/name).write_text('packaged table')
        result=subprocess.run(['sh',str(scripts/'setup-eda.sh')],env=self.env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((config/'sym-lib-table').read_text(),'personal symbols')
        self.assertEqual((config/'fp-lib-table').read_text(),'packaged table')
        self.assertIn('```text\nnative help fixture', (self.work/'.build/docs/kicad-cli.md').read_text())


if __name__=='__main__':unittest.main(verbosity=2)
