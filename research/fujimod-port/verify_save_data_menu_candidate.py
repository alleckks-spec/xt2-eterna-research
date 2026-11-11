"""Actual native SAVE DATA list and internal option packets on the exact ELF.

Native interface construction, menu-open, all stock rows, cursor/resource reads,
value packet processing and bank snapshots execute. The existing supplied
calibration/REC globals and uncontended transport are retained. Explicit stock
checkpoint calls are not a claim about physical OK/BACK event mapping. No
renderer completion, full UI task startup, storage persistence or camera proof.
"""
import argparse
import json
import struct
from collections import deque
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
from verify_ordinary_platform_card import main as verify_card
from verify_ordinary_platform_processing import actual_factory
from verify_film_menu_navigation import invoke
from verify_native_menu_descriptor import read_cursor
from probe_save_data_menu import machine,ROOT,BUILD
from build_modular_candidate import sha

RAM=0x8000000
RETURN=RAM+0xf000


def main(build=BUILD,output=None,words=72):
    build=Path(build);out=Path(output) if output else ROOT/'save-data-menu-check-unverified'
    out.mkdir(exist_ok=True)
    verify_card(build,words)
    u,s,call,loaded=machine(build,words)
    def word(a):return int.from_bytes(u.mem_read(a,4),'little')
    def value(name):return word(s[name])
    def state():return list(struct.unpack('<8I',u.mem_read(s['menu_node'],32)))
    def requested():return word(s['save_data_settings']+92)
    def data_value():return value('save_data_date_card_name')
    def execute_to(entry,end,budget):
        stop=u.hook_add(UC_HOOK_CODE,lambda uc,a,n,d:uc.emu_stop(),begin=end,end=end)
        try:u.emu_start(entry,RETURN,count=budget)
        finally:u.hook_del(stop)
        assert u.reg_read(UC_ARM_REG_PC)==end,hex(u.reg_read(UC_ARM_REG_PC))
    trace=[];native_stores=[]
    observed={s['setp_apply_row']:'apply',s['setp_effective_get']:'shown',
              s['bank_snapshot']:'snapshot',s['menucom_request']:'admission',
              s['setp_check_dependencies']:'dependencies',0xb51098:'stock-setting-write'}
    def record(uc,a,n,d):
        trace.append(dict(entry=observed[a],args=[uc.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2]]))
    for pc in observed:u.hook_add(UC_HOOK_CODE,record,begin=pc,end=pc)
    # Original stock records/resources remain immutable after the two table-pointer edits.
    original_rows=bytes(u.mem_read(s['setup_save_rows'],72))
    original_resources=bytes(u.mem_read(s['setup_save_resources'],384))
    def watch(uc,access,a,n,v,d):
        assert not (max(a,s['setup_save_rows'])<min(a+n,s['setup_save_rows']+72))
        assert not (max(a,s['setup_save_resources'])<min(a+n,s['setup_save_resources']+384))
        native_stores.append((a,n))
    u.hook_add(UC_HOOK_MEM_WRITE,watch)
    assert call(s['menu_table_by_key'],0x49)==s['setup_save_table']
    assert value('xpp_menu_status')==0
    rows=word(s['setup_save_table']+16);resources=word(s['setup_save_table']+20)
    assert bytes(u.mem_read(rows,64))==original_rows[:64]
    assert bytes(u.mem_read(resources,384))==original_resources
    option=call(s['menu_table_by_key'],0x7f03)
    assert word(rows+64)==0x7f10 and word(rows+68)==option and word(rows+72)==0x7ffffffe
    assert struct.unpack('<HH',u.mem_read(option,4))==(0x349,0x7f01)
    assert word(option+12)==s['setup_save_table'] and word(option+24)==0x7f03
    options=word(option+16)
    assert list(struct.iter_unpack('<II',u.mem_read(options,24)))==[(0,0),(1,0),(0x7ffffffe,0)]
    # Compare every stock row through the original 40-byte native cursor ABI.
    baseline=actual_factory()
    assert invoke(baseline,0xcec598,instruction_limit=5000000)==0
    baseline.mem_write(s['ui_mode'],b'\x05')
    cursor=[]
    for index in range(8):
        expected=read_cursor(baseline,s['setup_save_table'],index)
        actual=read_cursor(u,s['setup_save_table'],index)
        assert actual==expected,index
        cursor.append(dict(index=index,property=int.from_bytes(actual[8:10],'little'),key=int.from_bytes(actual[12:16],'little')))
    extra=read_cursor(u,s['setup_save_table'],8)
    assert int.from_bytes(extra[8:10],'little')==6 and int.from_bytes(extra[12:16],'little')==0x7f10
    # Original native open/refresh classifies the eight stock rows identically.
    assert invoke(baseline,0x13debf0,1,0x49,0,0,instruction_limit=5000000)==1
    baseline_count=int.from_bytes(baseline.mem_read(s['menu_node']+24,4),'little')
    assert baseline_count==8
    expected_status=bytes(baseline.mem_read(s['menu_node']+32,8))
    assert call(0x13debf0,1,0x49,0,0)==1
    assert state()[0]==s['setup_save_table'] and state()[1]==0xf8 and state()[6]==9
    assert bytes(u.mem_read(s['menu_node']+32,8))==expected_status
    assert u.mem_read(s['menu_node']+40,1)==b'\0'
    assert u.mem_read(s['menu_open'],1)==b'\x01'
    labels=[]
    for table,index,field,expected in [(0x49,8,2,'FORMAT CARD NAME'),(0x7f03,0,2,'ON'),(0x7f03,1,2,'OFF')]:
        tag=call(0x13db71c,table,index,field)
        assert tag>>24==0xfe
        pointer=call(s['xt2_save_menu_text'],tag)
        text=bytes(u.mem_read(pointer,24)).split(b'\0',1)[0].decode()
        assert text==expected,(table,index,text,expected)
        # Execute the actual delivered OSD hook and stock prologue to its native body.
        obj=RAM+0x5000
        data=bytearray(0x60);struct.pack_into('<III',data,4,tag,0,16)
        struct.pack_into('<HH',data,0x10,20,30);struct.pack_into('<HH',data,0x2a,24,24)
        struct.pack_into('<H',data,0x30,24);data[0x3c:0x40]=bytes([100,255,255,255])
        u.mem_write(obj,bytes(data));u.reg_write(UC_ARM_REG_SP,RAM+0xe000)
        u.reg_write(UC_ARM_REG_LR,RETURN);u.reg_write(UC_ARM_REG_R0,obj)
        entry=s['osd_line_object_draw'];execute_to(entry,entry+4,200000)
        assert u.reg_read(UC_ARM_REG_PC)==entry+4 and u.reg_read(UC_ARM_REG_SP)==RAM+0xe000-36
        assert word(obj+8)==pointer and word(obj+12)==13
        assert bytes(u.mem_read(obj+0x28,24))==bytes(data[0x28:0x40])
        u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.reg_write(UC_ARM_REG_LR,RETURN);u.reg_write(UC_ARM_REG_R0,obj)
        execute_to(entry,0x2758e00,300000)
        assert u.reg_read(UC_ARM_REG_PC)==0x2758e00,hex(u.reg_read(UC_ARM_REG_PC))
        font_args=[u.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]]
        assert font_args==[0,pointer,0,24],font_args
        # Reuse the object for a stock message through the same actual entry.
        u.mem_write(obj+4,struct.pack('<I',0x951));u.reg_write(UC_ARM_REG_SP,RAM+0xe000)
        u.reg_write(UC_ARM_REG_LR,RETURN);u.reg_write(UC_ARM_REG_R0,obj)
        execute_to(entry,entry+4,200000)
        assert word(obj+12)==16 and bytes(u.mem_read(obj+0x28,24))==bytes(data[0x28:0x40])
        labels.append(dict(table=table,row=index,text=text,native_resource_tag=hex(tag),
            native_font_measurement_args=font_args,style_preserved=True,stock_type_restored=True))
    # No native synthetic-setting stores or owner changes outside the measured menu modes.
    guards=[];args=RAM+0x4000
    manifest=json.loads((build/'manifest.json').read_text());start=int(manifest['regions'][0]['address'],0)
    for mode in [0,1,2,7,32]:
        u.mem_write(s['ui_mode'],bytes([mode]));u.mem_write(args,struct.pack('<4I',0x7f01,1,1,0))
        before=bytes(u.mem_read(start,manifest['regions'][0]['size']))
        for name in ['setp_apply_row_hook','setp_effective_get_hook','menu_shown_value_hook','bank_snapshot_hook',
                     'menucom_request_hook','setp_check_dependencies_hook']:
            assert call(s[name],args)==0,(mode,name)
        assert bytes(u.mem_read(start,manifest['regions'][0]['size']))==before
        guards.append(mode)
    u.mem_write(s['ui_mode'],b'\x05')
    assert data_value()==1 and requested()==0
    changes=[]
    def observe(phase):
        row=call(s['setp_effective_get'],0x7f01)
        item=dict(phase=phase,value=data_value(),shown=row,requested=requested(),menu_open=u.mem_read(s['menu_open'],1)[0],state=state())
        changes.append(item);return item
    def packet(action):
        u.mem_write(RAM+0xe000,bytes(4))
        call(0xbf7b88,0x1f,action,0x49,1)
        u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.reg_write(UC_ARM_REG_LR,RETURN)
        u.emu_start(0x14a7f1c,0x141cd64,count=3000000)
        assert u.reg_read(UC_ARM_REG_PC)==0x141cd64
    assert call(0x13debf0,1,0x7f03,0,0)==1
    assert state()[0]==option and state()[6]==2
    call(0xb51088,0)
    observe('opened ON')
    setters_before=sum(t['entry']=='stock-setting-write' for t in trace)
    packet(4)
    row=observe('preview OFF from native packet')
    assert (row['value'],row['shown'],row['requested'],row['menu_open'])==(0,1,1,1)
    assert state()[2:4]==[1,1]
    assert call(s['setp_apply_row'],0x7f01,1)==0 and requested()==1
    assert call(s['setp_apply_row'],0x7f01,2)==0 and requested()==1 and data_value()==0
    assert call(0x13debf0,2,0,0x22,0)==1 and u.mem_read(s['menu_open'],1)==b'\0'
    call(0xb51088,1)
    row=observe('cancel through stock snapshot')
    assert (row['value'],row['shown'],row['requested'])==(1,0,2)
    # New open computes the ON cursor from the restored value; no host cursor writes.
    assert call(0x13debf0,1,0x7f03,0,0)==1 and state()[2:4]==[0,0]
    call(0xb51088,0)
    packet(4)
    assert data_value()==0 and requested()==3
    call(0xb51088,0);call(0xb51088,0)
    assert requested()==3
    assert call(0x13debf0,2,0,0x22,0)==1 and u.mem_read(s['menu_open'],1)==b'\0'
    call(0xb51088,1)
    row=observe('committed OFF; repeated commit and later restore unchanged')
    assert (row['value'],row['shown'],row['requested'])==(0,1,3)
    assert sum(t['entry']=='stock-setting-write' for t in trace)==setters_before
    assert bytes(u.mem_read(s['setup_save_rows'],72))==original_rows
    assert bytes(u.mem_read(s['setup_save_resources'],384))==original_resources
    assert value('xpp_menu_status')==value('xpp_menu_stock_status')==0
    # The exact existing owner emits the committed value; this is not a file write.
    writer=RAM+0x6000;buffer=RAM+0x6100
    u.mem_write(writer,struct.pack('<9I',buffer,128,0,0,0,0,0,0,0))
    assert call(word(s['save_data_settings']+12),writer)==0
    size=call(s['x70_json_finish'],writer)
    document=bytes(u.mem_read(buffer,size)).decode();assert json.loads(document)=={'date_card_name':False}
    report=dict(scope=__doc__,status='PASS',elf_sha256=sha((build/'mods.elf').read_bytes()),
        words=words,original_stock_rows=cursor,stock_row_resources_unchanged=True,stock_statuses=list(expected_status),
        new_row_property=6,new_row_key=0x7f10,option_property=0x7f01,option_id=0x7f03,
        labels=labels,mode_guards=guards,changes=changes,committed_owner_json=document,
        native_constructor='0xcec598',native_open='0x13debf0',native_cursor='0xb518d4',
        native_internal_packet='0xbf7b88 -> 0x14a7f1c -> 0x141cd64',native_bank_snapshot='0xb51088 -> 0xbbc924',
        native_menu_open_flag=True,synthetic_internal_setting_writes=0,settings_api_substitutes=0,
        physical_key_mapping=False,physical_storage=False,full_boot=False,hardware_verified=False,
        native_trace=trace,cpu_store_count=len(native_stores),checker_sha256=sha(Path(__file__).read_bytes()),
        source_sha256=loaded['source_sha256'])
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',stock_rows=8,new_rows=1,labels=len(labels),mode_guards=len(guards),
        owner_transitions=len(changes),elf_sha256=report['elf_sha256'])))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=BUILD);parser.add_argument('--output',type=Path)
    parser.add_argument('--words',type=int,default=72)
    args=parser.parse_args();main(args.build,args.output,args.words)
