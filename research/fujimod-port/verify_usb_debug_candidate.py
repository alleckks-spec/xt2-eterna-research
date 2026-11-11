"""Native RAM configuration and bounded Fn return checks for the XPP USB variant.

USB state, GPIO contacts, REC mode and cache contents are explicit function
fixtures. The native cache-pointer initialization prefix, getters/setters and
GPIO read execute. No native USB connection, host debug exchange or persistent
write is claimed. Reuses the existing initialized native UI instruction harness.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
import verify_full_storage_guard as common
ROOT=Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(build, output):
    SYMBOLS=json.loads((build/'target.json').read_text())['symbols']
    common.BUILD=build
    (u,symbols,call,api,clock,init,exceptions),setup=common.fixture_machine(True)
    word=lambda a:struct.unpack('<I',u.mem_read(a,4))[0]
    put=lambda a,v:u.mem_write(a,struct.pack('<I',v))
    s=symbols['usb_debug_xt20_state']
    state=lambda:list(struct.unpack('<6I',u.mem_read(s,24)))
    cache=SYMBOLS['xt20_usb_debug_expected_cache']
    gpio=SYMBOLS['xt20_usb_debug_physical_vbus']
    try:u.mem_read(gpio,4)
    except Exception:u.mem_map(gpio&~4095,4096)
    # The inherited UI fixture maps stock modules, not the native cache RAM.
    # Supply one explicit cache-data page; native prefix publishes its address.
    u.mem_map(cache,0x1000)
    u.mem_write(cache,bytes(0x1000))
    # Reuse actual native initialization up to the pointer publication, before
    # loading NVRAM. Do not claim complete cache or native camera initialization.
    cpu=u.context_save()
    u.reg_write(UC_ARM_REG_SP,0x800e000)
    u.emu_start(0xce3978,0xce3998,count=100)
    assert u.reg_read(UC_ARM_REG_PC)==0xce3998
    assert word(SYMBOLS['xt20_usb_debug_cfg_pointer_cell'])==cache
    u.context_restore(cpu)
    cfg_get=SYMBOLS['xt20_usb_debug_cfg_get']
    cfg_set=SYMBOLS['xt20_usb_debug_cfg_set_ram']
    for value,expected in [(0,0),(0x4000,1),(0x3fff,0),(0xffff,1)]:
        put(gpio,value)
        assert call(0x157eacc,task=True)==expected
    events=[]
    def observe(uc,pc,size,data):
        if pc==cfg_set:events.append(dict(kind='native-ram-setter',index=uc.reg_read(UC_ARM_REG_R0),value=uc.reg_read(UC_ARM_REG_R1)))
        if pc==symbols['usb_debug_xt20_toggle']:
            assert uc.reg_read(UC_ARM_REG_SP)%8==0
    u.hook_add(UC_HOOK_CODE,observe,begin=cfg_set,end=cfg_set)
    u.hook_add(UC_HOOK_CODE,observe,begin=symbols['usb_debug_xt20_toggle'],end=symbols['usb_debug_xt20_toggle'])
    def reset():
        u.mem_write(s,bytes(24));u.mem_write(SYMBOLS['xt20_usb_debug_mode_byte'],b'\x03')
        put(gpio,0);put(SYMBOLS['xt20_usb_debug_debounced_vbus'],0)
        u.mem_write(SYMBOLS['xt20_usb_debug_driver_state'],b'\x02\0')
        u.mem_write(SYMBOLS['xt20_usb_debug_context_state'],b'\x02')
        u.mem_write(SYMBOLS['xt20_usb_debug_cable_decision'],b'\0')
        # Deliberately nonzero adjacent bytes prove class uses its native width.
        u.mem_write(SYMBOLS['xt20_usb_debug_context_class'],b'\0\x93\x5a\xe1')
        u.mem_write(cache+0xf6,b'\xa7\0\x6c')
        put(SYMBOLS['xt20_usb_debug_cfg_pointer_cell'],cache)
        events.clear()
    cases=[]
    toggle=lambda:api('usb_debug_xt20_toggle')
    for mode in [0,1,2,4,255]:
        reset();u.mem_write(SYMBOLS['xt20_usb_debug_mode_byte'],bytes([mode]))
        before=state();assert toggle()==0 and state()==before and not events
        cases.append(dict(case='non-REC',mode=mode,private_state_unchanged=True))
    guards=[('physical',gpio,b'\0\x40\0\0',2),
        ('debounced',SYMBOLS['xt20_usb_debug_debounced_vbus'],b'\x01\0\0\0',3),
        ('driver',SYMBOLS['xt20_usb_debug_driver_state'],b'\x01\0',4),
        ('context',SYMBOLS['xt20_usb_debug_context_state'],b'\x01',5),
        ('cable',SYMBOLS['xt20_usb_debug_cable_decision'],b'\x01',9),
        ('class',SYMBOLS['xt20_usb_debug_context_class'],b'\x04',6),
        ('cache',SYMBOLS['xt20_usb_debug_cfg_pointer_cell'],struct.pack('<I',cache+4),7),
        ('F7',cache+0xf7,b'\x01',8)]
    for name,address,data,reason in guards:
        reset();u.mem_write(address,data);assert toggle()==0
        assert state()==[0,1,1,reason,0,0] and not events,(name,state(),events)
        cases.append(dict(case='refusal',guard=name,reason=reason,native_setter_calls=0))
    reset();assert toggle()==0 and state()==[1,1,0,0,0,1]
    assert call(cfg_get,0xf7,task=True)==1
    for _ in range(16):assert toggle()==0
    assert state()==[1,17,16,6,0,1] and len(events)==1
    u.mem_write(SYMBOLS['xt20_usb_debug_context_class'],b'\x03')
    assert toggle()==0 and state()==[2,18,16,0,0,2]
    assert call(cfg_get,0xf7,task=True)==0
    for _ in range(16):assert toggle()==0
    assert state()==[2,34,32,1,0,2] and len(events)==2
    assert bytes(u.mem_read(cache+0xf6,3))==b'\xa7\0\x6c'
    cases.append(dict(case='enable-repeat16-restore-terminal16',state=state(),native_setters=list(events)))
    # Negative memory-fault fixture after the actual RAM store. No successful
    # setter result is fabricated; the subsequent native getter sees corruption.
    reset();injected=[]
    def corrupt(uc,pc,size,data):
        uc.mem_write(cache+0xf7,b'\x02');injected.append(pc)
    h=u.hook_add(UC_HOOK_CODE,corrupt,begin=0xce351c,end=0xce351c)
    try:assert toggle()==0
    finally:u.hook_del(h)
    assert injected==[0xce351c] and state()==[3,1,1,10,0,0]
    assert toggle()==0 and state()==[3,2,2,1,0,0] and len(events)==1
    cases.append(dict(case='explicit-post-store-memory-fault',state=state(),injection=hex(injected[0])))
    # Enter the actual delivered instruction branch and execute native epilogue.
    # The native frame and mode are declared; no physical Fn routing claim.
    reset();cpu=u.context_save();sp=0x800d000;ret=0x800f000
    native_saved=[0xa3333333,0xa4444444,0xafffffff,ret]
    u.mem_write(sp,struct.pack('<4I',*native_saved))
    u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_LR,0xabcd1234)
    regs=[UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
    for i,reg in enumerate(regs):u.reg_write(reg,0x76540000+i)
    u.emu_start(SYMBOLS['xt20_usb_debug_fn_image_size_site'],ret,count=100000)
    assert u.reg_read(UC_ARM_REG_PC)==ret and u.reg_read(UC_ARM_REG_R0)==0
    assert u.reg_read(UC_ARM_REG_SP)==sp+16
    assert u.reg_read(UC_ARM_REG_R3)==native_saved[0] and u.reg_read(UC_ARM_REG_R4)==native_saved[1]
    for i,reg in enumerate(regs[:-1]):assert u.reg_read(reg)==0x76540000+i
    assert u.reg_read(UC_ARM_REG_R11)==native_saved[2]
    assert state()==[1,1,0,0,0,1] and len(events)==1
    u.context_restore(cpu)
    cases.append(dict(case='delivered-Fn-branch-native-epilogue',return_value=0,stack_delta=16,callee_saved=True))
    report=dict(scope=__doc__,status='PASS',cases=cases,
        elf_sha256=sha((build/'mods.elf').read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),
        setup=setup,init_calls=init,native_vfp_exceptions=exceptions,
        native_cache_pointer_prefix='0xce3978..0xce3998',native_gpio_controls=4,
        physical_Fn_routing=False,usb_connection=False,host_debug_protocol=False,
        persistent_write=False,hardware_verified=False)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',cases=len(cases),elf=report['elf_sha256'])))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=ROOT/'usb-debug-build-unverified')
    p.add_argument('--output',type=Path,default=ROOT/'usb-debug-check-unverified/verification.json')
    a=p.parse_args();verify(a.build,a.output)
