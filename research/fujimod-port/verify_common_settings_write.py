"""AI-assisted native commit, save request and actual write-open refusal.

Start from the frozen successful settings/file/UI/still chain. Capture its
existing FS fixture and retained worker frames, then let the original settings
timer submit the write. No write/open/close or kernel success is substituted.
"""
import hashlib,json,struct
from collections import deque
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.arm_const import *
import verify_common_settings_restore as restore
from verify_cardio_native_worker import RAM,RETURN

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'common-settings-write-check-unverified'

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    pins=json.loads((ROOT/'common-settings-restore-check-unverified/freeze.json').read_text())['files']
    dependency=Path(restore.__file__).resolve();assert sha(dependency.read_bytes())==pins[str(dependency)]
    captured={};original=restore.settle_startup
    def capture(m,fs,ticks,callbacks):
        captured.update(m=m,fs=fs,ticks=ticks,callbacks=callbacks);return original(m,fs,ticks,callbacks)
    (OUT/'setup').mkdir(parents=True,exist_ok=True)
    restore.settle_startup=capture;restore.OUT=OUT/'setup';restore.main()
    m=captured['m'];fs=captured['fs'];ticks=captured['ticks'];u=m.u;trace=deque(maxlen=36);faults=[];requests=[];callbacks=[]
    native=[];pending={};missing_driver_branches=[]
    u.hook_add(UC_HOOK_CODE,lambda uc,a,z,d:missing_driver_branches.append(a),begin=0x955e08,end=0x955e08)
    watched={0x96c950:'native open',0x96d804:'path parse',0x9709b8:'volume preflight',0x971458:'write mode setup',0x971490:'write preflight',0x955de8:'registered driver check'}
    def native_trace(uc,a,z,d):
        trace.append(hex(a))
        if a in pending:
            for index in reversed(pending.pop(a)):native[index]['result']=uc.reg_read(UC_ARM_REG_R0)
        if a in watched:
            index=len(native);native.append(dict(function=watched[a],entry=hex(a),args=[uc.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]]))
            pending.setdefault(uc.reg_read(UC_ARM_REG_LR),[]).append(index)
    u.hook_add(UC_HOOK_CODE,native_trace)
    def invalid(uc,access,address,size,value,data):
        faults.append(dict(access=access,address=hex(address),size=size,pc=hex(uc.reg_read(UC_ARM_REG_PC))));return False
    u.hook_add(UC_HOOK_MEM_INVALID,invalid)
    for address,kind in [(0xced3e0,'open'),(0xced504,'write'),(0xced554,'close')]:
        def observe(uc,a,z,d,kind=kind):
            args=[uc.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]]
            record=dict(kind=kind,args=args)
            if kind=='open':
                record['path']=bytes(u.mem_read(args[1],64)).split(b'\0',1)[0].decode()
                job=m.word(m.symbols['x70_cardio_active'])
                if job:
                    count=m.word(job+20);source=m.word(job+52);assert 0<count<8192
                    record['job_data']=bytes(u.mem_read(source,count)).decode()
            if kind=='write':
                blob=bytes(u.mem_read(args[3],args[2]));record.update(data=blob.decode(),sha256=sha(blob))
            requests.append(record)
        u.hook_add(UC_HOOK_CODE,observe,begin=address,end=address)
    for kind,arity in [('cb_open_write',2),('cb_write',2),('cb_close_write',1)]:
        for bank in range(4):
            address=m.symbols[f'{kind}_{bank}']
            u.hook_add(UC_HOOK_CODE,lambda uc,a,z,d,kind=kind,bank=bank,arity=arity:callbacks.append(dict(kind=kind,bank=bank,status=uc.reg_read(UC_ARM_REG_R0),value=uc.reg_read(UC_ARM_REG_R1) if arity==2 else None)),begin=address,end=address)
    owner=m.symbols['x70_stock_choice_settings']
    def owner_state():
        return dict(requested=m.word(owner+92),completed=m.word(owner+96),failed=m.word(owner+100),registered=m.word(owner+104),io=list(struct.unpack('<15i',u.mem_read(owner+32,60))))
    before=owner_state();error=None;runs=[];commits=[];selection=[];prior_lower_fs=list(fs.trace)
    driver_slots=list(struct.unpack('<3I',u.mem_read(0x9ae7fc,12)));assert driver_slots[0]==0
    try:
        commits.append(m.call(0xbbc924,0))
        m.call(0x154b700,0x1fc,32)
        assert owner_state()['requested']==0
        selection.append(dict(phase='preview',key=m.word(m.symbols['film_choice_key']),requested=0))
        m.call(0xbbc924,1)
        assert m.word(m.symbols['film_choice_key'])==38 and owner_state()['requested']==0
        selection.append(dict(phase='cancel',key=38,requested=0))
        m.call(0x154b700,0x1fc,32)
        commits.append(m.call(0xbbc924,0))
        commits.append(m.call(0xbbc924,0))
        selection.append(dict(phase='commit and repeat',key=m.word(m.symbols['film_choice_key']),requested=owner_state()['requested']))
        assert owner_state()['requested']==1,owner_state()
        ticks(121)
        for operation in ['open','write','close']:
            if not m.word(m.symbols['x70_cardio_active']):break
            outer=u.context_save()
            for entry,end,loop in [(0x969b54,0x969c00,0x969bb8),(0x969fcc,0x96a090,0x96a00c)]:
                u.context_restore(restore.startup_workers[entry]);u.emu_start(end,RETURN,count=1)
                assert u.reg_read(UC_ARM_REG_PC)==loop
                m.execute_to(loop,end);restore.startup_workers[entry]=u.context_save()
                runs.append(dict(operation=operation,start=hex(loop),end=hex(end)))
            u.context_restore(outer)
        ticks(121)
    except Exception as e:error=repr(e)
    assert error is None,(error,faults,list(trace))
    assert fs.trace==prior_lower_fs  # write refusal precedes all three lower FS hooks
    assert not faults and missing_driver_branches==[0x955e08]
    assert len(requests)==1 and requests[0]['kind']=='open' and requests[0]['args'][2]==1
    produced=json.loads(requests[0]['job_data'])
    assert produced==dict(stock_choices=dict(current=dict(values=[dict(setting='film_simulation',value='eterna')])))
    assert [(x['kind'],x['status']) for x in callbacks]==[('cb_open_write',5)]
    after=owner_state();assert after['requested']==after['failed']==1 and after['completed']==0
    assert after['io'][4]==1 and after['io'][7:9]==[1,5]
    assert m.word(m.symbols['x70_cardio_active'])==m.word(m.symbols['callbacks'])==m.word(m.symbols['x70_cardio_hold'])==0
    assert m.word(m.symbols['live'])==3 and bytes(u.mem_read(m.symbols['bank_state'],16))==bytes(16)
    resources={n:v for n,v in fs.summary()['resources'].items() if n not in ['pool_owned','queued']}
    assert resources==dict(alias_internal=0,alias_public=0,descriptor_id=0xffffffff,open_count=0,context_slot=0,reservation=0),resources
    assert next(x for x in native if x['entry']=='0x96c950')['args'][1]==ord('w')
    assert next(x for x in native if x['entry']=='0x955de8')['result']==4
    assert next(x for x in native if x['entry']=='0x971490')['result']==0x100
    assert next(x for x in native if x['entry']=='0x96c950')['result']==39
    OUT.mkdir(exist_ok=True)
    report=dict(scope=__doc__,status='PASS: native commit/request/driver-refusal contract; successful writing unqualified',selection=selection,driver_slots=driver_slots,missing_driver_branches=missing_driver_branches,resources=resources,error=error,before=before,after=owner_state(),native=native,commits=commits,requests=requests,callbacks=callbacks,runs=runs,faults=faults,trace=list(trace),
                active_cardio=m.word(m.symbols['x70_cardio_active']),lifetime_live=m.word(m.symbols['live']),outstanding_callbacks=m.word(m.symbols['callbacks']),
                lower_fs_calls=fs.trace,new_lower_fs_calls=fs.trace[len(prior_lower_fs):],hardware_verified=False,native_success_substitutes=0,write_body_executed=False,physical_storage=False,full_boot=False,
                elf_sha256=sha((restore.BUILD/'mods.elf').read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),
                dependencies={str(dependency):sha(dependency.read_bytes())})
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
