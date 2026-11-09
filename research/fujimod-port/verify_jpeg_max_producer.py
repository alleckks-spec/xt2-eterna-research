"""Native caller/descriptor/request -> first submit -> JPEG Max -> stock tables.

Exact existing ordinary ELF, manual init and previously declared stock RAM,
calibration/mode/transport fixture. Supply geometry/camera-info pointer and a
two-pointer worker header; never supply request tag/kind/attempts/index/scale.
Stop before the encoder entry executes. No pixels, JPEG file, scheduler, full
producer/overlay/service lifecycle or physical camera evidence. AI-assisted.
"""
import json
import struct
from pathlib import Path

from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from unicorn.unicorn_py3.unicorn import uclib
from verify_ordinary_platform_nr import load,ROOT,START,END,sha
from verify_ordinary_platform_processing import actual_factory,initialize,TRANSPORT
from verify_film_menu_navigation import invoke,RETURN
from build_eterna_payload import STOCK,STOCK_HASH
import verify_ordinary_platform_processing as platform

BUILD=ROOT/'jpeg-max-build-unverified'
OUT=ROOT/'jpeg-max-producer-check-unverified'
ELF='8bea01979955b1e751643cb1201975adc553e9efe2eafa5ef327fdc990c013eb'
RAM=0x8000000
OBJECT=0x22f5a18
EXTENT=0xf770
SETUP_STOP=0x2a759a0
ENCODER_STOP=0x15b2108


def main():
    sections,symbols,manifest=load(BUILD,63)
    assert manifest['elf_sha256']==ELF
    assert sha(STOCK.read_bytes())==STOCK_HASH
    library=Path(uclib._name).resolve()
    assert library==(ROOT.parents[1]/'.toolchains/unicorn-tci/libunicorn.2.dylib').resolve()
    pins={str(p):sha(p.read_bytes()) for p in [Path(__file__),Path(platform.__file__),
        BUILD/'mods.elf',BUILD/'manifest.json',BUILD/'freeze.json',STOCK,library]}
    generators=[];submissions=[]
    variants=[(0x2a79c14,key,1) for key in (6,7,0,2)]+[(0x2a9d35c,6,0)]
    for caller,key,tagged in variants:
        u=actual_factory()
        for a,data,name,size in sections:
            if name in ('.x70mod.hooks','.x70mod.strings'):continue
            assert START<=a<a+size<=END
            u.mem_write(a,data)
        for edit in manifest['edits']:
            assert bytes(u.mem_read(edit['address'],4))==struct.pack('<I',edit['expected'])
            u.mem_write(edit['address'],struct.pack('<I',edit['value']))
        def call(uc,entry,*args):
            result=invoke(uc,entry,*args,instruction_limit=3000000)
            assert uc.reg_read(UC_ARM_REG_SP)==RAM+0xe000
            return result
        initialize(u,symbols,call,3)
        call(u,0x154b700,0x1f1,key)
        stored=call(u,0xb510b8,0x1f1,0)
        assert stored=={6:0,7:2}.get(key,key)
        assert int.from_bytes(u.mem_read(symbols['jpeg_max_status'],4),'little')==0
        calibration=bytes(u.mem_read(0x9000000,0x40000))
        # Only caller input geometry/pointer is supplied. The real native caller
        # initializes its state object, stack descriptors and three requests.
        if tagged:
            u.mem_write(0x24825e8+0x2c,struct.pack('<I',RAM+0x4000))
            u.mem_write(RAM+0x4000+0x58c,struct.pack('<3H',6000,4000,6000))
            slot=0x24825e8+8
            flag_writer=0x2a79cb8
        else:
            slot=0x247f34c
            flag_writer=0x2a9d3e4
        u.mem_write(OBJECT-16,b'\xa5'*16)
        u.mem_write(OBJECT+EXTENT,b'\x5a'*16)
        writes=[];visited=set()
        def write(uc,access,a,n,value,d):
            pc=uc.reg_read(UC_ARM_REG_PC)
            assert a<0xf0000000,(hex(a),hex(pc))
            if 0x15a0dd0<=pc<0x15a0e38:
                ranges=[(RAM,RAM+0x10000),(0x22f2ec8,0x22f2f08),
                        (0x22f2708,0x22f2748),(0x1e0e1ad,0x1e0e1ec)]
                assert any(lo<=a and a+n<=hi for lo,hi in ranges),(hex(pc),hex(a),n)
            writes.append((a,n,value,pc))
        u.hook_add(UC_HOOK_MEM_WRITE,write)
        u.hook_add(UC_HOOK_CODE,lambda uc,a,n,d:visited.add(a))
        def run_to(entry,stop,r0=None):
            reached=[]
            def barrier(uc,a,n,d):
                reached.append(a);uc.emu_stop()
            hook=u.hook_add(UC_HOOK_CODE,barrier,begin=stop,end=stop)
            u.reg_write(UC_ARM_REG_SP,RAM+0xe000)
            u.reg_write(UC_ARM_REG_LR,RETURN)
            if r0 is not None:u.reg_write(UC_ARM_REG_R0,r0)
            try:u.emu_start(entry,RETURN,count=3000000)
            finally:u.hook_del(hook)
            assert reached==[stop] and u.reg_read(UC_ARM_REG_PC)==stop
        run_to(caller,SETUP_STOP)
        state=int.from_bytes(u.mem_read(slot,4),'little')
        assert state==OBJECT+8
        assert any(pc==flag_writer and n==4 and value==tagged for a,n,value,pc in writes)
        assert any(pc==0x2a758bc and n==4 and value==4*tagged for a,n,value,pc in writes)
        assert ENCODER_STOP not in visited
        requests=[]
        for kind,offset in [(0,0x150),(1,0x54),(2,0x25c)]:
            request=state+offset
            fields={o:int.from_bytes(u.mem_read(request+o,4),'little')
                    for o in (4,8,12,0x18,0x1c,0xac,0xb0,0xd8)}
            assert fields[4]==10 and fields[8]==0 and fields[12]==kind
            assert fields[0xd8]==(4*tagged if kind==1 else 0)
            assert u.mem_read(request+0xc9,1)==b'\x01'
            if kind==1:assert (fields[0xac],fields[0xb0])==((6000,4000) if tagged else (320,240))
            provenance={}
            for name,off,n,writer in [('attempts',4,4,0x2a23278),('kind',12,1,0x2a23208),
                                     ('tag',0xd8,4,0x2a232a0)]:
                events=[(value,pc) for a,size,value,pc in writes if a==request+off and size==n and pc==writer]
                assert len(events)==1,(name,hex(request),events)
                provenance[name]=dict(value=events[0][0],writer=hex(writer))
            requests.append(dict(kind=kind,address=request,fields=fields,provenance=provenance))
        generators.append(dict(caller=hex(caller),key=key,stored=stored,tag_flag=tagged,
            state=hex(state),native_init_entries=3,requests=requests,
            setup_cpu_writes=len(writes),calibration_sha256=sha(calibration)))
        # The worker ownership header is a declared function-boundary input.
        # Its request is the native-produced object above, not a synthetic copy.
        control,job=RAM+0x6000,RAM+0x6100
        u.mem_write(control,bytes(0x80));u.mem_write(job,bytes(0x80))
        u.mem_write(control+0x14,struct.pack('<I',job))
        order=bytes(u.mem_read(0x197091c,64))
        tables=[bytes(u.mem_read(a,64)) for a in (0x197089c,0x197085c,0x19708dc)]
        for item in requests:
            kind,request,fields=item['kind'],item['address'],item['fields']
            u.mem_write(job+0x20,struct.pack('<I',request))
            # Adjacent bytes are live stock parameter records. Poison only the
            # output buffers; constrain scaler writes rather than replacing
            # those neighboring records with synthetic canaries.
            for dest in (0x22f2ec8,0x22f2708):u.mem_write(dest,b'\xcc'*64)
            before=int.from_bytes(u.mem_read(symbols['jpeg_max_encodes'],4),'little')
            writes.clear();visited.clear()
            run_to(0x2a233e0,ENCODER_STOP,control)
            index=int.from_bytes(u.mem_read(request+8,4),'little')
            assert index==1
            assert any(a==request+8 and n==4 and value==1 and pc==0x2a233f8 for a,n,value,pc in writes)
            scale=int.from_bytes(u.mem_read(request+0x28,4),'little')
            changed=key in (6,7) and tagged and kind==1
            after=int.from_bytes(u.mem_read(symbols['jpeg_max_encodes'],4),'little')
            assert after==before+int(changed)
            if changed:assert scale==16
            history=[(value,pc) for a,n,value,pc in writes if a==request+0x28 and n==4]
            assert history and history[0][1]==0x2a233ac
            assert len(history)==(2 if changed else 1)
            if changed:assert START<=history[-1][1]<END and history[-1][0]==16
            for i,dest in enumerate((0x22f2ec8,0x22f2708)):
                base=tables[0 if i==0 else (1 if fields[0x1c] else 2)]
                expected=bytes([1]+[max(1,min(255,(scale*fields[0x18]*base[j])>>10)) for j in order[1:]])
                assert bytes(u.mem_read(dest,64))==expected
                if changed:assert expected==b'\x01'*64
            assert {0x2a233e0,0x2a2336c,0x2a232e8,0x15a0dd0}<=visited
            edit=next(e for e in manifest['edits'] if e['address']==0x2a232e8)
            disp=(edit['value']&0xffffff)<<2
            if disp&0x2000000:disp-=0x4000000
            assert edit['address']+8+disp in visited
            submissions.append(dict(caller=hex(caller),key=key,kind=kind,tag=fields[0xd8],
                width=fields[0xac],height=fields[0xb0],attempts=fields[4],index=index,
                scale=scale,changed=changed,history_writers=[hex(pc) for value,pc in history],
                stopped_before_encoder=True,cpu_writes=len(writes)))
        assert bytes(u.mem_read(OBJECT-16,16))==b'\xa5'*16
        assert bytes(u.mem_read(OBJECT+EXTENT,16))==b'\x5a'*16
        assert bytes(u.mem_read(0x9000000,0x40000))==calibration
    assert len(generators)==5 and len(submissions)==15
    assert sum(c['changed'] for c in submissions)==2
    assert all(sha(Path(p).read_bytes())==digest for p,digest in pins.items())
    report=dict(scope=__doc__,status='PASS: bounded native descriptor/request and first submit',
        elf_sha256=ELF,generators=generators,submissions=submissions,input_sha256=pins,
        transport_fixtures=TRANSPORT,worker_header_supplied=True,
        request_fields_supplied=False,new_peripheral_model=False,encoder_executed=False,
        full_producer_lifecycle=False,overlay_lifecycle=False,hardware_verified=False,accepted=False)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(generators=len(generators),submissions=len(submissions),
        changed=sum(c['changed'] for c in submissions),elf_sha256=ELF,encoder_executed=False)))


if __name__=='__main__':main()
