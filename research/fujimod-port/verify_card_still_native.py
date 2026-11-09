"""AI-assisted real still parameter body with supplied native settings inputs.

Reuse the frozen card-processing machine setup. Execute 0x170cda0 and its real
consumer bodies; no stock trampoline, kernel or device reply is substituted.
The native profile constructor and explicit data-class enables/settings are
inputs, not sensor capture, native mount, scheduler or camera qualification.
"""
import hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
import verify_card_processing as processing

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'card-still-native-check-unverified'

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    freeze=json.loads((processing.BUILD/'freeze.json').read_text())['files']
    fixture=Path(processing.__file__).resolve();assert sha(fixture.read_bytes())==freeze[str(fixture)]
    (u,symbols,call,api,clock,init,exceptions),setup=processing.make_machine()
    word=lambda a:struct.unpack('<I',u.mem_read(a,4))[0]
    profile=0x1c2e8fc;settings=0x1dadedc;observations={};pending={k:[] for k in ['matrix','curve','luma']};entries=[]
    state=symbols['xt2_card_access_state']
    def body(uc,a,z,d):entries.append(a);assert word(state)==1
    u.hook_add(UC_HOOK_CODE,body,begin=0x170cda4,end=0x170cda4)
    for kind,handler,arg,ret in [('matrix','film_matrix_hook',0,0x156cff8),('curve','film_curve_hook',1,0x156d368),('luma','film_luma_hook',1,0x156e024)]:
        def enter(uc,a,z,d,kind=kind,arg=arg):
            assert word(state)==1
            pending[kind].append(word(uc.reg_read(UC_ARM_REG_R0)+arg*4))
        pc=symbols[handler];u.hook_add(UC_HOOK_CODE,enter,begin=pc,end=pc)
        def leave(uc,a,z,d,kind=kind):
            p=pending[kind].pop()
            if kind=='matrix':v=list(struct.unpack('<9h',u.mem_read(p+2,18)))
            elif kind=='curve':v=list(struct.unpack('<28H',u.mem_read(p,56)))
            else:v=dict(enabled=u.mem_read(p+5,1)[0],bounds=list(u.mem_read(p+0x60,4)),pairs=list(struct.unpack('<10H',u.mem_read(p+0x64,20))))
            observations.setdefault(kind,[]).append(v)
        u.hook_add(UC_HOOK_CODE,leave,begin=ret,end=ret)
    def chroma(uc,a,z,d):
        observations.setdefault('chroma',[]).append(list(struct.unpack('<4q',u.mem_read(uc.reg_read(UC_ARM_REG_R11)-0x44,32))))
    u.hook_add(UC_HOOK_CODE,chroma,begin=0x156d548,end=0x156d548)
    def document(variant):
        return dict(name='Still '+variant,base='provia',icon='custom',
            matrix=([900,10,20,30,1100,40,50,60,1200] if variant=='A' else [1200,70,60,50,1000,40,30,20,800]),
            chroma=([1100,900,50,-30] if variant=='A' else [800,1200,-40,60]),
            luma=dict(bounds=[40,80,160,220],shift=([10,20,30,40,50] if variant=='A' else [-10,-20,-30,-40,-50]),gain=([260,270,280,290,300] if variant=='A' else [300,290,280,270,260])),
            tone_curve=dict(combined=dict(widths=[2,2,3,4,5,5,5,6,6],points=[round(16383*((i/27) if variant=='A' else (i/27)**2)) for i in range(28)])))
    def store(variant):
        user,text=processing.RAM+0xa000,processing.RAM+0xa800;doc=json.dumps(document(variant)).encode()
        u.mem_write(user,bytes(556));u.mem_write(user,struct.pack('<I',200));u.mem_write(user+406,b'200TEST.JSN\0')
        u.mem_write(text,doc+b'\0');assert api('film_parse',user,text,len(doc))==0
        assert api('film_user_store',user)==0;api('film_user_publish')
    def assemble(key):
        assert not any(pending.values());observations.clear()
        call(0x154b700,0x1fc,key,task=True);assert word(symbols['film_choice_key'])==key
        u.mem_write(profile,bytes(0x148));call(0x157a0fc,profile,task=True)
        for offset in [6,7,0x1a,0x1d,0x2b,0x2c,0x51]:u.mem_write(profile+offset,b'\x01')
        u.mem_write(settings,bytes(0x70))
        sp=u.reg_read(UC_ARM_REG_SP);u.reg_write(UC_ARM_REG_SP,sp-16)
        u.mem_write(sp-16,struct.pack('<3I',0xffffffff,settings,0))
        try:result=call(0x170cda0,0,0,0,0,task=True)
        finally:u.reg_write(UC_ARM_REG_SP,sp)
        assert word(state)==0 and not any(pending.values())
        return dict(result=result,groups=json.loads(json.dumps(observations)),tag=list(u.mem_read(profile+0x145,3)),
                    native_slot=u.mem_read(profile+0x52,1)[0],profile_flags=word(profile+0x6c),output_sha256=sha(u.mem_read(profile+0x1480,0x1674)))
    stock=assemble(0);print('Native stock still body returned; groups',list(stock['groups']),flush=True)
    # Check that the same real still body preserves all six already supplied
    # immutable recipes. Local linked table values are a compatibility oracle,
    # not independent donor/camera evidence; do not publish their raw values.
    builtins=[]
    for index in range(6):
        data=bytes(u.mem_read(symbols['xt20_film_recipes']+224*index,224))
        actual=assemble(32+index);groups=actual['groups']
        assert actual['tag']==[index+1,0x58,0x54] and actual['native_slot']==9,actual
        assert groups['matrix']==[list(struct.unpack_from('<9h',data,8))],actual
        assert groups['curve']==[list(struct.unpack_from('<28H',data,54))],actual
        chroma_values=struct.unpack_from('<4h',data,26)
        assert groups['chroma']==[[chroma_values[i] for i in [0,2,3,1]]],actual
        pairs=[]
        for j in range(5):pairs += [struct.unpack_from('<H',data,34+2*j)[0],struct.unpack_from('<H',data,44+2*j)[0]]
        assert groups['luma']==[dict(enabled=data[2],bounds=list(data[4:8]),pairs=pairs)],actual
        builtins.append(dict(key=32+index,tag=actual['tag'],four_groups_equal_linked_recipe=True,output_sha256=actual['output_sha256']))
    print('Native still six builtins /24 group comparisons PASS',flush=True)
    cases=[]
    for variant in ['A','B']:
        store(variant);actual=assemble(38);doc=document(variant);groups=actual['groups']
        assert actual['tag']==[7,0x58,0x54] and actual['native_slot']==0,actual
        assert set(groups)=={'matrix','curve','chroma','luma'},actual
        assert groups['matrix']==[doc['matrix']],actual
        assert groups['curve']==[doc['tone_curve']['combined']['points']],actual
        assert groups['chroma']==[[doc['chroma'][i] for i in [0,2,3,1]]],actual
        pairs=[]
        for shift,gain in zip(doc['luma']['shift'],doc['luma']['gain']):pairs.extend([shift&0xffff,gain])
        assert groups['luma']==[dict(enabled=1,bounds=doc['luma']['bounds'],pairs=pairs)],actual
        assert actual['groups']!=stock['groups'];cases.append(dict(variant=variant,**actual))
        print('Native still body JSON',variant,'four groups PASS',flush=True)
    assert cases[0]['groups']!=cases[1]['groups']
    OUT.mkdir(exist_ok=True)
    report=dict(scope=__doc__,status='PASS',setup=setup,stock=stock,builtins=builtins,cases=cases,native_body_entries=entries,
                native_still_body_executed=True,stock_trampoline_surrogates=0,kernel_api_stubs=0,
                supplied_settings_hex='00'*0x70,optional_lens_index=-1,profile_enable_offsets=[6,7,0x1a,0x1d,0x2b,0x2c,0x51],
                native_lazy_vfp_exceptions=exceptions,elf_sha256=sha((processing.BUILD/'mods.elf').read_bytes()),
                input_sha256={str(fixture):sha(fixture.read_bytes()),str(Path(__file__).resolve()):sha(Path(__file__).read_bytes())},
                full_capture=False,full_startup=False,hardware_verified=False)
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
