"""Rebuild the frozen minimal image in memory without changing either SD image.
Original Codex-assisted local audit; vendor inputs are locally supplied only.
"""
import hashlib,json,sys,shutil,subprocess,importlib.metadata
from pathlib import Path
from build_eterna_minimal_sd import build as base_build,OUTPUT as BASE
from build_xt2_minimal_protected import build as protected_build,OUT,ROOT

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 sources={Path(m.__file__).resolve() for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).resolve().parent==ROOT/'scripts'}
 sources.add(Path(__file__).resolve())
 sources.update(ROOT/'scripts'/n for n in ['xt2_minimal_compact_guard.S','xt2_minimal_boot_guard.S','xt2_minimal_data_entry.S','xt2_minimal_data_prepare.c','eterna_early_resident_gate.c','xt2_native_page_policy.c','xt2_native_page_policy.h'])
 pins={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sources}
 diagnostic=json.loads((ROOT/'research/xt2-delivery-probe-freeze.json').read_text())
 diagnostic_hashes={name:sha((ROOT/name).read_bytes()) for name in diagnostic['files']}
 inputs={};old_read=Path.read_bytes;old_text=Path.read_text
 def read_bytes(path,*args,**kwargs):
  value=old_read(path,*args,**kwargs)
  resolved=path.resolve()
  if resolved.is_relative_to(ROOT):inputs[str(resolved.relative_to(ROOT))]=dict(size=len(value),sha256=sha(value))
  return value
 def read_text(path,*args,**kwargs):
  value=old_text(path,*args,**kwargs)
  resolved=path.resolve()
  if resolved.is_relative_to(ROOT):
   data=old_read(path);inputs[str(resolved.relative_to(ROOT))]=dict(size=len(data),sha256=sha(data))
  return value
 Path.read_bytes=read_bytes;Path.read_text=read_text
 try:
  base,base_meta=base_build()
  image,meta,elf=protected_build()
 finally:Path.read_bytes=old_read;Path.read_text=old_text
 assert all(sha((ROOT/p).read_bytes())==v['sha256'] for p,v in inputs.items())
 linker=next((ROOT/'.toolchains/rustup/toolchains').glob('*/lib/rustlib/*/bin/gcc-ld/ld.lld'))
 compiler=Path(shutil.which('clang'))
 toolchain=dict(clang=str(compiler),clang_version=subprocess.run([str(compiler),'--version'],check=True,capture_output=True,text=True).stdout,
  linker=str(linker.relative_to(ROOT)),linker_sha256=sha(linker.read_bytes()),linker_version=subprocess.run([str(linker),'--version'],check=True,capture_output=True,text=True).stdout,
  python=sys.version,python_packages={p:importlib.metadata.version(p) for p in ['pyelftools','capstone','unicorn']})
 assert base==(BASE/'ffboot.bin').read_bytes()
 assert image==(OUT/'ffboot.bin').read_bytes()
 assert elf==(OUT/'late.elf').read_bytes()
 assert sha(image)=='0b92b7922acbe18216996be3808734f50a6d66558b520aa327d56b7bc0ef23ec'
 assert pins=={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sources}
 assert diagnostic_hashes=={name:sha((ROOT/name).read_bytes()) for name in diagnostic_hashes}
 # The protected builder checks all byte changes are confined to its wrapper,
 # root hook and early checker. Color tables/selectors/scalar bodies inherit base.
 report=dict(status='PASS',scope=__doc__,base_sha256=sha(base),image_sha256=sha(image),late_elf_sha256=sha(elf),image_size=len(image),early_checked_bytes=meta['early_checked_bytes'],
  source_sha256=pins,consumed_input_files=inputs,toolchain=toolchain,diagnostic_files_unchanged=diagnostic_hashes,
  inputs='Pinned local stock SD image, extracted X-T2/X-H1 units and their local metadata; no vendor material is bundled with public tooling.',
  numeric_evidence='Existing donor/function and nonalias selector checks inherited only for byte-identical color code/data. New native menu→slot assay is separate. No old numeric grid rerun.',
  hardware_verified=False,full_boot=False)
 (ROOT/'research/minimal-rebuild-verification.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['status','image_sha256','late_elf_sha256','early_checked_bytes']}))
if __name__=='__main__':main()
