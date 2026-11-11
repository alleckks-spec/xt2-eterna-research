"""Link the pinned existing XPP aspect crop hooks against the real chooser.

Isolated existing component placement only. Native RAF pointer ABI, JPEG
descriptor ABI and applied-aspect owner were qualified independently. The
private capture C is not redistributed. This is not a common SD build or a
capture lifetime/persistence result. No new runtime or encoder is introduced.
"""
import argparse
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path
from elftools.elf.elffile import ELFFile
from build_modular_candidate import ROOT,VENDOR,LIBS,sha
from firmware_analysis import Firmware

CHOOSER=ROOT/'native-chooser-component-unverified'
SOURCE=ROOT/'aspect-upstream-inputs/aspect-ratio/xpp/capture.c'
BUILD=ROOT/'aspect-capture-component-unverified'


def build(output):
    output=output.resolve();assert not output.exists();output.mkdir()
    source=SOURCE.read_bytes()
    assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='712b4e79cf720228d68343a5bfe00a509f2619b4'
    raw=(CHOOSER/'component.elf').read_bytes()
    assert sha(raw)=='f113fa3faef60da34b8e8db6c73a69c692fe83ae0236aa856af3324638aa73cb'
    elf=ELFFile(io.BytesIO(raw));symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols() if s['st_shndx']!='SHN_UNDEF'}
    native=Firmware('xt2-4.41',True)
    bindings=dict(jpeg_encoder_program=0x15b2244,raf_info_prepare=0x16dc9f0,input_aspect=0x119f2f5)
    assert native.word(bindings['jpeg_encoder_program'])==0xe92d4870
    assert native.word(bindings['raf_info_prepare'])==0xe92d4ff0
    assert native.listing(0xc01154,0xc01158)==['00c01154: strb r4, [r3, #0x99]']
    bindings['shape_aspect_ratio']=symbols['shape_aspect_ratio']
    compiler=ROOT.parents[1]/'.toolchains/arm-gnu-13.2-darwin-arm64/bin/arm-none-eabi-gcc'
    includes=[ROOT/'aspect-upstream-inputs/include',ROOT/'aspect-upstream-inputs/lib/shape-state/include',
        ROOT/'aspect-upstream-inputs/lib/settings/generated',VENDOR/'decomp/mods/include',
        LIBS/'xpp-hook/include',LIBS/'settings/include',LIBS/'settings/generated',
        LIBS/'menu/xpp/include',LIBS/'xpp-settings/include',LIBS/'libc/include',
        ROOT/'aspect-upstream-inputs/lib/xpp-icons/include']
    sources=[SOURCE,ROOT/'aspect-upstream-inputs/lib/shape-state/aspect_ratio.c',ROOT/'aspect-upstream-inputs/lib/shape-state/geometry.c']
    commands=[];objects=[]
    for index,path in enumerate(sources):
        obj=output/f'{index}.o';objects.append(str(obj))
        cmd=[str(compiler),'-march=armv7-a','-marm','-mfloat-abi=soft','-std=gnu11','-O2',
            '-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections','-DXPP_TARGET',
            *[f'-I{p}' for p in includes],'-MMD','-MF',str(output/f'{index}.d'),'-c',str(path),'-o',str(obj)]
        subprocess.run(cmd,check=True);commands.append(cmd)
    sys.path[:0]=[str(VENDOR/'decomp/tools')]
    import mod_xpp
    script=mod_xpp.linker_script(0x2040000,0x40000)
    script='EXTERN(jpeg_encoder_program_hook raf_info_prepare_hook)\n'+''.join(f'{n} = {a:#x};\n' for n,a in bindings.items())+script
    (output/'component.ld').write_text(script)
    linker=ROOT.parents[1]/'.toolchains/rustup/toolchains/1.89.0-aarch64-apple-darwin/lib/rustlib/aarch64-apple-darwin/bin/gcc-ld/ld.lld'
    runtime=ROOT.parents[1]/'.toolchains/arm-gnu-13.2-darwin-arm64/lib/gcc/arm-none-eabi/13.2.1/libgcc.a'
    link=[str(linker),'--threads=1','--gc-sections','-T',str(output/'component.ld'),'-Map='+str(output/'component.map'),*objects,str(runtime),'-o',str(output/'component.elf')]
    subprocess.run(link,check=True)
    report=dict(scope=__doc__,chooser_elf_sha256=sha(raw),capture_source_sha256=sha(source),bindings=bindings,
        commands=[*commands,link],elf_sha256=sha((output/'component.elf').read_bytes()),
        source_sha256={str(p):sha(p.read_bytes()) for p in sources},
        builder_sha256=sha(Path(__file__).read_bytes()),upstream_pin='9d22f1b41c70c20407158e699f2583ac4907ff16',
        hardware_verified=False,capture_lifetime_qualified=False)
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(elf=report['elf_sha256'],scope='component hooks linked; function/native-flow checks required')))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=BUILD)
    build(p.parse_args().output)
