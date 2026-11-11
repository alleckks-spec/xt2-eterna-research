"""Compare one-film chroma with and without a supplied same-core nested call.

Use the existing native caller and explicit calibration/transport fixtures.
This tests a counterexample ordering, not observed camera task preemption.
"""
import argparse
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
from verify_ordinary_platform_nr import load, ROOT
from verify_ordinary_platform_processing import actual_factory, initialize, select
from verify_interpolated_profile_outputs import call
from verify_profile_selectors import RAM, RETURN
from build_fixture import sha


def verify(build, output, expect_changed):
    sections,symbols,report=load(build,45)
    u=actual_factory()
    for address,data,name,size in sections:
        if name not in ['.x70mod.hooks','.x70mod.strings']:u.mem_write(address,data)
    for edit in report['edits']:
        assert bytes(u.mem_read(edit['address'],4))==struct.pack('<I',edit['expected'])
        u.mem_write(edit['address'],struct.pack('<I',edit['value']))
    u.ctl_flush_tb()
    def invoke(uc,entry,*args):
        uc.reg_write(UC_ARM_REG_SP,RAM+0xe000);call(uc,entry,*args)
        return uc.reg_read(UC_ARM_REG_R0)
    initialize(u,symbols,invoke,1);select(u,symbols,invoke,1,0)
    for profile in [RAM,RAM+0x400]:
        u.mem_write(profile,bytes(0x200))
        invoke(u,0x157a0fc,profile);invoke(u,0x157ac60,profile,0)
        u.mem_write(profile+0x51,b'\x01')
    base=RAM+0x2000
    u.mem_write(base-16,b'\xcc'*0x220)
    invoke(u,0x156af80,RAM,base)
    expected=bytes(u.mem_read(base,50))
    u.mem_write(base-16,b'\xcc'*0x220)
    u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.reg_write(UC_ARM_REG_LR,RETURN)
    u.reg_write(UC_ARM_REG_R0,RAM);u.reg_write(UC_ARM_REG_R1,base)
    hook=u.hook_add(UC_HOOK_CODE,lambda uc,a,s,d:uc.emu_stop(),begin=0x156afe0,end=0x156afe0)
    try:u.emu_start(0x156af80,RETURN,count=200000)
    finally:u.hook_del(hook)
    assert u.reg_read(UC_ARM_REG_PC)==0x156afe0
    saved=u.context_save()
    u.reg_write(UC_ARM_REG_SP,RAM+0xc000)
    call(u,0x156af80,RAM+0x400,RAM+0x2400)
    u.context_restore(saved);u.emu_start(0x156afe0,RETURN,count=200000)
    assert u.reg_read(UC_ARM_REG_PC)==RETURN
    actual=bytes(u.mem_read(base,50));changed=actual!=expected
    assert changed is expect_changed,(changed,expect_changed)
    assert bytes(u.mem_read(base-16,16))==b'\xcc'*16
    assert bytes(u.mem_read(base+50,16))==b'\xcc'*16
    result=dict(scope=__doc__,status='PASS: expected nested-call result observed',
                elf_sha256=report['elf_sha256'],nested_call_changes_output=changed,
                expected_sha256=sha(expected),nested_sha256=sha(actual),
                output_canaries_intact=True,actual_task_overlap_observed=False,
                full_boot=False,hardware_verified=False)
    output.parent.mkdir(exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--expect-changed',action='store_true')
    a=p.parse_args();verify(a.build.resolve(),a.output.resolve(),a.expect_changed)
