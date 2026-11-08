"""New guard-span checks and negative-only compiled late-wrapper fixtures.

Synthetic TCB/MMU/register storage and explicit native API error boundaries.
Successful native protection is proved by the separate native-prefix report,
never by these fault-injection returns. No ROM or physical power evidence.
"""
import json
import struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ,UC_MEM_WRITE
from unicorn import arm_const as reg
from build_xt2_minimal_protected import ROOT,OUT,LATE,build,compile_protected_guard
from build_xt2_delivery_probe import require,digest
from xt2_minimal_boot_guard import compile_guard,ENTRY,LED_CONFIG


def word(uc,address,value):uc.mem_write(address,struct.pack('<I',value&0xFFFFFFFF))


def early_cases(image,meta,points=None):
    _,symbols=compile_protected_guard();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    u.mem_map(0,(len(image)+4095)&~4095);u.mem_map(0xFFF0C000,4096)
    rows=struct.unpack_from('<I',image,LED_CONFIG)[0]
    gpio={a for a,_,_ in struct.iter_unpack('<III',image[LED_CONFIG+4:LED_CONFIG+4+rows*12])}
    state=dict(writes=[],reads=[])
    def memory(uc,access,address,size,value,data):
        if access==UC_MEM_WRITE:
            require(0x103058<=address and address+size<=0x103074 or size==4 and address in gpio,'Early write outside scratch/LED')
            state['writes'].append([address,size,value])
        elif address>=0xF0000000:state['reads'].append([address,size])
    u.hook_add(UC_HOOK_MEM_WRITE,memory)
    u.hook_add(UC_HOOK_MEM_READ,memory,begin=0xF0000000,end=0xFFFFFFFF)
    if points is None:points=[None,LATE,LATE+meta['late_bytes']-1,0xCF8214,symbols['xt2_minimal_guard_expected']]
    regs=[getattr(reg,'UC_ARM_REG_R'+str(i)) for i in range(13)]+[reg.UC_ARM_REG_SP,reg.UC_ARM_REG_LR,reg.UC_ARM_REG_CPSR]
    result=[]
    for mutation in points:
        address=mutation[0] if isinstance(mutation,tuple) else mutation
        u.mem_write(0,image);state.update(writes=[],reads=[])
        if address is not None:u.mem_write(address,mutation[1] if isinstance(mutation,tuple) else bytes([image[address]^1]))
        before=[0x12340000+256*i for i in range(13)]+[0xDEAD0000,0xBEEF0000,0xA0000013]
        for r,value in zip(regs,before):u.reg_write(r,value)
        for a in gpio:word(u,a,0x11223344)
        target=0x100 if address is None else symbols['xt2_minimal_guard_failed']+4
        u.emu_start(0,target,count=8000000)
        require(u.reg_read(reg.UC_ARM_REG_PC)==target,f'Early guard budget/return: corrupt={address!r}, pc={u.reg_read(reg.UC_ARM_REG_PC):#x}, target={target:#x}')
        led=[r for r in state['writes'] if r[0] in gpio]
        if address is None:require([u.reg_read(r) for r in regs]==before and len(led)==rows,'Early ABI/LED changed')
        else:require(not led and not state['reads'] and u.reg_read(reg.UC_ARM_REG_CPSR)&0x1C0==0x1C0,'Early fault did not stop before MMIO')
        result.append(dict(corrupted_address=None if address is None else hex(address),
                           mutation='replacement:'+mutation[1].hex() if isinstance(mutation,tuple) else 'xor1' if address is not None else 'none',
                           stopped_at=hex(target),led_writes=len(led),native_reset_reached=address is None))
    return result


def late_cases(image,meta):
    results=[]
    for name in ['wrong_root_context','unexpected_data_policy','unexpected_code_policy',
                 'bad_mmu_domain','corrupt_last_data_byte','native_protect_error',
                 'affinity_restore_error','success_status_without_page_effect',
                 'native_error_and_lost_context']:
        u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0,(len(image)+4095)&~4095);u.mem_write(0,image)
        u.mem_map(0x08000000,0x10000);u.mem_map(0xFFF10000,4096)
        # Negative-only identity translation and three TCB records. These are
        # declared fixtures, not evidence of native initialization/ownership.
        table=0x108000
        u.mem_write(table,b''.join(struct.pack('<I',(i<<20)|0x14C06) for i in range(4096)))
        coarse=0x88800;word(u,table+(0xDF7000>>20)*4,coarse|1)
        u.mem_write(coarse,b''.join(struct.pack('<I',0xD00000+i*4096|0x736) for i in range(256)))
        word(u,0x5BACC,table)
        u.mem_write(0x7A548,bytes(250*4))
        for i,address in enumerate((0x08001000,0x08002000,0x08003000),134):
            word(u,0x7A548+4*i,address);word(u,address,0x54485244)
            word(u,address+0xCC,i+1);word(u,address+0xE4,0xCF8060 if i==136 else 0xCF7C50)
        word(u,0x5BF90,0x08003000);word(u,0x5BF94,0x08001000)
        word(u,0x08003098,0xFFFFFFFE)
        if name=='wrong_root_context':word(u,0x7A548+136*4,0)
        if name=='unexpected_data_policy':word(u,table+(0x781000>>20)*4,0x714C16)
        if name=='unexpected_code_policy':word(u,coarse+((0xDF7000>>12)&255)*4,0xDF7536)
        if name=='corrupt_last_data_byte':u.mem_write(0x783FFF,bytes([image[0x783FFF]^1]))
        for el in (0,1):
            u.cpr_write(15,0,2,0,0,el,False,table)
            u.cpr_write(15,0,2,0,2,el,False,0)
            u.cpr_write(15,0,3,0,0,el,False,3 if name=='bad_mmu_domain' else 1)
            u.cpr_write(15,0,0,0,5,el,False,0x80000000)
            u.cpr_write(15,4,0,0,5,el,False,0x80000000)
            u.cpr_write(15,0,1,0,0,el,False,0x800001)
        for i in range(13):u.reg_write(getattr(reg,'UC_ARM_REG_R'+str(i)),0x12340000+256*i)
        u.reg_write(reg.UC_ARM_REG_SP,0x0800E000)
        u.reg_write(reg.UC_ARM_REG_LR,0xCF8218);u.reg_write(reg.UC_ARM_REG_CPSR,0x13)
        word(u,0xFFF10004,0x15)
        state=dict(calls=[],writes=[],reads=[],data_reads=0,status=None)
        def native(uc,pc,size,data):
            state['calls'].append(hex(pc))
            require(name in ('native_protect_error','affinity_restore_error','success_status_without_page_effect','native_error_and_lost_context'),
                    'Unexpected native API after required refusal: '+name)
            if pc==0x56618:
                word(uc,uc.reg_read(reg.UC_ARM_REG_R1),1);status=0
            elif pc==0xCF2100:
                status=0xFFFFFF01 if name in ('native_protect_error','native_error_and_lost_context') else 0
                if name=='native_error_and_lost_context':word(uc,0x7A548+136*4,0)
            else:status=0xFFFFFF01 if name=='affinity_restore_error' else 0
            uc.reg_write(reg.UC_ARM_REG_R0,status)
            uc.reg_write(reg.UC_ARM_REG_PC,uc.reg_read(reg.UC_ARM_REG_LR))
        for pc in (0x56618,0xCF2100,0x566D8):u.hook_add(UC_HOOK_CODE,native,begin=pc,end=pc)
        def original(uc,pc,size,data):raise ValueError('Refused wrapper continued startup')
        u.hook_add(UC_HOOK_CODE,original,begin=0xCF83CC,end=0xCF83CC)
        def failed(uc,pc,size,data):state['status']=uc.reg_read(reg.UC_ARM_REG_R0)
        u.hook_add(UC_HOOK_CODE,failed,begin=meta['symbols']['xt2_minimal_data_failed'],end=meta['symbols']['xt2_minimal_data_failed'])
        def memory(uc,access,address,size,value,data):
            if access==UC_MEM_WRITE:
                require(0x0800D000<=address and address+size<=0x0800E000 or address==0xFFF10004 and size==4,
                        'Late fixture CPU write outside stack/power request')
                if address>=0xF0000000:state['writes'].append([address,size,value])
            elif address>=0xF0000000:state['reads'].append([address,size])
            elif 0x781000<=address<0x784000:state['data_reads']+=1
        u.hook_add(UC_HOOK_MEM_WRITE,memory);u.hook_add(UC_HOOK_MEM_READ,memory)
        wait=meta['symbols']['xt2_minimal_data_wait']
        u.emu_start(LATE,wait,count=1000000)
        require(u.reg_read(reg.UC_ARM_REG_PC)==wait,'Late fixture did not reach terminal wait: '+name)
        expected=1 if name in ('wrong_root_context','native_error_and_lost_context') else 2
        require(state['status']==expected,'Wrong failure class: '+name)
        if expected==1:require(not state['reads'] and not state['writes'],'Unknown context requested power release')
        else:require(state['reads']==[[0xFFF10004,4]] and state['writes']==[[0xFFF10004,4,0x14]],'Power request differs')
        if name=='corrupt_last_data_byte':require(state['data_reads']==0x3000,'Data checksum did not cover full pages')
        require(u.reg_read(reg.UC_ARM_REG_CPSR)&0x1C0==0x1C0,'Late refusal did not mask interrupts')
        results.append(dict(case=name,**state,original_startup_reached=False))
    return results


def main():
    image,meta,_=build();require(image==(OUT/'ffboot.bin').read_bytes(),'Delivered image differs')
    report=dict(scope=__doc__,image_sha256=meta['image_sha256'],early_checked_bytes=meta['early_checked_bytes'],
                early_cases=early_cases(image,meta),late_failure_cases=late_cases(image,meta),
                hardware_verified=False,full_boot=False,proves_successful_native_protection=False,
                source_sha256=digest(Path(__file__).read_bytes()))
    (ROOT/'research/minimal-protected-failure-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
