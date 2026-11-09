"""Compile the original/adapted listing component at explicit assay placement.

AI-assisted original tool; private authorized upstream sources required.
Not an installable image or ordinary common SD candidate. No runtime service
or API success stub. Unused file operations are garbage-collected, not mocked.
"""
import argparse
import hashlib
import json
import shlex
import subprocess
from pathlib import Path
from prepare_cardio_listing import prepare


def sha(b):return hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--original',action='store_true');p.add_argument('--clang',default='clang')
    p.add_argument('--linker',required=True);a=p.parse_args();root=a.source_root.resolve();out=a.output.resolve()
    source=prepare(root/'lib/cardio/cardio.c',out,a.original)
    (out/'build.json').unlink(missing_ok=True)  # an interrupted rebuild must not authorize a stale ELF
    includes=[out,root/'include',root/'lib/cardio/include',root/'lib/lifetime/include',root/'lib/libc/include']
    sources=[source,root/'lib/lifetime/lifetime.c',root/'lib/libc/string.c']
    commands=[];objects=[];deps={Path(__file__),Path(__file__).with_name('prepare_cardio_listing.py')}
    for i,s in enumerate(sources):
        obj=out/f'{i}.o';objects.append(str(obj))
        cmd=[a.clang,'--target=armv7-none-eabi','-march=armv7-a','-marm','-mfloat-abi=soft',
             '-std=gnu11','-O2','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections',
             '-DXPP_TARGET',*[f'-I{x}' for x in includes],'-MMD','-MF',str(out/f'{i}.d'),'-c',str(s),'-o',str(obj)]
        subprocess.run(cmd,check=True);commands.append(cmd)
        deps.update(Path(x) for x in shlex.split((out/f'{i}.d').read_text().replace('\\\n',' ').split(':',1)[1]))
    script='''ENTRY(x70_cardio_list)
EXTERN(x70_cardio_abandon x70_cardio_bank x70_lifetime_live)
SECTIONS {
 . = 0x2000000; .text : { *(.text*) } .rodata : { *(.rodata*) }
 . = ALIGN(4096); .data : { *(.data*) *(.x70mod.shared*) }
 .bss : { *(.bss*) *(COMMON) }
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) }
}
storage_context_slot = 0x9c2260;
storage_media_ready = 0x967490;
storage_media_queue = 0x9c3544;
storage_send_request_packet = 0x969f24;
dispatch_current_task = 0xceed8c;
'''
    (out/'component.ld').write_text(script)
    cmd=[a.linker,'--threads=1','--gc-sections','-T',str(out/'component.ld'),'-Map='+str(out/'component.map'),
         *objects,'-o',str(out/'component.elf')]
    subprocess.run(cmd,check=True);commands.append(cmd)
    report=dict(scope=__doc__,original=a.original,commands=commands,
        dependencies={str(x):sha(x.read_bytes()) for x in sorted(deps)},
        elf_sha256=sha((out/'component.elf').read_bytes()),
        preparation_sha256=sha((out/'preparation.json').read_bytes()),hardware_verified=False)
    report['linker_sha256']=sha(Path(a.linker).read_bytes())
    report['compiler']=subprocess.check_output([a.clang,'--version'],text=True).splitlines()[0]
    (out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(original=a.original,elf_sha256=report['elf_sha256'])))


if __name__=='__main__':main()
