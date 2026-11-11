"""Rerun qualified dual-slot date checks and both native menu items on a composition.

Only expected artifact word count varies. Original native catalog/arbitration,
ABI, refusal/edge/transition and two-item UI checks remain intact. Original
source and frozen date reports are unchanged; adapted source hashes are pinned.
"""
import argparse
import inspect
import json
from pathlib import Path
from build_modular_candidate import ROOT,sha
import verify_date_folders_dual as native
import verify_date_folders_dual_menu as menu
import verify_date_folders_transitions as transitions


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();a.output.mkdir(exist_ok=True);words=len(json.loads((a.build/'manifest.json').read_text())['words']);pins={}
 text=inspect.getsource(native.main);assert text.count('verify_card(build,76)')==1
 text=text.replace('verify_card(build,76)',f'verify_card(build,{words})').replace('def main(','def execute(',1)
 ns=dict(vars(native));exec(compile(text,str(Path(native.__file__))+'::composition','exec'),ns);ns['execute'](a.build,a.output/'native')
 pins['native']=dict(original=sha(Path(native.__file__).read_bytes()),adapted=sha(text.encode()))
 transitions.main(a.build,a.output/'transitions');pins['transitions']=dict(original=sha(Path(transitions.__file__).read_bytes()))
 text=inspect.getsource(menu.run);assert text.count('Path(output)/item,76)')==1
 text=text.replace('Path(output)/item,76)',f'Path(output)/item,{words})').replace('def run(','def execute(',1)
 ns=dict(vars(menu));exec(compile(text,str(Path(menu.__file__))+'::composition','exec'),ns)
 (a.output/'menu').mkdir(exist_ok=True)
 for item in ['date','volume']:ns['execute'](a.build,a.output/'menu',item)
 pins['menu']=dict(original=sha(Path(menu.__file__).read_bytes()),adapted=sha(text.encode()))
 report=dict(scope=__doc__,status='PASS',elf_sha256=sha((a.build/'mods.elf').read_bytes()),words=words,checker_sha256=sha(Path(__file__).read_bytes()),source_sha256=pins,physical_storage=False,hardware_verified=False)
 (a.output/'adapter.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
