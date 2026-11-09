"""AI-assisted actual policy hook starts the unchanged ordinary common artifact.

No manual mod-init loop or loader boot in the adapted file-chain check. Native
FS/timer constructor order, borrowed UI1, calibration/REC/settings/FS boundaries
remain explicit. This is not a scheduled first policy call or full camera boot.
"""
import argparse,hashlib,inspect,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
import verify_common_card_file as common
from common_late_start_setup import make_machine
from verify_card_processing import BUILD
from verify_cardio_native_worker import RAM,RETURN

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'common-late-start-check-unverified'
startup_workers={}
startup_evidence={}
active_machine=None

def sha(b):return hashlib.sha256(b).hexdigest()

def settle_startup(m,fs,ticks,callbacks):
    # Explicit absent SETTINGS.JSN at the existing lower lookup boundary.
    # Do not fabricate a successful native open or bypass shared-channel busy.
    fs.lookup_error=0x10a
    ticks(121)
    job=m.word(m.symbols['x70_cardio_active']);assert job
    folder=bytes(m.u.mem_read(job+56,40)).split(b'\0',1)[0]
    name=bytes(m.u.mem_read(job+112,16)).split(b'\0',1)[0]
    assert folder==b'FUJIMOD' and name==b'SETTINGS.JSN',(folder,name)
    outer=m.u.context_save();runs=[]
    for entry,end,stack,arg in [(0x969b54,0x969c00,RAM+0xd000,0x9c3540),
                                (0x969fcc,0x96a090,RAM+0xb000,0)]:
        m.u.context_restore(outer);m.u.reg_write(UC_ARM_REG_SP,stack)
        m.u.reg_write(UC_ARM_REG_LR,RETURN);m.u.reg_write(UC_ARM_REG_R0,arg)
        m.execute_to(entry,end);startup_workers[entry]=m.u.context_save()
        runs.append(dict(entry=hex(entry),end=hex(end)))
    m.u.context_restore(outer)
    assert [(c['kind'],c['status']) for c in callbacks]==[('cb_open_read',6)],callbacks
    assert m.word(m.symbols['x70_cardio_active'])==0
    startup_evidence.update(folder=folder.decode(),name=name.decode(),callbacks=list(callbacks),
                            lower_calls=list(fs.trace),workers=runs,lookup_error=0x10a)
    callbacks.clear();fs.trace.clear();fs.lookup_error=0
    print('Native settings missing-file status6 retires; retained workers continue to loader',flush=True)

def make_started_machine():
    global active_machine
    (u,symbols,call,api,clock,exceptions),setup=make_machine()
    word=lambda a:struct.unpack('<I',u.mem_read(a,4))[0]
    def registry(a,b):return [word(p) for p in range(symbols[a],symbols[b],4)]
    inits=registry('__xpp_init_start','__xpp_init_end');lates=registry('__xpp_late_start_start','__xpp_late_start_end')
    files=registry('__xpp_settings_files_start','__xpp_settings_files_end')
    assert len(inits)==4 and len(lates)==2
    constructors=[0xcec598,0xcec634,0xcdf570]
    for entry in constructors:assert call(entry,task=True)==0
    events=[];stock=[]
    for phase,functions in [('init',inits),('late',lates)]:
        for fn in functions:
            u.hook_add(UC_HOOK_CODE,lambda uc,a,z,d,phase=phase:events.append([phase,a]),begin=fn,end=fn)
    policy=json.loads((BUILD/'target.json').read_text())['symbols']['ui_display_off_policy']
    u.hook_add(UC_HOOK_CODE,lambda uc,a,z,d:stock.append(a),begin=policy+4,end=policy+4)
    refused=[]
    for mode in [0,1,2,7]:
        u.mem_write(symbols['ui_mode'],bytes([mode]));assert call(policy,task=True)==0
        assert events==[];refused.append(mode)
    u.mem_write(symbols['ui_mode'],b'\x03');assert call(policy,task=True)==0
    expected=[['init',fn] for fn in inits]+[['late',fn] for fn in lates]
    assert events==expected and word(symbols['xpp_settings_start_errors'])==0
    loader=list(struct.unpack('<21I',u.mem_read(symbols['film_loader'],84)))
    assert loader[3]==0 and loader[4]!=0
    for mode in [3,4,5,6]:
        u.mem_write(symbols['ui_mode'],bytes([mode]));assert call(policy,task=True)==0
        assert events==expected
        assert list(struct.unpack('<21I',u.mem_read(symbols['film_loader'],84)))==loader
    assert len(stock)==9
    u.mem_write(symbols['ui_mode'],b'\x03')
    setup.update(policy_entry=hex(policy),refused_modes=refused,repeat_modes=[3,4,5,6],
                 native_policy_returns=9,stock_instruction_entries=stock,events=events,
                 init_registry=inits,late_registry=lates,settings_file_registry=files,late_names=[[n for n,a in symbols.items() if a==fn] for fn in lates],
                 constructors=list(map(hex,constructors)),loader_after_policy=loader,
                 start_errors=word(symbols['xpp_settings_start_errors']),manual_mod_init_calls=0,
                 manual_loader_boot_calls=0,scheduled_policy_call=False)
    print('Actual policy: four init/two late functions, mode gates and one-time startup PASS',flush=True)
    active_machine=(u,symbols,call)
    return (u,symbols,call,api,clock,list(map(hex,inits)),exceptions),setup

def main():
    # Retain the existing checker's CLI, native FS boundary, parser/UI and
    # still numeric assertions. Only startup setup/order is replaced.
    freeze=json.loads((ROOT/'common-card-file-check-unverified/freeze.json').read_text())['files']
    original=Path(common.__file__).resolve();assert sha(original.read_bytes())==freeze[str(original)]
    source=inspect.getsource(common.main)
    constructors='    for entry in [0xcec598,0xcec634,0xcdf570]:assert m.call(entry)==0\n'
    assert source.count(constructors)==1;source=source.replace(constructors,'')
    anchor="    code='def execute():\\n'+body"
    assert source.count(anchor)==1
    source=source.replace(anchor,"    boot=\"    m.api('film_loader_boot');ticks(121);assert state()[0]==1\\n\"\n"
        "    assert body.count(boot)==1\n"
        "    body=body.replace(boot,\"    SETTLE_STARTUP(m,fs,ticks,callbacks)\\n    ticks(121);assert state()[0]==1\\n\")\n"
        "    old_workers='    workers={};runs=[]\\n';assert body.count(old_workers)==1\n"
        "    body=body.replace(old_workers,'    workers=BOOT_WORKERS;runs=[]\\n')\n"
        "    old_live=\"m.word(m.symbols['live'])==2\";assert body.count(old_live)==1\n"
        "    body=body.replace(old_live,\"m.word(m.symbols['live'])==3\")\n"+anchor)
    old_namespace="namespace=dict(vars(filecheck));namespace.update("
    assert source.count(old_namespace)==1
    source=source.replace(old_namespace,"namespace=dict(vars(filecheck));namespace['SETTLE_STARTUP']=settle_startup;namespace['BOOT_WORKERS']=startup_workers;namespace.update(")
    source=source.replace('def main():','def execute_case():',1)
    namespace=dict(vars(common));namespace.update(make_machine=make_started_machine,OUT=OUT,
                                                settle_startup=settle_startup,startup_workers=startup_workers)
    exec(compile(source,str(original)+'::actual-policy-start','exec'),namespace)
    namespace['execute_case']()
    parser=argparse.ArgumentParser();parser.add_argument('--invalid-json',action='store_true');parser.add_argument('--read-error',type=int,default=0);a=parser.parse_args()
    name='invalid-json' if a.invalid_json else ('read-error' if a.read_error else 'valid')
    path=OUT/(name+'.json');report=json.loads(path.read_text())
    u,symbols,call=active_machine
    word=lambda a:struct.unpack('<I',u.mem_read(a,4))[0]
    # Linked shared 32-bit C layout: eight header words, fifteen IO words,
    # requested/completed/failed, then registered. Pin the header separately.
    owner=symbols['x70_stock_choice_settings'];runtime=symbols['x70_settings_runtime']
    settings=dict(registered=word(owner+104),loads=word(owner+52),found=word(owner+68),last_error=word(owner+64),
                  owners=word(runtime+128),running=word(runtime+140),last_start_status=word(runtime+144))
    assert settings==dict(registered=2,loads=1,found=0,last_error=0,owners=1,running=1,last_start_status=0),settings
    startup_evidence['settings_defaults']=settings
    report['fixture_checker_sha256']=report.pop('checker_sha256')
    report.update(scope=__doc__,checker_sha256=sha(Path(__file__).read_bytes()),
                  original_common_checker_sha256=sha(original.read_bytes()),adapted_common_checker_sha256=sha(source.encode()),
                  startup_adapter_sha256=sha(Path(make_machine.__code__.co_filename).read_bytes()),
                  native_settings_startup=startup_evidence,settings_missing_lower_fixture=True)
    path.write_text(json.dumps(report,indent=2)+'\n')
    print('Policy-started common file/native UI/still case PASS',name,flush=True)

if __name__=='__main__':main()
