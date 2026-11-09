"""AI-assisted saved choice restore through native settings/file/codec paths.

No manual mod-init loop or loader boot in the adapted file-chain check. Native
FS/timer constructor order, borrowed UI1, calibration/REC/settings/FS boundaries
remain explicit. This is not a scheduled first policy call or full camera boot.
"""
import argparse,hashlib,inspect,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
import verify_common_card_file as common
import verify_card_still_native as still
from common_late_start_setup import make_machine
from verify_card_processing import BUILD
from verify_cardio_native_worker import RAM,RETURN

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'common-settings-restore-check-unverified'
startup_workers={}
startup_evidence={}
active_machine=None
active_context=None
SAVED_NAMES=['eterna','classic_neg','bleach_bypass','nostalgic_neg','reala_ace','neutral','card_1']
SAVED_CHOICE='eterna'

def sha(b):return hashlib.sha256(b).hexdigest()

def settle_startup(m,fs,ticks,callbacks):
    # Both documents are locally supplied at the same existing three lower
    # filesystem boundaries; native open/read/close and codecs are unchanged.
    film_blob,film_error=fs.blob,fs.read_error
    settings_document=json.dumps(dict(stock_choices=dict(current=dict(values=[dict(setting='film_simulation',value=SAVED_CHOICE)])))).encode()
    fs.blob=settings_document.ljust(3008,b' ');fs.read_error=0
    ticks(121)
    job=m.word(m.symbols['x70_cardio_active']);assert job
    folder=bytes(m.u.mem_read(job+56,40)).split(b'\0',1)[0]
    name=bytes(m.u.mem_read(job+112,16)).split(b'\0',1)[0]
    assert folder==b'FUJIMOD' and name==b'SETTINGS.JSN',(folder,name)
    runs=[]
    for operation in ['settings-open','settings-read','settings-close']:
        outer=m.u.context_save()
        for entry,end,loop,stack,arg in [(0x969b54,0x969c00,0x969bb8,RAM+0xd000,0x9c3540),
                                         (0x969fcc,0x96a090,0x96a00c,RAM+0xb000,0)]:
            if entry in startup_workers:
                m.u.context_restore(startup_workers[entry]);m.u.emu_start(end,RETURN,count=1)
                assert m.u.reg_read(UC_ARM_REG_PC)==loop;start=loop
            else:
                m.u.context_restore(outer);m.u.reg_write(UC_ARM_REG_SP,stack)
                m.u.reg_write(UC_ARM_REG_LR,RETURN);m.u.reg_write(UC_ARM_REG_R0,arg);start=entry
            m.execute_to(start,end);startup_workers[entry]=m.u.context_save()
            runs.append(dict(operation=operation,start=hex(start),end=hex(end)))
        m.u.context_restore(outer)
    assert [(c['kind'],c['status']) for c in callbacks]==[('cb_open_read',0),('cb_read',0),('cb_close_read',0)],callbacks
    assert callbacks[1]['value']==3008 and m.semaphore_results==[0]
    assert m.word(m.symbols['x70_cardio_active'])==0
    startup_evidence.update(folder=folder.decode(),name=name.decode(),callbacks=list(callbacks),
                            lower_calls=list(fs.trace),workers=runs,settings_document_sha256=sha(fs.blob),lookup_error=0)
    callbacks.clear();fs.trace.clear();fs.blob=film_blob;fs.read_error=film_error
    print('Native SETTINGS.JSN open/read/close returned supplied choice document',flush=True)

def check_restore(m):
    key=m.word(m.symbols['film_choice_key']);stock=m.call(0xb510b8,0x1fc,0)
    index=SAVED_NAMES.index(SAVED_CHOICE);expected=32+index
    assert key==expected and stock==0,(key,stock,expected)
    startup_evidence.setdefault('restored_choice_observations',[]).append(dict(stage='before film listing',key=key,native_stored=stock))
    if SAVED_CHOICE=='card_1':
        assert m.word(m.symbols['film_card_count'])==m.word(m.symbols['film_card_shown'])==0
        assert m.api('film_xt20_select',0)==0
        print('Saved card_1 waits for its hidden row; native stock remains Provia',flush=True)
        return
    check_restored_still(m,key,index)

def verify_shown(m):
    index=SAVED_NAMES.index(SAVED_CHOICE);key=m.word(m.symbols['film_choice_key'])
    assert key==32+index,(SAVED_CHOICE,key)
    startup_evidence.setdefault('restored_choice_observations',[]).append(dict(stage='after native UI row show',key=key))
    if SAVED_CHOICE=='card_1':check_restored_still(m,key,index)

def check_restored_still(m,key,index):
    # Reuse the exact still checker on this loaded machine. Omit its explicit
    # property setter, so settings decode remains the sole source of key32.
    path=Path(still.__file__).resolve()
    pins=json.loads((ROOT/'common-late-start-check-unverified/freeze.json').read_text())['files']
    assert sha(path.read_bytes())==pins[str(path)]
    source=inspect.getsource(still.main);anchor='    stock=assemble(0);';assert source.count(anchor)==1
    prefix=source.split(anchor)[0]
    old='(u,symbols,call,api,clock,init,exceptions),setup=processing.make_machine()'
    assert prefix.count(old)==1
    prefix=prefix.replace(old,'(u,symbols,call,api,clock,init,exceptions),setup=SUPPLIED_MACHINE')
    setter="call(0x154b700,0x1fc,key,task=True);assert word(symbols['film_choice_key'])==key"
    assert prefix.count(setter)==1
    prefix=prefix.replace(setter,"assert word(symbols['film_choice_key'])==key")
    prefix=prefix.replace('def main():','def restored_helpers():',1)+'    return assemble,entries\n'
    namespace=dict(vars(still));namespace['SUPPLIED_MACHINE']=active_context
    exec(compile(prefix,str(path)+'::restored-no-setter','exec'),namespace)
    assemble,entries=namespace['restored_helpers']();actual=assemble(key)
    card=SAVED_CHOICE=='card_1'
    recipe=m.symbols['film_card_recipes'] if card else m.symbols['xt20_film_recipes']+224*index
    data=bytes(m.u.mem_read(recipe,224));groups=actual['groups']
    assert actual['native_slot']==(0 if card else 9) and actual['tag']==[index+1,0x58,0x54]
    assert groups['matrix']==[list(struct.unpack_from('<9h',data,8))]
    assert groups['curve']==[list(struct.unpack_from('<28H',data,54))]
    chroma=struct.unpack_from('<4h',data,26)
    assert groups['chroma']==[[chroma[i] for i in [0,2,3,1]]]
    pairs=[]
    for j in range(5):pairs += [struct.unpack_from('<H',data,34+2*j)[0],struct.unpack_from('<H',data,44+2*j)[0]]
    assert groups['luma']==[dict(enabled=data[2],bounds=list(data[4:8]),pairs=pairs)]
    assert len(entries)==1
    startup_evidence['restored_still']=dict(result=actual,body_entries=list(entries),explicit_selection_setters=0,
                                           adapted_prefix_sha256=sha(prefix.encode()),original_checker_sha256=sha(path.read_bytes()))
    print('Saved',SAVED_CHOICE,'restored into actual still groups without a selection setter',flush=True)

def make_started_machine():
    global active_machine,active_context
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
    active_context=((u,symbols,call,api,clock,list(map(hex,inits)),exceptions),setup)
    return (u,symbols,call,api,clock,list(map(hex,inits)),exceptions),setup

def main():
    global SAVED_CHOICE
    preliminary=argparse.ArgumentParser(add_help=False);preliminary.add_argument('--saved-choice',choices=SAVED_NAMES,default='eterna')
    SAVED_CHOICE=preliminary.parse_known_args()[0].saved_choice
    # Retain the existing checker's CLI, native FS boundary, parser/UI and
    # still numeric assertions. Only startup setup/order is replaced.
    freeze=json.loads((ROOT/'common-card-file-check-unverified/freeze.json').read_text())['files']
    original=Path(common.__file__).resolve();assert sha(original.read_bytes())==freeze[str(original)]
    source=inspect.getsource(common.main)
    parse='args=parser.parse_args()';assert source.count(parse)==1
    source=source.replace(parse,"parser.add_argument('--saved-choice',choices=SAVED_NAMES,default='eterna');"+parse)
    constructors='    for entry in [0xcec598,0xcec634,0xcdf570]:assert m.call(entry)==0\n'
    assert source.count(constructors)==1;source=source.replace(constructors,'')
    anchor="    code='def execute():\\n'+body"
    assert source.count(anchor)==1
    source=source.replace(anchor,"    boot=\"    m.api('film_loader_boot');ticks(121);assert state()[0]==1\\n\"\n"
        "    assert body.count(boot)==1\n"
        "    body=body.replace(boot,\"    SETTLE_STARTUP(m,fs,ticks,callbacks)\\n    ticks(121);assert state()[0]==1;CHECK_RESTORE(m)\\n\")\n"
        "    old_workers='    workers={};runs=[]\\n';assert body.count(old_workers)==1\n"
        "    body=body.replace(old_workers,'    workers=BOOT_WORKERS;runs=[]\\n')\n"
        "    old_live=\"m.word(m.symbols['live'])==2\";assert body.count(old_live)==1\n"
        "    body=body.replace(old_live,\"m.word(m.symbols['live'])==3\")\n"+anchor)
    old_namespace="namespace=dict(vars(filecheck));namespace.update("
    assert source.count(old_namespace)==1
    source=source.replace(old_namespace,"namespace=dict(vars(filecheck));namespace['SETTLE_STARTUP']=settle_startup;namespace['CHECK_RESTORE']=check_restore;namespace['BOOT_WORKERS']=startup_workers;namespace.update(")
    source=source.replace('def main():','def execute_case():',1)
    shown="assert m.word(symbols['film_card_shown'])==1"
    assert source.count(shown)==1
    source=source.replace(shown,shown+";VERIFY_SHOWN(m)")
    source=source.replace("namespace['CHECK_RESTORE']=check_restore;", "namespace['CHECK_RESTORE']=check_restore;namespace['VERIFY_SHOWN']=verify_shown;")
    namespace=dict(vars(common));namespace.update(make_machine=make_started_machine,OUT=OUT/SAVED_CHOICE,SAVED_NAMES=SAVED_NAMES,
                                                settle_startup=settle_startup,startup_workers=startup_workers,check_restore=check_restore,verify_shown=verify_shown,VERIFY_SHOWN=verify_shown)
    exec(compile(source,str(original)+'::actual-policy-start','exec'),namespace)
    namespace['execute_case']()
    parser=argparse.ArgumentParser();parser.add_argument('--invalid-json',action='store_true');parser.add_argument('--read-error',type=int,default=0);parser.add_argument('--saved-choice',choices=SAVED_NAMES,default='eterna');a=parser.parse_args()
    name='invalid-json' if a.invalid_json else ('read-error' if a.read_error else 'valid')
    path=OUT/SAVED_CHOICE/(name+'.json');report=json.loads(path.read_text())
    u,symbols,call=active_machine
    word=lambda a:struct.unpack('<I',u.mem_read(a,4))[0]
    # Linked shared 32-bit C layout: eight header words, fifteen IO words,
    # requested/completed/failed, then registered. Pin the header separately.
    owner=symbols['x70_stock_choice_settings'];runtime=symbols['x70_settings_runtime']
    settings=dict(registered=word(owner+104),loads=word(owner+52),found=word(owner+68),last_error=word(owner+64),
                  owners=word(runtime+128),running=word(runtime+140),last_start_status=word(runtime+144))
    assert settings==dict(registered=2,loads=1,found=1,last_error=0,owners=1,running=1,last_start_status=0),settings
    startup_evidence['settings_restore']=settings
    report['fixture_checker_sha256']=report.pop('checker_sha256')
    report.update(scope=__doc__,checker_sha256=sha(Path(__file__).read_bytes()),
                  original_common_checker_sha256=sha(original.read_bytes()),adapted_common_checker_sha256=sha(source.encode()),
                  startup_adapter_sha256=sha(Path(make_machine.__code__.co_filename).read_bytes()),
                  native_settings_startup=startup_evidence,settings_missing_lower_fixture=False,supplied_settings_document=True,saved_choice=SAVED_CHOICE)
    path.write_text(json.dumps(report,indent=2)+'\n')
    print('Policy-started common file/native UI/still case PASS',name,flush=True)

if __name__=='__main__':main()
