"""Execute actual native profile clear and the post-mapper field-copy fragment.

AI-assisted bounded functional check. Native live-builder prologue reaches its
real clear/default calls, stopped before settings-dependent work. The input-
object transfer is entered at its post-mapper continuation with supplied r4-r7;
this is not full 157b31c execution or proof of every caller/task/object lifetime.
No memcpy/memset or kernel/device success reply is substituted.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1] / 'scripts'))
from firmware_analysis import Firmware
from verify_profile_selectors import machine, RAM, RETURN
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
from unicorn.unicorn_py3.unicorn import uclib


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    backend = Path(uclib._name).resolve()
    assert backend == (ROOT.parents[1] / '.toolchains/unicorn-tci/libunicorn.2.dylib').resolve()
    f = Firmware('xt2-4.41')
    u = machine(f)
    native_profile = 0x1c2e8fc
    u.mem_map(0x1c2e000, 0x2000)
    writes, calls = [], []
    def written(uc, access, address, size, value, data):
        writes.append((uc.reg_read(UC_ARM_REG_PC), address, size))
    def entered(uc, address, size, data):
        if address in [0xcf2bbc, 0xcf2da0]:
            calls.append(dict(entry=address, caller=uc.reg_read(UC_ARM_REG_LR)-4,
                              destination=uc.reg_read(UC_ARM_REG_R0),
                              source_or_value=uc.reg_read(UC_ARM_REG_R1),
                              size=uc.reg_read(UC_ARM_REG_R2)))
    u.hook_add(UC_HOOK_MEM_WRITE, written)
    u.hook_add(UC_HOOK_CODE, entered)
    u.mem_write(native_profile-16, b'\xcc'*16+b'\xa5'*0x148+b'\xcc'*16)
    u.reg_write(UC_ARM_REG_R0, 0)
    u.reg_write(UC_ARM_REG_R1, RAM+0x6000)
    initial_sp = RAM+0xe000
    u.emu_start(0x170c770, 0x170c7a4, count=20000)
    assert u.reg_read(UC_ARM_REG_PC) == 0x170c7a4
    assert calls == [dict(entry=0xcf2da0, caller=0x15797e8,
                          destination=native_profile, source_or_value=0, size=0x148)]
    assert bytes(u.mem_read(native_profile+0x145,3)) == bytes(3)
    assert bytes(u.mem_read(native_profile-16,16)) == bytes(u.mem_read(native_profile+0x148,16)) == b'\xcc'*16
    assert all(native_profile <= a < a+n <= native_profile+0x148 or
               initial_sp-0x100 <= a < a+n <= initial_sp for pc,a,n in writes)
    clear = dict(actual_builder_entry=0x170c770, stop=0x170c7a4,
                 memory_call=calls[0], tail_cleared=True, canaries_intact=True,
                 tag_mapper_not_yet_reached=True, sp_delta=initial_sp-u.reg_read(UC_ARM_REG_SP))
    # The real continuation computes both memcpy sizes and destinations itself.
    # r4/r5/r6/r7 are the documented state at 157b6d8, not a direct memcpy call.
    dst, src, extra = RAM+0x1000, RAM+0x3000, RAM+0x5000
    src_data = bytes((i*37+11)&255 for i in range(0x580))
    extra_data = bytes((i*19+7)&255 for i in range(32))
    u.mem_write(src,src_data);u.mem_write(extra,extra_data)
    cases=[]
    for tag in [bytes([1,0x58,0x54]), bytes(3), b'\xff'*3]:
        original=bytearray(b'\xa5'*0x148);original[0x145:0x148]=tag
        u.mem_write(dst-16,b'\xcc'*16+bytes(original)+b'\xcc'*16)
        for reg,value in [(UC_ARM_REG_R4,dst),(UC_ARM_REG_R5,src),
                          (UC_ARM_REG_R6,0x7b),(UC_ARM_REG_R7,extra),
                          (UC_ARM_REG_SP,initial_sp),(UC_ARM_REG_LR,RETURN)]:
            u.reg_write(reg,value)
        calls.clear();writes.clear()
        u.emu_start(0x157b6d8,0x157b724,count=20000)
        assert u.reg_read(UC_ARM_REG_PC)==0x157b724
        assert u.reg_read(UC_ARM_REG_SP)==initial_sp
        assert calls==[
            dict(entry=0xcf2bbc,caller=0x157b6ec,destination=dst+0x134,source_or_value=src+0x55a,size=8),
            dict(entry=0xcf2bbc,caller=0x157b710,destination=dst+0x13e,source_or_value=extra+8,size=6)]
        actual=bytes(u.mem_read(dst,0x148))
        assert actual[0x134:0x13c]==src_data[0x55a:0x562]
        assert actual[0x13e:0x144]==extra_data[8:14]
        assert actual[0x145:0x148]==tag
        assert bytes(u.mem_read(dst-16,16))==bytes(u.mem_read(dst+0x148,16))==b'\xcc'*16
        assert bytes(u.mem_read(src,0x580))==src_data and bytes(u.mem_read(extra,32))==extra_data
        assert all(dst<=a<a+n<=dst+0x145 or initial_sp-64<=a<a+n<=initial_sp for pc,a,n in writes)
        cases.append(dict(tag=list(tag), memory_calls=list(calls),
                          tail_preserved=True, canaries_intact=True,
                          source_unchanged=True, sp_preserved=True,
                          last_written_profile_offset=max(a+n-dst for pc,a,n in writes if dst<=a<dst+0x148)-1))
    out=ROOT/'profile-tail-ownership-unverified';out.mkdir(exist_ok=True)
    report=dict(scope=__doc__,status='PASS: native clear and real copy continuation',
                clear=clear,copy_cases=cases,backend_sha256=sha(backend.read_bytes()),
                checker_sha256=sha(Path(__file__).read_bytes()),
                full_native_live_builder_executed=False,
                full_input_transfer_executed=False,
                whole_profile_copy_proven=False,all_tail_owners_qualified=False,
                hardware_verified=False,firmware_changed=False)
    (out/'native-transfer-execution.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: native live-builder clear/default prefix and three actual post-mapper field-copy continuations; tail and canaries verified.')


if __name__=='__main__':
    main()
