"""Observe actual X-T2 callback/issue tasks on the final SDK storage chain.

Reuse its exact native mount, SDK task/IRQ prerequisites and positive SETTINGS
write. Optional fault is one explicit negative native media-status bit at a
successful open callback for the final test read. No return value, callback,
ready registration or successful kernel/API result is substituted.
"""
import argparse
import inspect
import json
from pathlib import Path
import probe_sdk_native_fs_settings_commit as original
from build_modular_candidate import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--build',type=Path,default=ROOT/'wb-usb-date-build-unverified')
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--refuse-transfer',action='store_true')
 p.add_argument('--recorded-issue',action='store_true')
 p.add_argument('--transient-refusal',action='store_true',help='Restore the negative status input at the real read callback so native close can retire normally')
 a=p.parse_args();assert not (a.output/'probe.json').exists()
 receipt=json.loads((a.build/'preparation.json').read_text());digest=sha((a.build/'mods.elf').read_bytes());assert digest==receipt['elf_sha256']
 source=inspect.getsource(original.main)
 def replace(old,new):
  nonlocal source
  assert source.count(old)==1,old;source=source.replace(old,new)
 replace("        build=ROOT/'save-data-menu-native-build-unverified'",'        build=CONTRACT_BUILD')
 replace("        assert hashlib.sha256(raw).hexdigest()=='892f6d3b5cafb9ac86c4f32e9a625220d58593a7b2c7c6310fcf739c46fe482e'",'        assert hashlib.sha256(raw).hexdigest()==CONTRACT_ELF')
 replace('    stages = []','    stages = []\n    contract_trace=[];contract_points=set();contract_symbols={};fault_enabled=False;fault_applied=[];contract_result={}')
 replace("        for edit in json.loads((build/'manifest.json').read_text())['words']:","        contract_symbols.update(symbols)\n        contract_points.update([0x969f24,0x969f6c,0xced4b4,0xced500,0xced554,0xced5a0])\n        contract_points.update(v for k,v in symbols.items() if k.startswith(('cb_open_read_','cb_read_','cb_close_read_')) and k[-1:] in '0123')\n        for edit in json.loads((build/'manifest.json').read_text())['words']:")
 replace('        for core in range(2):board.native.instruction_points(core,sorted(points[core]))','        for core in range(2):\n            points[core].update(contract_points)\n            board.native.instruction_points(core,sorted(points[core]))')
 anchor='            stages.append(item)'
 addition='''            if pc in contract_points:
                regs=[observed.reg_read({'Arm32':{'R':n}}) for n in range(4)]
                bank_states=[word(contract_symbols['bank_state']+n*4) for n in range(4)]
                event=dict(pc=hex(pc),core=event_core,task=item['native_task_id'],args=regs,
                    lr=hex(observed.reg_read({'Arm32':{'R':14}})),banks=bank_states,
                    callbacks=word(contract_symbols['callbacks']),active=word(contract_symbols['x70_cardio_active']))
                if pc==0x969f24:
                    event['message']=list(struct.unpack('<HBBII',observed.mem_read(regs[0],12)))
                contract_trace.append(event)
                open_callbacks=[v for k,v in contract_symbols.items() if k.startswith('cb_open_read_') and k[-1:] in '0123']
                if FAULT_INPUT and fault_enabled and not fault_applied and pc in open_callbacks and regs[0]==0 and event['active']==RAM+0x5000:
                    context=word(0x9c2260);address=context+0x16b6c
                    old=bytes(observed.mem_read(address,1))[0]
                    assert not old&4
                    observed.mem_write(address,bytes([old|4]))
                    fault_applied.append(dict(native_media_flags_address=hex(address),old=old,new=old|4,at_callback=hex(pc),task=item['native_task_id']))
                read_callbacks=[v for k,v in contract_symbols.items() if k.startswith('cb_read_') and k[-1:] in '0123']
                if TRANSIENT_FAULT and fault_applied and 'restored_at_callback' not in fault_applied[0] and pc in read_callbacks and regs[0]==5:
                    fault=fault_applied[0];observed.mem_write(int(fault['native_media_flags_address'],0),bytes([fault['old']]))
                    fault['restored_at_callback']=hex(pc)

            stages.append(item)'''
 replace(anchor,addition)
 start=source.index('        job,folder,name,buffer=RAM+0x5000')
 end=source.index('    except Exception as exc:',start)
 tail='''        job,folder,name,buffer=RAM+0x5000,RAM+0x5200,RAM+0x5300,RAM+0x5400
        cpu.mem_write(job,bytes(132));cpu.mem_write(folder,b'FUJIMOD\\0');cpu.mem_write(name,b'SETTINGS.JSN\\0')
        fault_enabled=True
        assert execute_smp_call(symbols['x70_cardio_read'],job,folder,name,buffer,2048)==0
        for attempt in range(8):
            if word(job)!=1:break
            assert execute_smp_call(0xceed9c,300)==0
        state=word(job);status=word(job+8);banks=[word(symbols['bank_state']+n*4) for n in range(4)]
        contract_result=dict(job_state=state,status=status,banks=banks,callbacks=word(symbols['callbacks']),
            active=word(symbols['x70_cardio_active']),stale=word(symbols['x70_cardio_stale']),
            actual_open_count=word(0x9c3594),fault_applied=fault_applied)
        if FAULT_INPUT:
            assert len(fault_applied)==1
            if RECORDED_ISSUE:
                assert state==3 and status==5 and banks==[0]*4 and contract_result['callbacks']==contract_result['active']==0,contract_result
                if TRANSIENT_FAULT:assert contract_result['actual_open_count']==0,contract_result
            else:
                assert state==1 and status==0 and contract_result['callbacks']==0 and contract_result['active']==job,contract_result
                assert banks.count(1)==1 and contract_result['stale']==1,contract_result
        else:
            assert state==2 and status==0 and banks==[0]*4 and contract_result['callbacks']==contract_result['active']==0,contract_result
            content=bytes(cpu.mem_read(buffer,word(job+20))).decode()
            assert json.loads(content)['stock_choices']['current']['values']==[dict(setting='film_simulation',value='eterna')]
        if FAULT_INPUT and TRANSIENT_FAULT and RECORDED_ISSUE:
            stable_before=len(contract_trace)
            for repeat in range(3):assert execute_smp_call(0xceed9c,300)==0
            assert word(job)==3 and word(job+8)==5 and word(symbols['callbacks'])==word(symbols['x70_cardio_active'])==word(0x9c3594)==0
            assert len(contract_trace)==stable_before
            generation=word(symbols['x70_cardio_generation'])
            assert execute_smp_call(symbols['x70_cardio_read'],job,folder,name,buffer,2048)==0
            for attempt in range(8):
                if word(job)!=1:break
                assert execute_smp_call(0xceed9c,300)==0
            assert word(job)==2 and word(job+8)==0
            assert word(symbols['x70_cardio_generation'])==generation+1
            assert word(symbols['callbacks'])==word(symbols['x70_cardio_active'])==word(0x9c3594)==0
            assert [word(symbols['bank_state']+n*4) for n in range(4)]==[0]*4
            content=bytes(cpu.mem_read(buffer,word(job+20))).decode()
            assert json.loads(content)['stock_choices']['current']['values']==[dict(setting='film_simulation',value='eterna')]
            contract_result['retirement_stable_after_polls']=3
            contract_result['explicit_caller_retry']=dict(state=word(job),status=word(job+8),generation_before=generation,generation_after=word(symbols['x70_cardio_generation']),bytes=word(job+20),actual_open_count=word(0x9c3594),callbacks=word(symbols['callbacks']),active=word(symbols['x70_cardio_active']))
        stages.append(dict(contract_result=contract_result))
'''
 source=source[:start]+tail+source[end:]
 replace('report = dict(scope=__doc__, native_frame_chain=frames,sector_evidence=sector_evidence,','report = dict(scope=__doc__, contract_trace=contract_trace,contract_result=contract_result,native_frame_chain=frames,sector_evidence=sector_evidence,')
 source=source.replace('def main():','def execute():',1)
 ns=dict(vars(original),OUT=a.output,CONTRACT_BUILD=a.build,CONTRACT_ELF=digest,FAULT_INPUT=a.refuse_transfer,RECORDED_ISSUE=a.recorded_issue,TRANSIENT_FAULT=a.transient_refusal)
 exec(compile(source,str(Path(original.__file__))+'::native-task-contract','exec'),ns)
 try:ns['execute']()
 finally:
  path=a.output/'probe.json'
  if path.exists():
   report=json.loads(path.read_text());report.update(adapter_scope=__doc__,elf_sha256=digest,checker_sha256=sha(Path(__file__).read_bytes()),original_checker_sha256=sha(Path(original.__file__).read_bytes()),adapted_checker_sha256=sha(source.encode()),negative_media_status_input=a.refuse_transfer,recorded_issue_expected=a.recorded_issue,transient_refusal=a.transient_refusal)
   path.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
