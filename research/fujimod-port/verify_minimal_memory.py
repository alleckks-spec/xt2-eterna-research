"""Execute exact delivered allocator/BSS edits against the final SD candidate.

Bounded native calls using the existing function harness. Payload is loaded from
ffboot.bin, not supplied from a different ELF. Map-service arguments are recorded
without claiming installed MMU/cache state. This is not ROM/SD boot or a camera.
"""
import json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
from verify_minimal_runtime import machine,ROOT,BUILD,OUT,sha,RAM
from build_resident_reservation import START,END,BSS_START,BSS_END,HEAP_START


def main():
    (u,s,call,clock,exceptions),setup=machine()
    image=(Path(str(BUILD)+'-card')/'ffboot.bin').read_bytes()
    payload=image[START:END];assert len(payload)==END-START
    # Reload all actual candidate words and reserved bytes after supplied setup.
    manifest=json.loads((BUILD/'manifest.json').read_text())
    for w in manifest['words']:
        a=int(w['address'],0);assert image[a:a+4]==struct.pack('<I',int(w['new'],0))
        u.mem_write(a,image[a:a+4])
    u.mem_write(BSS_START,b'\xa5'*(START-BSS_START));u.mem_write(START,payload)
    u.mem_write(END,b'\xa5'*(BSS_END-END));u.ctl_flush_tb()
    # Run the native caller, delivered shim, and the actual native fill twice.
    u.reg_write(UC_ARM_REG_SP,RAM+0xe000)
    u.emu_start(0xcf7c78,0xcf7c94,count=4000000)
    assert u.reg_read(UC_ARM_REG_PC)==0xcf7c94
    assert bytes(u.mem_read(BSS_START,START-BSS_START))==bytes(START-BSS_START)
    assert bytes(u.mem_read(START,END-START))==payload
    assert bytes(u.mem_read(END,BSS_END-END))==bytes(BSS_END-END)
    # Exact native heap ceiling: a crossing allocation fails; no successful reply supplied.
    errno=RAM+0x4000;u.mem_write(0xfae334,struct.pack('<I',START-64));u.mem_write(errno,bytes(4))
    assert call(0xcf45a8,errno,33)==0xffffffff
    assert int.from_bytes(u.mem_read(errno,4),'little')==12
    assert int.from_bytes(u.mem_read(0xfae334,4),'little')==START-64
    maps=[]
    def record(uc,a,z,d):
        maps.append([uc.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2]])
        uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
    h=u.hook_add(UC_HOOK_CODE,record,begin=0xcf7cf0,end=0xcf7cf0)
    u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.emu_start(0xcf8170,0xcf8214,count=1000);u.hook_del(h)
    assert u.reg_read(UC_ARM_REG_PC)==0xcf8214
    assert maps[-1]==[START,END,7] and len(maps)==7
    assert maps[-2][1]<=START
    report=dict(scope=__doc__,status='PASS: final SD reservation/BSS/heap/map operands',
        elf_sha256=sha((BUILD/'mods.elf').read_bytes()),ffboot_sha256=sha(image),setup=setup,
        reserved_start=hex(START),reserved_end=hex(END),loaded_region_bytes=len((BUILD/'region.bin').read_bytes()),
        reserved_payload_preserved=True,native_prefix_and_suffix_zero=True,
        crossing_allocation_refused=True,heap_remaining_capacity=START-HEAP_START,
        map_arguments=maps,native_map_service_executed=False,full_boot=False,hardware_verified=False,
        checker_sha256=sha(Path(__file__).read_bytes()))
    OUT.mkdir(exist_ok=True);(OUT/'memory.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
