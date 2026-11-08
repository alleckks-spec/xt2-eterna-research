"""Bounded actual-menu live snapshot and native queued-pointer provenance assay.
Original Codex-assisted tooling; no firmware file changes.
Native caller phases and queue transport remain explicit test handoffs.
"""
import hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID,UcError
from unicorn.arm_const import *
from verify_eterna_minimal_menu_chain import routed,menu_rows
from firmware_analysis import Firmware
from xpp_gpio_configuration import GpioConfiguration
from xpp_clock_model import ClockModel
from collections import deque
IMAGE=Path("firmware/research/eterna-minimal-protected-unverified/ffboot.bin")
EXPECTED_HASH="0b92b7922acbe18216996be3808734f50a6d66558b520aa327d56b7bc0ef23ec"

BASE=0x1c21ab8
LAB=0x08000000
REGS=(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)
def args(u):return [u.reg_read(r) for r in REGS]
def wr(u,a,v):u.mem_write(a,struct.pack('<I',v))
def rd(u,a):return struct.unpack('<I',u.mem_read(a,4))[0]
def run(u,a,b,count=300000):
 u.emu_start(a,b,count=count)
 assert u.reg_read(UC_ARM_REG_PC)==b,(hex(a),hex(b),hex(u.reg_read(UC_ARM_REG_PC)))
def sha(data):return hashlib.sha256(data).hexdigest()


def assay(u,public):
 trace=[];task_ids=[]
 def record(uc,pc,size,data):trace.append(dict(pc=hex(pc),args=args(uc)))
 h=u.hook_add(UC_HOOK_CODE,record,begin=0xcf2bbc,end=0xcf2bbc)
 try:
  live=bytes(u.mem_read(0x119f25c,0x584));assert live[0x6f]==public
  neighbours=[bytes(u.mem_read(0x118a368,4)),bytes(u.mem_read(0x118a8f0,4))]
  # Original caller loads both real global addresses itself, then native memcpy.
  u.reg_write(UC_ARM_REG_SP,LAB+0xe000)
  run(u,0x141c2a4,0x141c2b8)
  assert bytes(u.mem_read(0x118a36c,0x584))==live
  assert neighbours==[bytes(u.mem_read(0x118a368,4)),bytes(u.mem_read(0x118a8f0,4))]
  assert trace[-1]['args'][:3]==[0x118a36c,0x119f25c,0x584]
  copy_trace=list(trace);trace.clear()
  # Run the actual caller's next complete message builder to its queue boundary.
  # RTOS task identity alone is declared transport fixture; other helpers execute.
  def task_id(uc,pc,size,data):
   task_ids.append(dict(pc=hex(pc),result=3));uc.reg_write(UC_ARM_REG_R0,3)
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  th=u.hook_add(UC_HOOK_CODE,task_id,begin=0xceed8c,end=0xceed8c)
  u.reg_write(UC_ARM_REG_LR,LAB+0xf000)
  try:run(u,0x14e210c,0xcef910)
  finally:u.hook_del(th)
  queue,descriptor=args(u)[:2]
  message=bytes(u.mem_read(descriptor,12));mid,sender,dest,length,source=struct.unpack('<HBBII',message)
  assert (queue,mid,dest,length)==(3,0x200,3,0x18)
  native_pointers=list(struct.unpack('<III',u.mem_read(source,12)))
  assert native_pointers==[0x1221eb0,0x118a36c,0x10c72dc]
  # Declared queue transport: execute both ORIGINAL copy blocks. Only pointers
  # and a lab stack are initialized by host, never profile/cache/object bytes.
  packet=LAB+0x4000;frame=LAB+0x3000
  wr(u,frame-0x10,packet)
  u.reg_write(UC_ARM_REG_FP,frame);u.reg_write(UC_ARM_REG_SP,LAB+0xa000)
  u.reg_write(UC_ARM_REG_R4,descriptor)
  run(u,0xcef9f0,0xcefa2c)
  assert bytes(u.mem_read(packet+8,length))==bytes(u.mem_read(source,length))
  wr(u,BASE+8,BASE+0xc)
  wr(u,frame-0x18,packet)
  u.reg_write(UC_ARM_REG_R4,BASE);u.reg_write(UC_ARM_REG_R1,packet)
  run(u,0xcefbbc,0xcefbf8)
  assert rd(u,BASE+0x10)==0x118a36c
  assert struct.unpack('<H',u.mem_read(BASE,2))[0]==0x200
  # Full original entry tests the received200 header, then assigns live pointers.
  u.reg_write(UC_ARM_REG_SP,LAB+0xa000)
  phase_context=u.context_save()
  u.reg_write(UC_ARM_REG_LR,LAB+0xf000)
  run(u,0xcec598,LAB+0xf000,2000000)
  assert rd(u,0x11892a4)==0x950400 and rd(u,0x118a304)==0
  u.context_restore(phase_context)
  run(u,0x15fca10,0x15f7254)
  native_phase_pointer=rd(u,0x1d00f7c)
  assert native_phase_pointer==rd(u,BASE+0x10)
  u.context_restore(phase_context)
  u.reg_write(UC_ARM_REG_LR,LAB+0xf000)
  run(u,0x1652948,0x16529a0)
  active=rd(u,0x1c24294);assert active==0x118a36c
  assert u.mem_read(active+0x6f,1)[0]==public
  # Continue the actual 200 handler. The old slice stopped before it initialized
  # the rest of the native context. Do not fill missing pointers from the host.
  recent=deque(maxlen=64);faults=[];calls=[]
  def trail(uc,pc,size,data):
   if not recent or recent[-1]!=hex(pc):recent.append(hex(pc))
   if pc==0x1633a40:uc.emu_stop()
   clocks.advance(clocks.now+1)
  def invalid(uc,access,address,size,value,data):
   faults.append(dict(pc=hex(uc.reg_read(UC_ARM_REG_PC)),lr=hex(uc.reg_read(UC_ARM_REG_LR)),address=hex(address),access=access,size=size,value=value,args=args(uc)));return False
  def observe(uc,pc,size,data):calls.append(dict(pc=hex(pc),lr=hex(uc.reg_read(UC_ARM_REG_LR)),args=args(uc)))
  hooks=[u.hook_add(UC_HOOK_CODE,trail),u.hook_add(UC_HOOK_MEM_INVALID,invalid)]
  hooks += [u.hook_add(UC_HOOK_CODE,observe,begin=pc,end=pc) for pc in (0x16d1940,0x16d1a14,0x16d2a54,0x16447fc,0x172fd44,0x1731234,0x16339d4,0x1638a38,0x173c8d4,0xd3444c,0xd25454,0xd36cbc)]
  th=u.hook_add(UC_HOOK_CODE,task_id,begin=0xceed8c,end=0xceed8c)
  failure=None
  stage="full native200 initialization";start_profile=None;gpio=GpioConfiguration();gpio.attach(u);clocks=ClockModel();clocks.attach(u)
  try:
   run(u,0x16529a0,LAB+0xf000,2000000)
   stage="full native1645174 context construction"
   u.reg_write(UC_ARM_REG_SP,LAB+0xa000);u.reg_write(UC_ARM_REG_LR,LAB+0xf000)
   run(u,0x1645174,LAB+0xf000,2000000)
   stage="original active snapshot property update"
   u.reg_write(UC_ARM_REG_SP,LAB+0xa000)
   run(u,0x1641a68,0x1641ac0,1000000)
   stage="full native16447fc start sender"
   u.reg_write(UC_ARM_REG_SP,LAB+0xa000);u.reg_write(UC_ARM_REG_LR,LAB+0xf000)
   run(u,0x16447fc,0xcef910,2000000)
   q0,d0=args(u)[:2];m0=list(struct.unpack('<HBBII',u.mem_read(d0,12)))
   assert(q0,m0[0],m0[3])==(0x38,0x148a,0x18)
   pointer0=rd(u,m0[4]+8);start_profile=u.mem_read(pointer0+0x97,1)[0]
   def packet_copy(descriptor,packet):
    frame=LAB+0x2000
    wr(u,frame-0x10,packet);u.reg_write(UC_ARM_REG_FP,frame);u.reg_write(UC_ARM_REG_R4,descriptor)
    run(u,0xcef9f0,0xcefa2c)
   packet_copy(d0,LAB+0x5000)
   # Queue both native messages before resuming processing; preserve the native
   # processing task's open stack separately from sender scratch frames.
   stage="native1498 active menu export"
   u.reg_write(UC_ARM_REG_SP,LAB+0xb000);u.reg_write(UC_ARM_REG_LR,LAB+0xf000);u.reg_write(UC_ARM_REG_R0,active)
   run(u,0x16435a4,0xcef910,1000000)
   q1,d1=args(u)[:2];m1=list(struct.unpack('<HBBII',u.mem_read(d1,12)))
   assert(q1,m1[0],m1[3])==(0x38,0x1498,0x10)
   export_profile=u.mem_read(rd(u,m1[4]+4)+0x97,1)[0]
   assert export_profile==public
   packet_copy(d1,LAB+0x6000)
   stage="native148a receiver and processing initialization"
   u.reg_write(UC_ARM_REG_SP,LAB+0x9000);u.reg_write(UC_ARM_REG_LR,LAB+0xf000)
   run(u,0x173c1f4,0x173c218)
   rc=u.reg_read(UC_ARM_REG_R4)
   def receive(packet):
    frame=LAB+0x2000
    wr(u,frame-0x18,packet);u.reg_write(UC_ARM_REG_FP,frame);u.reg_write(UC_ARM_REG_R4,rc+4)
    run(u,0xcefbbc,0xcefbf8)
    u.reg_write(UC_ARM_REG_R4,rc)
    run(u,0x173c23c,0x173c270)
    run(u,0x173c270,0x173c27c,2000000)
   receive(LAB+0x5000)
   stage="native1498 state dispatch and slot commit"
   receive(LAB+0x6000)
  except (UcError,AssertionError) as exc:failure=str(exc)
  finally:
   u.hook_del(th)
   for hook in hooks:u.hook_del(hook)
  message=None
  if u.reg_read(UC_ARM_REG_PC)==0xcef910:
   q,d=args(u)[:2];message=dict(queue=q,descriptor=list(struct.unpack('<HBBII',u.mem_read(d,12))))
  return dict(status="INCOMPLETE" if failure else "PASS bounded native slot commit",error=failure,
   pc=hex(u.reg_read(UC_ARM_REG_PC)),native_getter=public,active_blob=hex(active),message=message,stage=stage,start_profile=start_profile,gpio_trace=gpio.trace,gpio_errors=gpio.errors,clock_trace=clocks.trace,clock_errors=clocks.errors,
   calls=calls,faults=faults,recent_pcs=list(recent),native_phase_pointer=hex(native_phase_pointer),global_slot_profiles=[u.mem_read(0x10cd5e0+i*0x1fa0+0x97,1)[0] for i in range(2)],
   phase_boundary="Original15fca10→1651344 pointer setter runs before200 initialization; explicit phase sequencing, not actual state-engine dispatch.",
   scope="Actual menu snapshot and native queued pointers, then original 200 handler continuation. Queue identity/transport fixture remains; no missing context pointer synthesized.")
 finally:u.hook_del(h)

