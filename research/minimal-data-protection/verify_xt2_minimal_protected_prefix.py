"""Execute the image-contained data protection wrapper in native early root.

Host-preloaded image and existing two-core/device fixtures; no ROM/full boot.
No host protection calls or installer are supplied during the wrapper.
"""
import contextlib
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn import arm_const as reg
import probe_native_font_initialization as font
import probe_native_cpu_memory_bootstrap as cpu
from probe_native_resident_startup import main as startup
from arm_page_policy import inspect
from build_xt2_minimal_protected import build,OUT,ROOT,LATE,SOURCES
from build_xt2_delivery_probe import digest,require


def main():
    image,meta,_=build()
    require(image==(OUT/'ffboot.bin').read_bytes(),'Delivered protected image differs')
    pins={n:digest((ROOT/'scripts'/n).read_bytes()) for n in [*SOURCES,Path(__file__).name,'build_xt2_minimal_protected.py']}
    evidence=ROOT/'research'/('minimal-protected-prefix-'+meta['image_sha256'][:12])
    evidence.mkdir(exist_ok=True)
    font.STOCK=OUT/'ffboot.bin'
    snapshots={};events=[];writes=[];flash=[];native_calls=[]
    old_prepare=cpu.prepare
    registers=[getattr(reg,'UC_ARM_REG_R'+str(i)) for i in range(13)]
    registers += [reg.UC_ARM_REG_SP,reg.UC_ARM_REG_LR,reg.UC_ARM_REG_CPSR]
    def context(uc):return [uc.reg_read(r) for r in registers]
    def prepare(*args,**kwargs):
        uc=old_prepare(*args,**kwargs)
        require(bytes(uc.mem_read(0x781000,0x3000))==image[0x781000:0x784000],'Preload replaced data')
        def write(u,access,address,size,value,data):
            if max(address,0x781000)<min(address+size,0x784000) or max(address,0xDF7900)<min(address+size,0xDF8000):
                writes.append(dict(pc=hex(u.reg_read(reg.UC_ARM_REG_PC)),address=hex(address),size=size))
                raise ValueError('Immutable candidate CPU write')
        uc.hook_add(UC_HOOK_MEM_WRITE,write)
        def observe(u,pc,size,data):
            events.append(hex(pc))
            table=struct.unpack('<I',u.mem_read(0x5BACC,4))[0]
            if pc==LATE:
                snapshots['incoming']=context(u)
                snapshots['before']={a:inspect(u,a,table) for a in range(0x700000,0x800000,4096)}
                root=struct.unpack('<I',u.mem_read(0x7A548+136*4,4))[0]
                snapshots['root']=root
                snapshots['stack_base']=struct.unpack('<I',u.mem_read(root+0xC,4))[0]
                snapshots['stack_end']=snapshots['stack_base']+struct.unpack('<I',u.mem_read(root+0x14,4))[0]
                snapshots['affinity_before']=(~struct.unpack('<I',u.mem_read(root+0x98,4))[0])&3
                snapshots['entry_sp']=u.reg_read(reg.UC_ARM_REG_SP)
                snapshots['minimum_sp']=snapshots['entry_sp']
            elif pc==0xCF83CC:
                require('incoming' in snapshots,'Original root call before wrapper')
                snapshots['original_call']=context(u)
                require(snapshots['original_call']==snapshots['incoming'],'Original call ABI/flags/SP/LR changed')
                snapshots['after']={a:inspect(u,a,table) for a in range(0x700000,0x800000,4096)}
                snapshots['affinity_after']=(~struct.unpack('<I',u.mem_read(snapshots['root']+0x98,4))[0])&3
                require(snapshots['affinity_after']==snapshots['affinity_before'],'Affinity changed')
            elif pc==0xCF8218:
                snapshots['post_original']={a:inspect(u,a,table) for a in range(0x700000,0x800000,4096)}
                require(bytes(u.mem_read(0x781000,0x3000))==image[0x781000:0x784000],'Data changed through original call')
                raise RuntimeError('Controlled protected-prefix stop after original call')
            elif pc in (meta['symbols']['xt2_minimal_data_failed'],meta['symbols']['xt2_minimal_data_power_request']):
                snapshots['failure_status']=u.reg_read(reg.UC_ARM_REG_R0)
                raise ValueError('Protected wrapper rejected native state: '+hex(snapshots['failure_status']))
        for pc in (LATE,0xCF83CC,0xCF8218,meta['symbols']['xt2_minimal_data_failed'],meta['symbols']['xt2_minimal_data_power_request']):
            uc.hook_add(UC_HOOK_CODE,observe,begin=pc,end=pc)
        def native(u,pc,size,data):
            native_calls.append(dict(pc=hex(pc),args=[u.reg_read(r) for r in (reg.UC_ARM_REG_R0,reg.UC_ARM_REG_R1,reg.UC_ARM_REG_R2)]))
        for pc in (0xCF2100,0x56618,0x566D8):uc.hook_add(UC_HOOK_CODE,native,begin=pc,end=pc)
        def flash_entry(u,pc,size,data):flash.append(hex(pc));raise ValueError('Flash writer entered before bounded stop')
        for pc in (0xC59EE4,0xC5A0B8,0xC5A63C,0xC5AEDC):uc.hook_add(UC_HOOK_CODE,flash_entry,begin=pc,end=pc)
        def stack(u,pc,size,data):
            if 'entry_sp' in snapshots and 'original_call' not in snapshots:
                core=u.cpr_read(15,0,0,0,5,1,False)&3
                current=struct.unpack('<I',u.mem_read(0x5BF90+4*core,4))[0] if core<2 else 0
                if current==snapshots['root'] and u.reg_read(reg.UC_ARM_REG_CPSR)&31==19:
                    sp=u.reg_read(reg.UC_ARM_REG_SP)
                    inside=snapshots['stack_base']<=sp<=snapshots['stack_end']
                    # Scheduler context restoration can publish current=root
                    # before loading its SP (observed at40118). SVC+task ID
                    # alone is not proof of stack ownership there.
                    if LATE<=pc<meta['late_end']:
                        require(inside,'Compiled wrapper outside native root stack')
                    if inside:snapshots['minimum_sp']=min(snapshots['minimum_sp'],sp)
        uc.hook_add(UC_HOOK_CODE,stack,begin=0x40000,end=0xDF8000)
        return uc
    cpu.prepare=prepare
    # Preserve common historical report paths written by the existing harness.
    old_write=Path.write_text;backups={}
    def report_write(path,text,*args,**kwargs):
        if path.parent.resolve()==(ROOT/'research').resolve() and path.suffix=='.json':
            if path not in backups:backups[path]=path.read_bytes() if path.exists() else None
            old_write(evidence/path.name,text,*args,**kwargs)
        return old_write(path,text,*args,**kwargs)
    try:
        Path.write_text=report_write
        with (evidence/'startup.log').open('w') as stream,contextlib.redirect_stdout(stream):
            uc,boot=startup(running_plls=(0,),deliver_sgi=True,native_startup_task=True,max_rounds=2000)
    finally:
        Path.write_text=old_write
        for path,old in backups.items():
            if old is None:path.unlink(missing_ok=True)
            else:path.write_bytes(old)
    errors={k:v for k,v in boot.items() if (k.endswith('_errors') or k in ('error','faults')) and v}
    require(errors=={'error':'RuntimeError: Controlled protected-prefix stop after original call'},'Unexpected model errors: '+str(errors))
    require(events==[hex(LATE),'0xcf83cc','0xcf8218'],'Unexpected entry/original call/return sequence: '+str(events))
    require(not writes and not flash,'Unexpected region write or persistence entry')
    def semantic(row):
        raw=row.get('l2',row['l1']);section=row['kind'] in ('section','supersection')
        tex=(raw>>(12 if section or row['kind']=='large_page' else 6))&7
        shareable=(raw>>(16 if section else 10))&1
        nonglobal=(raw>>(17 if section else 11))&1
        ns=(row['l1']>>(19 if section else 3))&1
        domain=(row['l1']>>5)&15
        return row['physical'],row['ap'],row['xn'],tex,(raw>>3)&1,(raw>>2)&1,shareable,nonglobal,ns,domain
    before=snapshots['before'];after=snapshots['after']
    changed=[hex(a) for a in before if semantic(before[a])!=semantic(after[a])]
    require(changed==['0x781000','0x782000','0x783000'],'Unexpected page change')
    require(all(after[a]['ap']==7 and after[a]['xn'] for a in (0x781000,0x782000,0x783000)),'Data not RO/XN')
    require(all(semantic(after[a])==semantic(snapshots['post_original'][a]) for a in after),'Original call changed protection/attributes')
    require(all(semantic(before[a])[3:]==semantic(after[a])[3:] for a in before),'Memory cache/shareability/security attributes changed')
    terminal_mmu=boot['terminal_cpu']['cp15_banks']['0']
    require(terminal_mmu['sctlr']&1 and terminal_mmu['sctlr']&(1<<23) and
            (terminal_mmu['ttbr0']&0xFFFFC000)==0x108000 and terminal_mmu['dacr']&3==1,
            'Active backend MMU/domain changed through original call')
    require(pins=={n:digest((ROOT/'scripts'/n).read_bytes()) for n in pins},'Sources changed during run')
    report=dict(scope=__doc__,image_sha256=meta['image_sha256'],events=events,errors=errors,
                source_sha256=pins,changed_semantic_pages=changed,other_pages_in_megabyte_preserved=253,
                original_call_context_preserved=snapshots['incoming']==snapshots['original_call'],
                affinity_before=snapshots['affinity_before'],affinity_after=snapshots['affinity_after'],
                stack_bytes=snapshots['entry_sp']-snapshots['minimum_sp'],native_calls=native_calls,
                root_stack_remaining_bytes=snapshots['minimum_sp']-snapshots['stack_base'],
                compiled_wrapper_stack_within_native_allocation=True,
                post_original_backend_mmu=terminal_mmu,cache_shareability_security_attributes_preserved=True,
                protection_preserved_through_original_call=True,
                candidate_cpu_writes=writes,flash_writer_entries=flash,
                host_installer_used=False,protection_integrated_into_image=True,
                hardware_verified=False,full_boot=False,
                actual_native_protected_pages={hex(a):after[a] for a in (0x781000,0x782000,0x783000)},
                evidence_directory=str(evidence.relative_to(ROOT)),
                limitations='Host preloads and existing hardware/CPU scheduling fixtures apply; ROM/low loader before57980, physical cache/DMA and later remapping/full startup are not proved.')
    (ROOT/'research/minimal-protected-prefix-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
