"""Run the existing bounded processing cases on the exact ordinary SD candidate.

Manual init registry and native property setter/getter boundary; supplied mode,
stock SD RAM, calibration and uncontended kernel transport. No services started,
UI event dispatcher, continuous producer, SD transfer, pixels or camera proof.
AI-assisted original assay adapter; private inputs stay local.
"""
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_C1_C0_2, UC_ARM_REG_FPEXC
from verify_processing import verify
from verify_ordinary_platform_nr import load, BUILD, CARD, ROOT, START, END, sha
from build_eterna_payload import STOCK

OUT = ROOT/'ordinary-platform-processing-check-unverified'
TRANSPORT = {0x57e20:3, 0xcef4ac:0, 0xcef4f8:0}
selection_calls=[]
transport_calls=[]
init_calls=[]


def build(build_directory=BUILD):
    sections,symbols,report=load(build_directory)
    # Confirm these are the eight processing branches, not other package edits.
    from build_fixture import BINDINGS
    for edit in report['edits']:
        if edit['address'] not in {a for a,_ in BINDINGS.values()}:continue
        assert edit['value'] & 0xff000000 == 0xea000000
        displacement=(edit['value'] & 0xffffff) << 2
        if displacement & 0x2000000:displacement-=0x4000000
        edit['thunk']=edit['address']+8+displacement
    return sections,symbols,report


def actual_factory():
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    stock=STOCK.read_bytes()
    u.mem_map(0,(len(stock)+4095)&~4095)
    u.mem_write(0,stock)
    u.mem_map(0x8000000,0x10000)
    parameters=(ROOT.parents[1]/'firmware/extracted/xt2-4.41/inverted.bin').read_bytes()[0xc025c:0x10025c]
    u.mem_map(0x9000000,0x40000)
    u.mem_write(0x9000000,parameters)
    u.mem_write(0x1025344,struct.pack('<I',0x9000000))
    u.reg_write(UC_ARM_REG_C1_C0_2,0xf<<20)
    u.reg_write(UC_ARM_REG_FPEXC,1<<30)
    # Existing menu assay's explicit startup pointers and mode input.
    for a,v in [(0x10c62b0,0x120d8a0),(0x119162c,0x119f25c)]:
        u.mem_write(a,struct.pack('<I',v))
    u.mem_write(0x119f25c,b'\x24')
    u.mem_write(0x121d626,b'\x03')
    def boundary(uc,a,s,d):
        if a!=0x57e20:assert uc.reg_read(UC_ARM_REG_R0)==43
        transport_calls.append(a)
        uc.reg_write(UC_ARM_REG_R0,TRANSPORT[a])
        uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
    for a in TRANSPORT:u.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
    return u


def initialize(u,symbols,invoke):
    u.mem_write(symbols['ui_mode'],b'\x03')
    for a in range(symbols['__xpp_init_start'],symbols['__xpp_init_end'],4):
        fn=int.from_bytes(u.mem_read(a,4),'little')
        invoke(u,fn)
        init_calls.append(fn)
    assert len(init_calls)==2
    assert int.from_bytes(u.mem_read(symbols['film_choice_status'],4),'little')==0
    assert int.from_bytes(u.mem_read(symbols['xpp_menu_stock_status'],4),'little')==0


def select(u,symbols,invoke,enabled,stored):
    key=32 if enabled else 0
    from verify_film_menu_navigation import invoke as native_invoke
    native_invoke(u,0x154b700,0x1fc,key,instruction_limit=3000000)
    readback=invoke(u,0xb510b8,0x1fc,0)
    choice=int.from_bytes(u.mem_read(symbols['film_choice_key'],4),'little')
    assert readback==0 and choice==key,(readback,choice,key)
    selection_calls.append(dict(menu_key=key,stored_readback=readback,choice_key=choice))


def main(build_directory=BUILD,output_directory=OUT):
    BUILD=Path(build_directory)
    CARD=Path(str(BUILD)+'-card')
    OUT=Path(output_directory)
    # Reuse the correspondence checker, including complete SD file hashes.
    from verify_ordinary_platform_card import main as verify_card
    verify_card(BUILD)
    verify(build_function=lambda:build(BUILD),output_directory=OUT,resident_region=(START,END),
           actual_factory=actual_factory,initialize=initialize,select_profile=select,
           selection_write_ranges=((0xffd000,0x1000000),(0x1180000,0x1235000),(0x1ab0000,0x1ad0000)))
    path=OUT/'processing-verification-tci.json'
    report=json.loads(path.read_text())
    report.update(scope=__doc__,manual_init_registry=init_calls,native_selection=selection_calls,
        transport_fixtures=dict(results=TRANSPORT,calls=transport_calls),
        settings_cardio_timer_executed=False,full_boot=False,hardware_verified=False,
        artifact_sha256={str(p):sha(p.read_bytes()) for p in
            [Path(__file__),BUILD/'mods.elf',BUILD/'region.bin',BUILD/'manifest.json',
             BUILD/'card-correspondence.json',CARD/'manifest.json',STOCK]})
    path.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
