"""Bounded native selection -> original JPEG Max thunk -> stock X-T2 tables.

Exact ordinary common ELF. Existing supplied stock RAM, calibration, mode and
transport boundaries; manual init. No storage/timer startup, actual descriptor
producer, overlay loader, JPEG engine, image file or physical camera evidence.
Original AI-assisted checker; no private upstream code or coefficients embedded.
"""
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_SP
from verify_ordinary_platform_nr import load,ROOT,START,END,sha
from verify_ordinary_platform_card import main as verify_card
from verify_ordinary_platform_processing import actual_factory,initialize,TRANSPORT
from verify_film_menu_navigation import invoke

BUILD=ROOT/'jpeg-max-build-unverified'
OUT=ROOT/'jpeg-max-check-unverified'
RAM=0x8000000
PROPERTY=0x1f1
ENTRY=0x2a232e8


def main():
    verify_card(BUILD,63)
    sections,symbols,manifest=load(BUILD,63)
    u=actual_factory()
    state=[]
    for a,data,name,size in sections:
        if name in ('.x70mod.hooks','.x70mod.strings'):continue
        assert START<=a<a+size<=END
        u.mem_write(a,data)
        if name in ('.data','.bss','.x70mod.shared'):state.append((a,a+size))
    for e in manifest['edits']:
        assert bytes(u.mem_read(e['address'],4))==struct.pack('<I',e['expected']),hex(e['address'])
        u.mem_write(e['address'],struct.pack('<I',e['value']))
    phase=['init'];visited=set();writes=0
    def watch(uc,access,a,n,v,d):
        nonlocal writes
        ranges=[(RAM,RAM+0x10000),*state]
        if phase[0] in ('init','select'):
            ranges += [(0xffd000,0x1000000),(0x1180000,0x1235000),(0x1ab0000,0x1ad0000)]
        else:
            ranges += [(0x22f2ec8,0x22f2f08),(0x22f2708,0x22f2748),(0x1e0e1ad,0x1e0e1ec)]
        assert any(lo<=a and a+n<=hi for lo,hi in ranges),(phase[0],hex(uc.reg_read(UC_ARM_REG_PC)),hex(a),n)
        writes+=1
    u.hook_add(UC_HOOK_MEM_WRITE,watch)
    u.hook_add(UC_HOOK_CODE,lambda uc,a,n,d:visited.add(a))
    def call(uc,entry,*args):
        result=invoke(uc,entry,*args,instruction_limit=3000000)
        assert uc.reg_read(UC_ARM_REG_SP)==RAM+0xe000
        return result
    initialize(u,symbols,call,3)
    def word(name):return int.from_bytes(u.mem_read(symbols[name],4),'little')
    assert word('jpeg_max_status')==word('nr_xt20_status')==0
    menus=[]
    for kind in ['menu','fn','quick']:
        address=symbols[f'xpp_stock_quality_{kind}_rows']
        keys=[int.from_bytes(u.mem_read(address+i*8,4),'little') for i in range(8)]
        assert keys==[0,1,2,3,4,6,7,0x7ffffffe],(kind,keys)
        menus.append(dict(kind=kind,keys=keys))
    def select(key):
        phase[0]='select';u.mem_write(symbols['ui_mode'],b'\x03')
        call(u,0x154b700,PROPERTY,key)
        stored=call(u,0xb510b8,PROPERTY,0)
        assert stored==({6:0,7:2}.get(key,key)),(key,stored)
        assert word('jpeg_max_enabled')==int(key in (6,7))
        assert word('xpp_menu_stock_status')==0
        phase[0]='tables'
        return stored
    definitions=[]
    for key in (6,7):
        definitions.append(dict(key=key))
        for field,value in [('kind',0),('kind',2),('tag',0),('attempts',9),
                            ('index',2),('width',640),('enabled',0),('enabled',2),
                            ('option',2),('mode',2),('mode',4),('mode',5),('mode',6)]:
            definitions.append(dict(key=key,**{field:value}))
    definitions += [dict(key=key) for key in (0,1,2,3,4)]
    records=[]
    request=RAM+0x1000;channel=request+0xa0
    output=[0x22f2ec8,0x22f2708]
    tables=[bytes(u.mem_read(a,64)) for a in (0x197089c,0x197085c,0x19708dc)]
    order=bytes(u.mem_read(0x197091c,64))
    for overrides in definitions:
        case=dict(key=6,kind=1,tag=4,attempts=10,index=1,width=6000,
                  enabled=1,option=1,mode=3,scale=64,alternate=0)|overrides
        stored=select(case['key'])
        u.mem_write(symbols['ui_mode'],bytes([case['mode']]))
        u.mem_write(request-16,b'\xcc'*(0x100+32))
        u.mem_write(request,bytes(0x100))
        for offset,value in [(4,case['attempts']),(8,case['index']),(12,case['kind']),
                             (0xd8,case['tag']),(0xac,case['width']),(0xb0,4000),
                             (0x20+8*case['index'],case['scale'])]:
            u.mem_write(request+offset,struct.pack('<I',value))
        u.mem_write(channel+0x29,bytes([case['enabled']]))
        for dest in output:u.mem_write(dest-16,b'\xa5'*96)
        before=word('jpeg_max_encodes')
        call(u,ENTRY,channel,case['scale'],case['option'],case['alternate'])
        changed=(case['key'] in (6,7) and case['mode']==3 and case['enabled']==1 and
                 case['kind']==1 and case['tag']==4 and case['attempts']==10 and
                 case['index']==1 and case['option']==1 and case['width']>640)
        assert word('jpeg_max_encodes')==before+int(changed)
        history=int.from_bytes(u.mem_read(request+0x20+8*case['index'],4),'little')
        scale=16 if changed else case['scale']
        assert history==scale
        for i,dest in enumerate(output):
            actual=bytes(u.mem_read(dest,64))
            if case['enabled']==1:
                base=tables[0 if i==0 else (1 if case['alternate'] else 2)]
                expected=bytes([1]+[max(1,min(255,(scale*case['option']*base[j])>>10)) for j in order[1:]])
            else:expected=b'\xa5'*64
            assert actual==expected,case
            assert bytes(u.mem_read(dest-16,16))==bytes(u.mem_read(dest+64,16))==b'\xa5'*16
        assert bytes(u.mem_read(request-16,16))==bytes(u.mem_read(request+0x100,16))==b'\xcc'*16
        records.append(case|dict(stored=stored,changed=changed,history_scale=history))
    edit=next(e for e in manifest['edits'] if e['address']==ENTRY)
    disp=(edit['value']&0xffffff)<<2
    if disp&0x2000000:disp-=0x4000000
    assert ENTRY+8+disp in visited
    assert word('jpeg_max_encodes')==2
    OUT.mkdir(exist_ok=True)
    report=dict(scope=__doc__,status='PASS: exact common ELF JPEG selection/table boundary',
        elf_sha256=manifest['elf_sha256'],menus=menus,cases=records,cpu_writes=writes,
        native_selection=True,native_table_builder=True,entry_thunk_executed=True,
        transport_fixtures=TRANSPORT,hardware_verified=False,accepted=False,
        inputs=manifest['dependency_sha256']|{str(Path(__file__)):sha(Path(__file__).read_bytes())})
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(cases=len(records),menus=len(menus),encodes=word('jpeg_max_encodes'),elf_sha256=manifest['elf_sha256'])))


if __name__=='__main__':main()
