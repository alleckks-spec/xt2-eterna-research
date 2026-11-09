"""Execute the ordinary ELF timer wrapper against original X-T2 timer functions.

AI-assisted original bounded check. Native pools/UI/timer constructor execute;
native scheduling selects UI1. Calls borrow that stack/context. Explicit calls
to the native tick handler supply logical ticks, not hardware time/IRQs or a
running timer task. No internal API return stubs. The compiled callback is an
explicit assay from build_ui_post_component.py, never a production module.
"""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import Uc,UcError,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_ERR_INSN_INVALID
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_C1_C0_2,UC_ARM_REG_FPEXC,
    UC_ARM_REG_CPSR,UC_ARM_REG_SPSR)
from unicorn.unicorn_py3.unicorn import uclib
import kernel_timer_initialization as timer_model


def sha(b):return hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',required=True,type=Path)
    p.add_argument('--candidate',required=True,type=Path)
    p.add_argument('--callback-component',required=True,type=Path)
    p.add_argument('--expect-original-leak',action='store_true')
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();stock=a.stock.read_bytes()
    assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0,(len(stock)+4095)&~4095);u.mem_write(0,stock)
    ram=0x8000000;ret=ram+0xf000;u.mem_map(ram,0x10000)
    clock=timer_model.TimerInitialization();clock.attach(u)  # existing reset-time fixture for diagnostic log only
    u.reg_write(UC_ARM_REG_C1_C0_2,0xf<<20);u.reg_write(UC_ARM_REG_FPEXC,1<<30)
    exceptions=[]
    def word(address):return struct.unpack('<I',u.mem_read(address,4))[0]
    def call(entry,*args,task=False):
        for reg,value in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],list(args)+[0]*4):u.reg_write(reg,value)
        if not task:u.reg_write(UC_ARM_REG_SP,ram+0xe000)
        sp=u.reg_read(UC_ARM_REG_SP);u.reg_write(UC_ARM_REG_LR,ret)
        start=entry
        for attempt in range(3):
            try:u.emu_start(start,ret,count=2000000);break
            except UcError as error:
                if error.errno!=UC_ERR_INSN_INVALID:raise AssertionError((str(error),hex(u.reg_read(UC_ARM_REG_PC)),hex(u.reg_read(UC_ARM_REG_R0)))) from error
                assert not u.reg_read(UC_ARM_REG_FPEXC)&(1<<30)
                # Existing architectural UND transport: firmware enables VFP and
                # marks ownership. No host ready bit or successful API reply.
                pc=u.reg_read(UC_ARM_REG_PC);cpsr=u.reg_read(UC_ARM_REG_CPSR)
                assert not cpsr&0x20
                regs=[UC_ARM_REG_R0+i for i in range(13)]+[UC_ARM_REG_SP,UC_ARM_REG_LR]
                before=[u.reg_read(r) for r in regs]
                u.reg_write(UC_ARM_REG_CPSR,(cpsr&~0x3f)|0x1b|0x80)
                u.reg_write(UC_ARM_REG_SPSR,cpsr);u.reg_write(UC_ARM_REG_SP,ram+0xd000)
                u.reg_write(UC_ARM_REG_LR,pc+4);u.ctl_flush_tb()
                u.emu_start(0x5898c,pc,count=10000)
                assert u.reg_read(UC_ARM_REG_PC)==pc and u.reg_read(UC_ARM_REG_CPSR)==cpsr
                assert [u.reg_read(r) for r in regs]==before
                assert u.reg_read(UC_ARM_REG_FPEXC)&(1<<30)
                assert word(word(0x5bf90)+0xa0)==1
                exceptions.append(dict(pc=hex(pc),task=word(word(0x5bf90)+4)))
                start=pc
        assert u.reg_read(UC_ARM_REG_PC)==ret,hex(u.reg_read(UC_ARM_REG_PC))
        assert u.reg_read(UC_ARM_REG_SP)==sp
        return u.reg_read(UC_ARM_REG_R0)
    constructors=[]
    for entry in [0xcf0034,0x14d6fd8,0xcdf570]:
        result=call(entry);assert result==0
        constructors.append(hex(entry))
    assert u.mem_read(0x1020688,1)==b'\x01'
    reached=[]
    def stop(uc,address,size,data):reached.append(address);uc.emu_stop()
    h=u.hook_add(UC_HOOK_CODE,stop,begin=0x140fd9c,end=0x140fd9c)
    u.reg_write(UC_ARM_REG_R0,0);u.reg_write(UC_ARM_REG_SP,ram+0xe000);u.reg_write(UC_ARM_REG_LR,ret)
    try:u.emu_start(0x5593c,ret,count=1000000)
    except UcError as error:raise AssertionError(('scheduler',hex(u.reg_read(UC_ARM_REG_PC)),hex(u.reg_read(UC_ARM_REG_R0)))) from error
    u.hook_del(h)
    assert reached==[0x140fd9c] and call(0xceed8c,task=True)==1
    call(0x59240,task=True)
    assert 0x59200 in struct.unpack('<8I',u.mem_read(0x7f3c8,32))
    tcb=word(0x5bf90);stack=word(tcb+12);stack_size=word(tcb+20)
    assert stack<=u.reg_read(UC_ARM_REG_SP)<stack+stack_size
    inputs={};symbols=[]
    for path,bounds in [(a.candidate,(0x1390000,0x13c0000)),(a.callback_component,(0x2000000,0x2010000))]:
        raw=path.read_bytes();inputs[str(path)]=sha(raw);elf=ELFFile(io.BytesIO(raw))
        symbols.append({s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()})
        for section in elf.iter_sections():
            if not section['sh_flags']&2 or not section['sh_size'] or section.name in ['.x70mod.hooks','.x70mod.strings']:continue
            start,size=section['sh_addr'],section['sh_size'];assert bounds[0]<=start<start+size<=bounds[1]
            u.mem_write(start,b'\0'*size if section['sh_type']=='SHT_NOBITS' else section.data())
    syms,fixture=symbols;timer=ram+0x4000;callback=fixture['assay_callback']
    def callbacks():return word(fixture['assay_callbacks'])
    def ticks(n):
        before=callbacks()
        for _ in range(n):call(0xcdf968,task=True)
        return callbacks()-before
    def start(ms,once):return call(syms['x70_timer_start'],timer,0x10f if once else 0,ms,callback,task=True)
    # Resolve the real lifetime stop callback from the entry installed by hold,
    # rather than relying on a possibly duplicated local ELF symbol named stop.
    assert start(10,True)==0
    handle,hold,running=struct.unpack('<3I',u.mem_read(timer,12));assert hold==1 and running==1
    records=[]
    for s in ELFFile(io.BytesIO(a.candidate.read_bytes())).get_section_by_name('.symtab').iter_symbols():
        if s.name=='entries' and s['st_size']>=20 and s['st_value']:
            if word(s['st_value']+4)==timer:records.append(s['st_value'])
    assert len(records)==1;cleanup=word(records[0]);assert 0x1390000<=cleanup<0x13c0000
    assert ticks(4)==0 and ticks(1)==1 and ticks(3)==0
    assert word(fixture['assay_callback_task'])==1  # borrowed UI context, NOT timer-task proof
    assert call(cleanup,timer,task=True)==0 and word(timer+8)==0
    assert start(5,False)==0 and ticks(3)==1
    old_handle=word(timer);assert start(10,False)==0
    new_handle=word(timer);assert new_handle!=old_handle and word(timer+4)==hold
    after_restart=ticks(5)
    assert call(cleanup,timer,task=True)==0 and word(timer+8)==0
    after_stop=ticks(5)
    if a.expect_original_leak:
        assert after_restart==3 and after_stop==3
        # End the leaked timer so the independent negative case has no stray work.
        assert call(0xcdf8a0,old_handle,task=True)==0
    else:assert after_restart==1 and after_stop==0
    # Existing file loader uses a300ms periodic tick and10ms one-shot polls.
    assert start(300,False)==0
    assert ticks(120)==0 and ticks(1)==1 and ticks(120)==1
    assert call(cleanup,timer,task=True)==0 and ticks(121)==0
    assert start(300,True)==0
    # Native initialization-clear function creates a real cancellation refusal.
    call(0xcdf54c,task=True)
    refused=call(cleanup,timer,task=True);kept=word(timer+8)
    assert (refused,kept)==((0,0) if a.expect_original_leak else (0xffffff01,1))
    before_failed_restart=bytes(u.mem_read(timer,12))
    assert start(10,False)==0xffffff01
    if not a.expect_original_leak:assert bytes(u.mem_read(timer,12))==before_failed_restart
    assert not clock.errors and clock.elapsed_ticks==0
    assert all(x['offset']==0x1f0 and x['size']==4 and x['value'] is None for x in clock.trace)
    report=dict(scope=__doc__,status='PASS: reproduced original defects' if a.expect_original_leak else 'PASS: restart and refusal regression',
        original_defects_expected=a.expect_original_leak,constructors=constructors,
        start_entry=hex(syms['x70_timer_start']),native_start='0xcdf65c',native_cancel='0xcdf8a0',native_tick='0xcdf968',
        initial_handle=handle,hold=hold,old_handle=old_handle,new_handle=new_handle,
        callbacks_during_five_restart_ticks=after_restart,callbacks_after_cleanup=after_stop,
        cleanup_refusal_return=hex(refused),running_after_refusal=kept,
        periodic_300ms_rounding_checked=True,failed_restart_preserves_timer=not a.expect_original_leak,
        native_vfp_exceptions=exceptions,borrowed_task=1,native_stack=dict(base=hex(stack),bytes=stack_size),
        scheduler_initializer_returned=False,tick_handler_explicitly_invoked=True,
        hardware_clock_or_irq=False,timer_task_executed=False,concurrent_cancel=False,
        whole_service_startup=False,hardware_verified=False,internal_stubs=0,
        diagnostic_timestamp='Existing TimerInitialization reset counter0; no time advancement or IRQ',
        diagnostic_timestamp_reads=len(clock.trace),
        timer_fixture_sha256=sha(Path(timer_model.__file__).read_bytes()),
        input_sha256=inputs,stock_sha256=sha(stock),checker_sha256=sha(Path(__file__).read_bytes()),
        unicorn_library_sha256=sha(Path(uclib._name).read_bytes()))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],restart_callbacks=after_restart,after_cleanup=after_stop)))


if __name__=='__main__':main()
