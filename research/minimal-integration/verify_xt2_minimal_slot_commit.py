"""Reuse existing native kernel initialization for the minimal bridge assay.
Diagnostic phase sequencing and queue transport remain fixtures; no camera boot.
"""
import contextlib,json,struct,hashlib,sys
from pathlib import Path
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_FP,UC_ARM_REG_SP,UC_ARM_REG_R0
import probe_native_font_initialization as font
import verify_film_visibility as visibility
import xt2_minimal_slot_assay as bridge
from probe_native_overlay_publication import main as prepare
from verify_film_menu_navigation import invoke

OUT=Path('research/minimal-slot-commit');OUT.mkdir(exist_ok=True)
IMAGE=Path('firmware/research/eterna-minimal-protected-unverified/ffboot.bin')
class Reuse:
 def __init__(self,uc):self.uc=uc
 def __getattr__(self,name):return getattr(self.uc,name)
 def mem_map(self,address,size,*args):
  regions=list(self.uc.mem_regions())
  if any(lo<=address and address+size-1<=hi for lo,hi,_ in regions):return
  return self.uc.mem_map(address,size,*args)
 def mem_write(self,address,data):
  if address==0 and len(data)==46505984:return # Preserve initialized kernel state.
  return self.uc.mem_write(address,data)

def main():
 image=IMAGE.read_bytes();assert hashlib.sha256(image).hexdigest()==bridge.EXPECTED_HASH
 source_files={Path(m.__file__).resolve() for m in tuple(sys.modules.values()) if getattr(m,"__file__",None) and Path(m.__file__).resolve().parent==Path("scripts").resolve()}
 source_files.add(Path(__file__).resolve())
 pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
 original_write=Path.write_text;original_uc=visibility.Uc
 old_stock=font.STOCK
 writes=[];results=[]
 # Every native prepare report is isolated; common historical reports stay intact.
 def output(path,text,*args,**kwargs):
  if path.parent==Path('research'):path=OUT/path.name
  return original_write(path,text,*args,**kwargs)
 Path.write_text=output;font.STOCK=IMAGE
 try:
  for row in [r["row"] for r in bridge.menu_rows(image,0xedaaac)[1]]:
   with (OUT/f'prepare-{row}.log').open('w') as log,contextlib.redirect_stdout(log):
    uc=prepare()
    # Original main constructor's queue creation, without scheduling main.
    # Code supplies queue3 and its pool sizes; no host-crafted queue object.
    uc.reg_write(UC_ARM_REG_FP,0x800d000);uc.reg_write(UC_ARM_REG_SP,0x800c000)
    bridge.run(uc,0x15ed670,0x15ed68c,1000000)
    assert uc.reg_read(UC_ARM_REG_R0)==0, uc.reg_read(UC_ARM_REG_R0)
   def watch(u,access,address,size,value,data):
    if any(max(address,lo)<min(address+size,hi) for lo,hi in [(0x781000,0x784000),(0xdf7900,0xdf8000)]):
     writes.append(dict(pc=hex(u.reg_read(UC_ARM_REG_PC)),address=hex(address),size=size));raise AssertionError('Candidate carrier write')
   uc.hook_add(UC_HOOK_MEM_WRITE,watch)
   for lo,hi in [(0x781000,0x784000),(0xdf7900,0xdf8000)]:assert bytes(uc.mem_read(lo,hi-lo))==image[lo:hi]
   visibility.Uc=lambda *a,**kw:Reuse(uc)
   index=next(r['index'] for r in bridge.menu_rows(image,0xedaaac)[1] if r['row']==row)
   holder={}
   def callback(u,public):
    holder['downstream']=bridge.assay(u,public);holder['public']=public;return holder['downstream']
   try:result=bridge.routed(image,0xedaaac,index,callback)
   except AssertionError as exc:
    if not holder:raise
    result=dict(holder,outer_fixture_error=str(exc))
   e=result['downstream']
   assert e['error'] is None and e['stage']=="native1498 state dispatch and slot commit",e
   assert e['global_slot_profiles']==[0,e['native_getter']],(row,e['native_getter'],e['global_slot_profiles'])
   assert not e['faults'] and not e['clock_errors'] and not e['gpio_errors']
   assert any(x['pc']=='0x173c8d4' for x in e['calls'])
   results.append(result)
   print('Native menu to slot',row,'PASS',flush=True)
  assert pins=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
  report=dict(status="PASS bounded menu to native global slot",scope=__doc__,image_sha256=hashlib.sha256(image).hexdigest(),results=results,carrier_writes=writes,source_sha256=pins,
   limits=["Host preloaded image; existing serialized kernel/ELF constructor fixtures.","Main queue creation is an original constructor slice; phase ordering and queue packet/receive transport are explicit fixtures.","Menu mode36 and existing synchronization fixtures; no host profile-byte transfer supplies the bridge.","Processing state0 to state1 and1498 table dispatch execute; no state/handle/slot selected by host.","Live-view callback handle publication,15fc cache update, actual capture scheduling and JPEG remain unverified.","Carrier watcher covers the assay after prepared context, not original ROM delivery or arbitrary DMA."])
  (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 finally:
  font.STOCK=old_stock;visibility.Uc=original_uc;Path.write_text=original_write
 print(json.dumps(dict(report=str(OUT/'verification.json'),cases=len(results))))
if __name__=='__main__':main()
