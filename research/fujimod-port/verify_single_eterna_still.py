"""Run the real still parameter body on the final single-ETERNA ELF.

Existing native UI setup, explicit class enables/settings, and selected key are
inputs. Execute the actual 0x170cda0 body and four consumers without API success
substitutes. This produces parameters, not pixels, encoder output or a JPEG.
"""
import json,struct
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
from verify_single_eterna_runtime import machine,ROOT,BUILD,OUT,RAM,sha


def main():
    (u,s,call,clock,exceptions),setup=machine()
    policy=json.loads((BUILD/'target.json').read_text())['symbols']['ui_display_off_policy']
    call(policy,task=True)
    word=lambda a:struct.unpack('<I',u.mem_read(a,4))[0]
    profile=0x1c2e8fc;settings=0x1dadedc;observations={};pending={k:[] for k in ['matrix','curve','luma']};entries=[]
    u.hook_add(UC_HOOK_CODE,lambda uc,a,z,d:entries.append(a),begin=0x170cda4,end=0x170cda4)
    for kind,handler,arg,ret in [('matrix','film_matrix_hook',0,0x156cff8),('curve','film_curve_hook',1,0x156d368),('luma','film_luma_hook',1,0x156e024)]:
        def enter(uc,a,z,d,kind=kind,arg=arg):pending[kind].append(word(uc.reg_read(UC_ARM_REG_R0)+arg*4))
        pc=s[handler];u.hook_add(UC_HOOK_CODE,enter,begin=pc,end=pc)
        def leave(uc,a,z,d,kind=kind):
            p=pending[kind].pop()
            if kind=='matrix':v=list(struct.unpack('<9h',u.mem_read(p+2,18)))
            elif kind=='curve':v=list(struct.unpack('<28H',u.mem_read(p,56)))
            else:v=dict(enabled=u.mem_read(p+5,1)[0],bounds=list(u.mem_read(p+0x60,4)),pairs=list(struct.unpack('<10H',u.mem_read(p+0x64,20))))
            observations.setdefault(kind,[]).append(v)
        u.hook_add(UC_HOOK_CODE,leave,begin=ret,end=ret)
    def chroma(uc,a,z,d):observations.setdefault('chroma',[]).append(list(struct.unpack('<4q',u.mem_read(uc.reg_read(UC_ARM_REG_R11)-0x44,32))))
    u.hook_add(UC_HOOK_CODE,chroma,begin=0x156d548,end=0x156d548)
    # Initialize once; native slot changes must retire ETERNA without touching padding.
    u.mem_write(profile,bytes(0x148));call(0x157a0fc,profile,task=True)
    u.mem_write(profile+0x145,b'\xa5\x5a\xc3')
    tail_writes=[]
    from unicorn import UC_HOOK_MEM_WRITE
    def watch_tail(uc,access,address,size,value,data):
        if address<profile+0x148 and address+size>profile+0x145:tail_writes.append([address,size])
    u.hook_add(UC_HOOK_MEM_WRITE,watch_tail)
    def assemble(key):
        assert not any(pending.values());observations.clear()
        call(0x154b700,0x1fc,key,task=True);assert word(s['film_choice_key'])==key
        for offset in [6,7,0x1a,0x1d,0x2b,0x2c,0x51]:u.mem_write(profile+offset,b'\x01')
        u.mem_write(settings,bytes(0x70));sp=u.reg_read(UC_ARM_REG_SP);u.reg_write(UC_ARM_REG_SP,sp-16)
        u.mem_write(sp-16,struct.pack('<3I',0xffffffff,settings,0))
        try:result=call(0x170cda0,0,0,0,0,task=True)
        finally:u.reg_write(UC_ARM_REG_SP,sp)
        assert not any(pending.values())
        return dict(result=result,groups=json.loads(json.dumps(observations)),tag=list(u.mem_read(profile+0x145,3)),
                    native_slot=u.mem_read(profile+0x52,1)[0],output_sha256=sha(u.mem_read(profile+0x1480,0x1674)))
    stock=assemble(0);eterna=assemble(32);returned=assemble(0)
    assert stock==returned and len(entries)==3
    assert stock['tag']==eterna['tag']==returned['tag']==[0xa5,0x5a,0xc3]
    assert tail_writes==[]
    data=bytes(u.mem_read(s['xt20_film_recipes'],224));groups=eterna['groups']
    assert eterna['native_slot']==9
    assert groups['matrix']==[list(struct.unpack_from('<9h',data,8))]
    assert groups['curve']==[list(struct.unpack_from('<28H',data,54))]
    chroma_values=struct.unpack_from('<4h',data,26)
    assert groups['chroma']==[[chroma_values[i] for i in [0,2,3,1]]]
    pairs=[]
    for j in range(5):pairs += [struct.unpack_from('<H',data,34+2*j)[0],struct.unpack_from('<H',data,44+2*j)[0]]
    assert groups['luma']==[dict(enabled=data[2],bounds=list(data[4:8]),pairs=pairs)]
    assert not clock.errors
    report=dict(scope=__doc__,status='PASS: final native still ETERNA and stock return',
        elf_sha256=sha((BUILD/'mods.elf').read_bytes()),setup=setup,body_entries=len(entries),
        four_groups_equal_linked_recipe=True,stock_before_after_equal=True,
        same_profile_reused_without_host_clear=True,profile_tail_unchanged=True,profile_tail_write_events=tail_writes,
        eterna_tag=eterna['tag'],native_slot=eterna['native_slot'],
        stock_output_sha256=stock['output_sha256'],eterna_output_sha256=eterna['output_sha256'],
        internal_success_stubs=0,sensor_capture=False,encoder_executed=False,JPEG_produced=False,
        hardware_verified=False,checker_sha256=sha(__import__('pathlib').Path(__file__).read_bytes()))
    OUT.mkdir(exist_ok=True);(OUT/'still.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
