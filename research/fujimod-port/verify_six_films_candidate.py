"""Bounded six-built-in transfer checks on the exact ordinary X-T2 ELF.

Native selection -> separately supplied processing contexts -> native builders.
Expected substitutions are the pinned upstream recipes, NOT native X100VI color
accuracy. Supplied init/mode/calibration/transport and independent stock contexts;
no continuous producer, hardware, actual scheduler or service-start proof.
The original shared-latch counterexample is recorded as an OPEN gate, not hidden.
AI-assisted original assay; no vendor coefficients are embedded in this source.
"""
import json
import struct
from pathlib import Path
from collections import deque
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
from unicorn.unicorn_py3.unicorn import uclib
from verify_ordinary_platform_nr import load, ROOT, START, END, sha
from verify_ordinary_platform_card import main as verify_card
from verify_ordinary_platform_processing import actual_factory, initialize, TRANSPORT, transport_calls
from verify_film_menu_navigation import invoke
from verify_interpolated_profile_outputs import runtime, call
from firmware_analysis import Firmware

BUILD=ROOT/'six-films-build-unverified'
OUT=ROOT/'six-films-check-unverified'
RAM=0x8000000
RETURN=RAM+0xf000
FILM=0x1fc
NAMES=['eterna','classic_neg','bleach_bypass','nostalgic_neg','reala_ace','neutral']
LAYOUTS={'matrix':(0x156fad8,20),'curve':(0x15703f8,0x44),'luma':(0x156b7d4,0x80),
         'family':(0x156a068,1),'gain':(0x156a140,44),'live':(0x156d348,0x120),
         'still':(0x1570668,0x100),'chroma':(0x156af80,50)}


def main():
    assert Path(uclib._name).resolve()==(ROOT.parents[1]/'.toolchains/unicorn-tci/libunicorn.2.dylib').resolve()
    verify_card(BUILD,54)
    sections,symbols,manifest=load(BUILD,54)
    actual=actual_factory();stock=runtime('xt2-4.41',False)
    kernel=next(d for a,d in Firmware('xt2-4.41',True).units if a==0x40000)
    stock.mem_map(0x40000,(len(kernel)+4095)&~4095);stock.mem_write(0x40000,kernel)
    loaded=[]
    for a,data,name,size in sections:
        if name in ('.x70mod.hooks','.x70mod.strings'):continue
        assert START<=a<a+size<=END,name
        actual.mem_write(a,data);loaded.append((a,data,name,size))
    for edit in manifest['edits']:
        assert bytes(actual.mem_read(edit['address'],4))==struct.pack('<I',edit['expected'])
        actual.mem_write(edit['address'],struct.pack('<I',edit['value']))
    visited=set();recent=deque(maxlen=12);writes=0;phase=['init']
    state=[(a,a+size) for a,data,name,size in loaded if name in ('.data','.bss','.x70mod.shared')]
    def watch(u,access,a,size,value,d):
        nonlocal writes
        allowed=[(RAM,RAM+0x10000),*state]
        if phase[0] in ('init','selection','menu'):
            allowed += [(0xffd000,0x1000000),(0x1180000,0x1235000),(0x1ab0000,0x1ad0000)]
        if phase[0]=='menu':allowed += [(0x1c5380c,0x1c53888),(0x1c763f4,0x1c763f6),(0x1de8350,0x1de8352),(0x1e0dd8c,0x1e0dd90),(0x10c4758,0x10c4780)]
        bounded_cursor_output=False
        if phase[0]=='menu':
            pc=u.reg_read(UC_ARM_REG_PC);buffer=u.reg_read(UC_ARM_REG_R4)
            bounded_cursor_output=(0xb518d4<=pc<0xb51a14 and
                0x10c4000<=buffer<buffer+40<=0x10c5000 and buffer<=a<a+size<=buffer+40)
        assert any(lo<=a<a+size<=hi for lo,hi in allowed) or bounded_cursor_output,(phase[0],hex(u.reg_read(UC_ARM_REG_PC)),hex(a),size)
        writes+=1
    actual.hook_add(UC_HOOK_MEM_WRITE,watch)
    def trace(u,a,s,d):visited.add(a);recent.append(hex(a))
    actual.hook_add(UC_HOOK_CODE,trace)
    def invoke_checked(u,entry,*args):
        regs=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
        values=[0x31410000+i for i in range(8)]
        for r,v in zip(regs,values):u.reg_write(r,v)
        try:result=invoke(u,entry,*args,instruction_limit=3000000 if phase[0] in ('selection','menu') else 200000)
        except Exception:
            print('FAULT',hex(entry),hex(u.reg_read(UC_ARM_REG_PC)),list(recent),flush=True);raise
        assert u.reg_read(UC_ARM_REG_SP)==RAM+0xe000
        assert [u.reg_read(r) for r in regs]==values,(hex(entry),'callee saved')
        return result
    initialize(actual,symbols,invoke_checked)
    phase[0]='processing'
    def select(index):
        phase[0]='selection'
        key=0 if index is None else 32+index
        invoke_checked(actual,0x154b700,FILM,key)
        stored=invoke_checked(actual,0xb510b8,FILM,0)
        assert stored==0 and int.from_bytes(actual.mem_read(symbols['film_choice_key'],4),'little')==key
        phase[0]='processing'
        return stored
    def profile(u,at=RAM,stored=0,fields=None,slot=None):
        u.mem_write(at,bytes(0x200))
        invoke_checked(u,0x157a0fc,at);invoke_checked(u,0x157ac60,at,stored)
        for off,v in {0x51:1,**(fields or {})}.items():u.mem_write(at+off,bytes([v]))
        if slot is not None:u.mem_write(at+0x52,bytes([slot]))
    def output(u,kind,context=RAM,base=RAM+0x2000):
        entry,n=LAYOUTS[kind];u.mem_write(base-16,b'\xcc'*0x240)
        args={'matrix':(base,context),'curve':(context,base,base+0x40,base+0x42),
              'family':(context,0,base),'gain':(context,1,base)}.get(kind,(context,base))
        invoke_checked(u,entry,*args)
        assert bytes(u.mem_read(base-16,16))==b'\xcc'*16 and bytes(u.mem_read(base+n,16))==b'\xcc'*16,kind
        return bytes(u.mem_read(base,n))
    recipes=[]
    for i,name in enumerate(NAMES):
        data=bytes(actual.mem_read(symbols['xt20_film_recipes']+224*i,224))
        recipes.append(dict(name=name,value=data[0],family=data[1],luma=data[2],channels=data[3],
            bounds=data[4:8],matrix=struct.unpack_from('<9h',data,8),chroma=struct.unpack_from('<4h',data,26),
            luma_pairs=b''.join(data[34+2*j:36+2*j]+data[44+2*j:46+2*j] for j in range(5)),
            curves=[data[54+56*j:110+56*j] for j in range(3)],keep=data[222],sha256=sha(data)))
    assert [r['value'] for r in recipes]==list(range(18,24)) and all(r['keep']==0 for r in recipes)
    # Preserve the qualified ETERNA result on a separately loaded exact baseline.
    baseline=actual_factory()
    base_sections,base_symbols,base_manifest=load(ROOT/'modular-build-unverified',52)
    for a,data,name,size in base_sections:
        if name not in ('.x70mod.hooks','.x70mod.strings'):baseline.mem_write(a,data)
    for edit in base_manifest['edits']:
        assert bytes(baseline.mem_read(edit['address'],4))==struct.pack('<I',edit['expected'])
        baseline.mem_write(edit['address'],struct.pack('<I',edit['value']))
    baseline.mem_write(base_symbols['ui_mode'],b'\x03')
    for address in range(base_symbols['__xpp_init_start'],base_symbols['__xpp_init_end'],4):
        invoke_checked(baseline,int.from_bytes(baseline.mem_read(address,4),'little'))
    assert int.from_bytes(baseline.mem_read(base_symbols['film_choice_status'],4),'little')==0
    phase[0]='selection';invoke_checked(baseline,0x154b700,FILM,32);phase[0]='processing'
    profile(baseline)
    records=[]
    select(None)
    for stored in range(18):
        for u in (actual,stock):profile(u,stored=stored)
        assert actual.mem_read(RAM+0x52,1)==stock.mem_read(RAM+0x52,1)
        for kind in LAYOUTS:
            if kind=='chroma':continue
            a=output(actual,kind);b=output(stock,kind);assert a==b,('stock',stored,kind)
            records.append(dict(stage='stock',stored=stored,kind=kind,equal_stock=True,sha256=sha(a)))
    for i,r in enumerate(recipes):
        selected=select(i);profile(actual,stored=selected);profile(stock,slot=9)
        assert actual.mem_read(RAM+0x52,1)==b'\x09'
        observations={}
        for kind in LAYOUTS:
            a=output(actual,kind);b=output(stock,kind);expected=bytearray(b)
            if kind=='matrix':expected[0]=1;struct.pack_into('<9h',expected,2,*r['matrix'])
            elif kind=='curve':expected[:56]=r['curves'][0]
            elif kind=='family':expected[0]=r['family'] or b[0]
            elif kind=='luma':
                expected[5]=r['luma'];expected[0x60:0x64]=r['bounds'];expected[0x64:0x78]=r['luma_pairs']
            elif kind in ('live','still'):
                offsets=(0x6c,0xa8,0xe4) if kind=='live' else (0x4a,0x86,0xc2)
                for j,off in enumerate(offsets):expected[off:off+56]=r['curves'][j if r['channels'] else 0]
            elif kind=='gain' and r['family']:
                assert r['name']=='eterna'
                assert a==output(baseline,kind)
                records.append(dict(stage='builtin',name=r['name'],kind=kind,equal_qualified_eterna_baseline=True,sha256=sha(a)))
                observations[kind]=a;continue
            elif kind=='chroma':
                observations[kind]=a;continue
            assert a==bytes(expected),(r['name'],kind,a.hex(),bytes(expected).hex())
            records.append(dict(stage='builtin',name=r['name'],kind=kind,equal_expected_substitution=True,sha256=sha(a)))
            observations[kind]=a
        if i==0:
            for kind in LAYOUTS:
                assert observations[kind]==output(baseline,kind),('ETERNA baseline',kind)
                records.append(dict(stage='eterna-baseline',kind=kind,equal_baseline=True))
            for setting in range(9):
                for channel in range(6):
                    rows=[]
                    for u in (actual,baseline):
                        u.mem_write(RAM+0x2000,b'\xcc'*60)
                        invoke_checked(u,0x1569be4,10,setting,channel,RAM+0x2000)
                        assert bytes(u.mem_read(RAM+0x202c,16))==b'\xcc'*16
                        rows.append(bytes(u.mem_read(RAM+0x2000,44)))
                    assert rows[0]==rows[1],('gain10',setting,channel)
                    records.append(dict(stage='gain-family',setting=setting,channel=channel,equal_qualified_baseline=True))
        # Execute the second original select/read caller block with borrowed
        # frame; compare raw 4x64-bit rows before native scaling/arithmetic.
        actual.reg_write(UC_ARM_REG_R4,RAM);actual.reg_write(UC_ARM_REG_R11,RAM+0xc000)
        actual.reg_write(UC_ARM_REG_SP,RAM+0xb000)
        actual.mem_write(RAM+0xc000-0x60,b'\xcc'*0x60)
        actual.emu_start(0x156d4d4,0x156d548,count=200000)
        assert actual.reg_read(UC_ARM_REG_PC)==0x156d548
        assert struct.unpack('<4q',bytes(actual.mem_read(RAM+0xc000-0x44,32)))==tuple(r['chroma'][j] for j in (0,2,3,1))
        assert bytes(actual.mem_read(RAM+0xc000-0x60,16))==b'\xcc'*16 and bytes(actual.mem_read(RAM+0xc000-0x24,16))==b'\xcc'*16
        records.append(dict(stage='builtin',name=r['name'],kind='chroma-native-caller',equal_recipe_row=True,full_chroma_sha256=sha(observations['chroma']),borrowed_frame=True))
        # Actual native stock selection clears the shared recipe path.
        select(None);profile(actual,stored=3);profile(stock,stored=3)
        for kind in ('matrix','live','still'):
            assert output(actual,kind)==output(stock,kind),(r['name'],'fallback',kind)
            records.append(dict(stage='fallback',name=r['name'],kind=kind,equal_stock=True))
    # Distinguish disabled scale from enabled zero on every built-in.
    for i,r in enumerate(recipes):
        select(i)
        for label,fields,scale in [('disabled',{0x67:7,0x9b:0,0x9a:0},100),('nonzero',{0x67:7,0x9b:1,0x9a:8},126),('zero',{0x67:7,0x9b:1,0x9a:10,0x9c:0},0)]:
            profile(actual,fields=fields);a=output(actual,'matrix')
            assert struct.unpack_from('<9h',a,2)==tuple(int(v*scale/100) for v in r['matrix'])
            records.append(dict(stage='scale',name=r['name'],case=label,pass_check=True))
    for i,r in enumerate(recipes):
        select(i)
        for u in (actual,stock):profile(u,fields={0x144:1},slot=9 if u is stock else None)
        for kind in LAYOUTS:
            assert output(actual,kind)==output(stock,kind),(r['name'],'special',kind)
            records.append(dict(stage='special',name=r['name'],kind=kind,equal_stock=True))
        for key in (0xb5,0xf740):
            for u in (actual,stock):
                u.mem_write(0x9000000+key,b'\x01');profile(u,slot=9 if u is stock else None)
            for kind in ('curve','live','still'):
                assert output(actual,kind)==output(stock,kind),(r['name'],'forced',hex(key),kind)
                records.append(dict(stage='forced',name=r['name'],key=key,kind=kind,equal_stock=True))
            for u in (actual,stock):u.mem_write(0x9000000+key,b'\x00')
    menus=[]
    select(None)
    actual.mem_write(0x119299b,bytes([0,14,7]));actual.mem_write(0x119f2cb,b'\x00')
    for descriptor,count in [(0xeea334,15),(0xebcdfc,15),(0xedaaac,21)]:
        phase[0]='menu';actual.mem_write(0x11802c0,struct.pack('<I',descriptor))
        invoke_checked(actual,0x13df330,0,0,0,0)
        observed=int.from_bytes(actual.mem_read(0x11802d8,4),'little');assert observed==count,(hex(descriptor),observed)
        ptr=int.from_bytes(actual.mem_read(descriptor+16,4),'little')
        rows=[int.from_bytes(actual.mem_read(ptr+8*j,4),'little') for j in range(count)]
        assert rows[-6:]==list(range(32,38))
        reached=set();events=[]
        for event in [4]*(2*count)+[5]*(2*count):
            invoke_checked(actual,0x13debf0,event,actual.mem_read(descriptor,1)[0],1,0)
            assert invoke_checked(actual,0xb518d4,RAM+0x3000)==1
            setting=int.from_bytes(actual.mem_read(RAM+0x3008,2),'little')
            key=int.from_bytes(actual.mem_read(RAM+0x300c,4),'little')
            assert setting==FILM and key in rows
            if 32<=key<38:
                invoke_checked(actual,0x154b700,setting,key)
                assert int.from_bytes(actual.mem_read(symbols['film_choice_key'],4),'little')==key
                reached.add(key)
            events.append(dict(event=event,key=key))
        assert reached==set(range(32,38)),(hex(descriptor),reached)
        menus.append(dict(descriptor=descriptor,count=count,rows=rows,all_six_reached=True,events=events,native_commit_boundary=True))
    phase[0]='processing'
    captions=[]
    expected_captions=['ETERNA','CLASSIC Neg.','ETERNA BLEACH BYPASS','NOSTALGIC Neg.','REALA ACE','NEUTRAL']
    for i,name in enumerate(NAMES):
        word=invoke_checked(actual,0x13db71c,9,9+i,2)
        assert word==symbols[name+'_text']
        magic,text=struct.unpack('<II',bytes(actual.mem_read(word,8)));assert magic==0x54787058
        label=bytes(actual.mem_read(text,64)).split(b'\x00')[0].decode();assert label==expected_captions[i]
        obj=RAM+0x4000;blob=bytearray(0x60);struct.pack_into('<III',blob,4,word,0,16)
        blob[0x28:0x40]=bytes(range(24));actual.mem_write(obj,bytes(blob))
        def through_caption():
            actual.reg_write(UC_ARM_REG_R0,obj);actual.reg_write(UC_ARM_REG_SP,RAM+0xe000);actual.reg_write(UC_ARM_REG_LR,RETURN)
            actual.emu_start(0x24b9ffc,0x24ba000,count=200000)
            assert actual.reg_read(UC_ARM_REG_PC)==0x24ba000
            return bytes(actual.mem_read(obj,0x60))
        converted=through_caption();assert int.from_bytes(converted[12:16],'little')==13 and int.from_bytes(converted[8:12],'little')==text
        nativeword=invoke_checked(actual,0x13db71c,9,0,2);actual.mem_write(obj+4,struct.pack('<I',nativeword))
        restored=through_caption();assert int.from_bytes(restored[12:16],'little')==16 and restored[0x28:0x40]==bytes(blob[0x28:0x40])
        captions.append(dict(name=name,text=label,native_fn_record=True,actual_osd_thunk=True,stock_style_restored=True,full_draw=False))
    # Reproduce, do not conceal, the original global-latch contract failure.
    select(0);profile(actual);before=output(actual,'matrix')
    select(1);profile(actual,at=RAM+0x400)
    after=output(actual,'matrix')
    assert before!=after and actual.mem_read(RAM+0x52,1)==b'\x09'
    counterexample=dict(supplied_order=['A ETERNA context','A matrix','B Classic Neg context','A matrix'],
        a_slot_unchanged=True,a_output_changed=True,before_sha256=sha(before),after_sha256=sha(after),
        actual_task_overlap_observed=False,gate='OPEN: original shared-latch contract is not qualified')
    for address in [0x157a5d8,0x156fad8,0x156ac98,0x156ad14,0x15703f8,0x156b7d4,0x156a068,0x1569be4,0x156d348,0x1570668]:
        edit=next(e for e in manifest['edits'] if e['address']==address)
        disp=(edit['value']&0xffffff)<<2
        if disp&0x2000000:disp-=0x4000000
        assert address+8+disp in visited
    OUT.mkdir(exist_ok=True)
    report=dict(scope=__doc__,status='Six built-ins execute; shared-latch gate OPEN, not camera accepted',
        elf_sha256=manifest['elf_sha256'],records=records,menus=menus,captions=captions,global_latch_counterexample=counterexample,
        recipe_metadata=[{k:r[k] for k in ['name','value','family','luma','channels','keep','sha256']} for r in recipes],
        all_ten_processing_thunks_executed=True,cpu_writes=writes,backend=dict(path=str(Path(uclib._name).resolve()),sha256=sha(Path(uclib._name).read_bytes())),
        transport_fixtures=dict(results=TRANSPORT,calls=transport_calls),manual_init=True,continuous_producer=False,
        x100vi_native_color_comparison=False,hardware=False,accepted=False,
        inputs=manifest['dependency_sha256'] | {str(BUILD/'mods.elf'):manifest['elf_sha256'],str(Path(__file__)):sha(Path(__file__).read_bytes()),str(ROOT/'modular-build-unverified/mods.elf'):base_manifest['elf_sha256']})
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(cases=len(records),films=NAMES,shared_latch='OPEN',hardware=False)))


if __name__=='__main__':main()
