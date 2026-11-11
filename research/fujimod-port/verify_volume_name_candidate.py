"""Check the exact delivered formatter wrapper, codec and resized memory edits.

The cached calendar fields and card-write result/data sink are explicit
fixtures; the real calendar reader and lock execute. No native filesystem success,
physical write, DMA/cache behavior,
scheduled capture, general mod menu, full startup or camera result is claimed.
Reuse the existing function execution harness; do not create a new SD model.
"""
import argparse
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
from verify_ordinary_platform_processing import actual_factory
from verify_ordinary_platform_card import main as verify_card
from verify_film_menu_navigation import invoke
from build_volume_name_candidate import ROOT, sha

RAM=0x8000000
BUILD=ROOT/'volume-name-resized-build-unverified'


def verify(build_directory=BUILD, output_directory=None, words=68):
    build=Path(build_directory)
    out=Path(output_directory) if output_directory else ROOT/'volume-name-check-unverified'
    out.mkdir(exist_ok=True)
    verify_card(build,words)
    image=(Path(str(build)+'-card')/'ffboot.bin').read_bytes()
    manifest=json.loads((build/'manifest.json').read_text())
    with (build/'mods.elf').open('rb') as stream:
        elf=ELFFile(stream)
        symbols={s.name:int(s['st_value']) for s in elf.get_section_by_name('.symtab').iter_symbols() if s.name}
    u=actual_factory()
    u.mem_write(0,image)
    def word(a):return int.from_bytes(u.mem_read(a,4),'little')
    def call(entry,*args):
        result=invoke(u,entry,*args,instruction_limit=5000000)
        assert u.reg_read(UC_ARM_REG_SP)==RAM+0xe000
        return result
    def value(name):return word(symbols[name])
    fields=[26,11,11,12,34,56]
    sink=[]
    transport_status=[0]
    def write(uc,pc,size,data):
        args=[uc.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]]
        pointer=word(uc.reg_read(UC_ARM_REG_SP))
        sink.append(dict(device=args[0],block=args[1],count=args[2]|args[3]<<32,
                         payload=bytes(uc.mem_read(pointer,512)),pointer=pointer))
        uc.reg_write(UC_ARM_REG_R0,transport_status[0])
        uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
    # Native cached calendar path, no replacement calendar success callback.
    u.mem_write(0x1004b10,bytes(4));u.mem_write(0x1004b34,bytes(fields))
    u.mem_write(0x12206e0,b'\0')
    assert call(symbols['calendar_read'],RAM+0x6000)==0
    assert bytes(u.mem_read(RAM+0x6000,6))==bytes(fields)
    write_hook=u.hook_add(UC_HOOK_CODE,write,begin=symbols['card_write_pages_hook_stock'],end=symbols['card_write_pages_hook_stock'])
    # Decode/encode the exact linked owner, not a replacement settings object.
    owner=symbols['save_data_settings'];decode=word(owner+8);encode=word(owner+12)
    registered=[word(a) for a in range(symbols['__xpp_settings_files_start'],symbols['__xpp_settings_files_end'],4)]
    assert registered.count(owner)==1
    codec=[]
    for document,expected in [('{}',(0,1)),('{"date_folders":true,"date_card_name":false}',(1,0)),
                              ('{"date_card_name":true}',(0,1))]:
        blob=document.encode();u.mem_write(RAM+0x1000,blob+b'\0')
        assert call(decode,RAM+0x1000,len(blob))==1
        assert (value('save_data_date_folders'),value('save_data_date_card_name'))==expected
        u.mem_write(RAM+0x2000,struct.pack('<9I',RAM+0x3000,128,0,0,0,0,0,0,0))
        assert call(encode,RAM+0x2000)==0
        assert call(symbols['x70_json_finish'],RAM+0x2000)<128
        encoded=bytes(u.mem_read(RAM+0x3000,128)).split(b'\0',1)[0]
        parsed=json.loads(encoded)
        assert parsed.get('date_folders',False)==bool(expected[0])
        assert parsed.get('date_card_name',True)==bool(expected[1])
        codec.append(dict(document=document,values=expected,encoded=encoded.decode()))
    before=(value('save_data_date_folders'),value('save_data_date_card_name'))
    blob=b'{"date_card_name":"bad"}';u.mem_write(RAM+0x1000,blob+b'\0')
    assert call(decode,RAM+0x1000,len(blob))==0xffffffea
    assert (value('save_data_date_folders'),value('save_data_date_card_name'))==before
    # Preserve the original FORMAT CARD NAME declaration while exposing its missing consumer.
    item=symbols['sd_volume_name_item']
    assert word(item+12)==owner and word(item+16)==symbols['save_data_date_card_name']
    assert symbols['__x70mod_menu_items_start']<=item<symbols['__x70mod_menu_items_end']
    assert 'xpp_menu_entries_boot' not in symbols
    boot=bytearray(512)
    boot[0xd]=8;struct.pack_into('<H',boot,0xe,32);boot[0x10]=2
    struct.pack_into('<I',boot,0x1c,8192);struct.pack_into('<I',boot,0x24,123)
    struct.pack_into('<I',boot,0x2c,2);struct.pack_into('<H',boot,0x32,6)
    boot[0x42]=0x29;boot[0x47:0x52]=b'NO NAME    ';boot[0x52:0x5a]=b'FAT32   '
    struct.pack_into('<H',boot,0x1fe,0xaa55)
    root=8192+32+2*123
    cases=[]
    definitions=[dict(name='primary',block=8192),dict(name='backup',block=8198),
        dict(name='off',block=8192,enabled=0),dict(name='multi-page',block=8192,count=2),
        dict(name='high-count',block=8192,high=1),dict(name='null-buffer',block=8192,null=True),
        dict(name='signature',block=8192,mutate=(0x1fe,0)),dict(name='extended',block=8192,mutate=(0x42,0)),
        dict(name='exfat',block=8192,mutate=(0x52,ord('E'))),dict(name='foreign-block',block=9),
        dict(name='primary-error',block=8192,status=5),dict(name='backup-error',block=8198,status=7),
        dict(name='year-2000',block=8192,year=0),dict(name='year-2099',block=8192,year=99)]
    for definition in definitions:
        case=dict(enabled=1,count=1,high=0,status=0,year=26,null=False)|definition
        data=bytearray(boot)
        if 'mutate' in case:data[case['mutate'][0]]=case['mutate'][1]
        fields[0]=case['year'];u.mem_write(0x1004b34,bytes(fields))
        transport_status[0]=case['status'];sink.clear()
        u.mem_write(symbols['save_data_date_card_name'],struct.pack('<I',case['enabled']))
        buffer=RAM+0x5000;args=RAM+0x4800
        u.mem_write(buffer-16,b'\xa5'*16+data+b'\x5a'*16)
        arguments=[1,case['block'],case['count'],case['high'],0 if case['null'] else buffer]
        u.mem_write(args,struct.pack('<5I',*arguments))
        calls=value('sd_volume_name_calls');labeled=value('sd_volume_name_labeled')
        result=call(symbols['card_write_pages_hook'],args)
        active=case['name'] in ['primary','backup','primary-error','backup-error','year-2000','year-2099']
        assert result==int(active),(case,result)
        assert value('sd_volume_name_calls')==calls+1
        assert value('sd_volume_name_labeled')==labeled+int(active)
        assert bytes(u.mem_read(buffer-16,544))==b'\xa5'*16+data+b'\x5a'*16
        expected_writes=(2 if case['block']==8192 and case['status']==0 else 1) if active else 0
        assert len(sink)==expected_writes,(case,sink)
        label=f'20{fields[0]:02d}-11-11 '.encode()
        if active:
            assert word(args)==case['status']
            assert (sink[0]['device'],sink[0]['block'],sink[0]['count'])==(1,case['block'],1)
            expected=bytearray(data);expected[0x47:0x52]=label
            assert sink[0]['payload']==expected
            if expected_writes==2:
                assert (sink[1]['device'],sink[1]['block'],sink[1]['count'])==(1,root,1)
                assert sink[1]['payload']==label+b'\x08'+bytes(500)
        cases.append(case|dict(answered=bool(result),lower_writes=[{k:v for k,v in row.items() if k!='payload'} for row in sink]))
    # Execute the delivered entry branch/thunk, including its fifth stack argument.
    u.mem_write(symbols['save_data_date_card_name'],struct.pack('<I',1))
    u.mem_write(RAM+0x5000,bytes(boot));fields[0]=26;u.mem_write(0x1004b34,bytes(fields))
    transport_status[0]=0;sink.clear()
    for reg,val in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],[1,8192,1,0]):u.reg_write(reg,val)
    saved={r:0x61000000+i for i,r in enumerate([UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11])}
    for r,v in saved.items():u.reg_write(r,v)
    u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.mem_write(RAM+0xe000,struct.pack('<I',RAM+0x5000))
    return_address=RAM+0xf000;u.reg_write(UC_ARM_REG_LR,return_address)
    u.emu_start(symbols['card_write_pages'],return_address,count=100000)
    assert u.reg_read(UC_ARM_REG_PC)==return_address and u.reg_read(UC_ARM_REG_SP)==RAM+0xe000
    assert all(u.reg_read(r)==v for r,v in saved.items()) and len(sink)==2
    u.hook_del(write_hook)
    # Exercise the exact delivered BSS split and heap ceiling, without replacing native fill/_sbrk.
    region=manifest['regions'][0];start=int(region['address'],0);end=0x13c0000
    bss_start,bss_end=0xfb1000,0x13d4000
    payload=bytes(u.mem_read(start,end-start))
    u.mem_write(bss_start,b'\xa5'*(start-bss_start));u.mem_write(end,b'\xa5'*(bss_end-end))
    u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.emu_start(0xcf7c78,0xcf7c94,count=4000000)
    assert u.reg_read(UC_ARM_REG_PC)==0xcf7c94
    assert bytes(u.mem_read(bss_start,start-bss_start))==bytes(start-bss_start)
    assert bytes(u.mem_read(start,end-start))==payload
    assert bytes(u.mem_read(end,bss_end-end))==bytes(bss_end-end)
    errno=RAM+0x4000;u.mem_write(0xfae334,struct.pack('<I',start-64));u.mem_write(errno,bytes(4))
    assert call(0xcf45a8,errno,33)==0xffffffff and word(errno)==12 and word(0xfae334)==start-64
    report=dict(scope=__doc__,status='PASS',elf_sha256=sha((build/'mods.elf').read_bytes()),ffboot_sha256=sha(image),
        codec_cases=codec,invalid_codec_preserves_values=True,settings_owner_registered_once=True,
        native_calendar_and_lock=True,calendar_fixture=dict(cache='0x1004b34',mode='0x12206e0',fields=fields),
        format_cases=cases,delivered_entry_fifth_argument_and_callee_saved=True,
        bss_prefix_suffix_zero=True,reserved_payload_survives=True,crossing_heap_allocation_refused=True,
        reservation_start=hex(start),reservation_size=end-start,heap_capacity=start-0x12532fc,
        menu_declaration_retained=True,general_mod_menu_engine_exercised=False,hardware_verified=False,
        checker_sha256=sha(Path(__file__).read_bytes()))
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',cases=len(cases),codec_cases=len(codec)+1,elf_sha256=report['elf_sha256'])))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=BUILD)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--words',type=int,default=68)
    args=parser.parse_args();verify(args.build,args.output,args.words)
