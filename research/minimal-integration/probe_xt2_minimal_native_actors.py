"""Try actual main/processing/cache actors with existing kernel/ELF fixtures.
No host profile transfer, queue-copy fixture or forced state/handle after menu.
Not a complete reset/ROM or concurrent camera model.
"""
import contextlib,json,hashlib,struct,os,sys
from pathlib import Path
from collections import deque
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ,UcError,UC_ERR_INSN_INVALID
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_FPEXC
import probe_native_font_initialization as font
import verify_film_visibility as visibility
from verify_xt2_minimal_slot_commit import Reuse
from xt2_minimal_slot_assay import IMAGE,EXPECTED_HASH,run,routed,menu_rows
from probe_native_overlay_publication import main as prepare
from verify_film_menu_navigation import invoke
from xpp_clock_model import ClockModel
from xpp_gpio_configuration import GpioConfiguration
from native_vfp_exception import register as register_vfp,deliver as deliver_vfp
from arm_page_policy import inspect
from map_missing_ram import map_missing_ram
from xpp_serial_configuration import SerialConfiguration
from xpp_serial_transfer_probe import SerialTransferProbe

GPIO0=os.getenv('XT2_ASSAY_GPIO0')
SERIAL=os.getenv('XT2_ASSAY_SERIAL_CONFIG','0')
TRANSFER=SERIAL=='2'
TIME=os.getenv('XT2_ASSAY_POLL_TIMER')=='1'
OUT=Path('research/minimal-native-actors-input-boundary' if GPIO0 is None else 'research/minimal-native-actors-gpio0-'+GPIO0+('-transferprobe' if TRANSFER else '-serialconfig' if SERIAL=='1' else '')+('-polltimer' if TIME else ''));OUT.mkdir(exist_ok=True)
def main():
 original=Path.write_text;old_uc=visibility.Uc;old_stock=font.STOCK
 def output(path,text,*a,**kw):
  if path.parent==Path('research'):path=OUT/path.name
  return original(path,text,*a,**kw)
 Path.write_text=output;font.STOCK=IMAGE
 try:
  pins={str(Path(m.__file__).resolve()):hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in tuple(sys.modules.values()) if getattr(m,"__file__",None) and Path(m.__file__).resolve().parent==Path(__file__).resolve().parent}
  pins[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
  image=IMAGE.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED_HASH
  constructor_carrier_writes=[]
  with (OUT/'prepare.log').open('w') as log,contextlib.redirect_stdout(log):
   u=prepare();register_vfp(u);base_context=u.context_save()
   spans=[(0x781000,0x784000),(0xdf7900,0xdf8000)]
   constructor_bytes=[bytes(u.mem_read(lo,hi-lo)) for lo,hi in spans]
   def constructor_write(uc,access,address,size,value,data):
    constructor_carrier_writes.append(dict(pc=hex(uc.reg_read(UC_ARM_REG_PC)),address=hex(address),size=size));uc.emu_stop()
   constructor_hooks=[u.hook_add(UC_HOOK_MEM_WRITE,constructor_write,begin=lo,end=hi-1) for lo,hi in spans]
   invoke(u,0x16f591c,instruction_limit=2000000)
   invoke(u,0x15ed590,instruction_limit=2000000)
   invoke(u,0x172fc18,0,instruction_limit=2000000)
   invoke(u,0xcec598,instruction_limit=2000000)
   assert not constructor_carrier_writes
   assert constructor_bytes==[bytes(u.mem_read(lo,hi-lo)) for lo,hi in spans]
   for h in constructor_hooks:u.hook_del(h)
   u.context_restore(base_context)
  visibility.Uc=lambda *a,**kw:Reuse(u)
  recent=deque(maxlen=64);faults=[];events=[];profile_writes=[];carrier_writes=[]
  from unicorn import arm_const as reg
  def event(uc,pc,size,data):events.append(dict(pc=hex(pc),args=[uc.reg_read(getattr(reg,'UC_ARM_REG_R'+str(i))) for i in range(4)]))
  def write(uc,access,address,size,value,data):
   if any(address<=a<address+size for a in [0x1cfb23f,0x1dadf1c,0x10cd677,0x10cf617]):profile_writes.append(dict(pc=hex(uc.reg_read(UC_ARM_REG_PC)),address=hex(address),size=size,value=value))
   if any(max(address,lo)<min(address+size,hi) for lo,hi in [(0x781000,0x784000),(0xdf7900,0xdf8000)]):carrier_writes.append(dict(pc=hex(uc.reg_read(UC_ARM_REG_PC)),address=hex(address),size=size));uc.emu_stop()
  def invalid(uc,access,address,size,value,data):faults.append(dict(pc=hex(uc.reg_read(UC_ARM_REG_PC)),address=hex(address),access=access,size=size,value=value));return False
  scratch=[];scratch_errors=[];native_pools=[]
  def scratch_fill(uc,pc,size,data):
   from unicorn import arm_const as reg
   args=[uc.reg_read(getattr(reg,'UC_ARM_REG_R'+str(i))) for i in range(3)]
   if args!=[0x3f589b04,0,0xd230]:return
   table=struct.unpack('<I',uc.mem_read(0x5bacc,4))[0]
   try:
    pages=[inspect(uc,page,table) for page in range(0x3f589000,0x3f597000,4096)]
    assert all(x['physical']==x['address'] and x['ap']==3 for x in pages),pages
    mapped=map_missing_ram(uc,0x3f589000,0x3f597000)
    scratch.append(dict(args=args,pages=pages,added_pages=mapped))
   except (ValueError,AssertionError) as exc:scratch_errors.append(str(exc));uc.emu_stop()
  def scratch_access(uc,access,address,size,value,data):
   if not (0x3f589b04<=address and address+size<=0x3f596d34):
    scratch_errors.append('Access outside native fixed scratch object');uc.emu_stop()
  u.hook_add(UC_HOOK_CODE,scratch_fill,begin=0xd18830,end=0xd18830)
  # Bound backing to the observed original fixed-object initialization request.
  u.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,scratch_access,begin=0x3f589000,end=0x3f596fff)
  def native_pool(uc,pc,size,data):
   record=uc.reg_read(reg.UC_ARM_REG_R0)
   try:
    assert 0x1992530<=record<0x1992600 and (record-0x1992530)%16==0,hex(record)
    selector,count,start,companion=struct.unpack('<4I',uc.mem_read(record,16))
    assert 0<count<=0x9b
    end=start+count*0x3b00
    assert not any(max(start,lo)<min(end,hi) for lo,hi in [(0x781000,0x784000),(0xdf7900,0xdf8000)])
    table=struct.unpack('<I',uc.mem_read(0x5bacc,4))[0]
    pages=[inspect(uc,page,table) for page in range(start&~4095,(end+4095)&~4095,4096)]
    assert all(x['physical']==x['address'] and x['ap']==3 for x in pages),pages
    mapped=map_missing_ram(uc,start&~4095,(end+4095)&~4095)
    native_pools.append(dict(record=hex(record),selector=selector,count=count,start=hex(start),end=hex(end),companion=hex(companion),pages=pages,added_pages=mapped))
   except (ValueError,AssertionError) as exc:scratch_errors.append(str(exc));uc.emu_stop()
  u.hook_add(UC_HOOK_CODE,native_pool,begin=0x16a5cec,end=0x16a5cec)
  clocks=ClockModel();clocks.attach(u);gpio=GpioConfiguration(None if GPIO0 is None else {0:int(GPIO0,0)});gpio.attach(u)
  core_recent=[deque(maxlen=64),deque(maxlen=64)];active_core=[0]
  serial=SerialTransferProbe() if TRANSFER else SerialConfiguration()
  if SERIAL in ("1","2"):serial.attach(u,base=0xfff2c000)
  timer_steps=[];timer_expiries=[]
  def polled_timer(uc,pc,size,data):
   if TIME and uc.reg_read(reg.UC_ARM_REG_R0)&0xfffff000==0xfff1a000:
    fired=uc.xt2_timer_fixture.advance(1)
    timer_steps.append(dict(pc=pc,address=uc.reg_read(reg.UC_ARM_REG_R0),fired=fired))
    if fired:timer_expiries.extend(fired);uc.emu_stop()
  u.hook_add(UC_HOOK_CODE,polled_timer,begin=0x5ab9c,end=0x5ab9c)
  def trace(uc,pc,size,data):
   recent.append(hex(pc));clocks.advance(clocks.now+1)
   core_recent[active_core[0]].append(hex(pc))
   if pc==0x1633a40:uc.emu_stop()
  u.hook_add(UC_HOOK_CODE,trace);u.hook_add(UC_HOOK_MEM_INVALID,invalid);u.hook_add(UC_HOOK_MEM_WRITE,write)
  for pc in [0x16f39bc,0x16f1e84,0x16f5b7c,0x16f77e4,0x15fb5c4,0x1652948,0x173c1f4,0x1875174,0x173a420,0x179f0a8,0x179e8b0,0x188667c,0x18789c4,0x187b3f0]:u.hook_add(UC_HOOK_CODE,event,begin=pc,end=pc)
  outcome={};contexts=[None,u.xt2_secondary_context]
  def after(uc,public):
   outcome['public']=public;outcome['sender_error']=None
   uc.reg_write(UC_ARM_REG_SP,0x800b000);uc.reg_write(UC_ARM_REG_LR,0x800f000)
   run(uc,0x141c2a4,0x141c2b8)
   uc.reg_write(UC_ARM_REG_LR,0x800f000)
   try:run(uc,0x14e210c,0x800f000,1000000)
   except (UcError,AssertionError) as exc:outcome['sender_error']=str(exc)
   contexts[0]=u.context_save()
   return outcome
  row=next(r for r in menu_rows(image,0xedaaac)[1] if r['row']==5)
  selection=None
  try:selection=routed(image,0xedaaac,row['index'],after)
  except (UcError,AssertionError) as exc:outcome['menu_error']=str(exc)
  rounds=[];exceptions=[]
  if contexts[0] is not None and not faults:
   for turn in range(80):
    core=turn%2;active_core[0]=core;u.context_restore(contexts[core])
    for op in [0,4]:u.cpr_write(15,op,0,0,5,1,False,0x80000000|core)
    u.ctl_flush_tb();error=None
    # The source caller is borrowed for menu injection; resume native loader
    # after return, never execute the scratch return sled as an application.
    if core==0 and turn==0 and u.reg_read(UC_ARM_REG_PC)==0x800f000:u.context_restore(base_context)
    try:u.emu_start(u.reg_read(UC_ARM_REG_PC),0x800f000,count=100000)
    except UcError as exc:
     if exc.errno==UC_ERR_INSN_INVALID and not u.reg_read(UC_ARM_REG_FPEXC)&(1<<30):
      try:exceptions.append(deliver_vfp(u,core))
      except (UcError,AssertionError) as transport:error=str(transport)
     else:error=str(exc)
    contexts[core]=u.context_save();rounds.append(dict(core=core,pc=hex(u.reg_read(UC_ARM_REG_PC)),lr=hex(u.reg_read(UC_ARM_REG_LR)),sp=hex(u.reg_read(UC_ARM_REG_SP)),regs=[hex(u.reg_read(getattr(reg,'UC_ARM_REG_R'+str(i)))) for i in range(13)],error=error))
    if any(u.mem_read(0x1bde8b0,4))==False and core==0 and u.reg_read(UC_ARM_REG_PC)==0x16f7870:break
    if error or faults or clocks.errors or gpio.errors or serial.errors or timer_expiries or carrier_writes or scratch_errors:break
  report=dict(scope=__doc__,explicit_gpio0_fixture=GPIO0,explicit_serial_configuration=SERIAL,constructor_carrier_writes=constructor_carrier_writes,explicit_poll_timer=TIME,timer_steps=timer_steps,timer_expiries=timer_expiries,source_sha256=pins,serial_errors=serial.errors,serial_trace=serial.trace,image_sha256=EXPECTED_HASH,outcome=outcome,events=events,profile_writes=profile_writes,carrier_writes=carrier_writes,faults=faults,rounds=rounds,vfp_exceptions=exceptions,recent_pcs=list(recent),clock_errors=clocks.errors,gpio_errors=gpio.errors,gpio_trace=gpio.trace[-32:],scratch=scratch,scratch_errors=scratch_errors,native_pools=native_pools,core_recent=[list(x) for x in core_recent],predicate_pointer=hex(struct.unpack("<I",u.mem_read(0x1bde8b0,4))[0]),predicate_bytes=u.mem_read(struct.unpack("<I",u.mem_read(0x1bde8b0,4))[0],16).hex(),
   cache_profile=u.mem_read(0x1cfb23f,1)[0],capture_profile=u.mem_read(0x1dadf1c,1)[0],limits='Host preloaded image; borrowed caller for native menu input and full message sender; serialized native kernel contexts, timer/clock/GPIO models with explicit fixture options. Any virtual timer expiry stops before IRQ delivery. No reset boot, physical button or JPEG claim.')
  assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==v for p,v in pins.items())
  (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 finally:Path.write_text=original;font.STOCK=old_stock;visibility.Uc=old_uc
 print(json.dumps(dict(report=str(OUT/'verification.json'),outcome=outcome,faults=faults,cache=report['cache_profile'],events=len(events))))
if __name__=='__main__':main()
