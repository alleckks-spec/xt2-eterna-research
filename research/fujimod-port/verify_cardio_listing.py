"""Bounded listing adaptation through original X-T2 media/kernel transport.

AI-assisted original checker. Executes native pools/dispatch/media constructors,
native readiness guard/builders/sender/queue copy and compiled original/adapted
listing callbacks. Device context fields and directory entries are explicit
fixtures; callback delivery is an explicit boundary invocation. No mounted FAT,
storage worker execution, elapsed time, full boot or physical camera evidence.
"""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
from elftools.elf.elffile import ELFFile
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_C1_C0_2,UC_ARM_REG_FPEXC)
from unicorn.unicorn_py3.unicorn import uclib


def sha(b):return hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--component',type=Path,required=True)
    p.add_argument('--expect-original-defects',action='store_true');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();stock=a.stock.read_bytes();raw=a.component.read_bytes()
    assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    build=json.loads(a.component.with_name('build.json').read_text());assert sha(raw)==build['elf_sha256']
    assert sha(a.component.with_name('preparation.json').read_bytes())==build['preparation_sha256']
    for path,expected in build['dependencies'].items():assert sha(Path(path).read_bytes())==expected,path
    assert build['original']==a.expect_original_defects
    decoder=Cs(CS_ARCH_ARM,CS_MODE_ARM)
    def instruction(address):return next(decoder.disasm(stock[address:address+4],address))
    for address,code in [(0x964f34,0x1377),(0x9663c8,0x1378)]:
        i=instruction(address);assert i.mnemonic=='movw' and i.op_str.startswith('r3, #') and int(i.op_str.split('#')[1],0)==code
    for address,size in [(0x964f54,60),(0x9663e8,8)]:
        i=instruction(address);assert i.mnemonic=='mov' and i.op_str.startswith('r3, #') and int(i.op_str.split('#')[1],0)==size
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0,(len(stock)+4095)&~4095);u.mem_write(0,stock)
    ram=0x8000000;ret=ram+0xf000;u.mem_map(ram,0x10000)
    u.reg_write(UC_ARM_REG_C1_C0_2,0xf<<20);u.reg_write(UC_ARM_REG_FPEXC,1<<30)
    def word(address):return struct.unpack('<I',u.mem_read(address,4))[0]
    def call(entry,*args):
        context=u.context_save()
        for reg,val in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],list(args)+[0]*4):u.reg_write(reg,val)
        sp=ram+0xe000
        if len(args)>4:u.mem_write(sp,struct.pack('<'+'I'*(len(args)-4),*args[4:]))
        u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_LR,ret)
        u.emu_start(entry,ret,count=2000000)
        assert u.reg_read(UC_ARM_REG_PC)==ret,hex(u.reg_read(UC_ARM_REG_PC))
        assert u.reg_read(UC_ARM_REG_SP)==sp
        result=u.reg_read(UC_ARM_REG_R0);u.context_restore(context);return result
    constructors=[]
    for entry in [0xcf0034,0xcec598,0xcec634]:
        result=call(entry);assert result==0;constructors.append(hex(entry))
    assert word(0x11892a4)==0x950400 and word(0x11892a8)==0xa50400
    assert bytes(u.mem_read(0x9c3544,1))==b'\x78' and bytes(u.mem_read(0xac3544,1))==b'\x7b'
    assert word(0x9c2260)==word(0xac2260)==0
    assert word(0x10ad300+120*4)==88
    elf=ELFFile(io.BytesIO(raw));symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
    for s in elf.iter_sections():
        if not s['sh_flags']&2 or not s['sh_size']:continue
        start,size=s['sh_addr'],s['sh_size'];assert 0x2000000<=start<start+size<=0x2010000
        u.mem_write(start,b'\0'*size if s['sh_type']=='SHT_NOBITS' else s.data())
    def api(name,*args):return call(symbols[name],*args)
    # Constructed module deliberately has no mounted device. Supply only the
    # guard inputs required for the queue/callback assay, never file-read data.
    device=0x9000000;u.mem_map(device,0x17000)
    assert call(0x967490,0)==5  # real constructor left the device absent
    packets=[]
    def receive():
        u.mem_write(ram+0x6000,struct.pack('<3I',0,0,ram+0x6100))
        u.mem_write(ram+0x6100,b'\xa5'*128)
        assert call(0xcefb60,120,ram+0x6000,0)==0
        code,source,dest,size=struct.unpack('<HBBI',u.mem_read(ram+0x6000,8))
        assert source==0 and dest==120 and size in (8,60)
        assert bytes(u.mem_read(ram+0x6100+size,128-size))==b'\xa5'*(128-size)
        payload=bytes(u.mem_read(ram+0x6100,size));packets.append(dict(code=hex(code),bytes=size,source=source,destination=dest))
        return code,payload
    folder,pattern=ram+0x3000,ram+0x3100
    u.mem_write(folder,b'FUJIMOD\\FILMS\0');u.mem_write(pattern,b'*.TXT\0')
    jobs=[ram+0x1000,ram+0x1200];entries=[ram+0x4000,ram+0x4400]
    for j,e in zip(jobs,entries):u.mem_write(j,b'\0'*132);u.mem_write(e,b'\xcc'*80)
    def begin(index):return api('x70_cardio_list',jobs[index],folder,pattern,entries[index],4)
    assert begin(0)==0xffffffff and api('x70_lifetime_live')==0 and word(jobs[0])==0
    u.mem_write(0x9c2260,struct.pack('<I',device))
    assert call(0x967490,0)==0
    first_code=0x1370 if a.expect_original_defects else 0x1377
    next_code=0x1371 if a.expect_original_defects else 0x1378
    assert begin(0)==0
    code,first=receive();assert code==first_code and len(first)==60
    cb_a,details_a=struct.unpack('<2I',first[:8]);bank_a=api('x70_cardio_bank',jobs[0])
    assert 0<=bank_a<4 and api('x70_lifetime_live')==1
    assert first[8:40].split(b'\0',1)[0]==b'A:\\FUJIMOD\\FILMS\\'
    assert first[40:56].split(b'\0',1)[0]==b'*.TXT' and first[56]==1
    # Compare original native builder transport with the compiled mod's fields.
    path=ram+0x3200;u.mem_write(path,first[8:40])
    call(0x964ed0,cb_a,details_a,path,pattern,1,0)
    native_code,native_first=receive()
    assert native_code==0x1377 and native_first[:8]==first[:8]
    for lo,hi in [(8,40),(40,56)]:
        assert native_first[lo:hi].split(b'\0',1)[0]==first[lo:hi].split(b'\0',1)[0]
    assert native_first[56]==first[56]
    call(0x96638c,cb_a,details_a)
    native_next_code,native_next=receive()
    assert native_next_code==0x1378 and native_next==first[:8]
    # Abandon A, start B, then deliver A's late callback. No filesystem handler
    # ran: the fixed synthetic entry is an explicit callback boundary input.
    api('x70_cardio_abandon',jobs[0]);assert word(jobs[0])==3
    def second_request():
        assert begin(1)==0
        code,second=receive();assert code==first_code
        return struct.unpack('<2I',second[:8]),api('x70_cardio_bank',jobs[1])
    if a.expect_original_defects:
        (cb_b,details_b),bank_b=second_request()
        assert bank_a!=bank_b and api('x70_lifetime_live')==2
    else:
        assert word(symbols['x70_cardio_hold'])==bank_a+1
        assert begin(1)==0xffffffff and word(jobs[1])==0
        assert api('x70_lifetime_live')==1
    def entry(address,name):
        u.mem_write(address,b'\0'*100)
        u.mem_write(address,name+b'\0');u.mem_write(address+48,b'\x20')
        u.mem_write(address+52,struct.pack('<I',123))
    entry(details_a,b'A:\\FUJIMOD\\FILMS\\STALE.TXT');call(cb_a,0)
    contaminated=word(jobs[1]+24);stale=word(symbols['x70_cardio_stale'])
    stale_generated_next=None
    if a.expect_original_defects:
        assert cb_a==cb_b and details_a==details_b and contaminated==1 and stale==0
        assert word(symbols['bank_state']+4*bank_a)==3
        old_code,stale_generated_next=receive();assert old_code==next_code
    else:
        assert contaminated==0 and stale==1
        assert word(symbols['bank_state']+4*bank_a)==0
        assert word(symbols['x70_cardio_hold'])==0 and api('x70_lifetime_live')==0
        (cb_b,details_b),bank_b=second_request()
        assert cb_a!=cb_b and details_a==details_b and bank_a!=bank_b
        assert api('x70_lifetime_live')==1
    entry(details_b,b'A:\\FUJIMOD\\FILMS\\GOOD.TXT');call(cb_b,0)
    code,nxt=receive();assert code==next_code and len(nxt)==8
    assert nxt==struct.pack('<2I',cb_b,details_b)
    call(cb_b,5)  # explicit end-of-list boundary; preserved upstream semantics
    expected_count=2 if a.expect_original_defects else 1
    assert word(jobs[1])==2 and word(jobs[1]+8)==0 and word(jobs[1]+24)==expected_count
    final_names=[bytes(u.mem_read(entries[1]+20*i,13)).split(b'\0',1)[0].decode() for i in range(expected_count)]
    assert final_names==(['STALE.TXT','GOOD.TXT'] if a.expect_original_defects else ['GOOD.TXT'])
    for i in range(expected_count):
        assert bytes(u.mem_read(entries[1]+20*i+13,1))==b'\x20'
        assert word(entries[1]+20*i+16)==123
    assert bytes(u.mem_read(entries[1]+20*expected_count,80-20*expected_count))==b'\xcc'*(80-20*expected_count)
    if stale_generated_next:call(struct.unpack('<I',stale_generated_next[:4])[0],5)
    assert api('x70_lifetime_live')==0 and word(symbols['x70_cardio_active'])==0
    # Fixed per-bank state is reusable after both callbacks retire.
    states=list(struct.unpack('<4I',u.mem_read(symbols['bank_state'],16)))
    assert sum(x!=0 for x in states)==int(a.expect_original_defects)
    report=dict(scope=__doc__,status='PASS: reproduced original defects' if a.expect_original_defects else 'PASS: X-T2 listing code/ownership regression',
        original_defects_expected=a.expect_original_defects,constructors=constructors,
        bindings=dict(sender='0x969f24',readiness='0x967490',queue_address='0x9c3544',current_task='0xceed8c'),
        native_codes=['0x1377','0x1378'],component_codes=[hex(first_code),hex(next_code)],
        first_payload_bytes=60,next_payload_bytes=8,details_bytes=100,native_queue_bytes=88,
        native_details_layout_qualified=False,
        native_builder_payload_fields_match=True,packets=packets,
        stale_callback_changed_new_job=bool(contaminated),stale_callbacks_counted=stale,
        distinct_callback_banks=cb_a!=cb_b,shared_output_buffer=details_a==details_b,
        abandoned_listing_holds_queue=not a.expect_original_defects,
        final_entry_names=final_names,remaining_bank_states=states,outstanding_callbacks=0,
        supplied_device_context=True,synthetic_directory_entries=True,callback_delivery_supplied=True,
        absent_device_refused=True,
        mounted_media=False,native_storage_worker_executed=False,task_scheduling=False,
        internal_api_stubs=0,common_candidate_changed=False,hardware_verified=False,
        elf_sha256=sha(raw),stock_sha256=sha(stock),checker_sha256=sha(Path(__file__).read_bytes()),
        build_sha256=sha(a.component.with_name('build.json').read_bytes()),unicorn_sha256=sha(Path(uclib._name).read_bytes()))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],entries=final_names,remaining_banks=sum(x!=0 for x in states))))


if __name__=='__main__':main()
