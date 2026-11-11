"""Native request producer/worker through the installed XPP JPEG crop hook.

Uses existing SDK prerequisites and descriptor probe. Selected ratio, camera
geometry, blank destination-header memory and worker ownership header are explicit inputs. The native worker
builds its descriptor, enters the real patched function, executes the upstream
hook and original prologue. Stops before hardware programming. No image source,
successful encode, preview letterbox, Exif output or shot lifetime is claimed.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import probe_sdk_native_encoder_descriptor as descriptor

ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'aspect-capture-component-v2-unverified'
CHOOSER=ROOT/'native-chooser-component-unverified'


def main(kind,output):
    # Reuse the exact existing descriptor adapter up to its generated body.
    generator=inspect.getsource(descriptor.main)
    anchor='    namespace=dict(vars(setup.native),OUT=out)\n'
    assert generator.count(anchor)==1
    generator=generator.split(anchor)[0]+'    return source\n'
    scope=dict(vars(descriptor));exec(compile(generator,str(descriptor.__file__)+'::source-only','exec'),scope)
    source=scope['main'](kind,output)
    anchor='regions = [(0, 0x3000000), (RAM, 0x10000), (0xe000000, 0x100000)]'
    assert source.count(anchor)==1
    # Back the observed native destination addresses with declared blank RAM.
    # The FS mount buffer stays exactly 1 MiB. No Exif or encoded data is added.
    source=source.replace(anchor,anchor[:-1]+', (0x9200000,0x100000), (0xaa00000,0x200000)]')
    anchor='        # Same geometry boundary as the existing native JPEG producer assay.\n'
    assert source.count(anchor)==1
    install='''        import io
        from elftools.elf.elffile import ELFFile
        crop_symbols={}
        for directory,begin,end in [(CHOOSER,0x2000000,0x2040000),(BUILD,0x2040000,0x2080000)]:
            raw=(directory/'component.elf').read_bytes()
            elf=ELFFile(io.BytesIO(raw))
            crop_symbols.update({s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols() if s['st_shndx']!='SHN_UNDEF'})
            for section in elf.iter_sections():
                if section['sh_flags']&2 and section['sh_size'] and begin<=section['sh_addr']<end:
                    cpu.mem_write(section['sh_addr'],bytes(section['sh_size']) if section['sh_type']=='SHT_NOBITS' else section.data())
            if directory==BUILD:
                patches=[]
                for hook,address,target,expected,name in struct.iter_unpack('<5I',elf.get_section_by_name('.x70mod.hooks').data()):
                    if address!=0x15b2244:continue
                    assert hook==5 and word(address)==expected==0xe92d4870
                    delta=target-address-8
                    assert delta%4==0 and -(1<<25)<=delta<(1<<25)
                    cpu.mem_write(address,struct.pack('<I',0xea000000|((delta>>2)&0xffffff)))
                    patches.append(dict(address=hex(address),target=hex(target)))
                assert len(patches)==1
        cpu.mem_write(crop_symbols['shape_aspect_ratio'],struct.pack('<HH',1,1))
        stages.append(dict(installed_crop_hooks=patches,selected_ratio_fixture=[1,1]))
'''
    source=source.replace(anchor,install+anchor)
    source=source.replace('stop=0x15b2244','stop=0x15b2248')
    source=source.replace('stopped_before_program=True','stopped_after_original_prologue=True,stopped_before_hardware_programming=True,blank_header_ram_supplied=True')
    anchor='        stages.append(dict(native_encoder_descriptor=hex(pointer),program_entry=hex(0x15b2244),\n'
    assert source.count(anchor)==1
    source=source.replace(anchor,"        assert fields[1:5]==EXPECTED_WINDOW,fields\n"+anchor)
    namespace=dict(vars(descriptor.setup.native),OUT=Path(output),BUILD=BUILD,CHOOSER=CHOOSER,
        EXPECTED_WINDOW=[[0,0,160,120],[1000,0,4000,4000],[56,15,208,208]][kind])
    exec(compile(source,str(__file__)+'::native-installed-crop','exec'),namespace)
    try:namespace['main']()
    finally:
        path=Path(output)/'probe.json';report=json.loads(path.read_text())
        report.update(scope=__doc__,adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            descriptor_adapter_sha256=hashlib.sha256(Path(descriptor.__file__).read_bytes()).hexdigest(),
            adapted_body_sha256=hashlib.sha256(source.encode()).hexdigest(),request_kind=kind,
            component_sha256=hashlib.sha256((BUILD/'component.elf').read_bytes()).hexdigest(),
            encoded_result=False,shot_lifetime_qualified=False)
        path.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(error=report['error'],last=report['stages'][-1])))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kind',type=int,choices=[0,1],default=1)
    p.add_argument('--output',type=Path,default=ROOT/'sdk-native-aspect-main-unverified')
    a=p.parse_args();main(a.kind,a.output)
