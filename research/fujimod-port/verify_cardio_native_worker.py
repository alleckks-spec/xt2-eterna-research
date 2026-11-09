"""Native directory workers/error callback and bounded native details writers.

AI-assisted original checker. Constructor order/worker entry and scratch stacks
are harness-invoked, not native task scheduling. Device-context fields and FAT
records/raw EOF statuses are explicit fixtures. Error chains execute both native
workers and callbacks without internal API stubs. Success-side details checks
borrow the frame after the FAT call, never invent a successful mounted FAT read.
The stock semaphore bootstrap loop is separately harness-invoked. Its native
configuration, not a synthetic ready-post, satisfies the initial worker wait.
"""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R11,
    UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_C1_C0_2,UC_ARM_REG_FPEXC)
from unicorn.unicorn_py3.unicorn import uclib
import kernel_timer_initialization as timer_model

RAM=0x8000000
RETURN=RAM+0xf000
DEVICE=0x9000000
JOB=RAM+0x1000
ENTRIES=RAM+0x4000


def sha(b):return hashlib.sha256(b).hexdigest()


class Assay:
    def __init__(self,stock,component):
        self.u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u=self.u
        u.mem_map(0,(len(stock)+4095)&~4095);u.mem_write(0,stock)
        u.mem_map(RAM,0x10000);u.mem_map(DEVICE,0x17000)
        u.reg_write(UC_ARM_REG_C1_C0_2,0xf<<20);u.reg_write(UC_ARM_REG_FPEXC,1<<30)
        self.clock=timer_model.TimerInitialization();self.clock.attach(u)
        assert self.call(0xcf0034)==0
        self.semaphore_configuration=[];results=[]
        h=u.hook_add(UC_HOOK_CODE,lambda uc,a,z,d:self.semaphore_configuration.append(
            [uc.reg_read(UC_ARM_REG_R0),uc.reg_read(UC_ARM_REG_R1)]),begin=0xcef334,end=0xcef334)
        h2=u.hook_add(UC_HOOK_CODE,lambda uc,a,z,d:results.append(uc.reg_read(UC_ARM_REG_R0)),begin=0xcf8148,end=0xcf8148)
        context=u.context_save();u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.reg_write(UC_ARM_REG_LR,RETURN)
        self.execute_to(0xcf8134,0xcf8154)
        u.hook_del(h);u.hook_del(h2);u.context_restore(context)
        assert self.semaphore_configuration==[[i,1] for i in range(1,132)] and results==[0]*131
        for entry in [0xcec598,0xcec634]:assert self.call(entry)==0
        assert self.word(0x9c2260)==0
        elf=ELFFile(io.BytesIO(component));self.symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
        for s in elf.iter_sections():
            if not s['sh_flags']&2 or not s['sh_size']:continue
            start,size=s['sh_addr'],s['sh_size'];assert 0x2000000<=start<start+size<=0x2010000
            u.mem_write(start,b'\0'*size if s['sh_type']=='SHT_NOBITS' else s.data())
        u.mem_write(RAM+0x3000,b'FUJIMOD\\FILMS\0');u.mem_write(RAM+0x3100,b'*.TXT\0')
        u.mem_write(JOB,b'\0'*132);u.mem_write(ENTRIES,b'\xcc'*80)
        u.mem_write(DEVICE+0x16b84,struct.pack('<I',4096))
        self.callbacks=[];self.semaphore_results=[];self.workers=[]
        for n in range(4):
            pc=self.symbols[f'cb_list_{n}']
            u.hook_add(UC_HOOK_CODE,lambda uc,a,z,d:self.callbacks.append(uc.reg_read(UC_ARM_REG_R0)),begin=pc,end=pc)
        u.hook_add(UC_HOOK_CODE,lambda uc,a,z,d:self.semaphore_results.append(uc.reg_read(UC_ARM_REG_R0)),begin=0x969ff4,end=0x969ff4)

    def word(self,address):return struct.unpack('<I',self.u.mem_read(address,4))[0]

    def call(self,entry,*args):
        u=self.u;context=u.context_save()
        for reg,value in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],list(args)+[0]*4):u.reg_write(reg,value)
        if len(args)>4:u.mem_write(RAM+0xe000,struct.pack('<'+'I'*(len(args)-4),*args[4:]))
        u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.reg_write(UC_ARM_REG_LR,RETURN)
        u.emu_start(entry,RETURN,count=2000000)
        assert u.reg_read(UC_ARM_REG_PC)==RETURN,hex(u.reg_read(UC_ARM_REG_PC))
        assert u.reg_read(UC_ARM_REG_SP)==RAM+0xe000
        result=u.reg_read(UC_ARM_REG_R0);u.context_restore(context);return result

    def api(self,name,*args):return self.call(self.symbols[name],*args)

    def presence(self,present):self.u.mem_write(0x9c2260,struct.pack('<I',DEVICE if present else 0))

    def begin(self):
        self.presence(True)
        assert self.api('x70_cardio_list',JOB,RAM+0x3000,RAM+0x3100,ENTRIES,4)==0
        assert self.word(JOB)==1 and self.api('x70_lifetime_live')==1

    def execute_to(self,start,end):
        u=self.u;reached=[]
        def stop(uc,a,n,d):reached.append(a);uc.emu_stop()
        h=u.hook_add(UC_HOOK_CODE,stop,begin=end,end=end)
        try:u.emu_start(start,RETURN,count=2000000)
        finally:u.hook_del(h)
        assert reached==[end] and u.reg_read(UC_ARM_REG_PC)==end

    def pump(self):
        u=self.u;context=u.context_save()
        for entry,end,argument in [(0x969b54,0x969c00,0x9c3540),(0x969fcc,0x96a090,0)]:
            u.reg_write(UC_ARM_REG_R0,argument);u.reg_write(UC_ARM_REG_SP,RAM+0xd000)
            u.reg_write(UC_ARM_REG_LR,RETURN);self.execute_to(entry,end)
            self.workers.append(dict(entry=hex(entry),stop=hex(end)))
        u.context_restore(context)
        assert self.semaphore_results==[0],self.semaphore_results

    def take(self):
        u=self.u;descriptor=RAM+0x6000;payload=RAM+0x6100
        u.mem_write(descriptor,struct.pack('<3I',0,0,payload))
        assert self.call(0xcefb60,120,descriptor,0)==0
        code,source,destination,size=struct.unpack('<HBBI',u.mem_read(descriptor,8))
        assert source==0 and destination==120 and size in (8,60)
        return descriptor,payload,code

    def frame(self,descriptor,payload,status):
        u=self.u;fp=RAM+0xdffc
        for reg,value in [(UC_ARM_REG_R4,payload),(UC_ARM_REG_R5,descriptor),
            (UC_ARM_REG_R6,self.word(payload)),(UC_ARM_REG_R7,status),
            (UC_ARM_REG_R11,fp),(UC_ARM_REG_SP,fp-0x6c),(UC_ARM_REG_LR,RETURN)]:u.reg_write(reg,value)
        return fp

    def details(self,kind,size,attributes,live=False):
        u=self.u
        if live:descriptor,payload,code=self.take();assert code==0x1377 and kind=='first'
        else:
            descriptor,payload=RAM+0x6000,RAM+0x6100;code=0x1377 if kind=='first' else 0x1378
            u.mem_write(descriptor,struct.pack('<HBBII',code,0,39,60 if kind=='first' else 8,payload))
            u.mem_write(payload,struct.pack('<2I',0,ENTRIES))
            u.mem_write(ENTRIES-16,b'\xa5'*132)
        destination=self.word(payload+4);u.mem_write(destination,b'\xcc'*100)
        record=bytearray(80);name=b'A:\\FUJIMOD\\FILMS\\GOOD.TXT'
        record[:len(name)]=name;record[59]=attributes;record[61]=150
        def fat_time(year,month,day,hour,minute,second):
            return struct.pack('<HH',(hour<<11)|(minute<<5)|(second//2),((year-1980)<<9)|(month<<5)|day)
        record[62:66]=fat_time(2026,11,9,15,4,22)
        record[70:74]=fat_time(1999,7,14,3,2,4)
        record[76:80]=struct.pack('<I',size)
        fp=self.frame(descriptor,payload,0);u.mem_write(fp-0x6c,bytes(record))
        touched=set()
        def store(uc,access,address,length,value,data):
            assert RAM+0xc000<=address and address+length<=fp-0x6c or destination<=address and address+length<=destination+100,(hex(uc.reg_read(UC_ARM_REG_PC)),hex(address),length)
            if destination<=address<destination+100:touched.update(range(address-destination,address-destination+length))
        h=u.hook_add(UC_HOOK_MEM_WRITE,store)
        start,end=(0x967af8,0x967c20) if kind=='first' else (0x967c98,0x967dc0)
        try:self.execute_to(start,end)
        finally:u.hook_del(h)
        result=bytes(u.mem_read(destination,100))
        assert result[:48]==bytes(record[:48]) and result[48]==attributes
        assert result[49:52]==b'\xcc'*3 and struct.unpack('<2I',result[52:60])==(size,((size+4095)//4096)*4096)
        assert result[60:80]==b'2026.11.09 15:04:23\0' and result[80:100]==b'1999.07.14 03:02:04\0'
        assert touched==set(range(49))|set(range(52,100))
        assert bytes(u.mem_read(fp-0x6c,80))==bytes(record)
        if not live:
            assert bytes(u.mem_read(destination-16,16))==b'\xa5'*16
            assert bytes(u.mem_read(destination+100,16))==b'\xa5'*16
        return dict(kind=kind,size=size,attributes=attributes,bytes_written=len(touched),canaries=not live),end

    def callback_after_details(self,writer_stop,removed=False):
        if removed:self.presence(False)
        self.execute_to(writer_stop,0x967c3c)
        assert self.callbacks==[0] and self.word(JOB+24)==1
        assert bytes(self.u.mem_read(ENTRIES,13)).split(b'\0',1)[0]==b'GOOD.TXT'
        assert self.word(ENTRIES+16)==123 and self.u.mem_read(ENTRIES+13,1)==b'\x21'

    def eof_tail(self):
        descriptor,payload,code=self.take();assert code==0x1378
        self.frame(descriptor,payload,7)  # explicit raw FAT end status, not a filesystem success stub
        self.execute_to(0x967dc0,0x967ddc)
        assert self.callbacks==[0,6]

    def settled(self,state,status,count):
        assert (self.word(JOB),self.word(JOB+8),self.word(JOB+24))==(state,status,count)
        assert self.api('x70_lifetime_live')==0 and self.word(self.symbols['x70_cardio_active'])==0
        assert self.word(self.symbols['x70_cardio_hold'])==0
        assert bytes(self.u.mem_read(self.symbols['bank_state'],16))==bytes(16)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',required=True,type=Path);p.add_argument('--component',required=True,type=Path)
    p.add_argument('--expect-masked-error',action='store_true');p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();stock=a.stock.read_bytes();component=a.component.read_bytes()
    assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    build=json.loads(a.component.with_name('build.json').read_text());assert sha(component)==build['elf_sha256']
    assert sha(a.component.with_name('preparation.json').read_bytes())==build['preparation_sha256']
    for path,digest in (build['dependencies']|build.get('extension_dependencies',{})).items():assert sha(Path(path).read_bytes())==digest,path
    if a.expect_masked_error:assert sha(component)=='d2faea6b75dcf877dd75febef0375f77afaaa72eead1e20ab91872a577a3a44c'
    else:assert build.get('extension_dependencies')
    expected_state,expected_status=(2,0) if a.expect_masked_error else (3,5)
    cases=[]
    m=Assay(stock,component);m.begin();m.presence(False);m.pump()
    assert m.callbacks==[5];m.settled(expected_state,expected_status,0)
    cases.append(dict(name='device removed before first handler',native_callback_statuses=m.callbacks,job_state=expected_state,job_status=expected_status,workers=m.workers,semaphore=m.semaphore_results))
    m=Assay(stock,component);m.begin();m.api('x70_cardio_abandon',JOB);m.presence(False);m.pump()
    assert m.callbacks==[5];m.settled(3,0xffffffff,0)
    cases.append(dict(name='abandoned job retires through actual native error callback',native_callback_statuses=m.callbacks,job_state=3,job_status=-1,workers=m.workers))
    layouts=[]
    m=Assay(stock,component);m.presence(True)
    for kind in ['first','next']:
        for size,attributes in [(0,0),(1,0x10),(2048,0x21),(4097,0xff)]:
            result,_=m.details(kind,size,attributes);layouts.append(result)
    m=Assay(stock,component);m.begin();_,stop=m.details('first',123,0x21,True)
    m.callback_after_details(stop);m.presence(False);m.pump()
    assert m.callbacks==[0,5];m.settled(expected_state,expected_status,1)
    cases.append(dict(name='device removed before next handler preserves partial-count failure',native_callback_statuses=m.callbacks,job_state=expected_state,job_status=expected_status,count=1,workers=m.workers))
    m=Assay(stock,component);m.begin();_,stop=m.details('first',123,0x21,True)
    m.callback_after_details(stop,removed=True);m.settled(expected_state,expected_status,1)
    cases.append(dict(name='native readiness refusal before next submission',native_callback_statuses=m.callbacks,job_state=expected_state,job_status=expected_status,count=1))
    m=Assay(stock,component);m.begin();_,stop=m.details('first',123,0x21,True)
    m.callback_after_details(stop);m.eof_tail();m.settled(2,0,1)
    cases.append(dict(name='native details writer and end mapper feed actual C reader',native_callback_statuses=m.callbacks,job_state=2,job_status=0,count=1))
    # Execute actual FAT-wrapper EOF/error branches, then native status mapper.
    branch_results=[]
    for start,end in [(0x96b99c,0x96b9ac),(0x96b9d8,0x96b9e8),(0x96bb20,0x96bb30)]:
        for raw_status in [0x10a,0x100]:
            ctx=m.u.context_save();m.u.reg_write(UC_ARM_REG_R0,raw_status)
            m.u.emu_start(start,end,count=20);assert m.u.reg_read(UC_ARM_REG_PC)==end
            internal=m.u.reg_read(UC_ARM_REG_R0);m.u.context_restore(ctx)
            mapped=m.call(0x966ae0,0x1377,internal)
            assert (mapped==6)==(raw_status==0x10a)
            branch_results.append(dict(branch=hex(start),fat_status=raw_status,internal=internal,callback=mapped))
    maps=[];known={0:0,2:5,4:8,6:5,7:6,8:6,11:5,20:9}
    for internal in range(39):
        for code in [0x1377,0x1378]:
            value=m.call(0x966ae0,code,internal)
            if internal in known:assert value==known[internal]
            maps.append(dict(command=hex(code),internal=internal,callback=value))
    # Code6 must not hide any other status in the native mapper's full0..38 domain.
    for code in ['0x1377','0x1378']:
        assert {x['internal'] for x in maps if x['command']==code and x['callback']==6}=={7,8}
    assert not m.clock.errors and m.clock.elapsed_ticks==0
    report=dict(scope=__doc__,status='PASS: reproduced masked native error' if a.expect_masked_error else 'PASS: native error preservation and details ABI',
        expected_masked_error=a.expect_masked_error,cases=cases,layout_cases=layouts,status_mappings=maps,eof_branches=branch_results,
        native_details_writer_extent=100,native_details_padding=[49,50,51],native_details_bytes_written=97,
        raw_fat_record_supplied=True,positive_frame_borrowed=True,callbacks_manually_invoked=False,
        internal_api_stubs=0,worker_entries_harness_invoked=True,native_scheduler=False,
        initial_worker_gate_satisfied=True,initial_worker_wait=0,
        semaphore_bootstrap=dict(start='0xcf8134',stop='0xcf8154',creations=131,native_initial_count=1,harness_invoked=True),
        mounted_fat=False,whole_service_startup=False,concurrent_cancel=False,hardware_verified=False,
        common_candidate_changed=False,elf_sha256=sha(component),stock_sha256=sha(stock),
        checker_sha256=sha(Path(__file__).read_bytes()),build_sha256=sha(a.component.with_name('build.json').read_bytes()),
        timer_fixture_sha256=sha(Path(timer_model.__file__).read_bytes()),diagnostic_timer='Existing reset counter0 only; no advance/IRQ',
        unicorn_sha256=sha(Path(uclib._name).read_bytes()))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],cases=len(cases),layouts=len(layouts),status_maps=len(maps),worker_startup=False)))


if __name__=='__main__':main()
