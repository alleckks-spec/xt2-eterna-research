"""Bounded original UI-post component through real X-T2 kernel transport.

AI-assisted. Native pool/UI/UILIB constructors and dispatch registration run;
native scheduling selects UI1 and its allocated stack. Calls then borrow that
context, not the full UI event loop. No internal return stubs or device model.
Explicit inputs: local stock flat image and inverted calibration store, manual
constructor order, synthetic component placement, mode/last-screen fixtures.
Not a full boot, visible redraw, concurrent-producer or physical camera test.
"""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,
    UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,
    UC_ARM_REG_C1_C0_2,UC_ARM_REG_FPEXC)
from unicorn.unicorn_py3.unicorn import uclib

RAM=0x8000000
RETURN=RAM+0xf000


def sha(b):return hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',required=True,type=Path)
    p.add_argument('--inverted',required=True,type=Path)
    p.add_argument('--component',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();stock=a.stock.read_bytes();data=a.component.read_bytes()
    assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    calibration=a.inverted.read_bytes()[0xc025c:0x10025c]
    assert sha(calibration)=='f81a916dd77b634a233c03172be81e3de276dbc1eecdbfed902bd2b24ec65810'
    build=json.loads(a.component.with_name('build.json').read_text())
    assert sha(data)==build['elf_sha256']
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    u.mem_map(0,(len(stock)+4095)&~4095);u.mem_write(0,stock)
    u.mem_map(RAM,0x10000)
    u.reg_write(UC_ARM_REG_C1_C0_2,0xf<<20);u.reg_write(UC_ARM_REG_FPEXC,1<<30)
    def word(address):return struct.unpack('<I',u.mem_read(address,4))[0]
    def call(entry,*args,task=False):
        context=u.context_save()
        for reg,value in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],args):u.reg_write(reg,value)
        if not task:u.reg_write(UC_ARM_REG_SP,RAM+0xe000)
        sp=u.reg_read(UC_ARM_REG_SP);u.reg_write(UC_ARM_REG_LR,RETURN)
        u.emu_start(entry,RETURN,count=2000000)
        pc=u.reg_read(UC_ARM_REG_PC);result=u.reg_read(UC_ARM_REG_R0)
        assert pc==RETURN,hex(pc)
        assert u.reg_read(UC_ARM_REG_SP)==sp
        u.context_restore(context)
        return result
    constructors=[]
    for entry in [0xcf0034,0x14d6fd8,0xcf8e14,0x24c6284]:
        result=call(entry);assert result==0
        constructors.append(dict(entry=hex(entry),result=result))
    assert word(0xfae35c)==0xcf8a18
    assert word(0x10ad304)==84  # constructor's native queue size, not host widened
    # Same original calibration fixture as the prior bounded processing checks.
    u.mem_map(0x9000000,0x40000);u.mem_write(0x9000000,calibration)
    u.mem_write(0x1025344,struct.pack('<I',0x9000000))
    reached=[]
    def stop(uc,address,size,unused):reached.append(address);uc.emu_stop()
    h=u.hook_add(UC_HOOK_CODE,stop,begin=0x140fd9c,end=0x140fd9c)
    stages=[]
    for entry in [0x5593c,0x400c8]:
        u.reg_write(UC_ARM_REG_R0,0);u.reg_write(UC_ARM_REG_SP,RAM+0xe000)
        u.reg_write(UC_ARM_REG_LR,RETURN)
        u.emu_start(entry,RETURN,count=1000000)
        stages.append(dict(entry=hex(entry),pc=hex(u.reg_read(UC_ARM_REG_PC))))
        if reached:break
        assert u.reg_read(UC_ARM_REG_PC)==RETURN
    u.hook_del(h);assert reached==[0x140fd9c]
    tcb=word(0x5bf90);assert word(tcb+4)==1
    sp=u.reg_read(UC_ARM_REG_SP);base,size=word(tcb+12),word(tcb+20)
    assert base<=sp<base+size
    assert call(0xceed8c,task=True)==1
    # Only a bounded named-code check; this does not prove all stock producers absent.
    namespace={hex(x):call(x,0x6100,task=True) for x in [0xb764a4,0xb8c0bc,0xb8ce28,0xb8e304,0xb8f674]}
    assert set(namespace.values())=={0}
    elf=ELFFile(io.BytesIO(data));symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
    for section in elf.iter_sections():
        if not section['sh_flags']&2 or not section['sh_size']:continue
        start=section['sh_addr'];assert 0x2000000<=start<start+section['sh_size']<0x2010000
        u.mem_write(start,b'\0'*section['sh_size'] if section['sh_type']=='SHT_NOBITS' else section.data())
    hooks=elf.get_section_by_name('.x70mod.hooks').data();assert len(hooks)==20
    kind,target,thunk,expected,name=struct.unpack('<5I',hooks)
    assert target==0x14da7ac and thunk==symbols['ui_next_event_hook_entry']
    assert word(target)==expected==0xe92d4ff0
    delta=thunk-target-8;assert delta%4==0 and -(1<<25)<=delta<(1<<25)
    u.mem_write(target,struct.pack('<I',0xea000000|((delta>>2)&0xffffff)));u.ctl_flush_tb()
    def c(name,*args):return call(symbols[name],*args,task=True)
    def raw_receive(queue):
        u.mem_write(RAM+0x6000,struct.pack('<3I',0,0,RAM+0x6100))
        u.mem_write(RAM+0x6100,b'\xa5'*100)
        assert call(0xcefb60,queue,RAM+0x6000,0,task=True)==0
        command,source,dest,length=struct.unpack('<HBBI',u.mem_read(RAM+0x6000,8))
        assert source==1 and dest==queue
        assert length==(76 if queue==1 else 16)
        assert command==(0 if queue==1 else 0x1424)
        assert bytes(u.mem_read(RAM+0x6100+length,100-length))==b'\xa5'*(100-length)
        return bytes(u.mem_read(RAM+0x6100,length))
    def receive():
        u.mem_write(RAM+0x5000,b'\0'*80+b'\xa5'*16)
        result=call(0x14da7ac,RAM+0x5000,task=True)
        assert bytes(u.mem_read(RAM+0x5050,16))==b'\xa5'*16
        return result,bytes(u.mem_read(RAM+0x5000,80))
    def send(code,argument,payload=bytes(68)):
        u.mem_write(RAM+0x7000,struct.pack('<2I',code,argument)+payload)
        return call(0xcf8da8,RAM+0x7000,task=True)
    callback=symbols['assay_callback'];u.mem_write(0x1218a70,b'\x03')
    assert c('x70_menu_post',0)==0xffffffea
    assert c('x70_menu_post',callback)==0
    old=raw_receive(1);code,token=struct.unpack('<2I',old[:8]);assert code==0x6100 and len(old)==76
    assert send(code,token)==0 and receive()[0]==1
    assert word(symbols['assay_callbacks'])==1 and word(symbols['assay_callback_task'])==1
    # Reused slot: replay the previous generation before delivering the new token.
    assert send(code,token)==0
    assert c('x70_menu_post',callback)==0
    assert receive()[0]==1 and word(symbols['assay_callbacks'])==1
    assert receive()[0]==1 and word(symbols['assay_callbacks'])==2
    for i in range(16):assert c('x70_menu_post',callback)==0
    assert c('x70_menu_post',callback)==0xfffffff0
    for i in range(16):assert receive()[0]==1
    assert word(symbols['assay_callbacks'])==18
    payload=bytes(range(68));assert send(0x6005,0x12345678,payload)==0
    status,event=receive();assert status==0
    assert event[:8]==struct.pack('<2I',0x6005,0x12345678) and event[12:]==payload
    # Mode is a declared fixture; the native screen renderer itself is not run.
    c('x70_menu_redraw');assert word(symbols['xpp_menu_redraw_counts']+4)==1
    u.mem_write(0x1218a70,b'\x05');request=bytes(range(16));u.mem_write(0x22e7364,request)
    c('x70_menu_redraw');c('x70_menu_redraw')
    assert receive()[0]==1
    assert raw_receive(46)==request
    assert word(symbols['xpp_menu_redraw_counts'])==1
    assert word(symbols['assay_callbacks'])==18
    assert list(struct.unpack('<3I',u.mem_read(symbols['xpp_menu_post_counts'],12)))==[0,19,1]
    assert call(0xceed8c,task=True)==1 and word(0x5bf90)==tcb
    assert bytes(u.mem_read(0x9000000,0x40000))==calibration
    report=dict(scope=__doc__,status='PASS',constructors=constructors,scheduler_stages=stages,
        native_task_id=1,native_stack=dict(base=hex(base),bytes=size,sp=hex(sp)),
        active_post_registration=True,native_queue_bytes=84,packet_bytes=76,payload_bytes=68,
        named_code_6100_lookup_results=namespace,global_event_collision_proven_absent=False,
        callback_count=18,callback_task_id=1,software_queue_slots=16,stale_generation_dropped=True,
        ordinary_event_pass_through=True,redraw_requests_coalesced=2,native_uilib_submissions=1,
        internal_stubs=0,full_ui_loop_executed=False,visible_rendering=False,hardware_verified=False,
        common_candidate_changed=False,elf_sha256=sha(data),stock_sha256=sha(stock),
        calibration_sha256=sha(calibration),checker_sha256=sha(Path(__file__).read_bytes()),
        build_report_sha256=sha(a.component.with_name('build.json').read_bytes()),
        unicorn_library_sha256=sha(Path(uclib._name).read_bytes()))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',callbacks=18,callback_task=1,redraws=1,hardware=False)))


if __name__=='__main__':main()
