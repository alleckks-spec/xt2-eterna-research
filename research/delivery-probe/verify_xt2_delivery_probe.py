"""Bounded diagnostic path checks; power/ROM/caches are not physical evidence.

The only MMIO model is register storage. All executed blocks must stay in the
early entry/LED/probe, with no original reset, persistence or color execution.
"""
import json
import struct
from pathlib import Path
from unicorn import Uc, UcError, UC_ERR_INSN_INVALID, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_BLOCK, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MEM_WRITE
from unicorn import arm_const as reg
from build_xt2_delivery_probe import ROOT, OUT, STOCK, build, digest, require, branch


def main():
    names=['build_xt2_delivery_probe.py','xt2_delivery_probe.S','verify_xt2_delivery_probe.py']
    source_pins={n:digest((ROOT/'scripts'/n).read_bytes()) for n in names}
    image, built = build()
    require(image == (OUT/'ffboot.bin').read_bytes(), 'Delivered image differs')
    stock = (STOCK/'ffboot.bin').read_bytes()
    symbols = built['symbols']
    require(image[0x103050:0x103058]==struct.pack('<I',0xE320F002)+branch(0x103054,0x103050),'Terminal WFE/branch differs')
    gpio = sorted({a for a,_,_ in struct.iter_unpack('<III', stock[0x103078:0x1030F0])})
    power = 0xFFF10004
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    u.mem_map(0,(len(image)+4095)&~4095)
    u.mem_write(0,image)
    for page in sorted({a&~4095 for a in [power,*gpio]}):u.mem_map(page,4096)
    state=dict(blocks=set(),reads=[],writes=[])
    def block(uc,pc,size,_):
        require(pc==0 or 0x103000<=pc<0x103200, 'Execution left early diagnostic: '+hex(pc))
        state['blocks'].add(pc)
    def memory(uc,access,address,size,value,_):
        if access==UC_MEM_WRITE:
            require((0x103058<=address and address+size<=0x103074) or
                    (size==4 and address in [power,*gpio]), 'Unexpected CPU write')
            state['writes'].append([address,size,value])
        elif address>=0xF0000000:
            require(size==4 and address in [power,*gpio], 'Unexpected MMIO read')
            state['reads'].append([address,size])
    u.hook_add(UC_HOOK_BLOCK,block)
    u.hook_add(UC_HOOK_MEM_WRITE,memory)
    u.hook_add(UC_HOOK_MEM_READ,memory,begin=0xF0000000,end=0xFFFFFFFF)
    results=[]
    cases=[('clean',None,None),('lost profile',(0x781000,0x2A68),None),
           ('lost inactive code',(0xDF7900,0x1D4),None),
           ('bad expected',(symbols['probe_expected'],4),None),
           ('non-RAM descriptor',(symbols['probe_ranges'],4),struct.pack('<I',0xFFF10004))]
    for name,span,replacement in cases:
        print('checking '+name,flush=True)
        u.mem_write(0,image)
        if span:
            address,size=span
            u.mem_write(address,replacement if replacement is not None else bytes(size))
        state.update(blocks=set(),reads=[],writes=[])
        before=0xA5A50001
        u.mem_write(power,struct.pack('<I',before))
        for address in gpio:u.mem_write(address,struct.pack('<I',0x11223344))
        for i in range(13):u.reg_write(getattr(reg,'UC_ARM_REG_R'+str(i)),0x12340000+256*i)
        u.reg_write(reg.UC_ARM_REG_SP,0xDEAD0000) # deliberately unmapped: no stack
        u.reg_write(reg.UC_ARM_REG_CPSR,0xA0000013)
        u.emu_start(0,symbols['probe_wait'],count=6000000)
        require(u.reg_read(reg.UC_ARM_REG_PC)==symbols['probe_wait'], 'Instruction budget/termination')
        pw=[w for w in state['writes'] if w[0]==power]
        require(pw==[[power,4,before&~1]], 'Power request differs')
        require(u.reg_read(reg.UC_ARM_REG_CPSR)&0x1C0==0x1C0, 'AIF not masked')
        require(u.reg_read(reg.UC_ARM_REG_SP)==0xDEAD0000, 'Stack changed')
        led=[w for w in state['writes'] if w[0] in gpio]
        require(bool(led)==(name=='clean'), 'Success/failure indication differs')
        if name!='clean':require(state['reads']==[[power,4]], 'Failed path read other MMIO')
        results.append(dict(name=name,led_writes=len(led),power_writes=pw,
                            blocks=[hex(a) for a in sorted(state['blocks'])],
                            reached_native_reset=False,stack_used=False,
                            terminal_wait='WFE/branch closure checked statically'))
    before_wait=list(state['writes'])
    wait_status='bounded execution'
    try:
        u.emu_start(symbols['probe_wait'],0x180100,count=8)
    except UcError as error:
        # WFE exits with PC advanced to the following B and leaves this
        # backend instance halted. Do not reuse it or fabricate a wake event.
        require(error.errno==UC_ERR_INSN_INVALID and u.reg_read(reg.UC_ARM_REG_PC)==0x103054,
                'Unexpected wait error')
        wait_status='Unicorn WFE exit: UC_ERR_INSN_INVALID at next PC; no wakeup simulated'
    require(u.reg_read(reg.UC_ARM_REG_PC) in (0x103050,0x103054),'Terminal wait escaped')
    require(state['writes']==before_wait,'Terminal wait writes')
    # Compare requested register value against original X-T2 function itself,
    # not the X-T20 emulator's power model. Original MMIO helpers execute.
    original=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    original.mem_map(0,(len(stock)+4095)&~4095);original.mem_write(0,stock)
    original.mem_map(0xFFF10000,4096)
    register_cases=[]
    for before in (0,1,0xA5A50001,0xFFFFFFFF):
        original.mem_write(power,struct.pack('<I',before))
        original.reg_write(reg.UC_ARM_REG_SP,0x180000)
        original.reg_write(reg.UC_ARM_REG_LR,0x180100)
        original.reg_write(reg.UC_ARM_REG_R0,0)
        original.emu_start(0xC56390,0x180100,count=100)
        require(original.reg_read(reg.UC_ARM_REG_PC)==0x180100,'Original power helper return')
        after=struct.unpack('<I',original.mem_read(power,4))[0]
        require(after==before&~1,'Original power request differs')
        register_cases.append(dict(before=hex(before),after=hex(after)))
    require(source_pins=={n:digest((ROOT/'scripts'/n).read_bytes()) for n in names},'Sources changed during run')
    report=dict(image_sha256=digest(image),cases=results,original_xt2_power_bit_comparisons=register_cases,
                terminal_wait_backend=wait_status,
                hardware_verified=False,rom_transfer=False,actual_poweroff=False,
                persistent_commands_after_entry_observed=0,
                source_sha256=source_pins,sources_unchanged_during_run=True,
                runtime_sha256=digest((ROOT/'.toolchains/unicorn-tci/libunicorn.2.dylib').read_bytes()),
                limits='Host-preloaded RAM, declared MMIO register storage, single CPU; no ROM, DMA/cache, watchdog, supply release timing or physical recovery proof. Trusted entry, LED return branch and checker are preconditions. Delay is a fixed instruction count, not calibrated time.')
    path=ROOT/'research/xt2-delivery-probe-verification.json'
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
