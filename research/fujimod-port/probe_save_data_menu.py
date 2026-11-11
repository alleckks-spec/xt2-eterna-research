"""Inspect the existing native menu event doorway on the exact SAVE DATA build."""
import json,struct
from collections import deque
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_LR
import verify_ordinary_platform_nr as ordinary
from verify_ordinary_platform_processing import actual_factory,initialize
from verify_film_menu_navigation import invoke

ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'save-data-menu-native-build-unverified'


def machine(build=BUILD,words=72):
    ordinary.START=0x1380000;ordinary.END=0x13c0000
    sections,symbols,report=ordinary.load(build,words)
    u=actual_factory()
    for a,data,name,size in sections:
        if name not in ('.x70mod.hooks','.x70mod.strings'):u.mem_write(a,data)
    for edit in report['edits']:
        assert bytes(u.mem_read(edit['address'],4))==struct.pack('<I',edit['expected'])
        u.mem_write(edit['address'],struct.pack('<I',edit['value']))
    recent=deque(maxlen=24)
    u.hook_add(UC_HOOK_CODE,lambda uc,a,n,d:recent.append(hex(a)))
    def call(entry,*args):
        try:return invoke(u,entry,*args,instruction_limit=5000000)
        except Exception:
            print('FAULT',hex(entry),hex(u.reg_read(UC_ARM_REG_PC)),list(recent),flush=True);raise
    assert call(0xcec598)==0
    initialize(u,symbols,lambda uc,entry,*args:call(entry,*args),4)
    u.mem_write(symbols['ui_mode'],b'\x05')
    return u,symbols,call,report


if __name__=='__main__':
    u,s,call,report=machine()
    def state():return list(struct.unpack('<8I',u.mem_read(0x11802c0,32)))
    print('lookup',hex(call(s['menu_table_by_key'],0x49)),flush=True)
    print('status',int.from_bytes(u.mem_read(s['xpp_menu_status'],4),'little'),flush=True)
    print('open save',call(0x13debf0,1,0x49,0,0),state(),flush=True)
    option=call(s['menu_table_by_key'],0x7f03)
    print('open option',call(0x13debf0,1,0x7f03,0,0),state(),flush=True)
    print('shown',call(s['setp_effective_get'],0x7f01),flush=True)
    u.mem_write(0x800e000,bytes(4));call(0xbf7b88,0x1f,4,0x49,1)
    u.reg_write(UC_ARM_REG_SP,0x800e000);u.reg_write(UC_ARM_REG_LR,0x800f000)
    u.emu_start(0x14a7f1c,0x141cd64,count=3000000)
    print('packetapply',hex(u.reg_read(UC_ARM_REG_PC)),state(),int.from_bytes(u.mem_read(s['save_data_date_card_name'],4),'little'),flush=True)
    print('close option',call(0x13debf0,2,0,0x22,0),state(),flush=True)
    print('cancel snapshot',call(0xb51088,1),state(),int.from_bytes(u.mem_read(s['save_data_date_card_name'],4),'little'),flush=True)
    for event in [4,5]:
        print('event',event,call(0x13debf0,event,0x49,1,0),state(),flush=True)
    print('value',int.from_bytes(u.mem_read(s['save_data_date_card_name'],4),'little'),flush=True)
