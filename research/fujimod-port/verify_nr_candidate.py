"""Bounded NR menu/guard/register-write assay on the exact integrated ELF.

Manual init-registry boundary, supplied calibration/mode/NR RAM block and
uncontended kernel transport. MMIO stores are captured, never device success.
No native still producer, healthy startup, filesystem, pixels or hardware proof.
"""
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
from unicorn.unicorn_py3.unicorn import uclib
from build_nr_candidate import build, OUT, ROOT, WORKSPACE, NR, WRITE, BLOCK, sha
from verify_film_visibility import execute, RETURN
from verify_film_menu_navigation import invoke
from build_eterna_payload import STOCK

STRENGTH_WORDS = [i for i in range(0x30//4,0x70//4+1) if i not in (0x44//4,0x5c//4)]


def verify(*,build_function=build,output=OUT,resident_region=None,binding_audit=None,artifact_files=None,expected_init_count=2):
    OUT=Path(output)
    OUT.mkdir(parents=True,exist_ok=True)
    library = Path(uclib._name).resolve()
    assert library == (WORKSPACE/'.toolchains/unicorn-tci/libunicorn.2.dylib').resolve()
    sections, symbols, manifest = build_function()
    stock = STOCK.read_bytes()
    parameters_path = WORKSPACE/'firmware/extracted/xt2-4.41/inverted.bin'
    parameters = parameters_path.read_bytes()[0xc025c:0x10025c]
    pinned = {str(p):sha(p.read_bytes()) for p in [Path(__file__),STOCK,parameters_path,
               Path(binding_audit) if binding_audit is not None else OUT/'binding-audit.json',
               *(artifact_files if artifact_files is not None else [OUT/'build.json',OUT/'menu.elf'])]}
    pinned.update(manifest['dependency_sha256'])
    pinned.update({str(ROOT/p):digest for p,digest in manifest['source_sha256'].items()})

    def assay(u):
        for a,data,name,size in sections:
            if resident_region is not None and name in ('.x70mod.hooks','.x70mod.strings'):
                continue  # upstream metadata sections are not loaded RAM
            if resident_region is not None:
                assert resident_region[0]<=a<a+size<=resident_region[1],name
            u.mem_write(a,data)
        for edit in manifest['edits']:
            assert bytes(u.mem_read(edit['address'],4)) == struct.pack('<I',edit['expected'])
            u.mem_write(edit['address'],struct.pack('<I',edit['value']))
        if resident_region is None:u.mem_protect(0x2000000,0x40000,5)
        # The deliberate native reservation is RWX, matching its checked
        # original boot mapping; memory-write bounds below remain enforced.
        u.mem_map(0x2c68000,0x200000)
        u.mem_write(0x2c68000,parameters)
        u.mem_write(0x1025344,struct.pack('<I',0x2c68000))
        u.mem_write(0x121d626,b'\x03')
        u.mem_write(symbols['ui_mode'],b'\x03')
        fixtures=[]
        def transport(uc,a,s,d):
            if a != 0x57e20:
                assert uc.reg_read(UC_ARM_REG_R0) == 43
            fixtures.append(a)
            uc.reg_write(UC_ARM_REG_R0,3 if a==0x57e20 else 0)
            uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        for a in (0x57e20,0xcef4ac,0xcef4f8):
            u.hook_add(UC_HOOK_CODE,transport,begin=a,end=a)
        # Run the linked registry in its actual order, stopping before service
        # start. This detects enrollment-after-prepare ordering mistakes.
        init=[]
        for a in range(symbols['__xpp_init_start'],symbols['__xpp_init_end'],4):
            fn=int.from_bytes(u.mem_read(a,4),'little')
            init.append(fn);invoke(u,fn)
        assert len(init)==expected_init_count
        assert int.from_bytes(u.mem_read(symbols['nr_xt20_status'],4),'little')==0
        assert int.from_bytes(u.mem_read(symbols['xpp_menu_stock_status'],4),'little')==0
        menus=[]
        def run_to(start,end,budget=3000000,allow_return=False):
            stop=u.hook_add(UC_HOOK_CODE,lambda uc,a,s,d:uc.emu_stop(),begin=end,end=end)
            try:u.emu_start(start,RETURN,count=budget)
            finally:u.hook_del(stop)
            pc=u.reg_read(UC_ARM_REG_PC)
            assert pc==end or (allow_return and pc==RETURN),hex(pc)
            return pc
        # Every native list opens and computes its own cursor. Apply uses the
        # real stock setter/getter, never host writes of the selected key.
        for descriptor in (0xeab470,0xe9489c,0xea1a08):
            invoke(u,0x154b700,NR,0)
            u.mem_write(0x11802c0,struct.pack('<I',descriptor))
            for reg in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3):u.reg_write(reg,0)
            u.reg_write(UC_ARM_REG_SP,0x800e000);u.reg_write(UC_ARM_REG_LR,RETURN)
            run_to(0x13df330,RETURN)
            assert int.from_bytes(u.mem_read(0x11802d8,4),'little')==11
            rows_at=int.from_bytes(u.mem_read(descriptor+16,4),'little')
            rows=[int.from_bytes(u.mem_read(rows_at+i*8,4),'little') for i in range(11)]
            assert rows==list(range(8,-1,-1))+[10,11]
            states=[]
            for key in (10,11,0):
                invoke(u,0x154b700,NR,key)
                stored=invoke(u,0xb510b8,NR,0)
                enabled=int.from_bytes(u.mem_read(symbols['nr_xt20_enabled'],4),'little')
                chosen=int.from_bytes(u.mem_read(symbols['nr_xt20_value'],4),'little')
                assert stored==0 and enabled==int(key in (10,11)) and chosen==key
                states.append(dict(key=key,stored=stored,enabled=enabled))
            # Native cursor movement/record reader, then an explicit call boundary
            # to the real setter. The whole UI dispatcher is not claimed: its
            # NR branch returned before committing in the earlier probe.
            history=[]
            reached=set()
            for action in [4]*13+[5]*13:
                invoke(u,0x13debf0,action,u.mem_read(descriptor,1)[0],1,0)
                assert invoke(u,0xb518d4,0x8003000)==1
                setting=int.from_bytes(u.mem_read(0x8003008,2),'little')
                key=int.from_bytes(u.mem_read(0x800300c,4),'little')
                assert setting==NR and key in rows
                invoke(u,0x154b700,setting,key)
                chosen=int.from_bytes(u.mem_read(symbols['nr_xt20_value'],4),'little')
                if key in (10,11):
                    assert chosen==key and invoke(u,0xb510b8,NR,0)==0
                    reached.add(key)
                history.append(dict(action=action,row=key))
            assert reached=={10,11},(hex(descriptor),history)
            menus.append(dict(descriptor=descriptor,rows=rows,states=states,events=history))
        # Pure write-only unit boundary: actual writer and scalar store execute.
        # This mapping records writes, supplies no ready flag/ack/read result.
        u.mem_map(0xfffab000,0x1000)
        stores=[];allwrites=[];guarding=[False]
        if resident_region is None:
            state_end=max(a+size for a,d,n,size in sections if a>=0x2040000)
            state_ranges=[(0x2040000,state_end)]
        else:
            state_ranges=[(a,a+size) for a,d,n,size in sections if n in ('.data','.x70mod.shared','.bss')]
        allowed=[(BLOCK,BLOCK+144),*state_ranges,(0x8000000,0x8010000),(0xfffab000,0xfffab090),
                 (0xffe7c8,0xffe7c9)]  # native conversion lookup status byte, bf5f48
        def writes(uc,access,a,size,value,d):
            if not guarding[0]:return
            assert any(lo<=a<a+size<=hi for lo,hi in allowed),(hex(uc.reg_read(UC_ARM_REG_PC)),hex(a),size)
            allwrites.append((a,size))
            if a>=0xfffab000:stores.append((a,value&0xffffffff))
        u.hook_add(UC_HOOK_MEM_WRITE,writes)
        base=[0x31410000+i for i in range(36)]
        base[0x44//4]=base[0x5c//4]=0xc8966432
        for i in STRENGTH_WORDS:base[i]=40
        packed=lambda words:struct.pack('<36I',*words)
        registers=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
                   UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
        cases=[]
        def check(label,key,mode=3,bad_word=None,pointer=BLOCK,stock_level=None):
            u.mem_write(symbols['ui_mode'],b'\x03')
            invoke(u,0x154b700,NR,key)
            u.mem_write(symbols['ui_mode'],bytes([mode]))
            words=base.copy()
            if stock_level is not None:
                for i in STRENGTH_WORDS:words[i]=stock_level
            if bad_word is not None:words[bad_word]=41
            u.mem_write(pointer-16,b'\xa5'*16+packed(words)+b'\x5a'*16)
            expected=words.copy()
            if mode==3 and key in (10,11) and pointer==BLOCK and all(words[i]==40 for i in STRENGTH_WORDS):
                for i in STRENGTH_WORDS:expected[i]=10 if key==10 else 0
            for i,reg in enumerate(registers):u.reg_write(reg,0x64100000+i)
            stores.clear();allwrites.clear();guarding[0]=True
            try:invoke(u,WRITE,pointer)
            finally:guarding[0]=False
            assert bytes(u.mem_read(pointer,144))==packed(expected),label
            assert bytes(u.mem_read(pointer-16,16))==b'\xa5'*16
            assert bytes(u.mem_read(pointer+144,16))==b'\x5a'*16
            assert stores==[(0xfffab000+4*i,v) for i,v in enumerate(expected)],(label,stores)
            assert [u.reg_read(reg) for reg in registers]==[0x64100000+i for i in range(8)]
            assert u.reg_read(UC_ARM_REG_SP)==0x800e000
            cases.append(dict(label=label,key=key,mode=mode,changed_words=[i for i in range(36) if words[i]!=expected[i]],
                              mmio_stores=len(stores),cpu_writes=len(allwrites),output_sha256=sha(packed(expected))))
        check('minus5',10);check('minus6',11);check('stock-clears',0)
        for mode in range(16):
            if mode!=3:check('non-REC-'+str(mode),10,mode=mode)
        for i in STRENGTH_WORDS:check('mismatch-'+hex(4*i),10,bad_word=i)
        check('other-source-block',10,pointer=0x8004000)
        for strength in (40,70,100,130,160,180,200,220,240):
            check('supplied-stock-strength-'+str(strength),4,stock_level=strength)
        assert bytes(u.mem_read(0x2c68000,len(parameters)))==parameters
        return dict(init_registry=init,menus=menus,register_cases=cases,
                    explicit_fixtures=dict(kernel_transport=sorted(set(fixtures)),
                        calibration='Existing declared parameter-store fixture; no flash/NV write',
                        nr_block='Supplied 36-word RAM input, not output of native still producer',
                        mmio='Write-only capture at fffab000..fffab08f; no device reply',
                        initialization='Actual init entries manually invoked; services not started'),
                    bounded_nr_write_ranges=allowed,whole_ui_dispatch=False,
                    menu_setter_boundary='Native cursor/record output supplied to native apply_row entry')

    result=execute(stock,b'',{},36,0,False,after_call=assay)
    assert all(sha(Path(p).read_bytes())==digest for p,digest in pinned.items())
    report=dict(scope=__doc__,elf_sha256=manifest['elf_sha256'],**result,input_sha256=pinned,
                actual_backend=dict(path=str(library),sha256=sha(library.read_bytes())),
                resident_region=resident_region,compiler=manifest['compiler'],
                ordinary_build=False,sd_package=False,native_still_producer=False,
                services_started=False,full_boot=False,hardware=False)
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(menus=len(report['menus']),register_cases=len(report['register_cases']),
                         elf_sha256=report['elf_sha256'],hardware=False)))


if __name__=='__main__':verify()
