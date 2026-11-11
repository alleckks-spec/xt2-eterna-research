"""Measure the X-T2 dispatcher stack while it invokes an exact-ELF function.

Reuses the existing native UI constructor/scheduler setup via verify_minimal_runtime.
The tick is explicitly invoked; its actual switch to a dedicated stack and BLX
execute unmodified except for the declared SD literal edit. No hardware timer
thread, clock, IRQ or complete boot is claimed. Menu enrollment is intentionally
registered as a diagnostic callback, not a production scheduling change.
"""
import argparse, hashlib, io, json, struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from elftools.elf.elffile import ELFFile
from unicorn import Uc,UcError,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_ERR_INSN_INVALID
from unicorn.arm_const import *
from unicorn.unicorn_py3.unicorn import uclib
import kernel_timer_initialization as timer_model

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',required=True,type=Path)
    p.add_argument('--candidate',required=True,type=Path)
    p.add_argument('--card',required=True,type=Path)
    p.add_argument('--original-stack',action='store_true')
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();stock=a.stock.read_bytes()
    assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    from verify_minimal_runtime import machine,BUILD
    assert a.candidate.resolve()==(BUILD/'mods.elf').resolve()
    (u,symbols,call,clock,exceptions),setup=machine()
    ram=0x8000000
    word=lambda address:struct.unpack('<I',u.mem_read(address,4))[0]
    assert call(0xcdf570,task=True)==0
    raw=a.candidate.read_bytes()
    # Validate the actual dispatcher, constructor and literal, not a donor map.
    assert struct.unpack_from('<I',stock,0xcdfb04)[0]==0x1188000
    with (a.card/'ffboot.bin').open('rb') as stream:
        stream.seek(0xcdfb04);delivered=struct.unpack('<I',stream.read(4))[0]
    assert delivered==0x1187ffc
    u.mem_write(0xcdfb04,struct.pack('<I',0x1188000 if a.original_stack else delivered));u.ctl_flush_tb()
    base,end=0x1187000,0x1188000
    # Constructor word-fill initializes 0x800 words across 0x2000 bytes.
    # Dispatcher grows downward in the lower page; the upper page is separately mapped.
    assert bytes(u.mem_read(base,0x2000))==struct.pack('<I',0xefefefef)*0x800
    u.mem_write(base-16,b'\xa7'*16);u.mem_write(end,b'\xa9'*16)
    u.mem_write(symbols['ui_mode'],b'\x03')
    callback=symbols['xt2_menu_fixture_init']
    active=False;callback_sp=[];sps=[];writes=[];call_sites=[]
    dis=Cs(CS_ARCH_ARM,CS_MODE_ARM)
    def trace(uc,address,size,data):
        nonlocal active
        if address==0xcdf97c:active=True
        if address==0xcdfaf0:active=False
        if not active:return
        sp=uc.reg_read(UC_ARM_REG_SP);sps.append(sp)
        assert base<=sp<=end,(hex(address),hex(sp))
        if address==callback:callback_sp.append(sp)
        ins=list(dis.disasm_lite(bytes(uc.mem_read(address,size)),address))
        if ins and ins[0][2] in ('bl','blx'):
            call_sites.append(dict(pc=hex(address),sp=hex(sp),mod8=sp%8))
    def store(uc,access,address,size,value,data):
        if active and base-16<=address<end+16:
            assert base<=address<address+size<=end,(hex(uc.reg_read(UC_ARM_REG_PC)),hex(address),size)
            writes.append((address,size))
    u.hook_add(UC_HOOK_CODE,trace);u.hook_add(UC_HOOK_MEM_WRITE,store)
    # Native timer owns its slot/queue; no hand-written record or callback stub.
    assert call(0xcdf65c,10,0,callback,ram+0x4000,task=True)==0
    before_sp=u.reg_read(UC_ARM_REG_SP)
    for _ in range(5):call(0xcdf968,task=True)
    assert len(callback_sp)==1 and u.reg_read(UC_ARM_REG_SP)==before_sp
    assert callback_sp[0]%8==(4 if a.original_stack else 0)
    assert call_sites and all(x['mod8']==(4 if a.original_stack else 0) for x in call_sites)
    assert bytes(u.mem_read(base-16,16))==b'\xa7'*16 and bytes(u.mem_read(end,16))==b'\xa9'*16
    assert word(symbols['film_choice_status'])==0 and word(symbols['xpp_menu_stock_status'])==0
    assert not clock.errors
    report=dict(scope=__doc__,status='PASS: original misalignment reproduced' if a.original_stack else 'PASS: dedicated stack aligned',
        elf_sha256=sha(raw),stock_sha256=sha(stock),delivered_literal=hex(delivered),original_stack=a.original_stack,
        stack=dict(base=hex(base),end=hex(end),constructor_initialized_bytes=0x2000,
                   callback_sp=list(map(hex,callback_sp)),minimum_sp=hex(min(sps)),maximum_depth=end-min(sps),
                   observed_stack_stores=len(writes),sentinels_intact=True),
        calls=call_sites,compiled_callback=dict(name='xt2_menu_fixture_init',address=hex(callback),enrollment_status=0),
        native_dispatch_executed=True,explicit_ticks=5,borrowed_outer_task=1,
        timer_thread_scheduled=False,irq_or_real_time=False,hardware_verified=False,
        native_vfp_exceptions=exceptions,setup=setup,internal_return_stubs=0,
        checker_sha256=sha(Path(__file__).read_bytes()),unicorn_sha256=sha(Path(uclib._name).read_bytes()))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','stack','compiled_callback']}))

if __name__=='__main__':main()
