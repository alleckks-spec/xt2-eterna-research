"""Exact minimal ELF: native policy, menu navigation, volatile commit and stock get.

Reuse the existing native UI1 constructor/scheduler fixture before module init.
Supplied REC/calibration/settings inputs remain explicit. No peripheral success
replies, manual mod-init loop or full boot/camera claim. Each final UI row is
reached with native cursor packets; physical buttons are not exercised.
"""
import hashlib,inspect,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
import verify_card_films_menu as fixture
from verify_ordinary_platform_nr import load

ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'minimal-build-unverified'
OUT=ROOT/'minimal-check-unverified'
RAM=0x8000000

def sha(b):return hashlib.sha256(b).hexdigest()

def machine():
    source=inspect.getsource(fixture.main);anchor='    init=[]\n';assert source.count(anchor)==1
    prefix=source.split(anchor)[0].replace('def main():','def setup():',1)
    old="assert sha(raw)=='db56c69c993a30e9fbdfb024ad766e005234b50f76684082b29683a526dd3754'"
    assert prefix.count(old)==1
    digest=json.loads((BUILD/'preparation.json').read_text())['elf_sha256']
    prefix=prefix.replace(old,'assert sha(raw)=='+repr(digest))
    prefix+='    return u,symbols,call,clock,exceptions\n'
    namespace=dict(vars(fixture));namespace['BUILD']=BUILD
    exec(compile(prefix,str(Path(fixture.__file__))+'::minimal-before-init','exec'),namespace)
    return namespace['setup'](),dict(fixture_sha256=sha(Path(fixture.__file__).read_bytes()),
                                   adapted_prefix_sha256=sha(prefix.encode()))

def main():
    manifest=json.loads((BUILD/'manifest.json').read_text());load(BUILD,len(manifest['words']))
    (u,s,call,clock,exceptions),setup=machine()
    word=lambda a:struct.unpack('<I',u.mem_read(a,4))[0]
    def api(name,*args):return call(s[name],*args,task=True)
    policy=json.loads((BUILD/'target.json').read_text())['symbols']['ui_display_off_policy']
    inits=[word(p) for p in range(s['__xpp_init_start'],s['__xpp_init_end'],4)]
    lates=[word(p) for p in range(s['__xpp_late_start_start'],s['__xpp_late_start_end'],4)]
    assert len(inits)==len(lates)==1
    events=[];stock=[];storage=[]
    for fn in inits+lates:u.hook_add(UC_HOOK_CODE,lambda uc,a,z,d:events.append(a),begin=fn,end=fn)
    u.hook_add(UC_HOOK_CODE,lambda uc,a,z,d:stock.append(a),begin=policy+4,end=policy+4)
    # Observe/refuse actual requests, never provide replies for them.
    for name in ['storage_open_file_async','storage_read_async_wrapper','storage_write_file_async','storage_entry_async','storage_seek_async','software_timer_start']:
        pc=json.loads((BUILD/'target.json').read_text())['symbols'][name]
        def forbidden(uc,a,z,d):storage.append(a);raise AssertionError(('unexpected mod I/O',hex(a)))
        u.hook_add(UC_HOOK_CODE,forbidden,begin=pc,end=pc)
    for mode in [0,1,2,7]:
        u.mem_write(s['ui_mode'],bytes([mode]));call(policy,task=True);assert not events
    for mode in [3,3,4,5,6]:
        u.mem_write(s['ui_mode'],bytes([mode]));call(policy,task=True);assert events==inits+lates
    assert len(stock)==9 and word(s['xt2_volatile_late_starts'])==1
    assert word(s['film_choice_status'])==word(s['xpp_menu_stock_status'])==0
    u.mem_write(s['ui_mode'],b'\x03')
    # Native selection stores PROVIA for the additional menu key.
    def select(key):
        call(0x154b700,0x1fc,key,task=True)
        stored=call(0xb510b8,0x1fc,0,task=True)
        assert stored==0 if key==32 else 0<=stored<18, (key,stored)
        assert word(s['film_choice_key'])==(32 if key==32 else 0)
    select(0);call(0xbbc924,0,task=True)
    select(32);assert word(s['xt2_volatile_commits'])==0
    call(0xbbc924,1,task=True);assert word(s['film_choice_key'])==0 and word(s['xt2_volatile_commits'])==0
    select(32);call(0xbbc924,0,task=True);call(0xbbc924,0,task=True)
    assert word(s['xt2_volatile_commits'])==1
    # Non-menu readers, including unrecognized serializers, retain native key0.
    ptr=RAM+0x3000;u.mem_write(ptr,bytes(4))
    assert api('xpp_menu_stock_shown',0x1fc,ptr,0)==0 and word(ptr)==0
    cursor=json.loads((BUILD/'target.json').read_text())['symbols']['menu_list_cursor_shown_return']
    assert api('xpp_menu_stock_shown',0x1fc,ptr,cursor)==1 and word(ptr)==32
    select(3);assert api('film_xt20_select',3)==0
    select(0)
    menus=[];u.mem_write(0x119299b,bytes([0,14,7]));u.mem_write(0x119f2cb,b'\x00')
    for descriptor,count in [(0xeea334,10),(0xebcdfc,10),(0xedaaac,16)]:
        u.mem_write(0x11802c0,struct.pack('<I',descriptor));call(0x13df330,0,0,0,0,task=True)
        assert word(0x11802d8)==count,(hex(descriptor),word(0x11802d8))
        table=word(descriptor+16);rows=[word(table+8*j) for j in range(count)]
        assert rows[-1]==32 and len(set(rows))==count
        reached=set()
        for event in [4]*(2*count)+[5]*(2*count):
            call(0x13debf0,event,u.mem_read(descriptor,1)[0],1,0,task=True)
            assert call(0xb518d4,RAM+0x3000,task=True)==1
            setting=int.from_bytes(u.mem_read(RAM+0x3008,2),'little');key=word(RAM+0x300c)
            assert setting==0x1fc and key in rows;select(key);reached.add(key)
        assert reached==set(rows)
        menus.append(dict(descriptor=hex(descriptor),count=count,all_rows_reached=True,rows=rows))
    select(32);name=call(0x13db71c,9,9,2,task=True);assert name==s['eterna_text']
    magic,text=struct.unpack('<II',u.mem_read(name,8));assert magic==0x54787058
    assert bytes(u.mem_read(text,7))==b'ETERNA\0'
    # Marker and a separate stock context are built by original entry points.
    a,b=RAM+0x5000,RAM+0x5400
    for address in [a,b]:call(0x15797d8,address,task=True);call(0x157a0fc,address,task=True)
    call(0x157ac60,a,0,task=True);assert bytes(u.mem_read(a+0x145,3))==b'\x01XT'
    select(3);call(0x157ac60,b,3,task=True)
    assert bytes(u.mem_read(a+0x145,3))==b'\x01XT' and bytes(u.mem_read(b+0x145,3))==bytes(3)
    call(0x15797d8,a,task=True);assert bytes(u.mem_read(a+0x145,3))==bytes(3)
    assert not storage and not clock.errors
    OUT.mkdir(exist_ok=True)
    report=dict(scope=__doc__,status='PASS: exact minimal native policy/menu/volatile selection',
        elf_sha256=sha((BUILD/'mods.elf').read_bytes()),setup=setup,
        native_policy_returns=len(stock),init_calls=events,manual_mod_init_calls=0,
        volatile_commits=word(s['xt2_volatile_commits']),commit_repeat_deduplicated=True,cancel_restores_stock=True,
        menus=menus,fn_name='ETERNA',unrecognized_reader_retains_stock=True,
        native_stored_value_for_eterna=0,context_marker_clear_and_isolation=True,
        unexpected_storage_or_timer_requests=storage,native_vfp_exceptions=exceptions,
        full_boot=False,physical_buttons=False,poweroff_serializers_executed=False,
        internal_success_stubs=0,hardware_verified=False,checker_sha256=sha(Path(__file__).read_bytes()))
    (OUT/'runtime.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
