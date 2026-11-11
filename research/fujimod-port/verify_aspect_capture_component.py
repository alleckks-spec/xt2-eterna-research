"""Execute pinned crop hooks at explicit descriptor/Exif/RAF-record boundaries.

Reuse the existing native function fixture. All descriptor, selected-ratio and
metadata inputs here are supplied function fixtures, not captured frames.
Native descriptor production is covered separately by SDK probes. No encoder
success, preview pixel layout, shot lifetime or full-file result is claimed.
"""
import argparse
import io
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
import verify_full_storage_guard as fixture
from build_modular_candidate import ROOT, sha

BUILD=ROOT/'aspect-capture-component-v2-unverified'
CHOOSER=ROOT/'native-chooser-component-unverified'
OUT=ROOT/'aspect-capture-function-check-unverified'
RAM=0x8000000


def main(output=OUT):
    output=Path(output);assert not output.exists();output.mkdir()
    fixture.BUILD=ROOT/'save-data-menu-native-build-unverified'
    (u,base,call,api,clock,initial,exceptions),setup=fixture.fixture_machine(True)
    loaded={};hashes={}
    for directory,begin,end in [(CHOOSER,0x2000000,0x2040000),(BUILD,0x2040000,0x2080000)]:
        raw=(directory/'component.elf').read_bytes();elf=ELFFile(io.BytesIO(raw))
        hashes[directory.name]=sha(raw)
        symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols() if s['st_shndx']!='SHN_UNDEF'}
        loaded.update(symbols)
        for section in elf.iter_sections():
            if section['sh_flags']&2 and section['sh_size'] and begin<=section['sh_addr']<end:
                u.mem_write(section['sh_addr'],bytes(section['sh_size']) if section['sh_type']=='SHT_NOBITS' else section.data())
    assert hashes[CHOOSER.name]=='f113fa3faef60da34b8e8db6c73a69c692fe83ae0236aa856af3324638aa73cb'
    assert loaded['shape_aspect_ratio']==json.loads((BUILD/'build.json').read_text())['bindings']['shape_aspect_ratio']
    descriptor,args,info,copy=RAM+0x4000,RAM+0x4100,RAM+0x4200,RAM+0x4300
    u.mem_map(0xa000000,0x80000)
    header=0xa040000;destination=header+0x2000
    def word(a):return int.from_bytes(u.mem_read(a,4),'little')
    def invoke(name,*values):return call(loaded[name],*values,task=True)
    def select(ratio):u.mem_write(loaded['shape_aspect_ratio'],struct.pack('<HH',*ratio))
    def crop(fields):
        u.mem_write(descriptor,struct.pack('<7I',*fields));u.mem_write(args,struct.pack('<4I',descriptor,0,0,0))
        assert invoke('jpeg_encoder_program_hook',args)==0
        return list(struct.unpack('<7I',u.mem_read(descriptor,28)))
    def exif(width,height,kind):
        data=bytearray(128);data[:12]=b'\xff\xd8\xff\xe1\x00\x7cExif\0\0'
        data[12:20]=b'II\x2a\0\x08\0\0\0'
        struct.pack_into('<H',data,20,1)
        struct.pack_into('<HHII',data,22,0x8769,4,1,26)
        struct.pack_into('<H',data,38,2)
        struct.pack_into('<HHII',data,40,0xa002,kind,1,width)
        struct.pack_into('<HHII',data,52,0xa003,kind,1,height)
        u.mem_write(header,bytes(data))
    cases=[]
    # Explicit independently stated aligned dimensions for each native size.
    sizes=[(6000,4000,3376,2120),(4240,2832,2384,1496),(3008,2000,1696,1064)]
    for width,height,h169,h176 in sizes:
        for ratio,expected in [((1,1),(height,height)),((16,9),(width,h169)),((17,6),(width,h176))]:
            for kind in (3,4):
                select(ratio);exif(width,height,kind)
                for pointer in (info,copy):u.mem_write(pointer,b'\xa5'*64)
                u.mem_write(args,struct.pack('<4I',0,0,info,copy))
                assert invoke('raf_info_prepare_hook',args)==0
                before=word(loaded['xt20_capture_crops']);rewrites=word(loaded['xt20_capture_exif_rewrites'])
                original=[width,0,0,width,height,0x6000000,destination]
                result=crop(original)
                ew,eh=expected
                assert result==[width,((width-ew)//2)&~7,((height-eh)//2)&~1,ew,eh,original[5],destination],result
                assert word(loaded['xt20_capture_crops'])==before+1
                assert word(loaded['xt20_capture_exif_rewrites'])==rewrites+1
                assert word(header+48)==ew and word(header+60)==eh
                for pointer in (info,copy):
                    actual=bytes(u.mem_read(pointer,64));wanted=bytearray(b'\xa5'*64)
                    struct.pack_into('<HH',wanted,0x14,ratio[1],ratio[0]);assert actual==wanted
                # Consumed RAF references must not be written again.
                for pointer in (info,copy):u.mem_write(pointer,b'\x5a'*64)
                crop(original)
                assert all(bytes(u.mem_read(p,64))==b'\x5a'*64 for p in (info,copy))
                cases.append(dict(size=[width,height],ratio=ratio,exif_type=kind,result=result,raf_pairs_and_canaries=True))
    select((3,2))
    original=[6000,0,0,6000,4000,0x6000000,destination]
    assert crop(original)==original
    select((1,1))
    guards=[]
    for fields in ([160,0,0,160,120,1,2],[6000,8,0,6000,4000,1,2],
                   [6000,0,2,6000,4000,1,2],[640,0,0,640,480,1,2]):
        assert crop(fields)==fields;guards.append(fields)
    u.mem_write(args,bytes(16));assert invoke('jpeg_encoder_program_hook',args)==0
    select((0,0));assert crop(original)==original
    preview=[320,0,0,320,240,0x6000000,destination];select((1,1))
    u.mem_write(0x119f2f5,b'\0');assert crop(preview)==preview
    u.mem_write(0x119f2f5,b'\1');changed=crop(preview)
    assert changed==[320,56,15,208,208,preview[5],destination]
    report=dict(scope=__doc__,status='PASS',artifacts=hashes,setup=setup,cases=cases,
        unchanged_guards=guards,null_guard=True,invalid_ratio_guard=True,
        supplied_preview_geometry_result=changed,checker_sha256=sha(Path(__file__).read_bytes()),
        hardware_verified=False,encoded_result=False,shot_lifetime_qualified=False,
        preview_letterbox_qualified=False,native_exif_header_qualified=False)
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',main_cases=len(cases),scope='explicit function fixtures only')))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUT)
    main(parser.parse_args().output)
