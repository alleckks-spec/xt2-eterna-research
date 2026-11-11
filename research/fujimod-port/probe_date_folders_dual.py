"""Qualify both native catalog owners and ordinary CEC148 arbitration.

Reuse the existing constructor and post-enumeration native scan fixture. The B
owner is initialized by its own native command handlers, not an alias of A.
No mount completion, ready field or successful filesystem result is supplied.
Original AI-assisted native function probe; no camera operation.
"""
import argparse
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
from probe_date_folders_native import setup,ROOT,RAM,CONTEXT,CONTEXT_BYTES
from build_modular_candidate import sha

B_CONTEXT=CONTEXT+0x20000
DELTA=0x100000


def add_b(m):
    u=m['u'];ex=m['execute_to'];word=m['word'];call=m['call']
    u.mem_map(B_CONTEXT-0x1000,0x1a000)
    u.mem_write(B_CONTEXT-16,b'\x5a'*16+b'\xa5'*CONTEXT_BYTES+b'\x5a'*16)
    registration=[]
    def stores(uc,access,a,n,v,d):
        if a==0xac2260:registration.append(dict(pc=hex(uc.reg_read(UC_ARM_REG_PC)),value=v))
        if max(a,B_CONTEXT-16)<min(a+n,B_CONTEXT+CONTEXT_BYTES+16):
            assert B_CONTEXT<=a and a+n<=B_CONTEXT+CONTEXT_BYTES
    u.hook_add(UC_HOOK_MEM_WRITE,stores)
    req,params=RAM+0x7000,RAM+0x7100
    u.mem_write(req,bytes(64));u.mem_write(req+8,struct.pack('<I',params))
    data=bytearray(0x40);struct.pack_into('<I',data,4,B_CONTEXT)
    data[0x15]=1;struct.pack_into('<I',data,0x18,1)
    data[0x1c:0x20]=b'DSCF';data[0x20:0x25]=b'_FUJI';data[0x34]=ord('B')
    u.mem_write(params,bytes(data))
    ex(0xa69348,0xa694d0,req)
    assert word(0xac2260)==B_CONTEXT
    assert registration==[dict(pc='0xa69428',value=B_CONTEXT)]
    # B's own scan-command frame and catalog iteration boundaries.
    scan_req,scan_params=RAM+0x7200,RAM+0x7300
    u.mem_write(scan_req,bytes(32));u.mem_write(scan_req+8,struct.pack('<I',scan_params))
    data=bytearray(16);data[8]=1;data[9]=1;u.mem_write(scan_params,bytes(data))
    parent,pfp,_=ex(0xa64274,0xa6384c,scan_req)
    frame,fp,_=ex(0xa5bf50,0xa5c02c)
    def directory(number,suffix,cluster):
        nonlocal frame,fp
        entry=bytearray(32);entry[:11]=f'{number:03d}{suffix}   '.encode();entry[11]=0x10
        struct.pack_into('<H',entry,0x1a,cluster);u.mem_write(fp-0x3c,bytes(entry))
        frame,fp,stop=ex(0xa5c070,0xa5c1e8,frame=frame,allowed_stops=(0xa5c02c,))
        assert stop==0xa5c1e8
        assert word(B_CONTEXT+0x2598+4*number)==cluster
        assert bytes(u.mem_read(B_CONTEXT+0x16c00+5*number,5))==suffix.encode()
    def summary():
        nonlocal frame,fp
        frame,fp,_=ex(0xa5c1ec,0xa5c294,frame=frame)
        return dict(max_folder=word(B_CONTEXT+0x20fc),largest_matching=word(B_CONTEXT+0x214c))
    def file_summary(folder,file):
        pf,pfp,_=ex(0xa6385c,0xa63984,frame=parent)
        ff,ffp,_=ex(0xa63984,0xa625dc,frame=pf)
        ff,ffp,_=ex(0xa625f0,0xa62614,frame=ff)
        entry=bytearray(32);entry[:11]=f'DSCF{file:04d}JPG'.encode();entry[11]=0x20
        struct.pack_into('<H',entry,0x1a,30);u.mem_write(ffp-0x44,bytes(entry))
        ff,ffp,_=ex(0xa6266c,0xa62614,frame=ff)
        aggregate=bytes(u.mem_read(pfp-0x68,24))
        assert struct.unpack_from('<I',aggregate,4)[0]==file
        ex(0xa63994,0xa63b9c,frame=pf)
        assert word(B_CONTEXT+0x2100)==file
        assert int.from_bytes(u.mem_read(B_CONTEXT+0x216a,2),'little')==file
        return dict(folder=folder,file=file,aggregate=aggregate.hex())
    return dict(directory=directory,summary=summary,file_summary=file_summary,registration=registration)


def run_case(build,afolder,bfolder,afile,bfile,*,enabled=None,asuffix="_FUJI",bsuffix="_FUJI",refusal_owner=None,return_machine=False,calendar=(26,11,11,12,34,56),initial_pair=(100,1),expected_errors=None):
    m=setup(build);u=m['u'];call=m['call'];word=m['word'];b=add_b(m)
    
    if afolder:m['publish_directory'](f'{afolder:03d}{asuffix}   '.encode(),10)
    a_summary=m['summarize']()
    assert call(0xceaba0,afolder or 100)==0 and call(0xcea990,afile)==0
    a_files=m['publish_file_summary'](afolder,afile) if afolder and afile else None
    
    if bfolder:b['directory'](bfolder,bsuffix,20)
    b_summary=b['summary']()
    assert call(0xceaba0,bfolder or 100)==0 and call(0xcea990,bfile)==0
    b_files=b['file_summary'](bfolder,bfile) if bfolder and bfile else None
    assert call(0xceaba0,initial_pair[0])==0 and call(0xcea990,initial_pair[1])==0
    if enabled is not None:
        payload=json.dumps(dict(date_folders=enabled)).encode()
        u.mem_write(RAM+0x4000,payload)
        decoder=word(m['symbols']['save_data_settings']+8)
        assert call(decoder,RAM+0x4000,len(payload))==1
        u.mem_write(0x1004b34,bytes(calendar))
    refusal=None
    if refusal_owner is not None:
        delta=0 if refusal_owner=='a' else DELTA
        frame,fp,_=m['execute_to'](0x966cfc+delta,0x966d14+delta,0,0)
        # Explicit lower-boundary native device-status snapshot. Stop before
        # the device query; no API result or callback is replaced.
        packet=bytearray(0x40);packet[4]=1
        u.mem_write(fp-0x48,bytes(packet))
        m['execute_to'](0x966d18+delta,0x966d64+delta,frame=frame)
        context=CONTEXT if refusal_owner=='a' else B_CONTEXT
        assert word(context+0x16b6c)==1
        refusal=dict(owner=refusal_owner,status_packet=packet.hex(),native_flags=1,
                     boundary='device-status record publication, physical query not run')
    calls=[];counter_writes=[]
    def observe_writes(uc,access,a,n,v,d):
        if max(a,0x10a8c00)<min(a+n,0x10a8c06):
            counter_writes.append(dict(pc=hex(uc.reg_read(UC_ARM_REG_PC)),address=hex(a),bytes=n,value=v))
    u.hook_add(UC_HOOK_MEM_WRITE,observe_writes)

    def observe(uc,pc,n,d):
        calls.append(dict(pc=hex(pc),args=[uc.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]]))
    for pc in [0xcec148,0x959398,0xa59398,0xcebf50]:u.hook_add(UC_HOOK_CODE,observe,begin=pc,end=pc)
    results=[]
    for drive in [0x41,0x41,0x42,0x42,0xffffffff,0xffffffff]:
        out=RAM+0x5000;u.mem_write(out,b'\xcc'*0xc4);before=len(calls);writes_before=len(counter_writes);pair_before=bytes(u.mem_read(0x10a8c00,6)).hex()
        outer=u.context_save()
        integer_regs=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
        integer_values=[0x41000000+index*0x101 for index in range(8)]
        fp_regs=[UC_ARM_REG_D8+index for index in range(8)]
        fp_values=[0x3ff0000000000000+index*0x10001 for index in range(8)]
        for reg,value in zip(integer_regs+fp_regs,integer_values+fp_values):u.reg_write(reg,value)
        u.reg_write(UC_ARM_REG_SP,RAM+0xe000)
        try:
            status=call(0xcee2e0,drive,out,0,0,task=True)
            assert [u.reg_read(r) for r in integer_regs]==integer_values
            assert [u.reg_read(r) for r in fp_regs]==fp_values
        finally:u.context_restore(outer)
        raw=bytes(u.mem_read(out,0xc4));name=raw.split(b'\0',1)[0].decode(errors='replace') if status==0 else None
        if status:assert raw==b'\xcc'*0xc4
        print(hex(drive),status,name,flush=True)
        expected=1 if refusal_owner and (drive==0xffffffff or drive==(0x41 if refusal_owner=='a' else 0x42)) else 0
        if expected_errors:expected=expected_errors.get(drive,expected)
        assert status==expected,(drive,status,name,expected)
        results.append(dict(drive=drive,status=status,name=name,output_sha256=sha(raw),calls=calls[before:],
            counter_bytes_before=pair_before,counter_bytes_after=bytes(u.mem_read(0x10a8c00,6)).hex(),
            counter_writes=counter_writes[writes_before:],callee_saved_integer=True,callee_saved_d8_d15=True,stack_restored=True,
            candidate_a=bytes(u.mem_read(0x10ad16c,0xc4)).hex() if drive==0xffffffff else None,
            candidate_b=bytes(u.mem_read(0x10ad230,0xc4)).hex() if drive==0xffffffff else None))
    for context in [CONTEXT,B_CONTEXT]:
        assert bytes(u.mem_read(context-16,16))==bytes(u.mem_read(context+CONTEXT_BYTES,16))==b'\x5a'*16
    report=dict(scope=__doc__,status='PASS',elf_sha256=sha((build/'mods.elf').read_bytes()),
        native_a_registration=m['registration'],native_b_registration=b['registration'],
        a_summary=a_summary,b_summary=b_summary,a_file_summary=a_files,b_file_summary=b_files,refusal=refusal,
        results=results,native_stops=m['stops'],physical_storage=False,full_mount=False,hardware_verified=False)
    return (report,m,b) if return_machine else report


def main(build,output):
    output.mkdir(exist_ok=True)
    cases=[]
    for name,args in [('equal',(100,100,1,1)),('b-newer-folder',(100,101,1,1001)),
                      ('a-newer-folder',(102,100,2001,1)),('b-larger-file',(100,100,1,99))]:
        report=run_case(build,*args);report['case']=name;cases.append(report)
        assert all(r['counter_bytes_before']==r['counter_bytes_after'] and not r['counter_writes'] for r in report['results'])
    (output/'verification.json').write_text(json.dumps(dict(status='PASS',cases=cases,checker_sha256=sha(Path(__file__).read_bytes())),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.build,a.output)
