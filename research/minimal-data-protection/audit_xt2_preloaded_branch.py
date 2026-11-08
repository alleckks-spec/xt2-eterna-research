"""Bounded original low-loader branch check on supplied preloaded RAM bytes.

Two branch segments after early hardware/chip initialization; does not execute
ROM or claim a continuous loader run. Original Codex-assisted analysis.
"""
import json
import struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn import arm_const as reg
from build_xt2_minimal_protected import OUT,ROOT
from build_xt2_delivery_probe import require,digest


def main():
    image=(OUT/'ffboot.bin').read_bytes()
    require(digest(image)=='274de1d23e82c0a18a97d67b893a14961ceb18f75dd8a6b7fe440a38c362d6d3','Candidate identity')
    mode=struct.unpack_from('<I',image,0xE978)[0]
    bss_start,bss_end=struct.unpack_from('<2I',image,0x374)
    require(mode==1 and not bss_start<=0xE978<bss_end,'Mode field is not initialized outside BSS clear')
    results=[]
    for supplied in (mode,0):
        u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
        u.mem_map(0,(len(image)+4095)&~4095);u.mem_write(0,image)
        u.mem_map(0x08000000,0x10000)
        u.mem_write(0xE978,struct.pack('<I',supplied))
        u.reg_write(reg.UC_ARM_REG_SP,0x0800E000)
        u.reg_write(reg.UC_ARM_REG_R5,0)
        u.reg_write(reg.UC_ARM_REG_CPSR,0x13)
        state=dict(transfers=[],writes=[])
        def transfer(uc,pc,size,data):
            state['transfers'].append(dict(pc=hex(pc),args=[uc.reg_read(r) for r in
                                      (reg.UC_ARM_REG_R0,reg.UC_ARM_REG_R1,reg.UC_ARM_REG_R2)]))
            uc.emu_stop() # observe the attempted original transfer; no success supplied
        for pc in (0xAF6C,0xA90,0xB84,0xAF4):u.hook_add(UC_HOOK_CODE,transfer,begin=pc,end=pc)
        def write(uc,access,address,size,value,data):
            require(0x0800D000<=address and address+size<=0x0800E000 or address==0x950008 and size==4,
                    'Unexpected low-branch write')
            state['writes'].append([address,size,value])
        u.hook_add(UC_HOOK_MEM_WRITE,write)
        u.emu_start(0x59C,0x648,count=10000)
        if supplied:
            require(u.reg_read(reg.UC_ARM_REG_PC)==0x648,'First branch segment did not end')
            # The intervening time logger and section lookups are not faked.
            # This second assay checks only the next explicit mode branch.
            u.emu_start(0x66C,0x6E4,count=1000)
        pc=u.reg_read(reg.UC_ARM_REG_PC)
        if supplied:
            require(pc==0x6E4 and not state['transfers'],'Pinned mode did not skip original transfers')
            require([r for r in state['writes'] if r[0]==0x950008]==[[0x950008,4,1]],'Preloaded table flag not retained')
        else:require(pc==0xAF6C and len(state['transfers'])==1,'Zero-mode counterexample not observed')
        results.append(dict(supplied_mode=supplied,stopped_at=hex(pc),**state))
    report=dict(scope=__doc__,image_sha256=digest(image),mode_address='0xe978',packaged_mode=mode,
                native_bss_clear=[hex(bss_start),hex(bss_end)],cases=results,
                conclusion='Given the packaged mode1 at block59c, original code retains preloaded section table and skips both signature/source transfer and full load branch. Mode0 attempts flash copy; no transfer success was fabricated.',
                executed_segments=[['0x59c','0x648'],['0x66c','0x6e4']],
                limitations='Not continuous: intervening648..66c time logger and section lookups omitted. ROM handoff, hardware/chip initialization before59c, indirect/DMA writes to mode, final secondary-core release and later lifetime are outside this assay.',
                hardware_verified=False,source_sha256=digest(Path(__file__).read_bytes()))
    (ROOT/'research/minimal-preloaded-branch-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
