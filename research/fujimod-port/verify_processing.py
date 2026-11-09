"""Bounded native functions with actual community entry thunks, no UI/boot proof."""
import json
import struct
import sys
from collections import deque
from pathlib import Path
from build_fixture import build, OUT, ROOT, WORKSPACE, CODE, BINDINGS, sha
from unicorn import UC_HOOK_MEM_WRITE, UC_HOOK_CODE
from unicorn.arm_const import *
from unicorn.unicorn_py3.unicorn import uclib
from verify_interpolated_profile_outputs import runtime, call
from verify_profile_selectors import RAM, RETURN
from firmware_analysis import Firmware


def verify(*, build_function=build, output_directory=OUT, resident_region=None,
           actual_factory=None, initialize=None, select_profile=None, selection_write_ranges=()):
    library=Path(uclib._name).resolve()
    assert library==(WORKSPACE/'.toolchains/unicorn-tci/libunicorn.2.dylib').resolve(),library
    sections, symbols, build_report = build_function()
    actual = actual_factory() if actual_factory else runtime('xt2-4.41', False)
    stock, donor = runtime('xt2-4.41', False), runtime('xh1-2.15', False)
    # Scaling calls the original kernel's signed 64-bit division helper.
    kernel = next(b for a,b in Firmware('xt2-4.41', True).units if a==0x40000)
    for uc in [actual,stock]:
        if not any(a<=0x40000 and 0x40000+len(kernel)<=b+1 for a,b,_ in uc.mem_regions()):
            uc.mem_map(0x40000,(len(kernel)+4095)&~4095)
        uc.mem_write(0x40000,kernel)
    if resident_region is None:
        actual.mem_map(CODE, 0x20000)
    loaded_sections=[]
    for address, data, name, size in sections:
        if resident_region is not None:
            if name in ('.x70mod.hooks', '.x70mod.strings'):continue
            assert resident_region[0]<=address<address+size<=resident_region[1],name
        actual.mem_write(address, data)
        loaded_sections.append((address,data,name,size))
    for edit in build_report['edits']:
        assert bytes(actual.mem_read(edit['address'],4))==struct.pack('<I',edit['expected'])
        actual.mem_write(edit['address'], struct.pack('<I', edit['value']))
    if resident_region is None:actual.mem_protect(CODE,0x10000,5)
    state_ranges = [(a,a+size) for a,d,n,size in loaded_sections if n in ('.data','.x70mod.shared','.bss')]
    selecting=[False]
    writes = dict(count=0)
    visited = set()
    recent = deque(maxlen=12)
    def write_watch(uc, access, address, size, value, user):
        assert (RAM <= address < address+size <= RAM+0x10000 or
                any(lo<=address<address+size<=hi for lo,hi in state_ranges) or
                (selecting[0] and any(lo<=address<address+size<=hi for lo,hi in selection_write_ranges))), (hex(uc.reg_read(UC_ARM_REG_PC)),hex(address),size)
        writes['count'] += 1
    actual.hook_add(UC_HOOK_MEM_WRITE, write_watch)
    def trace(uc,a,s,u):
        visited.add(a)
        recent.append(hex(a))
    actual.hook_add(UC_HOOK_CODE, trace)
    records=[]
    def invoke(uc, entry, *args):
        uc.reg_write(UC_ARM_REG_SP, RAM+0xe000)
        regs=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
        expected=[0x31410000+i for i in range(len(regs))]
        for reg,v in zip(regs,expected):uc.reg_write(reg,v)
        try:call(uc,entry,*args)
        except Exception:
            print('FAIL',hex(entry),hex(uc.reg_read(UC_ARM_REG_PC)),hex(uc.reg_read(UC_ARM_REG_LR)),list(recent),flush=True)
            raise
        assert uc.reg_read(UC_ARM_REG_SP)==RAM+0xe000
        assert [uc.reg_read(r) for r in regs]==expected
        return uc.reg_read(UC_ARM_REG_R0)
    def profile(uc, donor_model, stored, fields=None):
        uc.mem_write(RAM,bytes(0x200))
        invoke(uc,0x17612a8 if donor_model else 0x157a0fc,RAM)
        invoke(uc,0x1761e18 if donor_model else 0x157ac60,RAM,stored)
        for off,val in {0x51:1,**(fields or {})}.items():uc.mem_write(RAM+off,bytes([val]))
    def output(uc,entry,kind):
        base=RAM+0x2000
        uc.mem_write(base-16,b'\xcc'*0x220)
        if kind=='matrix':args=(base,RAM);n=20
        elif kind=='family':args=(RAM,0,base);n=1
        elif kind=='curve':args=(RAM,base,base+0x40,base+0x42);n=0x44
        elif kind=='gain':args=(RAM,1,base);n=44
        elif kind=='chroma':args=(RAM,base);n=50
        elif kind=='luma':args=(RAM,base);n=0x80
        elif kind=='live':args=(RAM,base);n=0x120
        elif kind=='still':args=(RAM,base);n=0x100
        else:raise AssertionError(kind)
        ret=invoke(uc,entry,*args)
        assert bytes(uc.mem_read(base-16,16))==b'\xcc'*16
        assert bytes(uc.mem_read(base+n,16))==b'\xcc'*16
        return bytes(uc.mem_read(base,n)),ret
    funcs={'matrix':(0x156fad8,0x1756a90),'chroma':(0x156af80,0x17524c0),
           'curve':(0x15703f8,0x1757390),'family':(0x156a068,0x17515e8),
           'luma':(0x156b7d4,0x1752d14),'gain':(0x156a140,0x175167c),
           'live':(0x156d348,0x1754c08),'still':(0x1570668,0x1757600)}
    def select(enabled,stored=0):
        selecting[0]=True
        try:
            if select_profile is None:
                actual.mem_write(symbols['xt2_fixture_eterna'],struct.pack('<I',enabled))
            else:select_profile(actual,symbols,invoke,enabled,stored)
        finally:selecting[0]=False
    if initialize:
        selecting[0]=True
        try:initialize(actual,symbols,invoke)
        finally:selecting[0]=False
    # Real native profile setter calls the hooked stored->slot function.
    for stored in range(18):
        for uc in [actual,stock]:
            invoke(uc,0x157a0fc,RAM+0x400)
            invoke(uc,0x157ac60,RAM+0x400,stored)
        slot=actual.mem_read(RAM+0x452,1)
        assert slot==stock.mem_read(RAM+0x452,1) and slot!=b'\x09'
        records.append(dict(stage='stock-slot',stored=stored,slot=slot[0],equal_stock=True))
    for enabled,stored in [(0,0),(1,0),(0,3)]:
        select(enabled,stored)
        for uc,d,ident in [(actual,False,stored),(stock,False,stored),(donor,True,18 if enabled else stored)]:profile(uc,d,ident)
        assert actual.mem_read(RAM+0x52,1)==(b'\x09' if enabled else stock.mem_read(RAM+0x52,1))
        for kind,(xt2,xh1) in funcs.items():
            observed,ret=output(actual,xt2,kind)
            expected,refret=output(donor if enabled else stock,xh1 if enabled else xt2,kind)
            assert observed==expected,(kind,stored,enabled,observed.hex(),expected.hex())
            records.append(dict(stage='eterna' if enabled else 'stock',stored=stored,kind=kind,
                equal_reference=observed==expected,return_matches=ret==refret,
                observed_r0=ret,reference_r0=refret,
                observed_sha256=sha(observed),reference_sha256=sha(expected),
                different_offsets=[i for i,(a,b) in enumerate(zip(observed,expected)) if a!=b]))
    # The gain mismatch justifies checking all 9 settings x 6 channels of the
    # newly supplied immutable family, independently against donor execution.
    select(1)
    profile(actual,False,0)
    for setting in range(9):
        for channel in range(6):
            values=[]
            for uc,entry in [(actual,0x1569be4),(donor,0x1751164)]:
                uc.mem_write(RAM+0x2000,b'\xcc'*60)
                invoke(uc,entry,10,setting,channel,RAM+0x2000)
                assert bytes(uc.mem_read(RAM+0x202c,16))==b'\xcc'*16
                values.append(bytes(uc.mem_read(RAM+0x2000,44)))
            assert values[0]==values[1],('gain-family',setting,channel)
            records.append(dict(stage='gain-family',setting=setting,channel=channel,equal_donor=True,sha256=sha(values[0])))
    for adjustment in [0,8]:
        for uc,d,ident in [(actual,False,0),(donor,True,18)]:
            profile(uc,d,ident,{0x4f:adjustment,0x50:adjustment,0x66:adjustment})
        for kind in ['gain','live','still']:
            a,_=output(actual,funcs[kind][0],kind);b,_=output(donor,funcs[kind][1],kind)
            assert a==b,('adjustment',adjustment,kind,a.hex(),b.hex())
            records.append(dict(stage='adjustment',kind=kind,adjustment=adjustment,equal_donor=True,sha256=sha(a)))
    # Minimal distinguishing scale cases, including all custom-zero step aliases.
    select(1)
    matrix=struct.unpack('<9h', bytes(actual.mem_read(symbols['xt20_film_recipes']+8,18)))
    for label,fields,scale in [('disabled',{0x67:7,0x9b:0,0x9a:0},100),
                              ('nonzero',{0x67:7,0x9b:1,0x9a:8},126),
                              *[(f'zero-step{s}',{0x67:7,0x9b:1,0x9a:s,0x9c:0},0) for s in [10,11,12]]]:
        profile(actual,False,0,fields)
        observed,_=output(actual,0x156fad8,'matrix')
        expected=tuple(int(v*scale/100) for v in matrix)
        assert struct.unpack_from('<9h',observed,2)==expected,label
        assert observed[0]==1
        if scale==0:
            profile(stock,False,0,fields)
            baseline,_=output(stock,0x156fad8,'matrix')
            assert observed==baseline
        records.append(dict(stage='scale',case=label,pass_check=True,output_sha256=sha(observed)))
    # Special path must remain stock with a selected ETERNA.
    for kind,(xt2,xh1) in funcs.items():
        for uc in [actual,stock]:
            profile(uc,False,0,{0x144:1})
            uc.mem_write(RAM+0x52,b'\x09')
        a,ar=output(actual,xt2,kind);b,br=output(stock,xt2,kind)
        assert a==b,('special',kind)
        records.append(dict(stage='special',kind=kind,equal_stock=True))
    # Reach both forced native branches without pretending they are donor ETERNA.
    for key in [0xb5,0xf740]:
        for uc in [actual,stock]:
            profile(uc,False,0)
            uc.mem_write(RAM+0x52,b'\x09')
            uc.mem_write(0x9000000+key,b'\x01')
        a,ar=output(actual,0x15703f8,'curve');b,br=output(stock,0x15703f8,'curve')
        assert a==b and ar==br,('forced',key)
        records.append(dict(stage='forced',key=key,tone_points_equal_stock=a[:56]==b[:56],
            scalars_equal_stock=a[0x40:]==b[0x40:],return_matches=ar==br,
            note='Adapter preserves native forced points/scalars; pinned community handler did not.'))
        for uc in [actual,stock]:uc.mem_write(0x9000000+key,b'\x00')
    # A bounded counterexample to assuming that a sequential PASS proves the
    # shared latch safe. Two actual native setters/consumers, explicit ordering;
    # this is not evidence of a real task/core race on a camera.
    select(1)
    profile(actual,False,0)
    before,_=output(actual,0x156fad8,'matrix')
    invoke(actual,0x157a0fc,RAM+0x400)
    invoke(actual,0x157ac60,RAM+0x400,3)
    after,_=output(actual,0x156fad8,'matrix')
    assert before==after,'Immutable context binding must survive another context selecting stock'
    interleaving=dict(supplied_order=['A selected ETERNA', 'A matrix', 'B selected stock', 'A matrix'],
        a_context=RAM,b_context=RAM+0x400,a_slot_unchanged=actual.mem_read(RAM+0x52,1)==b'\x09',
        before_sha256=sha(before),after_sha256=sha(after),changed=False,
        actual_task_overlap_observed=False,
        conclusion='Immutable profile binding survives this supplied ordering without caller exclusion; no real scheduling claim.')
    # Pause A after its native select, execute B's whole native chroma builder
    # on a different stack, then resume A. This stresses same-core nesting at
    # exactly the old per-core arming boundary without a scheduler model.
    expected,_=output(actual,0x156af80,'chroma')
    base=RAM+0x2000
    actual.mem_write(base-16,b'\xcc'*0x220)
    actual.reg_write(UC_ARM_REG_SP,RAM+0xe000)
    actual.reg_write(UC_ARM_REG_LR,RETURN)
    actual.reg_write(UC_ARM_REG_R0,RAM)
    actual.reg_write(UC_ARM_REG_R1,base)
    stopper=actual.hook_add(UC_HOOK_CODE,lambda uc,a,s,u:uc.emu_stop(),begin=0x156afe0,end=0x156afe0)
    try:actual.emu_start(0x156af80,RETURN,count=200000)
    finally:actual.hook_del(stopper)
    assert actual.reg_read(UC_ARM_REG_PC)==0x156afe0
    saved=actual.context_save()
    actual.reg_write(UC_ARM_REG_SP,RAM+0xc000)
    call(actual,0x156af80,RAM+0x400,RAM+0x2400)
    actual.context_restore(saved)
    actual.emu_start(0x156afe0,RETURN,count=200000)
    assert actual.reg_read(UC_ARM_REG_PC)==RETURN
    assert bytes(actual.mem_read(base,50))==expected
    assert bytes(actual.mem_read(base-16,16))==b'\xcc'*16
    assert bytes(actual.mem_read(base+50,16))==b'\xcc'*16
    interleaving['nested_native_chroma_unchanged']=True
    interleaving['nested_fixture_stacks']=[RAM+0xe000,RAM+0xc000]
    # Second real caller, with an explicitly borrowed native frame, to the
    # boundary before it consumes the filled 32-byte temporary.
    actual.reg_write(UC_ARM_REG_R4,RAM)
    actual.mem_write(RAM+0xc000-0x60,b'\xcc'*0x60)
    actual.reg_write(UC_ARM_REG_R11,RAM+0xc000)
    actual.reg_write(UC_ARM_REG_SP,RAM+0xb000)
    actual.emu_start(0x156d4d4,0x156d548,count=200000)
    assert actual.reg_read(UC_ARM_REG_PC)==0x156d548
    chroma=struct.unpack('<4h',bytes(actual.mem_read(symbols['xt20_film_recipes']+26,8)))
    assert struct.unpack('<4q',bytes(actual.mem_read(RAM+0xc000-0x44,32)))==(chroma[0],chroma[2],chroma[3],chroma[1])
    assert bytes(actual.mem_read(RAM+0xc000-0x60,16))==b'\xcc'*16
    assert bytes(actual.mem_read(RAM+0xc000-0x24,16))==b'\xcc'*16
    interleaving['second_native_chroma_caller_block']=dict(start=0x156d4d4,stop=0x156d548,borrowed_frame=True,pass_check=True)
    # Calls from any unqualified caller remain native and do not touch the
    # caller-owned tag area. This is a deliberate fail-stock boundary.
    for uc in [actual,stock]:uc.mem_write(RAM+0x3000,b'\xcc'*32)
    invoke(actual,0x156ac98,RAM,RAM+0x3000)
    invoke(stock,0x156ac98,RAM,RAM+0x3000)
    assert actual.mem_read(RAM+0x3000,32)==stock.mem_read(RAM+0x3000,32)
    interleaving['unqualified_chroma_caller_left_stock']=True
    # Confirm every actual entry thunk and displaced stock continuation was executed.
    for edit in build_report['edits']:
        if edit['address'] in {a for a,_ in BINDINGS.values()}:
            assert edit['thunk'] in visited
    for name,(address,_) in BINDINGS.items():assert address+4 in visited,name
    report=dict(scope=__doc__,status='bounded processing assay; discrepancies retained',
        build=build_report,records=records,cpu_writes=writes,state_write_bound_bytes=sum(hi-lo for lo,hi in state_ranges),state_write_ranges=state_ranges,all_eight_thunks_executed=True,
        checked_callee_saved_and_stack=True,kernel_division_bytes_sha256=sha(kernel),synthetic_selector=select_profile is None,synthetic_placement=resident_region is None,
        resident_region=resident_region,selection_write_ranges=selection_write_ranges,
        concurrency_proven=False,shared_selection_latch_removed=True,per_core_chroma_arming_removed=True,
        menu_verified=False,hardware_verified=False,
        sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [Path(__file__),ROOT/'selector.c']},
        interleaving=interleaving,
        runtime_source_sha256={str(p.relative_to(WORKSPACE)):sha(p.read_bytes()) for p in
            [WORKSPACE/'scripts'/n for n in ['verify_interpolated_profile_outputs.py','verify_profile_selectors.py','firmware_analysis.py','eterna_ram_fixture.py','verify_tone_table_port.py']]},
        input_sha256={str(p.relative_to(WORKSPACE)):sha(p.read_bytes()) for m in ['xt2-4.41','xh1-2.15'] for p in (WORKSPACE/'firmware/extracted'/m).iterdir() if p.name in ['manifest.json','inverted.bin']})
    report['actual_backend']=dict(path=str(library),sha256=sha(library.read_bytes()))
    Path(output_directory).mkdir(exist_ok=True)
    (Path(output_directory)/'processing-verification-tci.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(cases=len(records),differences=[r for r in records if r.get('equal_reference') is False or r['stage']=='forced']),indent=2))


if __name__=='__main__':verify()
