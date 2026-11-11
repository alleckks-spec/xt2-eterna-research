"""Execute the existing native context/catalog/name lower boundaries.

The mount-command caller data and post-enumeration FAT directory entries are
explicit inputs. Native code clears/registers the declared workspace, parses
and publishes catalog ownership, and computes its summary. No ready flag,
registration word or successful filesystem API result is supplied by the host.
This is not a completed mount or physical SD experiment. AI-assisted glue.
"""
import argparse
import json
import struct
import sys
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import verify_full_storage_guard as fixture

ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'save-data-menu-native-build-unverified'
OUT=ROOT/'date-folders-native-context-unverified'
RAM=0x8000000
CONTEXT=0xe000000
CONTEXT_BYTES=0x1878c


def setup(build=BUILD,*,stock_suffix=b'_FUJI'):
    fixture.BUILD=Path(build)
    (u,symbols,call,api,clock,exceptions),evidence=fixture.fixture_machine(False)
    for entry in [0xcec598,0xcec634]:assert call(entry)==0
    def word(a):return int.from_bytes(u.mem_read(a,4),'little')
    # Page-rounded mapping covers only the native declared object plus canaries.
    u.mem_map(CONTEXT-0x1000,0x1a000)
    u.mem_write(CONTEXT-16,b'\x5a'*16+b'\xa5'*CONTEXT_BYTES+b'\x5a'*16)
    req,params=RAM+0x1000,RAM+0x1100
    u.mem_write(req,bytes(64));u.mem_write(req+8,struct.pack('<I',params))
    data=bytearray(0x40);struct.pack_into('<I',data,4,CONTEXT)
    data[0x15]=1;struct.pack_into('<I',data,0x18,1)
    assert len(stock_suffix)==5
    data[0x1c:0x20]=b'DSCF';data[0x20:0x25]=stock_suffix;data[0x34]=ord('A')
    u.mem_write(params,bytes(data))
    stops=[]
    def execute_to(entry,end,*args,frame=None,allowed_stops=()):
        outer=u.context_save()
        if frame is not None:
            u.context_restore(frame)
            # The shared call wrapper zeros omitted argument registers. A
            # resumed native basic block must retain its native live inputs.
            if not args:args=tuple(u.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3])
        reached=[]
        def stop(uc,pc,n,d):reached.append(pc);uc.emu_stop()
        handles=[u.hook_add(UC_HOOK_CODE,stop,begin=pc,end=pc) for pc in [end,*allowed_stops]]
        try:
            try:call(entry,*args,task=frame is not None)
            except AssertionError:
                assert u.reg_read(UC_ARM_REG_PC) in [end,*allowed_stops],hex(u.reg_read(UC_ARM_REG_PC))
            assert len(reached)==1,reached
            saved=u.context_save();fp=u.reg_read(UC_ARM_REG_R11)
            stops.append(dict(entry=hex(entry),end=hex(reached[0]),frame_pointer=hex(fp),stack=hex(u.reg_read(UC_ARM_REG_SP))))
            return saved,fp,reached[0]
        finally:
            for handle in handles:u.hook_del(handle)
            u.context_restore(outer)
    registration=[]
    def stores(uc,access,a,n,v,d):
        if a==0x9c2260:registration.append(dict(pc=hex(uc.reg_read(UC_ARM_REG_PC)),value=v))
        if max(a,CONTEXT-16)<min(a+n,CONTEXT+CONTEXT_BYTES+16):
            assert CONTEXT<=a and a+n<=CONTEXT+CONTEXT_BYTES,(hex(a),n)
    u.hook_add(UC_HOOK_MEM_WRITE,stores)
    execute_to(0x969348,0x9694d0,req)
    assert word(0x9c2260)==CONTEXT
    assert registration==[dict(pc='0x969428',value=CONTEXT)],registration
    assert word(CONTEXT+0x114)==0 and u.mem_read(CONTEXT+0x2594,1)==b'\x01'
    assert bytes(u.mem_read(CONTEXT,4))==b'DSCF'
    assert bytes(u.mem_read(CONTEXT+0x216e,5))==stock_suffix
    assert word(CONTEXT+0x21a4)==1
    assert bytes(u.mem_read(CONTEXT-16,16))==bytes(u.mem_read(CONTEXT+CONTEXT_BYTES,16))==b'\x5a'*16
    context_initial=fixture.sha(bytes(u.mem_read(CONTEXT,CONTEXT_BYTES)))
    # Create the actual file-scan caller frame before publishing directories.
    scan_req,scan_params=RAM+0x1800,RAM+0x1900
    u.mem_write(scan_req,bytes(32));u.mem_write(scan_req+8,struct.pack('<I',scan_params))
    scan_data=bytearray(16);scan_data[8]=1;scan_data[9]=1
    u.mem_write(scan_params,bytes(scan_data))
    # Actual command handler loads its two caller-supplied scan modes.
    parent_frame,parent_fp,_=execute_to(0x964274,0x96384c,scan_req)
    frame,fp,stop=execute_to(0x95bf50,0x95c02c)
    assert bytes(u.mem_read(CONTEXT+0x2598,4000))==bytes(4000)
    assert bytes(u.mem_read(CONTEXT+0x21ac,1000))==b'\xff'*1000
    def publish_directory(name,cluster):
        nonlocal frame,fp
        assert len(name)==11 and 0<cluster<0x10000
        entry=bytearray(32);entry[:11]=name;entry[11]=0x10
        struct.pack_into('<H',entry,0x1a,cluster)
        u.mem_write(fp-0x3c,bytes(entry))
        frame,fp,stop=execute_to(0x95c070,0x95c1e8,frame=frame,allowed_stops=(0x95c02c,))
        assert stop==0x95c1e8,(name,hex(stop))
        number=int(name[:3])
        assert word(CONTEXT+0x2598+number*4)==cluster
        assert bytes(u.mem_read(CONTEXT+0x16c00+5*number,5))==name[3:8]
        return dict(name=name.decode(),cluster=cluster,number=number,
                    suffix_offset=hex(0x16c00+5*number),suffix=name[3:8].decode())
    def summarize():
        nonlocal frame,fp
        frame,fp,stop=execute_to(0x95c1ec,0x95c294,frame=frame)
        return dict(max_folder=word(CONTEXT+0x20fc),drive_folder=int.from_bytes(u.mem_read(CONTEXT+0x2168,2),'little'),
                    largest_matching=word(CONTEXT+0x214c))
    def publish_file_summary(folder,file):
        # Existing directory metadata and the native counter getter select the
        # folder in the real caller. Only a post-enumeration FAT entry is an
        # explicit input; no context summary field or success return is set.
        assert 100<=folder<=999 and 1<=file<=9999
        pf,pfp,_=execute_to(0x96385c,0x963984,frame=parent_frame)
        ff,ffp,_=execute_to(0x963984,0x9625dc,frame=pf)
        # Stop before starting the physical iterator; resume its initialized
        # local state at the same post-enumeration boundary as directory scan.
        ff,ffp,_=execute_to(0x9625f0,0x962614,frame=ff)
        entry=bytearray(32);entry[:11]=f'DSCF{file:04d}JPG'.encode();entry[11]=0x20
        struct.pack_into('<H',entry,0x1a,20);struct.pack_into('<I',entry,0x1c,1024)
        u.mem_write(ffp-0x44,bytes(entry))
        ff,ffp,_=execute_to(0x96266c,0x962614,frame=ff)
        aggregate=bytes(u.mem_read(pfp-0x68,24))
        assert struct.unpack_from('<I',aggregate,4)[0]==file
        execute_to(0x963994,0x963b9c,frame=pf)
        assert word(CONTEXT+0x2100)==file
        assert int.from_bytes(u.mem_read(CONTEXT+0x216a,2),'little')==file
        return dict(folder=folder,name=entry[:11].decode(),aggregate=aggregate.hex(),
                    max_file=word(CONTEXT+0x2100),native_extension_registration=False,
                    scope='native numeric filename reservation; extension list not mounted')
    return dict(u=u,symbols=symbols,call=call,api=api,clock=clock,exceptions=exceptions,
        setup=evidence,word=word,execute_to=execute_to,registration=registration,
        context_initial_sha256=context_initial,publish_directory=publish_directory,summarize=summarize,
        publish_file_summary=publish_file_summary,stops=stops)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=BUILD);parser.add_argument('--output',type=Path,default=OUT)
    a=parser.parse_args();a.output.mkdir(exist_ok=True)
    m=setup(a.build);u=m['u'];call=m['call'];word=m['word'];entries=[]
    for name,cluster in [(b'100_FUJI   ',2),(b'101_1111   ',3),(b'102_1110   ',4)]:entries.append(m['publish_directory'](name,cluster))
    summary=m['summarize']();assert summary==dict(max_folder=102,drive_folder=102,largest_matching=100),summary
    assert call(0xceaba0,102)==0
    assert call(0xcea990,2000)==0
    output=RAM+0x5000;u.mem_write(output-16,b'\x5a'*16+b'\xcc'*0xc4+b'\x5a'*16)
    result=call(0xcee2e0,ord('A'),output,0,0)
    native_name=bytes(u.mem_read(output,0xc4)).split(b'\0',1)[0].decode(errors='replace')
    assert result==0 and native_name=='A:\\DCIM\\103_FUJI\\DSCF3001'
    assert bytes(u.mem_read(output-16,16))==bytes(u.mem_read(output+0xc4,16))==b'\x5a'*16
    print('native_name',result,native_name,flush=True)
    report=dict(scope=__doc__,status='PASS: native constructor/catalog writer/summary boundaries',
        setup=m['setup'],context=dict(address=hex(CONTEXT),native_declared_bytes=CONTEXT_BYTES,
            mapping_base=hex(CONTEXT-0x1000),mapping_bytes=0x1a000,guard_bytes=16,
            initial_sha256=m['context_initial_sha256'],last_possible_suffix_end=hex(0x16c00+5*999+5)),
        registration=m['registration'],directories=entries,summary=summary,stops=m['stops'],
        native_name=dict(status=result,path=native_name),
        native_vfp_exceptions=m['exceptions'],host_registration_writes=0,host_ready_writes=0,
        native_api_success_substitutions=0,full_mount=False,hardware_verified=False)
    (a.output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
