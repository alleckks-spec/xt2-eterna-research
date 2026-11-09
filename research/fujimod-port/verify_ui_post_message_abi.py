"""Qualify the X-T2 UI post copy ABI, not a working queue or UI callback.

Original AI-assisted checker. Local extracted X-T20/X-T2 inputs only; no firmware
or instruction listings emitted. Executes the original active-post copy block
with an explicitly borrowed native frame, stopping before queue submission.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
from unicorn import Uc,UcError,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_INVALID,UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R4,UC_ARM_REG_R11,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from unicorn.unicorn_py3.unicorn import uclib


def sha(b):return hashlib.sha256(b).hexdigest()


def load(root,expected):
    manifest=json.loads((root/'manifest.json').read_text())
    assert manifest['sha256']==expected
    result=[]
    for row in manifest['streams']:
        b=(root/row['file']).read_bytes()
        assert sha(b)==row['sha256']
        result.append((row['inner_header']['base'],b))
    return result


def read(units,address,size):
    for base,b in units:
        if base<=address and address+size<=base+len(b):return b[address-base:address-base+size]
    raise ValueError(f'Unmapped input {address:#x}+{size:#x}')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',required=True,type=Path)
    p.add_argument('--target',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    source=load(args.reference,'b37faf524e6e2c72410e615a48feff05d6d2236f73f5cc6027c25863d7d48fad')
    target=load(args.target,'dd02ec5a862cf0e6f03a519a600ed99435efa442848249945b13ca6d78fabb25')
    c=Cs(CS_ARCH_ARM,CS_MODE_ARM)
    # Inspect the real post dispatch slot, not a same-prologue wrapper elsewhere.
    for units,wrapper,slot,deferred in [(source,0xcec178,0xf83438,0xcebd58),
                                      (target,0xcf8da8,0xfae35c,0xcf8988)]:
        ins=list(c.disasm(read(units,wrapper,28),wrapper))
        assert len(ins)==7 and ins[2].mnemonic=='movw' and ins[3].mnemonic=='movt'
        low=int(ins[2].op_str.split('#')[1],0);high=int(ins[3].op_str.split('#')[1],0)
        assert low|(high<<16)==slot
        assert struct.unpack('<I',read(units,slot,4))[0]==deferred
        assert (ins[4].mnemonic,ins[4].op_str)==('ldr','r3, [r3]')
        assert (ins[5].mnemonic,ins[5].op_str)==('blx','r3')
    copies=[]
    for units,start,end,expected in [(source,0xcebd58,0xcec178,44),(target,0xcf8988,0xcf8da8,68)]:
        ins=list(c.disasm(read(units,start,end-start),start))
        found=[]
        for i in range(1,len(ins)-2):
            a,b,d=ins[i:i+3]
            if (a.mnemonic,a.op_str)==('add','r1, r4, #8') and b.mnemonic=='mov' and b.op_str.startswith('r2, #') and d.mnemonic=='bl':
                found.append((ins[i-1].address,int(b.op_str.split('#')[1],0)))
        assert len(found)==1 and found[0][1]==expected
        copies.append(found[0])
    assert copies[1]==(0xcf8a9c,68)
    # The receiver uses the same code/argument/flags/payload destinations;
    # the queue request ID changes from11a to11c, and call/pointer bindings move.
    receiver=list(c.disasm(read(target,0x14da7ac,0x34),0x14da7ac))
    assert (receiver[4].mnemonic,receiver[4].op_str)==('mov','r3, #0x11c')
    assert [i.op_str for i in receiver[5:11]]==[
        'r3, [fp, #-0x34]','r0, [fp, #-0x30]','r3, r0, #4',
        'r3, [fp, #-0x2c]','r3, r0, #0xc','r3, [fp, #-0x28]']
    results=[]
    for packet_bytes in (52,76):
        u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
        u.mem_map(0,0x1000000)
        base,data=next((base,b) for base,b in target if base<0x1300000)
        u.mem_write(base,data)
        stack,source_page=0x2000000,0x3000000
        u.mem_map(stack,0x10000);u.mem_map(source_page,0x1000)
        end=source_page+0x1000;packet=end-packet_bytes
        payload=bytes(range(packet_bytes-8))
        u.mem_write(packet,struct.pack('<2I',0x6100,0x12345678)+payload)
        fp=stack+0xe004;dest=fp-0x5c
        u.mem_write(dest,b'\xcc'*(68+16))
        faults=[];writes=[];reached=[]
        def invalid(uc,access,a,n,v,d):
            faults.append(dict(address=hex(a),bytes=n,pc=hex(uc.reg_read(UC_ARM_REG_PC))));return False
        u.hook_add(UC_HOOK_MEM_INVALID,invalid)
        u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,access,a,n,v,d:writes.append((a,n)))
        def stop(uc,a,n,d):reached.append(a);uc.emu_stop()
        u.hook_add(UC_HOOK_CODE,stop,begin=0xcf8aac,end=0xcf8aac)
        for reg,value in [(UC_ARM_REG_R4,packet),(UC_ARM_REG_R11,fp),
                          (UC_ARM_REG_SP,fp-0x64),(UC_ARM_REG_LR,stack+0xf000)]:u.reg_write(reg,value)
        error=None
        try:u.emu_start(0xcf8a9c,stack+0xf000,count=200000)
        except UcError as exc:error=str(exc)
        if packet_bytes==52:
            assert error and faults and not reached
            assert int(faults[0]['address'],0)==end
        else:
            assert error is None and not faults and reached==[0xcf8aac]
            assert bytes(u.mem_read(dest,68))==payload
            assert bytes(u.mem_read(dest+68,16))==b'\xcc'*16
        assert all((stack+0xd000<=a and a+n<=fp-0x64) or (dest<=a and a+n<=dest+68) for a,n in writes)
        results.append(dict(packet_bytes=packet_bytes,payload_bytes=packet_bytes-8,
            expected_overread=packet_bytes==52,faults=faults,copy_completed=bool(reached),
            writes=len(writes),stopped_before_queue_submission=bool(reached)))
    report=dict(scope=__doc__,status='PASS: old52-byte packet overreads; adapted76-byte packet copies safely',
        bindings=dict(post_wrapper=hex(0xcf8da8),dispatch_slot=hex(0xfae35c),
                      initial_deferred_body=hex(0xcf8988),active_post_body=hex(0xcf8a18),
                      copy_block=hex(0xcf8a9c),receiver=hex(0x14da7ac)),
        source_payload_bytes=44,target_payload_bytes=68,target_packet_bytes=76,cases=results,
        inputs=[dict(base=hex(base),bytes=len(b),sha256=sha(b)) for base,b in source+target],
        source_sha256=sha(Path(__file__).read_bytes()),unicorn_library_sha256=sha(Path(uclib._name).read_bytes()),
        borrowed_frame=True,runtime_dispatch_registration=False,event_code_collision_checked=False,
        queue_submission_executed=False,ui_callback_executed=False,hardware_verified=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],cases=len(results),payload_bytes=68,packet_bytes=76)))


if __name__=='__main__':main()
