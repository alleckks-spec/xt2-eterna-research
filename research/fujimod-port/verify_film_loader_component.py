"""Bounded upstream loader -> native timer -> native directory error -> retry.

AI-assisted original checker. Reuses the frozen native-worker assay. Device
presence and REC-idle bytes are explicit input fixtures; native constructors,
software-timer tick handler, storage queue workers and C callbacks execute.
No mounted FAT, physical timer IRQ, scheduler ownership or camera claim.
"""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0
from verify_cardio_native_worker import Assay


def sha(data): return hashlib.sha256(data).hexdigest()


def load(m,raw,low,high):
    elf=ELFFile(io.BytesIO(raw))
    for s in elf.iter_sections():
        if not s['sh_flags']&2 or not s['sh_size'] or s.name in ['.x70mod.hooks','.x70mod.strings']:continue
        start,size=s['sh_addr'],s['sh_size'];assert low<=start<start+size<=high
        m.u.mem_write(start,bytes(size) if s['sh_type']=='SHT_NOBITS' else s.data())
    return {s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['stock','baseline','common','component','output']:p.add_argument('--'+n,required=True,type=Path)
    a=p.parse_args();stock=a.stock.read_bytes();common=a.common.read_bytes();component=a.component.read_bytes()
    assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    build=json.loads(a.component.with_name('build.json').read_text())
    assert sha(component)==build['elf_sha256'] and sha(common)==build['common_sha256']
    for path,digest in build['dependencies'].items():assert sha(Path(path).read_bytes())==digest,path
    m=Assay(stock,a.baseline.read_bytes())
    load(m,common,0x1390000,0x13c0000)
    m.symbols=load(m,component,0x2100000,0x2140000)
    m.callbacks=[]
    for i in range(4):
        pc=m.symbols[f'cb_list_{i}']
        m.u.hook_add(UC_HOOK_CODE,lambda uc,a,z,d:m.callbacks.append(uc.reg_read(UC_ARM_REG_R0)),begin=pc,end=pc)
    constructors=[]
    for entry in [0x14d6fd8,0xcdf570]:
        result=m.call(entry);assert result==0,(hex(entry),result)
        constructors.append(hex(entry))
    # Actual shared parser + generated schema + supplied source profiles.
    # The input is a host-supplied document, not a file claimed read from SD.
    parser_cases=[];user=0x8007000;text=0x8007800
    for icon,expected in [('custom',0),('provia',0),('unknown-icon',0xfffffffc)]:
        doc=json.dumps(dict(name='Port check',base='provia',icon=icon)).encode()
        m.u.mem_write(user,bytes(556));m.u.mem_write(user,struct.pack('<I',200))
        m.u.mem_write(user+406,b'200TEST.JSN\0');m.u.mem_write(text,doc+b'\0')
        result=m.api('film_parse',user,text,len(doc));assert result==expected,(icon,hex(result))
        if result==0:
            assert m.word(user)==200 and bytes(m.u.mem_read(user+378,11))==b'Port check\0'
            assert (m.word(user+120),m.word(user+124))==(0,0)
        parser_cases.append(dict(icon=icon,status=result))
    # Explicit loader gate inputs, not reconstructed camera startup state.
    for n,v in dict(ui_mode=3,ui_capture_state=0,ui_capture_block=0,raw_backup_flag=0,menu_open=0).items():
        m.u.mem_write(m.symbols[n],bytes([v]))
    m.presence(True)
    loader=m.symbols['film_loader']
    def state():return list(struct.unpack('<21I',m.u.mem_read(loader,84)))
    def ticks(n):
        for _ in range(n):m.call(0xcdf968)
    m.api('film_loader_boot');print('boot',state(),flush=True)
    assert state()[3]==0 and state()[4]!=0
    ticks(121);print('first tick',state(),flush=True)
    assert state()[0]==1 and state()[1]==1
    assert m.word(m.symbols['x70_cardio_active'])!=0
    m.presence(False);m.pump();m.presence(True)
    assert m.callbacks==[5]
    ticks(5);print('after error poll',state(),flush=True)
    assert state()[0]==5 and state()[11]==5 and state()[17]==1 and state()[18]==10
    assert m.api('film_loader_ready')==0 and m.api('film_loader_idle')==1
    assert m.word(m.symbols['film_users'])==0 and m.word(m.symbols['film_card_count'])==0
    failed=state()
    # 121 native ticks per 300ms callback. The ten callbacks, not host state
    # writes, must consume retry_ticks and submit the next listing.
    ticks(121*9);assert state()[0]==5 and state()[18]==1
    ticks(121);print('retry',state(),flush=True)
    assert state()[0]==1 and state()[17]==1 and m.word(m.symbols['x70_cardio_active'])!=0
    report=dict(scope=__doc__,status='PASS',failed=failed,retry=state(),parser_cases=parser_cases,
                native_callback_statuses=m.callbacks,constructors=constructors,
                scratch_call_task_context=m.call(0xceed8c),native_tick_handler='0xcdf968',
                internal_api_stubs=0,worker_entries_harness_invoked=True,
                rec_idle_fixture=True,device_presence_fixture=True,hardware_verified=False,
                common_candidate_changed=False,elf_sha256=sha(component),common_sha256=sha(common),
                checker_sha256=sha(Path(__file__).read_bytes()))
    report['assay_dependencies']={str(path):sha(path.read_bytes()) for path in [
        Path(__file__).with_name('verify_cardio_native_worker.py'),
        Path(__file__).parents[2]/'scripts/kernel_timer_initialization.py']}
    report['baseline_sha256']=sha(a.baseline.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'])


if __name__=='__main__':main()
