"""Native coherent parameter assembly with the existing card publisher.

AI-assisted bounded checker. Reuse the frozen native UI setup prefix, changing
only its selected candidate digest/path; no device model or successful API
reply is added. Profile/capture/calibration inputs and deliberate interleaving
boundaries are fixtures, not full boot or physical task/camera evidence.
"""
import hashlib
import inspect
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ
from unicorn.arm_const import *
import verify_card_films_menu as menu_fixture

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'card-films-expanded-build-unverified'
BUILD=ROOT/'card-processing-build-unverified'
OUT=ROOT/'card-processing-check-unverified'
RAM=0x8000000
RETURN=RAM+0xf000


def sha(data):return hashlib.sha256(data).hexdigest()


def make_machine(build=BUILD):
    path=Path(menu_fixture.__file__).resolve()
    frozen=json.loads((BASE/'freeze.json').read_text())['files']
    assert sha(path.read_bytes())==frozen[str(path)]
    source=inspect.getsource(menu_fixture.main);anchor='    selected=[]\n';assert source.count(anchor)==1
    prefix=source.split(anchor)[0]
    old="assert sha(raw)=='db56c69c993a30e9fbdfb024ad766e005234b50f76684082b29683a526dd3754'"
    assert prefix.count(old)==1
    prefix=prefix.replace(old,'assert sha(raw)==EXPECTED_ELF_SHA256')
    prefix=prefix.replace('def main():','def setup():',1)
    prefix+='    return u,symbols,call,api,clock,init,exceptions\n'
    namespace=dict(vars(menu_fixture));namespace['BUILD']=build
    namespace['EXPECTED_ELF_SHA256']=sha((build/'mods.elf').read_bytes())
    exec(compile(prefix,str(path)+':setup-prefix','exec'),namespace)
    return namespace['setup'](),dict(source_sha256=sha(path.read_bytes()),adapted_prefix_sha256=sha(prefix.encode()))


def main():
    (u,symbols,call,api,clock,init,exceptions),setup=make_machine()
    word=lambda address:struct.unpack('<I',u.mem_read(address,4))[0]
    profile=RAM+0x1000;out=RAM+0x4000;event=RAM+0x500
    state=symbols['xt2_card_access_state'];pending=symbols['xt2_card_publish_pending']
    observations={};awaiting={kind:[] for kind in ['matrix','curve','luma']}
    for kind,handler,argument,returns in [
        ('matrix','film_matrix_hook',0,[0x156cff8,0x1570038]),
        ('curve','film_curve_hook',1,[0x156d368,0x1570688]),
        ('luma','film_luma_hook',1,[0x1565e60,0x156e024])]:
        pc=symbols[handler]
        def enter(uc,a,z,d,kind=kind,argument=argument):
            pointer=word(uc.reg_read(UC_ARM_REG_R0)+argument*4);awaiting[kind].append(pointer)
        u.hook_add(UC_HOOK_CODE,enter,begin=pc,end=pc)
        def leave(uc,a,z,d,kind=kind):
            pointer=awaiting[kind].pop()
            if kind=='matrix':value=list(struct.unpack('<9h',u.mem_read(pointer+2,18)))
            elif kind=='curve':value=list(struct.unpack('<28H',u.mem_read(pointer,56)))
            else:value=dict(enabled=u.mem_read(pointer+5,1)[0],bounds=list(u.mem_read(pointer+0x60,4)),
                            pairs=list(struct.unpack('<10H',u.mem_read(pointer+0x64,20))))
            observations.setdefault(kind,[]).append(value)
        for target in returns:u.hook_add(UC_HOOK_CODE,leave,begin=target,end=target)
    def chroma(uc,a,z,d):
        offset=0x3c if a==0x156b048 else 0x44
        observations.setdefault('chroma',[]).append(list(struct.unpack('<4q',u.mem_read(uc.reg_read(UC_ARM_REG_R11)-offset,32))))
    for target in [0x156b048,0x156d548]:u.hook_add(UC_HOOK_CODE,chroma,begin=target,end=target)
    def document(variant):
        return dict(name='Card '+variant,base='provia',icon='custom',
            matrix=([900,10,20,30,1100,40,50,60,1200] if variant=='A' else [1200,70,60,50,1000,40,30,20,800]),
            chroma=([1100,900,50,-30] if variant=='A' else [800,1200,-40,60]),
            luma=dict(bounds=[40,80,160,220],shift=([10,20,30,40,50] if variant=='A' else [-10,-20,-30,-40,-50]),
                      gain=([260,270,280,290,300] if variant=='A' else [300,290,280,270,260])),
            tone_curve=dict(combined=dict(widths=[2,2,3,4,5,5,5,6,6],
                points=[round(16383*((i/27) if variant=='A' else (i/27)**2)) for i in range(28)])))
    def store(variant,task=True):
        user,text=RAM+0xa000,RAM+0xa800;doc=json.dumps(document(variant)).encode()
        u.mem_write(user,bytes(556));u.mem_write(user,struct.pack('<I',200));u.mem_write(user+406,b'200TEST.JSN\0')
        u.mem_write(text,doc+b'\0');result=call(symbols['film_parse'],user,text,len(doc),task=task)
        assert result==0,(variant,hex(result))
        assert call(symbols['film_user_store'],user,task=task)==0
    def make_profile(key):
        call(0x154b700,0x1fc,key,task=True);assert word(symbols['film_choice_key'])==key
        u.mem_write(profile,bytes(0x148));call(0x157a0fc,profile,task=True);call(0x157ac60,profile,0,task=True)
        # Explicit native data-class enable fields for the eight custom groups.
        # They are not camera/peripheral readiness values.
        for offset in [6,7,0x1a,0x1d,0x2b,0x2c,0x51]:u.mem_write(profile+offset,b'\x01')
        return bytes(u.mem_read(profile,0x148))
    def assemble(inputs):
        assert not any(awaiting.values())
        observations.clear();u.mem_write(profile,inputs);u.mem_write(out-16,b'\xa5'*(0x1674+32))
        call(0x1565c20,out,profile,task=True)
        assert bytes(u.mem_read(out-16,16))==bytes(u.mem_read(out+0x1674,16))==b'\xa5'*16
        assert word(state)==0
        return bytes(u.mem_read(out,0x1674)),json.loads(json.dumps(observations))
    def expected_groups(actual,variant):
        doc=document(variant)
        assert len(actual['matrix'])==len(actual['curve'])==2 and len(actual['chroma'])==len(actual['luma'])==1,actual.keys()
        assert actual['matrix']==[doc['matrix']]*2
        assert actual['curve']==[doc['tone_curve']['combined']['points']]*2
        assert actual['chroma']==[[doc['chroma'][i] for i in [0,2,3,1]]]
        pairs=[]
        for shift,gain in zip(doc['luma']['shift'],doc['luma']['gain']):pairs += [shift&0xffff,gain]
        assert actual['luma']==[dict(enabled=1,bounds=doc['luma']['bounds'],pairs=pairs)]
    stock_profile=make_profile(0);stock_output,stock_groups=assemble(stock_profile)
    store('A');api('film_user_publish');assert word(state)==0
    u.mem_write(event,bytes(80));assert call(0x14da7ac,event,task=True)==1
    assert word(symbols['film_card_shown'])==1
    card_profile=make_profile(38)
    assert card_profile[0x145:0x148]==bytes([7,0x58,0x54]) and card_profile[0x52]==0
    a_output,a_groups=assemble(card_profile)
    expected_groups(a_groups,'A');assert a_output!=stock_output
    print('Card A whole assembly and six group observations PASS',flush=True)
    original_table=bytes(u.mem_read(symbols['film_card_recipes'],224))
    results=[];base_sp=u.reg_read(UC_ARM_REG_SP)
    def set_call(entry,args,stack):
        for reg,value in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],list(args)+[0]*4):u.reg_write(reg,value)
        u.reg_write(UC_ARM_REG_SP,stack);u.reg_write(UC_ARM_REG_LR,RETURN)
        return entry
    def stop_once(entry,args,stack,pc):
        stopped=[]
        def stop(uc,a,z,d):stopped.append(a);uc.emu_stop()
        h=u.hook_add(UC_HOOK_CODE,stop,begin=pc,end=pc)
        try:u.emu_start(set_call(entry,args,stack),RETURN,count=3000000)
        finally:u.hook_del(h)
        assert stopped==[pc] and u.reg_read(UC_ARM_REG_PC)==pc
        return u.context_save(),pc
    def resume(context,pc,stack):
        u.context_restore(context);u.emu_start(pc,RETURN,count=3000000)
        assert u.reg_read(UC_ARM_REG_PC)==RETURN and u.reg_read(UC_ARM_REG_SP)==stack
    def output_bytes():
        assert bytes(u.mem_read(out-16,16))==bytes(u.mem_read(out+0x1674,16))==b'\xa5'*16
        assert not any(awaiting.values())
        return bytes(u.mem_read(out,0x1674))
    # Reader first: pause the real API after some groups have completed.
    observations.clear();u.mem_write(profile,card_profile);u.mem_write(out-16,b'\xa5'*(0x1674+32))
    context,pc=stop_once(0x1565c20,[out,profile],base_sp,symbols['film_luma_hook']+4)
    assert word(state)==1
    publications=word(symbols['film_card_publishes'])
    store('B',task=False);call(symbols['film_user_publish'],task=False)
    assert word(pending)==1 and word(state)==1 and word(symbols['film_card_publishes'])==publications
    assert bytes(u.mem_read(symbols['film_card_recipes'],224))==original_table
    resume(context,pc,base_sp)
    assert output_bytes()==a_output and word(state)==0
    expected_groups(observations,'A')
    api('film_cards_tick')  # existing observer's retry; not timer-thread delivery
    assert word(pending)==0 and word(state)==0 and word(symbols['film_card_publishes'])==publications+1
    b_output,b_groups=assemble(card_profile);expected_groups(b_groups,'B');assert b_output!=a_output
    b_table=bytes(u.mem_read(symbols['film_card_recipes'],224));assert b_table!=original_table
    results.append(dict(case='publication deferred while native API reads',old_output_unchanged=True,retried_on_existing_observer=True,next_output_changed=True))
    print('Reader-first native interleaving PASS',flush=True)
    # Writer first: stop after a genuine partial table copy, not a supplied
    # successful publication. Start a native reader, then finish the writer
    # while that reader is paused. Its complete output must remain stock.
    store('A');table=symbols['film_card_recipes'];touched=set();armed=[False];writer_stop=[]
    def store_watch(uc,access,address,size,value,data):
        if max(address,table)<min(address+size,table+224):
            touched.update(range(max(address,table)-table,min(address+size,table+224)-table))
            if len(touched)>=80:armed[0]=True
    def stop_writer(uc,address,size,data):
        if armed[0]:writer_stop.append(address);uc.emu_stop()
    h=u.hook_add(UC_HOOK_MEM_WRITE,store_watch);h2=u.hook_add(UC_HOOK_CODE,stop_writer)
    try:u.emu_start(set_call(symbols['film_user_publish'],[],base_sp),RETURN,count=3000000)
    finally:u.hook_del(h);u.hook_del(h2)
    assert len(writer_stop)==1 and 0<len(touched)<224 and word(state)==0x80000000
    partial=bytes(u.mem_read(table,224));assert partial not in (original_table,b_table)
    writer_context=u.context_save();writer_pc=u.reg_read(UC_ARM_REG_PC)
    observations.clear();u.mem_write(profile,card_profile);u.mem_write(out-16,b'\xa5'*(0x1674+32))
    reads=[];actor=['reader']
    def read_watch(uc,access,address,size,value,data):
        if actor[0]=='reader':reads.append([address,size])
    h=u.hook_add(UC_HOOK_MEM_READ,read_watch,begin=table,end=table+223)
    reader_context,reader_pc=stop_once(0x1565c20,[out,profile],RAM+0xe000,symbols['film_luma_hook']+4)
    assert word(state)==0xc0000001
    actor[0]='writer';resume(writer_context,writer_pc,base_sp)
    assert word(state)==0x40000001 and bytes(u.mem_read(table,224))==original_table
    actor[0]='reader';resume(reader_context,reader_pc,RAM+0xe000)
    u.hook_del(h)
    assert output_bytes()==stock_output and word(state)==0 and not reads
    # Return to the borrowed UI caller stack after the explicit scratch reader.
    u.reg_write(UC_ARM_REG_SP,base_sp)
    after_output,after_groups=assemble(card_profile);expected_groups(after_groups,'A')
    assert after_output==a_output
    results.append(dict(case='reader starts during partial publication; writer finishes midway',stock_only_entire_output=True,card_table_reads_during_fallback=0,next_output_custom=True))
    print('Writer-first native interleaving PASS',flush=True)
    # Verify the seven-argument wrapper mechanically with an explicit surrogate
    # at our stock trampoline. This is NOT execution of the native still body.
    forwarded=[];arguments=[0x101,0x202,0x303,0x404,0xffff8001,0xabcdef00,0x7654]
    def forwarding_boundary(uc,address,size,data):
        values=[uc.reg_read(reg) for reg in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]]
        stack=uc.reg_read(UC_ARM_REG_SP);assert not stack&7
        values += list(struct.unpack('<3I',uc.mem_read(stack,12)))
        assert word(state)==1;forwarded.append(values)
        uc.reg_write(UC_ARM_REG_R0,0x13579bdf);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
    target=symbols['xt2_still_params_build_guard_stock']
    h=u.hook_add(UC_HOOK_CODE,forwarding_boundary,begin=target,end=target)
    u.reg_write(UC_ARM_REG_SP,base_sp-16);u.mem_write(base_sp-16,struct.pack('<3I',*arguments[4:]))
    try:result=call(0x170cda0,*arguments[:4],task=True)
    finally:u.hook_del(h);u.reg_write(UC_ARM_REG_SP,base_sp)
    assert forwarded==[arguments] and result==0x13579bdf and word(state)==0
    results.append(dict(case='still API seven-argument wrapper',forwarded=True,native_body_executed=False,surrogate_trampoline=True))
    print('Still wrapper ABI7 boundary PASS',flush=True)
    OUT.mkdir(exist_ok=True)
    (OUT/'verification.json').write_text(json.dumps(dict(scope=__doc__,status='PASS',setup=setup,groups=a_groups,cases=results,
        stock_sha256=sha(stock_output),card_a_sha256=sha(a_output),elf_sha256=sha((BUILD/'mods.elf').read_bytes()),
        native_lazy_vfp_exceptions=exceptions,native_central_api_executed=True,central_kernel_api_stubs=0,
        native_still_body_executed=False,still_trampoline_surrogates=1,manual_observer_retry=True,
        checker_sha256=sha(Path(__file__).read_bytes()),hardware_verified=False),indent=2)+'\n')


if __name__=='__main__':main()
