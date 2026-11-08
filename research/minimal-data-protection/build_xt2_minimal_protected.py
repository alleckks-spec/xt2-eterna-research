"""Add a fixed early data-RO/XN step to the pinned minimal research image.

Private locally supplied images are required. This is not a flash installer or
a camera-qualified build. Original OpenAI Codex-assisted tooling.
"""
import json
import struct
import subprocess
import tempfile
from pathlib import Path
from elftools.elf.elffile import ELFFile
from xt2_minimal_boot_guard import checksum,compile_guard,RANGES,ENTRY,LIMIT,HOOK
from build_xt2_delivery_probe import branch,digest,require

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'firmware/research/eterna-minimal-sd-candidate'
OUT=ROOT/'firmware/research/eterna-minimal-protected-unverified'
LATE=0xDF7B00
SOURCES=['xt2_minimal_data_entry.S','xt2_minimal_data_prepare.c',
         'eterna_early_resident_gate.c','xt2_native_page_policy.c']


def compile_late(expected):
    with tempfile.TemporaryDirectory(prefix='xt2-fixed-ro-') as tmp:
        tmp=Path(tmp);objects=[]
        for name in SOURCES:
            obj=tmp/(name+'.o')
            subprocess.run(['clang','--target=armv7-none-eabi','-marm','-march=armv7-a','-Oz',
                            '-ffunction-sections','-fdata-sections','-ffreestanding','-fno-builtin',
                            '-fno-unwind-tables','-fno-asynchronous-unwind-tables',
                            '-c',str(ROOT/'scripts'/name),'-o',str(obj)],check=True,capture_output=True)
            objects.append(str(obj))
        script=tmp/'image.ld'
        script.write_text('ENTRY(xt2_minimal_data_entry)\n'
                          'xt2_minimal_original_root_call = 0xcf83cc;\n'
                          f'xt2_minimal_expected_data_fnv = {expected};\n'
                          f'SECTIONS {{ . = {LATE}; .text : {{ *(.text.entry) *(.text*) *(.rodata*) }} '
                          '/DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) } }\n')
        linker=next((ROOT/'.toolchains/rustup/toolchains').glob('*/lib/rustlib/*/bin/gcc-ld/ld.lld'))
        output=tmp/'image.elf'
        subprocess.run([str(linker),'-T',str(script),'--gc-sections','--no-undefined',
                        *objects,'-o',str(output)],check=True,capture_output=True)
        elf_bytes=output.read_bytes()
        with output.open('rb') as stream:
            elf=ELFFile(stream);section=elf.get_section_by_name('.text');code=section.data()
            symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols() if s.name}
            require(section['sh_addr']==LATE and LATE+len(code)<=0xDF8000,'Existing RX tail capacity exceeded')
            require(not any(s['sh_size'] and s['sh_flags']&1 for s in elf.iter_sections()),'Writable ELF section')
    return code,symbols,elf_bytes


def build():
    base=(BASE/'ffboot.bin').read_bytes()
    require(digest(base)=='c1aee308e0b6c54dfede3de4c48885223365b2b8e90c282c74d87a112d58fc10','Base identity')
    expected_data=checksum([base[0x781000:0x784000]])
    code,symbols,elf=compile_late(expected_data)
    require(not any(base[LATE:LATE+len(code)]),'Existing late storage occupied')
    image=bytearray(base);edits=[]
    def write(address,data):
        old=bytes(image[address:address+len(data)])
        edits.append(dict(address=address,old=old.hex(),new=bytes(data).hex()))
        image[address:address+len(data)]=data
    write(LATE,code)
    original_call=bytearray(branch(0xCF8214,0xCF83CC));original_call[3]=0xEB
    require(base[0xCF8214:0xCF8218]==bytes(original_call),'Original root call differs')
    call=bytearray(branch(0xCF8214,LATE));call[3]=0xEB
    write(0xCF8214,call)
    early,s=compile_guard()
    expected_address=s['xt2_minimal_guard_expected']
    ranges=list(RANGES)
    ranges[1]=(0xDF7900,LATE+len(code)-0xDF7900)
    # Preserve the seven naturally aligned descriptors. Cover the new root BL
    # by extending the existing initialized resident-code span, not its count.
    ranges[2]=(0xC4D298,0xCF8218-0xC4D298)
    ranges.append((ENTRY,expected_address-ENTRY))
    early=bytearray(early)
    struct.pack_into('<14I',early,s['xt2_minimal_guard_ranges']-ENTRY,*(x for r in ranges for x in r))
    write(ENTRY,early)
    value=checksum(image[a:a+n] for a,n in ranges)
    write(expected_address,struct.pack('<I',value))
    require(image[HOOK:HOOK+4]==base[HOOK:HOOK+4],'Existing early entry changed')
    allowed=[(LATE,LATE+len(code)),(0xCF8214,0xCF8218),(ENTRY,LIMIT)]
    require(all(a==b or any(lo<=i<hi for lo,hi in allowed)
                for i,(a,b) in enumerate(zip(base,image))),'Unexpected variant change')
    meta=dict(base_sha256=digest(base),image_sha256=digest(image),image_size=len(image),
              variant='fixed early data RO/XN, not camera-qualified',late_entry=LATE,
              late_bytes=len(code),late_end=LATE+len(code),symbols=symbols,
              data_pages=[0x781000,0x782000,0x783000],expected_data_fnv=expected_data,
              early_ranges=ranges,early_checksum=value,early_checked_bytes=sum(n for _,n in ranges),
              edits_from_base=edits,source_sha256={n:digest((ROOT/'scripts'/n).read_bytes()) for n in SOURCES},
              hardware_verified=False,full_boot=False,admission='HOLD pending image-contained verification')
    return bytes(image),meta,elf


def main():
    image,meta,elf=build()
    OUT.mkdir(parents=True,exist_ok=True)
    require(not any(p.suffix.lower()=='.dat' for p in OUT.iterdir()),'Update DAT present')
    header=(BASE/'ffsys.bin').read_bytes()
    require(digest(header)=='b1e52216d083b43b430b2abcb880ebf72ca055c0ff9623d23bc03bddcb539351','Header identity')
    (OUT/'ffboot.bin').write_bytes(image);(OUT/'ffsys.bin').write_bytes(header)
    (OUT/'late.elf').write_bytes(elf)
    (OUT/'local-build.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({k:meta[k] for k in ['image_sha256','late_bytes','late_end','early_checked_bytes','admission']},indent=2))


if __name__=='__main__':main()
