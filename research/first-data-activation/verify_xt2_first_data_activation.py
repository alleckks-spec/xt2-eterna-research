"""Bounded compiled first data publication; modeled explicit operation transport.
No installed camera hooks, native task/IRQ adapter, reload, pixels or full boot.
"""
import json,struct,hashlib,sys,tempfile,shutil,traceback
from pathlib import Path
from datetime import datetime,timezone
import verify_xt2_normal_reader_pipeline as pipeline
from verify_xt2_loaded_profile_consumption import variants
from firmware_analysis import Firmware
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_INVALID,UC_HOOK_MEM_READ
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_C1_C0_2,UC_ARM_REG_FPEXC
from verify_profile_selectors import RAM,RETURN
from verify_interpolated_profile_outputs import call as native_call,runtime
import verify_native_parameter_builder as aggregate_helper
from verify_native_parameter_builder import build as aggregate
from verify_custom_profile_interpolation import setup
def bounded_native_call(u,entry,*args):
 u.reg_write(UC_ARM_REG_LR,RETURN)
 for reg,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):u.reg_write(reg,value)
 u.emu_start(entry,RETURN,count=2000000)
 assert u.reg_read(UC_ARM_REG_PC)==RETURN,(hex(entry),hex(u.reg_read(UC_ARM_REG_PC)))
# Original aggregate helper's200k instruction budget is exceeded by compiled
# linear149-key dispatch; arithmetic/control remain original firmware.
aggregate_helper.call=bounded_native_call
native_call=bounded_native_call
ROOT=pipeline.ROOT
EXTRA=['xt2_profile_first_bank.c','xt2_first_dispatch_fixture.c','xt2_first_dispatch_fixture.S']
def sha(b):return hashlib.sha256(b).hexdigest()
def pins():
 # Complete local source inventory covers imported dynamic helpers and headers;
 # source bytes archived, firmware pinned without copying vendor images.
 files=list((ROOT/'scripts').glob('*.py'))+list((ROOT/'scripts').glob('*.c'))+list((ROOT/'scripts').glob('*.h'))+list((ROOT/'scripts').glob('*.S'))+list((ROOT/'firmware/research/profile-materializer-unverified').glob('*'))
 files += [p for p in (ROOT/'firmware/extracted/xt2-4.41').rglob('*') if p.is_file()]
 files += [ROOT/'firmware/research/xt2-stock-sd-unverified/ffboot.bin']
 files += [ROOT/'research/color-parameter-port-execution.json',ROOT/'research/selection-parameter-port-execution.json',ROOT/'research/first-data-activation-20261108T111701Z/verified-report.json',ROOT/'.toolchains/unicorn-tci/libunicorn.2.dylib']
 files += [p for p in (ROOT/'firmware/extracted/xh1-2.15').rglob('*') if p.is_file()]
 return {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(set(files)) if p.is_file() and 'sony' not in p.name.lower()}
def runtime_dependencies():
 import unicorn,capstone,elftools
 paths=[Path(sys.executable).resolve(),Path('/usr/bin/clang')]
 for module in (unicorn,capstone,elftools):
  paths += [p for p in Path(module.__file__).parent.rglob('*') if p.is_file() and p.suffix in ('.py','.so','.dylib')]
 paths += list((ROOT/'.toolchains/rustup/toolchains').glob('*/lib/rustlib/*/bin/gcc-ld/ld.lld'))
 return {str(p.resolve()):sha(p.read_bytes()) for p in sorted(set(paths))}
def main():
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');evidence=ROOT/'research'/('first-data-activation-'+stamp);evidence.mkdir()
 pre=pins();deps=runtime_dependencies();(evidence/'pre-runtime-dependencies.json').write_text(json.dumps(deps,indent=2)+'\n')
 (evidence/'pre-input-hashes.json').write_text(json.dumps(pre,indent=2)+'\n')
 for name in pre:
  if name.startswith('scripts/') or name.endswith('.h'):
   q=evidence/'snapshot'/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,q)
 try:
  name,profile,blob,changes=variants()[0]
  (evidence/'profile-input.json').write_text(json.dumps(dict(name=name,container_sha256=sha(blob),profile_sha256=profile.digest(),changes=changes),indent=2)+'\n')
  manifest=(ROOT/'firmware/research/profile-materializer-unverified/runtime-template.reloc').read_bytes()
  pipeline.SOURCES=pipeline.SOURCES+EXTRA
  with tempfile.TemporaryDirectory(prefix='xt2-first-data-') as temp:
   sections,syms,compiled=pipeline.build(Path(temp))
   session={};op0=0x0f000100;op1=0x0f000110;request=0x0f000000
   def api(u,name,*args):
    for reg,v in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):u.reg_write(reg,v)
    u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.reg_write(UC_ARM_REG_LR,RETURN)
    u.emu_start(syms[name],RETURN,count=2000000)
    assert u.reg_read(UC_ARM_REG_PC)==RETURN,(name,hex(u.reg_read(UC_ARM_REG_PC)))
    return u.reg_read(UC_ARM_REG_R0)
   def install(u):
    stock=(ROOT/'firmware/extracted/xt2-4.41/inverted.bin').read_bytes()[0xc025c:0x10025c]
    u.mem_map(0x09000000,0x40000);u.mem_write(0x09000000,stock)
    u.mem_map(0x1025000,4096);u.mem_write(0x1025344,struct.pack('<I',0x09000000))
    u.reg_write(UC_ARM_REG_C1_C0_2,0xf<<20);u.reg_write(UC_ARM_REG_FPEXC,1<<30)
    def badmem(uc,access,address,size,value,data):
     print('INVALID_MEMORY',hex(uc.reg_read(UC_ARM_REG_PC)),hex(address),size,hex(uc.reg_read(UC_ARM_REG_SP)),flush=True);return False
    u.hook_add(UC_HOOK_MEM_INVALID,badmem)
    session.update(installed=True,reader_started=False,redirects={},armed=False,publication_events=[],writes=[],native_entries=[],bank_reads=0)
    for entry in (0x156a140,0x156fad8,0x15703f8):
     u.hook_add(UC_HOOK_CODE,lambda uc,pc,size,data:session['native_entries'].append(hex(pc)),begin=entry,end=entry)
    for entry,target in [(0x157a5d8,'xf_selector'),(0xce323c,'xf_parameter'),(0xc4d298,'xf_tone'),(0xc4d4f4,'xf_gain')]:
     def redirect(uc,pc,size,data,target=target):
      session['redirects'][target]=session['redirects'].get(target,0)+1
      uc.reg_write(UC_ARM_REG_PC,syms[target])
     u.hook_add(UC_HOOK_CODE,redirect,begin=entry,end=entry)
    def publish_high(uc,pc,size,data):
     if session['armed']:
      session['armed']=False;session['publication_events'].append(dict(site=hex(pc),high_key=hex(uc.reg_read(UC_ARM_REG_R0)),native_entries_before=list(session['native_entries'])))
      uc.reg_write(UC_ARM_REG_LR,0xce3610);uc.reg_write(UC_ARM_REG_PC,syms['xf_publish_parameter'])
    u.hook_add(UC_HOOK_CODE,publish_high,begin=0xce360c,end=0xce360c)
    def started(uc,pc,size,data):session['reader_started']=True
    u.hook_add(UC_HOOK_CODE,started,begin=syms['xt2_reader_start'],end=syms['xt2_reader_start'])
    api(u,'xt2_first_begin',op0);assert bytes(u.mem_read(op0,8))==bytes(8)
    api(u,'xf_transport',op0)
   def consume(u,payload,hooks,base):
    assert session['installed'] and session['reader_started']
    oldwords=bytes(u.mem_read(hooks,348));hookpins={a:bytes(u.mem_read(a,4)) for a,old,new in struct.iter_unpack('<3I',oldwords)}
    written=[]
    def watchwrite(uc,access,address,size,value,data):
     if any(address<a+4 and a<address+size for a in hookpins):written.append(dict(address=hex(address),size=size))
    u.hook_add(UC_HOOK_MEM_WRITE,watchwrite)
    def bankread(uc,access,address,size,value,data):session['bank_reads']+=1
    u.hook_add(UC_HOOK_MEM_READ,bankread,begin=syms['bank'],end=syms['bank']+2943)
    codepins={a:bytes(u.mem_read(a,8)) for a in [0x157a5d8,0xce323c,0xc4d298,0xc4d4f4]}
    # Rejected malformed candidate leaves bank EMPTY and live data unchanged.
    saved=bytes(u.mem_read(payload+0x1e58,1));u.mem_write(payload+0x1e58,b'\xff')
    assert api(u,'xt2_first_extract',request,1)==4 and api(u,'xt2_first_state')==0
    u.mem_write(payload+0x1e58,saved)
    assert api(u,'xt2_first_extract',request,2)==2 and api(u,'xt2_first_state')==0
    assert api(u,'xt2_first_extract',request,1)==0 and api(u,'xt2_first_state')==2
    assert api(u,'xt2_first_extract',request,1)==1
    # NULL operation selected before publish. All wrappers original native code.
    native_call(u,0x157a0fc,RAM);native_call(u,0x157ac60,RAM,18)
    assert bytes(u.mem_read(RAM+0x52,1))==b'\0'
    for offset,value in {6:1,7:1,0x1d:1,0x51:1,0x4f:4,0x50:4,0x66:4}.items():u.mem_write(RAM+offset,bytes([value]))
    u.mem_write(RAM+0x40,struct.pack('<H',6))
    dst=RAM+0x8000
    def incremental(machine,arm=False):
     machine.mem_write(dst,bytes(0x200));machine.mem_write(dst+3,b'\1\1\1')
     native_call(machine,0x1579ac8,RAM,dst)
     if arm:session['armed']=True
     native_call(machine,0x1579b04,RAM,dst)
     native_call(machine,0x1579b30,RAM,dst)
     return bytes(machine.mem_read(dst,0x200))
    # The matrix high-byte read publishes A after gain and before tone. NULL
    # snapshot remains stock for both compound coefficient and whole trio.
    reference_stock=runtime('xt2-4.41',False)
    native_call(reference_stock,0x157a0fc,RAM);native_call(reference_stock,0x157ac60,RAM,0)
    for offset,value in {6:1,7:1,0x1d:1,0x51:1,0x4f:4,0x50:4,0x66:4}.items():reference_stock.mem_write(RAM+offset,bytes([value]))
    reference_stock.mem_write(RAM+0x40,struct.pack('<H',6))
    expected_pre=incremental(reference_stock)
    actual_pre=incremental(u,True)
    assert session['publication_events'] and not session['armed']
    assert api(u,'xt2_first_state')==4 and actual_pre==expected_pre
    native_call(u,0x157ac60,RAM,18);assert bytes(u.mem_read(RAM+0x52,1))==b'\0'
    active_hash=sha(bytes(u.mem_read(syms['bank'],2944)))
    assert api(u,'xt2_first_publish')==1 and api(u,'xt2_first_extract',request,1)==1
    assert active_hash==sha(bytes(u.mem_read(syms['bank'],2944)))
    u.mem_write(op1,struct.pack('<2I',0x12345678,1));assert api(u,'xt2_first_admit',op1,18)==0
    api(u,'xt2_first_begin',op1);api(u,'xf_transport',op1)
    reference=setup(profile,False)
    rows=[]
    for slot in (18,3,0):
     actual=aggregate(u,False,slot,4);expected=aggregate(reference if slot==18 else reference_stock,False,slot,4)
     assert actual==expected,('aggregate',slot,[i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b][:30])
     rows.append(dict(kind='aggregate1565c20',slot=slot,sha256=sha(actual)))
    # Build custom context then compare original incremental wrappers separately.
    aggregate(u,False,18,4);aggregate(reference,False,18,4)
    a=incremental(u);b=incremental(reference);assert a==b
    aggregate(reference_stock,False,0,4);stock_incremental=incremental(reference_stock)
    assert a!=stock_incremental,'Custom incremental output must differ from enabled stock context'
    from verify_interpolated_profile_outputs import outputs
    custom_outputs=outputs(u,False,18,0,3,4);stock_outputs=outputs(reference_stock,False,0,0,3,4)
    assert custom_outputs['tone']!=stock_outputs['tone'] and custom_outputs['gain']!=stock_outputs['gain']
    rows.append(dict(kind='incremental1579ac8_1579b04_1579b30',slot=18,sha256=sha(a)))
    for mode in ('stock','unscoped','ended'):
     if mode=='stock':api(u,'xt2_first_admit',op1,3)
     elif mode=='unscoped':api(u,'xf_transport',0)
     else:api(u,'xt2_first_end',op1);api(u,'xf_transport',op1)
     for key in (0x9bbc,0x9f40,0x1234):
      native_call(u,0xce323c,key);value=u.reg_read(UC_ARM_REG_R0)
      assert value==bytes(reference_stock.mem_read(0x09000000+key,1))[0],(mode,key,value)
    assert session['bank_reads']>0
    assert not written and all(bytes(u.mem_read(a,4))==b for a,b in hookpins.items())
    assert bytes(u.mem_read(hooks,348))==oldwords
    assert all(bytes(u.mem_read(a,8))==v for a,v in codepins.items())
    return dict(passed=True,rows=rows,null_snapshot_preserved_across_publish=True,compound_and_gain_tone_interleaving=session['publication_events'],replacement_rejected=True,malformed_candidate_rejected=True,unknown_stock_unscoped_ended_fallback=True,bank_sha256=active_hash,permanent_dispatch_installed_before_reader=True,late_native_hookword_writes=0,redirect_counts=session['redirects'],bank_read_count=session['bank_reads'],native_entries=session['native_entries'],all29_hookwords_unchanged=True,memory_requirement='Static2944-byte immutable bank plus state/request/transport and operation storage in separate harness BSS; frozen resident has only84 bytes spare, so this is NOT resident-compatible. Requires separately owned persistent allocation/layout integration.',task_irq_adapter='Explicit modeled transport only; no production task/exception adapter',full170cda0_executed=False)
   case=pipeline.assay(Firmware('xt2-4.41',True),sections,syms,blob,manifest,pre_reader_observer=install,prepared_observer=consume)
   def revoked(u,payload,hooks,base):
    original_hooks=bytes(u.mem_read(hooks,348))
    assert api(u,'xt2_first_extract',request,1)==0 and api(u,'xt2_first_state')==2
    # Existing pipeline explicitly invalidates eligibility on every prepare
    # attempt, including ALREADY_USED; no reader/owner internals are modified.
    assert api(u,'xt2_profile_prepare',request)==107
    assert api(u,'xt2_profile_candidate_eligible',request,1)==0
    assert api(u,'xt2_first_publish')==2 and api(u,'xt2_first_state')==5
    api(u,'xt2_first_begin',op1);assert bytes(u.mem_read(op1,8))==bytes(8)
    assert api(u,'xt2_first_admit',op1,18)==0
    api(u,'xf_transport',op1)
    native_call(u,0x157a0fc,RAM);native_call(u,0x157ac60,RAM,18)
    assert bytes(u.mem_read(RAM+0x52,1))==b'\0'
    stock=runtime('xt2-4.41',False)
    for key in (0x9bbc,0x9f40,0x1234):
     native_call(u,0xce323c,key);assert u.reg_read(UC_ARM_REG_R0)==bytes(stock.mem_read(0x09000000+key,1))[0]
    assert api(u,'xt2_first_publish')==1 and api(u,'xt2_first_extract',request,1)==1
    assert bytes(u.mem_read(hooks,348))==original_hooks
    return dict(passed=True,extracted_state=2,revocation='existing pipeline prepare ALREADY_USED resets eligibility',publish_result=2,terminal_state=5,ready_remains_null=True,selector_denied=True,stock_parameters_preserved=True,retry_denied=True)
   revoked_case=pipeline.assay(Firmware('xt2-4.41',True),sections,syms,blob,manifest,pre_reader_observer=install,prepared_observer=revoked)
  baseline_path=ROOT/'research/first-data-activation-20261108T111701Z/verified-report.json'
  baseline=json.loads(baseline_path.read_text())
  previous=baseline['case']['prepared_consumption'];current=case['prepared_consumption']
  assert current['rows']==previous['rows'] and current['bank_sha256']==previous['bank_sha256']
  assert current['bank_read_count']<previous['bank_read_count']
  current['lookup_optimization']=dict(algorithm='binary search of validated sorted149 keys; at most8 probes',baseline_report_sha256=sha(baseline_path.read_bytes()),baseline_bank_reads=previous['bank_read_count'],current_bank_reads=current['bank_read_count'],identical_native_outputs=True)
  postdeps=runtime_dependencies();assert deps==postdeps
  (evidence/'post-runtime-dependencies.json').write_text(json.dumps(postdeps,indent=2)+'\n')
  post=pins();(evidence/'post-input-hashes.json').write_text(json.dumps(post,indent=2)+'\n');assert pre==post
  report=dict(scope=__doc__,passed=True,evidence_directory=str(evidence.relative_to(ROOT)),compiled=compiled,case=case,revoked_eligibility_case=revoked_case,input_hashes_pre_run=pre,inputs_unchanged_post_run=True,runtime_dependencies_unchanged_pre_post=True,physical_camera=False,mounted_media=False,live_reload=False,owner_tail_changed=False,limitations=['Native storage lower layers and owner release remain existing explicit fixture models.','Publication is compiled C release/acquire; real data-cache coherency not proven.','Original aggregate and incremental wrappers run, with modeled outer operation and explicit operation-pointer transport; full170cda0/task/IRQ integration is not executed.','Representation validation is not numeric/hardware safety. No pixels/full boot/camera or live reload proof.'])
  out=ROOT/'research/first-data-activation-verification.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(out),evidence=str(evidence))))
 except BaseException:
  error=sys.exc_info()[1]
  (evidence/'failure.txt').write_text(traceback.format_exc()+'\n'+repr(getattr(error,'stdout',None))+'\n'+repr(getattr(error,'stderr',None)));raise
if __name__=='__main__':main()
