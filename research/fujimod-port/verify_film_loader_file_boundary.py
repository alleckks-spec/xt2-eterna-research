"""Existing loader consumes supplied file bytes through native open/read/close.

AI-assisted bounded checker, not a mounted-card result. Reuse the existing
initialized filesystem/directory/data boundary fixture, retaining ONLY its
three lower filesystem hooks. Native kernel pools/queues/semaphores, both
storage workers and actual compiled C callbacks execute. The directory writer
borrows a post-FAT frame. No camera startup, IRQ or mutable-processing claim.
"""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from verify_cardio_native_worker import Assay,RAM,RETURN
from verify_film_loader_component import load
from xt2_native_profile_fs_fixture import NativeProfileFSFixture


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['stock','baseline','common','component','output']:p.add_argument('--'+n,required=True,type=Path)
    p.add_argument('--invalid-json',action='store_true')
    p.add_argument('--read-error',type=lambda value:int(value,0),default=0)
    a=p.parse_args();stock=a.stock.read_bytes();component=a.component.read_bytes();common=a.common.read_bytes()
    assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    build=json.loads(a.component.with_name('build.json').read_text())
    assert sha(component)==build['elf_sha256'] and sha(common)==build['common_sha256']
    for path,digest in build['dependencies'].items():assert sha(Path(path).read_bytes())==digest,path
    m=Assay(stock,a.baseline.read_bytes());load(m,common,0x1390000,0x13c0000)
    m.symbols=load(m,component,0x2100000,0x2140000)
    for entry in [0x14d6fd8,0xcdf570]:assert m.call(entry)==0
    for n,v in dict(ui_mode=3,ui_capture_state=0,ui_capture_block=0,raw_backup_flag=0,menu_open=0).items():
        m.u.mem_write(m.symbols[n],bytes([v]))
    assert not(a.invalid_json and a.read_error)
    doc=b'{"name":' if a.invalid_json else json.dumps(dict(name='Port file',base='provia',icon='custom')).encode()
    # Existing fixture has an exact3008-byte input contract. Whitespace padding
    # is legal JSON and does not add a second parser or a profile container.
    doc=doc+b' '*(3008-len(doc))
    # Restore every transport/bootstrap location the old fixture overwrites.
    # Keep only its declared downstream initialized-FS boundary assumptions.
    locations=[(0x11892a4,8),(0x118a304,8),(0x9c3544,4),(0x9c354c,1),
               (0x10ad304+119*4,4),(0xfae330,4)]
    saved={address:bytes(m.u.mem_read(address,size)) for address,size in locations}
    fs=NativeProfileFSFixture(m.u,doc)
    fs.read_error=a.read_error
    fs.hooks={address:fs.hooks[address] for address in [0x96e94c,0x96f8a0,0x96ffdc]}
    fs.boundary_roles={hex(address):fs.boundary_roles[hex(address)] for address in fs.hooks}
    for address,data in saved.items():m.u.mem_write(address,data)
    assert all(bytes(m.u.mem_read(address,len(data)))==data for address,data in saved.items())
    m.u.mem_write(fs.ctx+0x16b84,struct.pack('<I',4096))
    assert m.word(0x9c3544)&0xffff==0x4478  # native queue120 / semaphore68
    callbacks=[]
    for kind,arity in [('cb_list',1),('cb_open_read',2),('cb_read',2),('cb_close_read',1)]:
        for bank in range(4):
            pc=m.symbols[f'{kind}_{bank}']
            def observe(uc,address,size,data,kind=kind,bank=bank,arity=arity):
                callbacks.append(dict(kind=kind,bank=bank,status=uc.reg_read(UC_ARM_REG_R0),
                                      value=uc.reg_read(UC_ARM_REG_R1) if arity==2 else None))
            m.u.hook_add(UC_HOOK_CODE,observe,begin=pc,end=pc)
    loader=m.symbols['film_loader'];states=[]
    def state():return list(struct.unpack('<21I',m.u.mem_read(loader,84)))
    def ticks(n):
        for _ in range(n):m.call(0xcdf968)
    m.api('film_loader_boot');ticks(121);assert state()[0]==1
    descriptor,payload,code=m.take();assert code==0x1377
    record=bytearray(80);name=b'A:\\FUJIMOD\\FILMS\\200TEST.JSN'
    record[:len(name)]=name;record[59]=0x20;record[61]=0
    stamp=struct.pack('<HH',0,((2026-1980)<<9)|(11<<5)|9)
    record[62:66]=stamp;record[70:74]=stamp;record[76:80]=struct.pack('<I',len(doc))
    context=m.u.context_save();fp=m.frame(descriptor,payload,0)
    m.u.mem_write(fp-0x6c,bytes(record));m.execute_to(0x967af8,0x967c3c);m.u.context_restore(context)
    assert [x['status'] for x in callbacks]==[0]
    descriptor,payload,code=m.take();assert code==0x1378
    context=m.u.context_save();m.frame(descriptor,payload,7)
    m.execute_to(0x967dc0,0x967ddc);m.u.context_restore(context)
    assert [x['status'] for x in callbacks]==[0,6]
    ticks(5);print('after listing',state(),flush=True);assert state()[0]==2
    # Retain actual worker frames across open/read/close. Their bootstrap wait
    # executes once; no repeated entry, semaphore post or successful wait stub.
    workers={};runs=[]
    for operation in ['open','read','close']:
        outer=m.u.context_save()
        for entry,end,loop,stack,arg in [(0x969b54,0x969c00,0x969bb8,RAM+0xd000,0x9c3540),
                                         (0x969fcc,0x96a090,0x96a00c,RAM+0xb000,0)]:
            if entry in workers:
                m.u.context_restore(workers[entry]);m.u.emu_start(end,RETURN,count=1)
                assert m.u.reg_read(UC_ARM_REG_PC)==loop
                start=loop
            else:
                m.u.context_restore(outer);m.u.reg_write(UC_ARM_REG_SP,stack)
                m.u.reg_write(UC_ARM_REG_LR,RETURN);m.u.reg_write(UC_ARM_REG_R0,arg);start=entry
            m.execute_to(start,end);workers[entry]=m.u.context_save()
            runs.append(dict(operation=operation,start=hex(start),end=hex(end)))
        m.u.context_restore(outer)
        print(operation,callbacks[-1],flush=True)
    assert [x['kind'] for x in callbacks]==['cb_list','cb_list','cb_open_read','cb_read','cb_close_read']
    if a.read_error:
        assert [x['status'] for x in callbacks[:3]]==[0,6,0]
        assert callbacks[3]['status']!=0 and callbacks[3]['value']==0 and callbacks[4]['status']==0
    else:
        assert [x['status'] for x in callbacks]==[0,6,0,0,0] and callbacks[3]['value']==len(doc)
    assert m.semaphore_results==[0]
    ticks(5);print('loaded',state(),flush=True)
    rejected=bool(a.invalid_json or a.read_error)
    assert state()[0]==4 and state()[5:11]==[1,1,1,int(not rejected),0,int(rejected)]
    if a.read_error:assert state()[11]==callbacks[3]['status']
    assert m.api('film_loader_ready')==1 and m.api('film_loader_idle')==1
    users=m.symbols['film_users'];assert m.word(users)==int(not rejected)
    if not rejected:
        assert m.word(users+8)==200
        assert bytes(m.u.mem_read(users+8+378,10))==b'Port file\0'
    assert m.word(m.symbols['x70_cardio_active'])==0
    # Both timer objects keep their registry holds for reuse. Live==2 is not
    # a leaked file request: callbacks and all cardio banks have retired.
    assert m.api('x70_lifetime_live')==2 and m.word(m.symbols['callbacks'])==0
    assert bytes(m.u.mem_read(m.symbols['bank_state'],16))==bytes(16)
    # No card rows/processing admission: the disabled card publisher keeps zero.
    assert m.word(m.symbols['film_card_count'])==0
    resources={n:v for n,v in fs.summary()['resources'].items() if n not in ['pool_owned','queued']}
    assert resources==dict(alias_internal=0,alias_public=0,descriptor_id=0xffffffff,
        open_count=0,context_slot=0,reservation=0),resources
    assert [x['address'] for x in fs.trace]==['0x96e94c','0x96f8a0','0x96ffdc']
    report=dict(scope=__doc__,status='PASS',loader=state(),callbacks=callbacks,workers=runs,
        lower_boundary_calls=fs.trace,lower_boundary_roles=fs.boundary_roles,resources=resources,
        initialized_fs_context_fixture=True,post_fat_listing_frame=True,rec_idle_fixture=True,
        native_worker_frames_retained=True,native_semaphore_initial_wait=m.semaphore_results,
        kernel_api_stubs=0,mounted_card_success=False,physical_storage_executed=False,
        card_processing_enabled=False,common_candidate_changed=False,hardware_verified=False,
        elf_sha256=sha(component),common_sha256=sha(common),file_fixture_sha256=sha(doc),
        checker_sha256=sha(Path(__file__).read_bytes()))
    report.update(invalid_json=a.invalid_json,supplied_lower_read_error=a.read_error,
        live_timer_holds=2,outstanding_callbacks=0,baseline_sha256=sha(a.baseline.read_bytes()),
        stock_sha256=sha(stock),checker_dependencies={str(path):sha(path.read_bytes()) for path in [
            Path(__file__).with_name('verify_film_loader_component.py'),
            Path(__file__).with_name('verify_cardio_native_worker.py'),
            Path(__file__).parents[2]/'scripts/kernel_timer_initialization.py',
            Path(__file__).parents[2]/'scripts/xt2_native_profile_fs_fixture.py']})
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS')


if __name__=='__main__':main()
