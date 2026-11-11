"""AI-assisted exact892f native settings commit/cancel and SD fixture readback.

Existing pinned SDK two-A7 board, standard RAM-only FAT32 SD node and original
mount caller establish CPU/VFP/tasks, SDK context, registration and filesystem.
Native REC policy starts the exact linked module. Real timer8 IRQ56 and task34
execute settings ticks; original async storage workers execute callbacks.
Native B51088→BBC924 checkpoint/restore calls supply declared MENU/OK/BACK
function boundaries; physical UI events and full reset boot are not claimed.
No API substitutions, host ready/registration/VFP enables or injected ticks.
"""
import hashlib
import json
from pathlib import Path
import struct

from fujimod.emulator import Asset, Definition, Image, make_board

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent.parent
OUT = ROOT / 'sdk-native-fs-settings-commit-unverified'
RAM = 0x08000000
RETURN = RAM + 0xf000


def main():
    OUT.mkdir(exist_ok=True)
    stock = (WORKSPACE / 'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    stock_sha = hashlib.sha256(stock).hexdigest()
    assert stock_sha == 'fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    regions = [(0, 0x3000000), (RAM, 0x10000), (0xe000000, 0x100000)]
    graph = dict(processors=[dict(model='cortex-a7', released=True, mprofile=None,
                   rprofile=None, registers=[['Pc', RETURN], ['Pstate', 0xd3]]) for _ in range(2)],
                 ram=[dict(base=a, size=n) for a, n in regions], decoders=[],
                 mappings=[dict(core=core, address=a, physical=a, size=n, permissions=7)
                           for core in range(2) for a, n in regions],
                 dma_mappings=[dict(address=a, physical=a, size=n, permissions=3)
                               for a, n in regions],
                 peripherals=[dict(core=core,address=0xf0000000,physical=0xf0000000,
                                   size=0x10000000) for core in range(2)], instructions_per_tick=[1, 1])
    inputs = [0] * 16
    inputs[10] = 0x100  # Explicit A present, B absent, same prior probe input.
    nodes = [dict(name='gpio', model=dict(kind='gpio', base=0xfff0c000, inputs=inputs)),
             dict(name='clocks', model=dict(kind='clock-control',
                  options=dict(base=0xfff0b000, lock_ticks=4800))),
             dict(name='resets', model=dict(kind='reset-gates', base=0xfff0a000)),
             dict(name='timer', model=dict(kind='timer', base=0xfff1a000, routes=[(8,56),(15,63)])),
             # Existing SDK SD model, native X-T2 slot-A register base from
             # original c6b6d8/c6b740, same options as prior SDK dependency probe.
             dict(name='sd', model=dict(kind='sd',
                  format=dict(sectors=0x800000,max_dirty_sectors=4096,
                              partition_start=2048,sectors_per_cluster=64,label='SDKPROBE'),
                  files={},irq=83,reset_channel=0,
                  options=dict(base=0xfff92000,register_offset=0x200,
                               transfer_ticks=10,clock_ticks=2,reset_ticks=3,
                               rca=1,ram_bytes=0x3000000,
                               ram_banks=[(RAM,0x10000),(0xe000000,0x100000)])))]
    devices = dict(kind='xpp', cpus=[dict(mpidr=0x80000000+core,
                   configuration_base=0xffff0000, cycles_per_tick=64) for core in range(2)],
                   gic=dict(distributor=0xffff1000, cpu_interface=0xffff2000, lines=512),
                   nodes=nodes)
    definition = Definition(execution=graph, devices=devices,
                            assets=(Asset('stock', len(stock)),),
                            images=(Image('stock', 0, core=0),), quantum=1000)
    board = make_board(definition, {'stock': stock})
    cpu = board.cpus[0]
    board.native.driver_select_core(0)  # Existing SDK isolated-caller parking.
    stages = []
    error = None
    word = lambda a: struct.unpack('<I', cpu.mem_read(a, 4))[0]

    def execute(entry, stop, *args, limit=20_000_000):
        for n in range(4):
            cpu.reg_write({'Arm32': {'R': n}}, args[n] if n < len(args) else 0)
        cpu.reg_write('Sp', RAM + 0xe000)
        cpu.reg_write({'Arm32': {'R': 14}}, RETURN)
        cpu.reg_write('Pc', entry)
        watched = {0x5898c, 0x59214, 0x59230, 0x59238, 0xc69540, 0x5abb4, 0x5ab54, 0x5ab64, 0x53f4c, 0xc6cea0, 0x58af0, 0xcef224, 0xcef264, 0xcef13c, 0xcef16c, 0xc6c93c, 0x53ea0, 0x53e60, 0x452a4, 0xcefb7c, 0x53e7c, 0x53e84, 0x53e8c, 0x53e94, 0x970ad8, 0x970adc, 0x955c48, 0x955dd4, 0x974f34, 0xcf1ee4, 0xcf1ef4, 0xcf1ef8} if entry == 0x96bf88 else set()
        before = board.instructions
        for observation in range(2000):
            board.native.instruction_points(0, [stop, 4, 8, 12, 16, 24, 28, *watched])
            board.run(limit)
            pc = cpu.reg_read('Pc')
            if pc not in watched:
                break
            if pc in (0x5ab54, 0x5ab64):
                address=cpu.reg_read({'Arm32': {'R': 0}})
                if 0xfff92000<=address<0xfff93000:
                    stages.append(dict(native_sd_store=hex(pc),address=hex(address),
                        value=hex(cpu.reg_read({'Arm32': {'R': 1}})),
                        lr=hex(cpu.reg_read({'Arm32': {'R': 14}}))))
                if address == 0xfff9220c and (cpu.reg_read({'Arm32': {'R': 1}}) >> 24) == 17:
                    watched.update([0xc6f834,0xc6c9e0,0xcef13c,0xcef16c])
                board.native.instruction_points(0, [])
                board.run(1)  # Execute the observed original store, no PC/register write.
                continue
            if pc in (0xcf1ee4,0xcf1ef4,0xcf1ef8):
                block=cpu.reg_read({'Arm32': {'R': 5}})
                stages.append(dict(native_affinity_observation=hex(pc),
                    callback=hex(cpu.reg_read({'Arm32': {'R': 4}})),
                    argument_block=hex(block),buffer=hex(word(block)),bytes=word(block+4),
                    affinity_request=cpu.reg_read({'Arm32': {'R': 1}}),
                    processor_count=len(board.cpus)))
            if pc in (0xc6f834,0xc6c9e0):
                host=next(d['state']['host'] for d in board.state()['bus']['devices'] if d['kind']=='xpp-sd')
                regs=host['registers']
                stages.append(dict(native_dma_observation=hex(pc),
                    args=[hex(cpu.reg_read({'Arm32': {'R': n}})) for n in range(4)],
                    normal_status=hex(regs[0x30//2]),error_status=hex(regs[0x32//2]),
                    status_enable=hex(regs[0x34//2]),signal_enable=hex(regs[0x38//2]),
                    reads=host['reads']))
            stages.append(dict(native_exception_observation=hex(pc),
                lr=hex(cpu.reg_read({'Arm32': {'R': 14}})),
                pstate=hex(cpu.reg_read('Pstate')),
                cpacr=hex(cpu.cpr_read(15,0,1,0,2,0,False)),
                fpexc=hex(cpu.reg_read({'Arm32': 'Fpexc'})),
                args=[hex(cpu.reg_read({'Arm32': {'R': n}})) for n in range(7)],
                kernel_gate=hex(word(0x5bf38)), current_dispatch_count=word(word(0x5bf90)+4),
                current_tcb=hex(word(0x5bf90)), task_fp_owned=word(word(0x5bf90)+0xa0)))
            watched.remove(pc)
            if pc == 0x59230:
                watched.add(0x5898c)  # Observe a second genuine UND entry if it occurs.
        pc = cpu.reg_read('Pc')
        result = cpu.reg_read({'Arm32': {'R': 0}})
        stages.append(dict(entry=hex(entry), stop=hex(stop), pc=hex(pc), result=result,
                           instructions=board.instructions - before))
        assert pc == stop, stages[-1]
        board.native.instruction_points(0, [])
        return result

    def secondary_call(entry, stop=RETURN+4):
        secondary=board.cpus[1]
        board.native.driver_select_core(1)
        secondary.reg_write('Sp',RAM+0xc000)
        secondary.reg_write({'Arm32': {'R': 14}},RETURN+4)
        secondary.reg_write('Pc',entry)
        board.native.instruction_points(1,[stop,4,8,12,16,24,28])
        before=board.instructions
        board.run(100_000)
        reached=secondary.reg_read('Pc')
        stages.append(dict(secondary_native_init=hex(entry),stop=hex(stop),pc=hex(reached),
                           instructions=board.instructions-before))
        assert reached==stop
        board.native.instruction_points(1,[])

    active_core = 0
    def execute_smp_call(entry,*args):
        nonlocal active_core
        # Fixed, declared core parking schedule through the existing SDK harness.
        # No device or completion depends on an observed PC.
        caller=board.cpus[active_core]
        board.native.driver_select_core(active_core)
        for n,value in enumerate(list(args[:4])+[0]*(4-len(args[:4]))):caller.reg_write({'Arm32':{'R':n}},value)
        if len(args)>4:caller.mem_write(RAM+0xe000,struct.pack('<'+'I'*(len(args)-4),*args[4:]))
        caller.reg_write('Sp',RAM+0xe000)
        caller.reg_write({'Arm32':{'R':14}},RETURN)
        caller.reg_write('Pc',entry)
        points={core:{RETURN,0xcf1ee4,0xcf1ef4,0xcf1ef8,0xcf1f04,0xcf1f14,0x970adc,0x955dd4,0xcdf968,0xce0198,0xce02e8,0x13833dc}
                for core in range(2)}
        for core in range(2):board.native.instruction_points(core,sorted(points[core]))
        (OUT/'progress.json').write_text(json.dumps(dict(calling=hex(entry),args=list(args),stages=stages[-5:],
            irq56_callback=hex(word(0x10005f4+56*16+12)),irq56_enabled=board.state()['gic']['enabled'][0][56])))
        before=board.instructions
        turn=0
        while board.instructions-before<300_000_000 and turn<30_000:
            core=turn%2;turn+=1
            board.native.driver_select_core(core)
            board.run(10_000,pause_at_tick=board.virtual_ticks+10_000)
            if turn%1000==0:
                (OUT/'heartbeat.json').write_text(json.dumps(dict(entry=hex(entry),turn=turn,
                    instructions=board.instructions-before,ticks=board.virtual_ticks,
                    pcs=[hex(c.reg_read('Pc')) for c in board.cpus],stages=stages[-8:],state=board.state())))
            event=board.native.instruction_event()
            if event is None:continue
            event_core,pc=event
            observed=board.cpus[event_core]
            if pc not in points[event_core]:continue
            r0=observed.reg_read({'Arm32':{'R':0}})
            owner=word(0x5bf90+event_core*4)
            item=dict(smp_native_point=hex(pc),core=event_core,r0=hex(r0),
                      current_tcb=hex(owner),native_task_id=word(owner+0xcc) if owner else None)
            if pc in (0xcf1ee4,0xcf1ef4,0xcf1ef8,0xcf1f04,0xcf1f14):
                block=observed.reg_read({'Arm32':{'R':5}})
                item.update(callback=hex(observed.reg_read({'Arm32':{'R':4}})),
                            buffer=hex(word(block)),bytes=word(block+4))
            stages.append(item)
            if pc==RETURN:
                assert observed.reg_read('Sp')==RAM+0xe000
                stages.append(dict(smp_fs_return=r0,core=event_core,instructions=board.instructions-before,
                                   fixed_core_quantum=10_000,pause_at_tick_delta=10_000,host_success_substitutions=0))
                active_core=event_core
                stages.append(dict(native_file_call=hex(entry),args=list(args),result=r0))
                for completed_core in range(2):board.native.instruction_points(completed_core,[])
                return r0
            points[event_core].remove(pc)
            board.native.instruction_points(event_core,sorted(points[event_core]))
        raise AssertionError(dict(smp_fs_limit=board.instructions-before,turns=turn,state=board.state(),
            pcs=[hex(c.reg_read('Pc')) for c in board.cpus]))

    try:
        secondary_call(0x579a4,0x57a58)
        for entry in (0x49184,0x59240,0x492d0):secondary_call(entry)
        secondary=board.cpus[1]
        secondary.reg_write({'Arm32':{'R':0}},0xff)
        # Native priority-mask helper takes r0; secondary_call preserves it.
        secondary_call(0x49300)
        secondary.reg_write('Pc',0x400c8)
        board.native.driver_select_core(0)
        stages.append(dict(initial_scr=hex(cpu.cpr_read(15,0,1,1,0,0,False)),
                           initial_nsacr=hex(cpu.cpr_read(15,0,1,1,2,0,False))))
        # Original boot-prefix establishes all banked exception stacks and VBAR.
        # It stops before controller/MMU setup; no host VFP/vector registers set.
        execute(0x579a4, 0x57a58)
        # Native original GIC setup from boot prefix and primary-core branch.
        execute(0x49184, RETURN)
        execute(0x49004, RETURN)
        execute(0x49204, RETURN)
        execute(0x492d0, RETURN)
        execute(0x49300, RETURN, 0xff)
        # Observe the actual native CP15 instruction effects without register writes.
        cpu.reg_write('Sp', RAM + 0xe000)
        cpu.reg_write({'Arm32': {'R': 14}}, RETURN)
        cpu.reg_write('Pc', 0x58ccc)
        for checkpoint in (0x58cd0, 0x58cd4, 0x58cd8, 0x58ce0, 0x58ce8, RETURN):
            board.native.instruction_points(0, [checkpoint, 4, 8, 12, 16, 24, 28])
            board.run(1000)
            assert cpu.reg_read('Pc') == checkpoint
            stages.append(dict(native_cp15_checkpoint=hex(checkpoint),
                r1=hex(cpu.reg_read({'Arm32': {'R': 1}})),
                cpacr=hex(cpu.cpr_read(15, 0, 1, 0, 2, 0, False)),
                cpacr_register=hex(cpu.reg_read({'Arm32': 'Cpacr'})),
                cpacr_secure=hex(cpu.cpr_read(15, 0, 1, 0, 2, 1, False)),
                fpexc=hex(cpu.reg_read({'Arm32': 'Fpexc'}))))
        board.native.instruction_points(0, [])
        execute(0x59240, RETURN)  # Native CPACR setup, FPEXC disable, lazy UND registration.
        stages.append(dict(native_cpacr_after_setup=hex(cpu.cpr_read(15, 0, 1, 0, 2, 0, False))))
        assert cpu.reg_read({'Arm32': 'Fpexc'}) & (1 << 30) == 0
        assert 0x59200 in struct.unpack('<8I', cpu.mem_read(0x7f3c8, 32))
        # Full native kernel-list/timer-wheel constructor used by41f94.
        # No global-ready handoff or secondary-core handshake is asserted.
        execute(0x41e50, RETURN)
        stages.append(dict(native_timer_lists=[hex(word(0x5c084)),hex(word(0x5c154))]))
        assert execute(0xcf0034, RETURN) == 0
        assert execute(0x14d6fd8, RETURN) == 0
        assert execute(0xcdf570, RETURN) == 0
        execute(0x58c04, RETURN)  # Native kernel tick init from58ba8, timer15 -> IRQ63.
        execute(0x400c8, 0x140fd9c)  # Actual scheduler selects UI1/native stack.
        # Full native root-start helper, original caller argument from5bb30.
        # Borrow the actual established UI1 context; not full reset/root boot.
        initial_ui_tcb = word(0x5bf90)
        execute(0x5593c, RETURN, word(0x5bb30))
        stages.append(dict(native_start_gates=[word(0x5ba90),word(0x5ba94)],
                           original_start_argument=word(0x5bb30)))
        assert execute(0xceed8c, RETURN) == 1
        tcb = word(0x5bf90)
        assert tcb and tcb == initial_ui_tcb
        stages.append(dict(native_task=1, tcb=hex(tcb),
                           cpacr=hex(cpu.cpr_read(15, 0, 1, 0, 2, 0, False)),
                           fpexc=hex(cpu.reg_read({'Arm32': 'Fpexc'}))))
        execute(0xcf8134, 0xcf8154)  # Actual root semaphore configuration loop.
        for entry in [0xcec598, 0xcec634]:
            assert execute(entry, RETURN) == 0
        request,params=RAM+0x9000,RAM+0x9100
        cpu.mem_write(request,bytes(64))
        cpu.mem_write(request+8,struct.pack('<I',params))
        data=bytearray(0x40)
        struct.pack_into('<IIII',data,4,0xe000000,0x100000,4,0)
        data[0x15]=1
        struct.pack_into('<I',data,0x18,1)
        data[0x1c:0x20]=b'DSCF';data[0x20:0x25]=b'_FUJI';data[0x34]=ord('A')
        cpu.mem_write(params,bytes(data))
        result=execute_smp_call(0x969348,request)
        stages.append(dict(native_mount_caller=result,context=hex(word(0x9c2260)),
            fs_workspace=hex(word(0x9c3560)),drive=cpu.mem_read(0x9c35e8,1).hex()))
        assert result==0 and word(0x9c2260)==0xe000000
        import io
        from elftools.elf.elffile import ELFFile
        build=ROOT/'save-data-menu-native-build-unverified'
        raw=(build/'mods.elf').read_bytes()
        assert hashlib.sha256(raw).hexdigest()=='892f6d3b5cafb9ac86c4f32e9a625220d58593a7b2c7c6310fcf739c46fe482e'
        elf=ELFFile(io.BytesIO(raw))
        symbols={item.name:item['st_value'] for item in elf.get_section_by_name('.symtab').iter_symbols()}
        for section in elf.iter_sections():
            if not section['sh_flags']&2 or not section['sh_size'] or section.name in ('.x70mod.hooks','.x70mod.strings'):continue
            start,size=section['sh_addr'],section['sh_size']
            assert 0x1380000<=start<start+size<=0x13c0000
            cpu.mem_write(start,bytes(size) if section['sh_type']=='SHT_NOBITS' else section.data())
        for edit in json.loads((build/'manifest.json').read_text())['words']:
            address=int(edit['address'],0);assert word(address)==int(edit['old'],0)
            cpu.mem_write(address,struct.pack('<I',int(edit['new'],0)))
        for entry in (0xcf8e14,0x24c6284):assert execute_smp_call(entry)==0
        for address,value in [(0x10c62b0,0x120d8a0),(0x119162c,0x119f25c)]:cpu.mem_write(address,struct.pack('<I',value))
        cpu.mem_write(0x119f25c,b'\x24');cpu.mem_write(0x121d626,b'\x03');cpu.mem_write(symbols['ui_mode'],b'\x03')
        target=json.loads((build/'target.json').read_text())
        policy=target['symbols']['ui_display_off_policy']
        assert execute_smp_call(policy)==0
        owner=symbols['x70_stock_choice_settings']
        def settings_state():
            return dict(requested=word(owner+92),completed=word(owner+96),failed=word(owner+100),
                        registered=word(owner+104),io=list(struct.unpack('<15i',cpu.mem_read(owner+32,60))))
        stages.append(dict(native_policy=hex(policy),settings_initial=settings_state()))
        for attempt in range(10):
            assert execute_smp_call(0xceed9c,300)==0
            stages.append(dict(startup_attempt=attempt,settings=settings_state(),
                callbacks=word(symbols['callbacks']),active=hex(word(symbols['x70_cardio_active']))))
            if word(owner+104)==2 and not word(symbols['x70_cardio_active']):break
        assert word(owner+104)==2
        initial_key=word(symbols['film_choice_key'])
        execute_smp_call(0xb51088,0)
        assert execute_smp_call(0x154b700,0x1fc,33)==0
        assert word(symbols['film_choice_key'])==33 and word(owner+92)==0
        execute_smp_call(0xb51088,1)
        stages.append(dict(native_cancel=True,key=word(symbols['film_choice_key']),expected=initial_key,
                           settings=settings_state()))
        assert word(symbols['film_choice_key'])==initial_key and word(owner+92)==0
        assert execute_smp_call(0x154b700,0x1fc,32)==0
        execute_smp_call(0xb51088,0)
        execute_smp_call(0xb51088,0)
        assert word(owner+92)==1
        stages.append(dict(settings_commit=settings_state(),key=word(symbols['film_choice_key'])))
        for attempt in range(6):
            assert execute_smp_call(0xceed9c,300)==0
            stages.append(dict(save_attempt=attempt,settings=settings_state(),
                callbacks=word(symbols['callbacks']),active=hex(word(symbols['x70_cardio_active']))))
            if word(owner+96)==word(owner+92) and word(owner+92):break
        assert word(owner+92)==word(owner+96)==1 and word(owner+100)==0
        job,folder,name,buffer=RAM+0x5000,RAM+0x5200,RAM+0x5300,RAM+0x5400
        cpu.mem_write(job,bytes(132));cpu.mem_write(folder,b'FUJIMOD\0')
        cpu.mem_write(name,b'SETTINGS.JSN\0')
        assert execute_smp_call(symbols['x70_cardio_read'],job,folder,name,buffer,2048)==0
        for attempt in range(8):
            if word(job)!=1:break
            assert execute_smp_call(0xceed9c,100)==0
        assert word(job)==2 and word(job+8)==0
        content=bytes(cpu.mem_read(buffer,word(job+20))).decode()
        (OUT/'settings-readback.json').write_bytes(content.encode())
        produced=json.loads(content)
        stages.append(dict(settings_content=produced,bytes=word(job+20),content_sha256=hashlib.sha256(content.encode()).hexdigest(),
            settings_final=settings_state(),callbacks=word(symbols['callbacks'])))
        assert produced['stock_choices']['current']['values']==[dict(setting='film_simulation',value='eterna')]
        assert word(symbols['callbacks'])==0
        execute_smp_call(0xb51088,1)
        banks=[word(symbols['bank_state']+n*4) for n in range(4)]
        stages.append(dict(native_committed_restore=True,key=word(symbols['film_choice_key']),
            settings=settings_state(),native_open_count=word(0x9c3594),banks=banks,
            active=word(symbols['x70_cardio_active']),hold=word(symbols['x70_cardio_hold']),
            callbacks=word(symbols['callbacks'])))
        assert word(symbols['film_choice_key'])==32 and word(owner+92)==1
        assert word(0x9c3594)==0 and banks==[0]*4
        assert word(symbols['x70_cardio_active'])==word(symbols['x70_cardio_hold'])==word(symbols['callbacks'])==0
    except Exception as exc:
        error = repr(exc)
        import traceback
        error += '\n' + traceback.format_exc()
    finally:
        frame = cpu.reg_read({'Arm32': {'R': 11}})
        frames = []
        for depth in range(12):
            if frame & 3 or frame < 4 or frame > 0x3000000 or any(f['fp'] == hex(frame) for f in frames):
                break
            try:
                frames.append(dict(fp=hex(frame), return_pc=hex(word(frame)),
                                   caller_fp=hex(word(frame-4))))
                frame=word(frame-4)
            except Exception:
                break
        from fujimod._native import emulator as native
        fmt = dict(sectors=0x800000,max_dirty_sectors=4096,partition_start=2048,
                   sectors_per_cluster=64,label='SDKPROBE')
        medium = native.CardMedium.formatted(json.dumps(fmt), [])
        mbr=bytes(medium.sector(0));boot=bytes(medium.sector(2048))
        staging=bytes(cpu.mem_read(0xff9740,512))
        native_mbr_address=word(0x9c3570)
        loaded=bytes(cpu.mem_read(native_mbr_address,512))
        sector_evidence=dict(expected_mbr_sha256=hashlib.sha256(mbr).hexdigest(),
            expected_mbr_signature=mbr[510:].hex(),partition_type=mbr[0x1c2],
            partition_lba=struct.unpack_from('<I',mbr,0x1c6)[0],
            partition_sectors=struct.unpack_from('<I',mbr,0x1ca)[0],
            boot_signature=boot[510:].hex(),bytes_per_sector=struct.unpack_from('<H',boot,11)[0],
            sectors_per_cluster=boot[13],reserved_sectors=struct.unpack_from('<H',boot,14)[0],
            fats=boot[16],fat32_sectors=struct.unpack_from('<I',boot,36)[0],
            total_sectors=struct.unpack_from('<I',boot,32)[0],
            root_cluster=struct.unpack_from('<I',boot,44)[0],
            dma_staging_address='0xff9740',dma_staging_sha256=hashlib.sha256(staging).hexdigest(),
            dma_staging_matches_mbr=staging==mbr,dma_staging_signature=staging[510:].hex(),
            native_mbr_address=hex(native_mbr_address),native_mbr_sha256=hashlib.sha256(loaded).hexdigest(),
            native_mbr_matches=loaded==mbr,native_mbr_signature=loaded[510:].hex())
        pools=[]
        for index in range(2):
            address=word(0x9c374c+index*4)
            if not 0xe000000<=address<0xe100000:
                pools.append(dict(index=index,address=hex(address),qualified=False))
                continue
            unit=word(address);count=cpu.mem_read(address+12,1)[0]
            data=word(address+8);end=data+unit*count
            pools.append(dict(index=index,address=hex(address),unit_bytes=unit,count=count,
                data=hex(data),end=hex(end),within_original_workspace=0xe000000<=address<=data<=end<=0xe100000))
        report = dict(scope=__doc__, native_frame_chain=frames,sector_evidence=sector_evidence,
                      native_cache_pools=pools,
                      input_geometry_variant='Existing SDK FAT32 formatter: same4GiB card,64-sector clusters',
                      core_registers=[dict(core=i,pc=hex(c.reg_read('Pc')),
                          general=[hex(c.reg_read({'Arm32':{'R':n}})) for n in range(13)])
                          for i,c in enumerate(board.cpus)], stock_sha256=stock_sha, stages=stages,
                      error=error, pc=hex(cpu.reg_read('Pc')), state=board.state(),
                      registers=dict(pstate=hex(cpu.reg_read('Pstate')),
                                     lr=hex(cpu.reg_read({'Arm32': {'R': 14}})),
                                     spsr=hex(cpu.reg_read({'Arm32': 'Spsr'})),
                                     general=[hex(cpu.reg_read({'Arm32': {'R': n}})) for n in range(13)]),
                      registration_words=[word(0x9ae7fc + n * 4) for n in range(3)],
                      driver_types=list(cpu.mem_read(0x9ae7f4, 3)),
                      devices=devices, firmware_api_substitutions=0,
                      host_registration_writes=0, host_vfp_enable_writes=0,
                      original_probe_sha256='ca4eb2110ff766509e6163c2a024dae33d038d7f73f4ee1db103cff9d2406cd1',
                      fpexc=hex(cpu.reg_read({'Arm32': 'Fpexc'})),
                      cpacr=hex(cpu.cpr_read(15, 0, 1, 0, 2, 0, False)),
                      current_task=word(0x5bf90),
                      kernel_global_gates={hex(a):hex(word(a)) for a in [0x5ba90,0x5ba94,0x5bf8c,0x5bf38]},
                      current_native_id=word(word(0x5bf90)+0xcc),
                      native_task_limit=word(0x5bac4),
                      mailbox120=hex(word(0x5d394+119*4)),
                      mailbox121=hex(word(0x5d394+120*4)),
                      storage_vtable=hex(word(0x11892a4)),
                      storage_init=hex(word(word(0x11892a4))),
                      current_dispatch_count=word(word(0x5bf90)+4),
                      kernel_gate=hex(word(0x5bf38)),
                      native_first_dispatch='0x400c8',
                      sd_irq83_callback=hex(word(0x10005f4+83*16+12)),
                      sd_irq83_enabled=board.state()['gic']['enabled'][0][83],
                      scr=hex(cpu.cpr_read(15,0,1,1,0,0,False)),
                      nsacr=hex(cpu.cpr_read(15,0,1,1,2,0,False)),
                      native_core_count=2,declared_core_schedule='existing SDK parking: alternating instruction cap10000, guest tick cap10000',
                      camera_tested=False)
        (OUT / 'probe.json').write_text(json.dumps(report, indent=2) + '\n')
        board.close()
    print(json.dumps({k: report[k] for k in ['error', 'pc', 'registration_words']}))
    assert error is None, error


if __name__ == '__main__':
    main()
