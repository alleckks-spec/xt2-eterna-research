"""Ordinary card-film publisher -> native UI queue -> actual stock menu rows.

AI-assisted bounded integration. Native constructors/scheduling select UI1;
calls borrow that context/stack. REC/calibration/settings pointers and the
post-parser film record are explicit inputs. Not a complete UI loop, file read,
mutable processing, full boot or physical camera result.
"""
import hashlib
import io
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import Uc,UcError,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_ERR_INSN_INVALID
from unicorn.arm_const import *
import kernel_timer_initialization as timer_model

ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parents[1]
BUILD=ROOT/'card-films-expanded-build-unverified'
OUT=ROOT/'card-films-expanded-check-unverified'
RAM=0x8000000
RETURN=RAM+0xf000


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    stock=(WORKSPACE/'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    raw=(BUILD/'mods.elf').read_bytes();assert sha(raw)=='db56c69c993a30e9fbdfb024ad766e005234b50f76684082b29683a526dd3754'
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0,(len(stock)+4095)&~4095);u.mem_write(0,stock)
    u.mem_map(RAM,0x10000);u.reg_write(UC_ARM_REG_C1_C0_2,0xf<<20);u.reg_write(UC_ARM_REG_FPEXC,1<<30)
    clock=timer_model.TimerInitialization();clock.attach(u);exceptions=[]
    def word(a):return struct.unpack('<I',u.mem_read(a,4))[0]
    def call(entry,*args,task=False):
        saved=u.context_save()
        for reg,value in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],list(args)+[0]*4):u.reg_write(reg,value)
        if not task:u.reg_write(UC_ARM_REG_SP,RAM+0xe000)
        sp=u.reg_read(UC_ARM_REG_SP);u.reg_write(UC_ARM_REG_LR,RETURN)
        resume=entry
        for attempt in range(3):
            try:u.emu_start(resume,RETURN,count=3000000);break
            except UcError as error:
                if error.errno!=UC_ERR_INSN_INVALID:raise
                # Existing timer check's architectural lazy-VFP exception
                # transport: execute the actual native UND handler. Do not
                # force FPEXC or a successful API result to skip the fault.
                assert not u.reg_read(UC_ARM_REG_FPEXC)&(1<<30)
                pc=u.reg_read(UC_ARM_REG_PC);cpsr=u.reg_read(UC_ARM_REG_CPSR);assert not cpsr&0x20
                regs=[UC_ARM_REG_R0+i for i in range(13)]+[UC_ARM_REG_SP,UC_ARM_REG_LR]
                before=[u.reg_read(reg) for reg in regs]
                u.reg_write(UC_ARM_REG_CPSR,(cpsr&~0x3f)|0x1b|0x80)
                u.reg_write(UC_ARM_REG_SPSR,cpsr);u.reg_write(UC_ARM_REG_SP,RAM+0xd000)
                u.reg_write(UC_ARM_REG_LR,pc+4);u.ctl_flush_tb()
                u.emu_start(0x5898c,pc,count=10000)
                assert u.reg_read(UC_ARM_REG_PC)==pc and u.reg_read(UC_ARM_REG_CPSR)==cpsr
                assert [u.reg_read(reg) for reg in regs]==before
                assert u.reg_read(UC_ARM_REG_FPEXC)&(1<<30) and word(word(0x5bf90)+0xa0)==1
                exceptions.append(dict(pc=hex(pc),task=word(word(0x5bf90)+4)));resume=pc
        assert u.reg_read(UC_ARM_REG_PC)==RETURN,hex(u.reg_read(UC_ARM_REG_PC))
        assert u.reg_read(UC_ARM_REG_SP)==sp
        result=u.reg_read(UC_ARM_REG_R0)
        if not task:u.context_restore(saved)
        return result
    assert call(0xcf0034)==0
    # Original root semaphore configuration fragment, not successful-wait stubs.
    saved=u.context_save();u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.reg_write(UC_ARM_REG_LR,RETURN)
    u.emu_start(0xcf8134,0xcf8154,count=100000)
    assert u.reg_read(UC_ARM_REG_PC)==0xcf8154;u.context_restore(saved)
    for entry in [0x14d6fd8,0xcf8e14,0x24c6284]:assert call(entry)==0
    assert word(0xfae35c)==0xcf8a18 and word(0x10ad304)==84
    calibration=(WORKSPACE/'firmware/extracted/xt2-4.41/inverted.bin').read_bytes()[0xc025c:0x10025c]
    u.mem_map(0x9000000,0x40000);u.mem_write(0x9000000,calibration)
    u.mem_write(0x1025344,struct.pack('<I',0x9000000))
    reached=[]
    def stop(uc,address,size,data):reached.append(address);uc.emu_stop()
    h=u.hook_add(UC_HOOK_CODE,stop,begin=0x140fd9c,end=0x140fd9c)
    for entry in [0x5593c,0x400c8]:
        u.reg_write(UC_ARM_REG_R0,0);u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.reg_write(UC_ARM_REG_LR,RETURN)
        u.emu_start(entry,RETURN,count=1000000)
        if reached:break
        assert u.reg_read(UC_ARM_REG_PC)==RETURN
    u.hook_del(h);assert reached==[0x140fd9c]
    assert call(0xceed8c,task=True)==1
    call(0x59240,task=True)
    tcb=word(0x5bf90);stack=word(tcb+12);stack_size=word(tcb+20)
    assert stack<=u.reg_read(UC_ARM_REG_SP)<stack+stack_size
    assert not(max(stack,0x1388000)<min(stack+stack_size,0x13c0000))
    elf=ELFFile(io.BytesIO(raw));symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
    for s in elf.iter_sections():
        if not s['sh_flags']&2 or not s['sh_size'] or s.name in ['.x70mod.hooks','.x70mod.strings']:continue
        start,size=s['sh_addr'],s['sh_size'];assert 0x1388000<=start<start+size<=0x13c0000
        u.mem_write(start,bytes(size) if s['sh_type']=='SHT_NOBITS' else s.data())
    manifest=json.loads((BUILD/'manifest.json').read_text())
    for edit in manifest['words']:
        address=int(edit['address'],0);assert word(address)==int(edit['old'],0)
        u.mem_write(address,struct.pack('<I',int(edit['new'],0)))
    u.ctl_flush_tb()
    def api(name,*args):return call(symbols[name],*args,task=True)
    for address,value in [(0x10c62b0,0x120d8a0),(0x119162c,0x119f25c)]:u.mem_write(address,struct.pack('<I',value))
    u.mem_write(0x119f25c,b'\x24');u.mem_write(0x121d626,b'\x03');u.mem_write(symbols['ui_mode'],b'\x03')
    init=[]
    for address in range(symbols['__xpp_init_start'],symbols['__xpp_init_end'],4):
        fn=word(address);call(fn,task=True);init.append(hex(fn))
    assert len(init)==4 and word(symbols['film_choice_status'])==word(symbols['xpp_menu_stock_status'])==0
    print('enrolled',init,flush=True)
    selected=[]
    for key in range(32,38):
        call(0x154b700,0x1fc,key,task=True)
        assert word(symbols['film_choice_key'])==key and call(0xb510b8,0x1fc,0,task=True)==0
        assert api('film_xt20_select',0)==symbols['xt20_film_recipes']+(key-32)*224
        selected.append(key)
    call(0x154b700,0x1fc,0,task=True)
    user,text=RAM+0x7000,RAM+0x7800
    doc=json.dumps(dict(name='Card menu',base='provia',icon='custom')).encode()
    u.mem_write(user,bytes(556));u.mem_write(user,struct.pack('<I',200));u.mem_write(user+406,b'200TEST.JSN\0')
    u.mem_write(text,doc+b'\0');assert api('film_parse',user,text,len(doc))==0
    assert api('film_user_store',user)==0
    api('film_user_publish');print('published',word(symbols['film_card_count']),flush=True)
    assert word(symbols['film_card_count'])==word(symbols['film_card_wanted'])==1
    assert word(symbols['film_card_shown'])==0
    event=RAM+0x5000;u.mem_write(event,bytes(80)+b'\xa5'*16)
    assert call(0x14da7ac,event,task=True)==1
    assert bytes(u.mem_read(event+80,16))==b'\xa5'*16
    assert word(symbols['film_card_shown'])==1 and word(symbols['film_card_show_refusals'])==0
    name_record=symbols['film_card_names'];magic,name_pointer=struct.unpack('<2I',u.mem_read(name_record,8))
    assert magic==0x54787058 and bytes(u.mem_read(name_pointer,10))==b'Card menu\0'
    assert call(0x13db71c,9,15,2,task=True)==name_record  # actual Fn name lookup
    menus=[]
    for name,stock_count in [('menu',9),('fn',9),('quick',15)]:
        address=symbols[f'xpp_stock_film_{name}_rows'];keys=[word(address+i*8) for i in range(stock_count+8)]
        assert keys[stock_count:]==list(range(32,39))+[0x7ffffffe],(name,keys)
        menus.append(dict(name=name,keys=keys,visible_card_key=38))
    call(0x154b700,0x1fc,38,task=True);assert word(symbols['film_choice_key'])==38
    assert api('film_xt20_select',0)==symbols['film_card_recipes']
    profile=RAM+0x1000;u.mem_write(profile,bytes(0x148));call(0x157a0fc,profile,task=True)
    call(0x157ac60,profile,0,task=True)
    assert bytes(u.mem_read(profile+0x145,3))==bytes(3) and u.mem_read(profile+0x52,1)==b'\0'
    # Exercise the original removal/publish path and the second UI callback.
    api('film_user_remove',200);api('film_user_publish')
    assert word(symbols['film_card_count'])==0 and word(symbols['film_card_shown'])==1
    assert call(0x14da7ac,event,task=True)==1
    assert word(symbols['film_card_shown'])==0 and api('film_xt20_select',0)==0
    assert word(symbols['film_card_show_refusals'])==0
    for name,stock_count in [('menu',9),('fn',9),('quick',15)]:
        address=symbols[f'xpp_stock_film_{name}_rows']
        assert [word(address+i*8) for i in range(stock_count,stock_count+7)]==list(range(32,38))+[0x7ffffffe]
    report=dict(scope=__doc__,status='PASS',elf_sha256=sha(raw),init=init,immutable_keys=selected,menus=menus,
        native_task=1,native_stack=[stack,stack+stack_size],card_count=1,shown=1,property=0x1fc,
        real_ui_callback_transport=True,kernel_api_stubs=0,parser_record_supplied=True,
        card_processing_supported=False,card_pointer_declined_by_context_adapter=True,
        full_boot=False,hardware_verified=False,checker_sha256=sha(Path(__file__).read_bytes()))
    report['native_lazy_vfp_exceptions']=exceptions
    report.update(native_fn_card_name='Card menu',card_removal_callback=True,
                  final_card_count=0,final_shown=0)
    OUT.mkdir(exist_ok=True);(OUT/'menu.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS')


if __name__=='__main__':main()
