"""Run existing bounded assays on the reduced single-ETERNA candidate.

Separate reports and explicit artifact selection preserve the old candidate.
No full boot, peripheral readiness or hardware acceptance is inferred.
"""
import argparse
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def ablations(build, output):
    import verify_single_eterna_runtime as runtime
    from build_resident_reservation import START, END, BSS_START, BSS_END
    from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_PC
    (u, symbols, call, clock, exceptions), setup = runtime.machine()
    image = (Path(str(build)+'-card')/'ffboot.bin').read_bytes()
    stock = (ROOT.parents[1]/'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    # Remove only BSS preservation: the real original clear must erase the mod.
    u.mem_write(START, image[START:END])
    u.mem_write(0xcf7c90, stock[0xcf7c90:0xcf7c94]); u.ctl_flush_tb()
    u.reg_write(UC_ARM_REG_SP, runtime.RAM+0xe000)
    u.emu_start(0xcf7c78, 0xcf7c94, count=4000000)
    assert u.reg_read(UC_ARM_REG_PC)==0xcf7c94
    assert bytes(u.mem_read(START, END-START))==bytes(END-START)
    assert any(image[START:END])
    # Remove only the heap ceiling: the real allocator admits a crossing block.
    for address in [0xcf45c4, 0xcf45c8]:u.mem_write(address,stock[address:address+4])
    u.ctl_flush_tb()
    u.mem_write(0xfae334,struct.pack('<I',START-64))
    errno=runtime.RAM+0x4000;u.mem_write(errno,bytes(4))
    result=call(0xcf45a8,errno,256)
    new_break=int.from_bytes(u.mem_read(0xfae334,4),'little')
    assert result==START-64 and new_break>START, (hex(result),hex(new_break))
    report=dict(scope=__doc__,elf_sha256=runtime.sha((build/'mods.elf').read_bytes()),
                status='PASS: removing BSS/heap protection reproduces destructive overlap',
                original_bss_clear_erases_reserved_payload=True,
                original_heap_allows_crossing=True,allocation_return=hex(result),new_break=hex(new_break),
                qualification='Required for this placement; no claim that all X-T2 placements require these edits.',
                setup=setup,full_boot=False,hardware_verified=False)
    (output/'placement-ablations.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=ROOT/'single-eterna-build-unverified')
    p.add_argument('--output',type=Path,default=ROOT/'single-eterna-check-unverified')
    p.add_argument('--case',required=True,choices=['all','runtime','still','memory','processing','placement','storage'])
    a=p.parse_args();build=a.build.resolve();output=a.output.resolve();output.mkdir(exist_ok=True)
    if a.case=='all':
        import subprocess,sys
        for case in ['runtime','still','memory','processing','placement','storage']:
            print('Checking '+case,flush=True)
            subprocess.run([sys.executable,'-u',str(Path(__file__).resolve()),
                            '--build',str(build),'--output',str(output),'--case',case],check=True)
        return
    import verify_minimal_runtime as old_runtime
    import verify_single_eterna_runtime as runtime
    for module in [old_runtime,runtime]:module.BUILD=build;module.OUT=output
    if a.case=='runtime':runtime.main()
    elif a.case=='placement':ablations(build,output)
    elif a.case=='storage':
        from audit_minimal_storage import audit
        print(json.dumps(audit(build)))
    else:
        if a.case=='still':import verify_single_eterna_still as checker
        elif a.case=='memory':import verify_minimal_memory as checker
        else:import verify_minimal_processing as checker
        checker.BUILD=build;checker.OUT=output/'processing' if a.case=='processing' else output
        checker.main()


if __name__=='__main__':main()
