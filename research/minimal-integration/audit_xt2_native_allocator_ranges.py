"""Audit named native allocation registries against the fixed minimal carriers.
Original Codex-assisted research. Supplied X-T2 4.41 inputs stay local.
Static descriptor inventory and optional bounded OS-pool construction only;
not an exhaustive audit of arbitrary dynamic allocator arguments or later DMA.
"""
import contextlib,hashlib,json,struct,sys
from pathlib import Path
from firmware_analysis import Firmware
ROOT=Path(__file__).resolve().parents[1]
SPANS={'data':(0x781000,0x784000),'code':(0xdf7900,0xdf8000)}
OUT=ROOT/'research/minimal-native-allocator-ranges';OUT.mkdir(exist_ok=True)
def overlaps(start,end):
 assert 0<=start<end<=0x100000000
 return [n for n,(lo,hi) in SPANS.items() if max(start,lo)<min(end,hi)]
def source_pins():
 paths={Path(__file__).resolve()}
 paths.update(Path(m.__file__).resolve() for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).resolve().parent==ROOT/'scripts')
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
def main():
 pins=source_pins()
 f=Firmware('xt2-4.41',True);image_path=ROOT/'firmware/research/eterna-minimal-protected-unverified/ffboot.bin'
 image=image_path.read_bytes();assert hashlib.sha256(image).hexdigest()=='0b92b7922acbe18216996be3808734f50a6d66558b520aa327d56b7bc0ef23ec'
 descriptors=[]
 for i in range(13):
  address=0x1992530+16*i
  identifier,count,primary,companion=struct.unpack('<4I',f.read(address,16))
  if identifier==11:
   assert (count,primary,companion)==(0,0,0);break
  assert 0<count<=155
  row=dict(record=hex(address),identifier=identifier,count=count,primary=dict(start=hex(primary),end=hex(primary+count*0x3b00)),
   companion=dict(start=hex(companion),end=hex(companion+count*0x1820)),
   limit='Primary count/stride follow16a5cdc; companion stride follows16d1a14. Companion range is the matching nonzero-index capacity, not an executed allocation claim.')
  assert not overlaps(primary,primary+count*0x3b00)
  assert not overlaps(companion,companion+count*0x1820)
  descriptors.append(row)
 assert len(descriptors)==12
 # These are the two explicit backing arrays in cf0034, not allocator outputs.
 fixed=[dict(start=0x11a00ac,size=0x64000),dict(start=0x10d9b64,size=0x95400)]
 for x in fixed:assert not overlaps(x['start'],x['start']+x['size'])
 native=None
 if '--execute' in sys.argv:
  import probe_native_font_initialization as font
  from probe_native_kernel_preinitialization import main as prepare
  from verify_film_menu_navigation import invoke
  from kernel_gic_initialization import GicInitialization
  from kernel_timer_initialization import TimerInitialization
  from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
  from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_PC
  pins=source_pins()
  old_stock=font.STOCK;old_write=Path.write_text
  def output(path,text,*args,**kwargs):
   if path.parent.resolve()==(ROOT/'research').resolve():path=OUT/path.name
   return old_write(path,text,*args,**kwargs)
  Path.write_text=output;font.STOCK=image_path
  calls=[];carrier_writes=[]
  try:
   with (OUT/'prepare.log').open('w') as log,contextlib.redirect_stdout(log):u=prepare(early_only=True)
   def watch(uc,access,address,size,value,data):
    if any(max(address,lo)<min(address+size,hi) for lo,hi in SPANS.values()):
     carrier_writes.append(dict(pc=hex(uc.reg_read(UC_ARM_REG_PC)),address=hex(address),size=size));uc.emu_stop()
   u.hook_add(UC_HOOK_MEM_WRITE,watch)
   def pool_create(uc,pc,size,data):
    r0=uc.reg_read(UC_ARM_REG_R0)
    if pc==0x49c7c:
     attr,size,base=struct.unpack('<3I',uc.mem_read(r0,12));calls.append(dict(entry=hex(pc),attr=attr,size=size,base=base))
    else:
     base=uc.reg_read(UC_ARM_REG_R2);size=uc.reg_read(UC_ARM_REG_R3)
     calls.append(dict(entry=hex(pc),object=r0,base=base,size=size))
    assert not overlaps(base,base+size)
   for pc in [0x49c7c,0x40f20]:u.hook_add(UC_HOOK_CODE,pool_create,begin=pc,end=pc)
   assert invoke(u,0xcf0034,instruction_limit=1000000)==0
   assert [dict(start=x['base'],size=x['size']) for x in calls if x['entry']=='0x49c7c']==fixed
   # Continue the original kernel caller through its optional-heap setup,
   # stopping immediately on return before the later core handshake.
   gic=GicInitialization();gic.attach(u);timer=TimerInitialization();timer.attach(u)
   u.emu_start(0x41ef8,0x41f58,count=1000000)
   assert u.reg_read(UC_ARM_REG_PC)==0x41f58
   assert not gic.errors and not timer.errors
   kernel_heap=[x for x in calls if x.get('object')==0x5cdb4]
   assert len(kernel_heap)==1 and kernel_heap[0]['base']==0x16c014 and kernel_heap[0]['size']==0x1000
   limit=struct.unpack('<I',u.mem_read(0x5bab8,4))[0];assert 0<limit<=1000
   registered=[]
   for index in range(limit):
    pointer=struct.unpack('<I',u.mem_read(0x79fc4+index*4,4))[0]
    if not pointer:continue
    attr,size,requested,backing=struct.unpack('<4I',u.mem_read(pointer+0x40,16))
    header_base,header_size=struct.unpack('<2I',u.mem_read(pointer+0x18,8))
    assert pointer==0x7a008+index*0x54
    assert backing==requested==header_base and (size&~3)==header_size
    assert not overlaps(backing,backing+size) and not overlaps(pointer,pointer+0x54)
    registered.append(dict(id=index+1,object=hex(pointer),attr=attr,start=hex(backing),size=size,end=hex(backing+size)))
   assert len(registered)==2 and not carrier_writes
   native=dict(status='PASS bounded native OS-pool construction',calls=calls,registry_capacity=limit,registered=registered,
    kernel_optional_heap_pointer=hex(struct.unpack('<I',u.mem_read(0x5bb30,4))[0]),carrier_writes=carrier_writes,
    kernel_heap=kernel_heap[0],limits='Host-preloaded native CPU/bootstrap and41f94; explicit callcf0034 before scheduler. Original41ef8..41f58 optional-heap setup with fixed-time GIC/timer. No late registry mutation or full camera boot claim.')
  finally:Path.write_text=old_write;font.STOCK=old_stock
 assert pins=={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in pins}
 report=dict(scope=__doc__,image_sha256=hashlib.sha256(image).hexdigest(),fixed_os_pool_backings=fixed,
  processing_descriptors=descriptors,native=native,
  native_function_hashes={hex(a):hashlib.sha256(f.read(a,b-a)).hexdigest() for a,b in [(0xcf0034,0xcf0154),(0x49c7c,0x49d68),(0x4b89c,0x4b944),(0x40f20,0x41024),(0x5593c,0x55974),(0x58ba8,0x58bd4),(0x16a5cdc,0x16a5d70),(0x16d1a14,0x16d1aec)]},
  source_sha256=pins,
  remaining='Parameterized pool creation/reinitialization and other computed destinations are not globally bounded here; later normal execution remains blocked at the separately recorded NV/peripheral inputs. Read this as named registry evidence only.',hardware_verified=False,full_boot=False)
 (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(report=str(OUT/'verification.json'),processing_records=len(descriptors),native=native)))
if __name__=='__main__':main()
