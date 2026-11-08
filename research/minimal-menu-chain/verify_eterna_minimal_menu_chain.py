"""Bounded actual-menu selection, RAM readback and processing/development assays.

The delivered SEPIA-alias image is loaded unchanged. Original input routing,
conversion, RAM setting access and refresh execute with declared RTOS sync
fixtures. Processing caller/development capture handoffs are explicit laboratory
fixtures, not claims of a continuous live capture producer or physical pipeline.
"""
import argparse,gc,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
 UC_ARM_REG_R4,UC_ARM_REG_R7,UC_ARM_REG_FP,UC_ARM_REG_SP,UC_ARM_REG_PC)
from build_eterna_payload import ROOT,STOCK
from build_eterna_minimal_sd import OUTPUT,CODE,DATA
from verify_film_visibility import execute as menu_fixture
from verify_film_confirmation_route import route
from verify_film_menu_navigation import invoke
from verify_film_routed_commit import PARAMETERS
from verify_interpolated_profile_outputs import runtime,outputs as reference_outputs,call
from verify_native_parameter_builder import build as reference_aggregate
from verify_development_selector_extension import execute as development
from verify_profile_selectors import RAM

IMAGE=OUTPUT/'ffboot.bin'
EXPECTED_HASH='0f14244971768d783e09d4eb21fe59e60262ea183b938d31ff1fff170caceddf'
DESCRIPTORS=(0xeea334,0xedaaac,0xebcdfc)
PARAM=0x02c68000
CALIB_KEYS=(0xb5,0xf740,0xf741,0xf742,0xf02b,0xf02c)


def digest(data):return hashlib.sha256(data).hexdigest()
def word(data,a):return struct.unpack_from('<I',data,a)[0]


def menu_rows(image,descriptor):
 items=word(image,descriptor+16);rows=[]
 for index in range(64):
  row,child=struct.unpack_from('<II',image,items+index*8)
  if row==0x7ffffffe:return items,rows
  rows.append(dict(index=index,row=row,child=child,address=items+index*8))
 raise ValueError('Native menu terminator absent')


def registers(u):return [u.reg_read(r)for r in(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]


def routed(image,descriptor,index,after=None):
 original_items,original_rows=menu_rows(image,descriptor)
 trace=[];conversion_reads=[];sync=[]
 def work(u):
  # The visibility helper copied these rows byte-for-byte into scratch RAM.
  # Restore the ACTUAL image table pointer before original input/dispatch.
  assert bytes(u.mem_read(0x08001000,(len(original_rows)+1)*8))==image[original_items:original_items+(len(original_rows)+1)*8]
  u.mem_write(descriptor+16,struct.pack('<I',original_items))
  u.mem_protect(CODE&~4095,4096,5);u.mem_protect(DATA,0x4000,1)
  u.mem_map(PARAM,0x200000);u.mem_write(PARAM,PARAMETERS);u.mem_write(0x1025344,struct.pack('<I',PARAM))
  u.mem_write(0x121d626,b'\x03')  # Optional logging path, not a calibration-ready flag.
  def event(uc,pc,size,data):trace.append(dict(pc=pc,args=registers(uc)))
  def conversion(uc,access,address,size,value,data):
   if len(conversion_reads)<100:conversion_reads.append(dict(pc=uc.reg_read(UC_ARM_REG_PC),address=address,size=size,bytes=bytes(uc.mem_read(address,size)).hex()))
  hooks=[u.hook_add(UC_HOOK_CODE,event,begin=pc,end=pc)for pc in (0x154b700,0xbf5e44,0xb51098,0xb510b8,0xbff2c8,0xc23ab8,0xc21cdc,0x1543344)]
  hooks.append(u.hook_add(UC_HOOK_MEM_READ,conversion,begin=0xe8bbb4,end=0xe8bbb4+21*16-1))
  def synchronize(uc,pc,size,data):
   from unicorn.arm_const import UC_ARM_REG_LR
   sync.append(pc);uc.reg_write(UC_ARM_REG_R0,0);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  hooks += [u.hook_add(UC_HOOK_CODE,synchronize,begin=pc,end=pc)for pc in (0xcf8b48,0xcf8b74)]
  try:
   routing=route(u,index)
   u.emu_start(0x154b700,0x141cd64,count=3000000)
   assert u.reg_read(UC_ARM_REG_PC)==0x141cd64
   readback=[invoke(u,0xb510b8,setting,0)for setting in (0x1fc,0x1fd,0x1fe)]
  finally:
   for h in hooks:u.hook_del(h)
  assert routing['row']==original_rows[index]['row']
  assert any(e['pc']==0xbf5e44 for e in trace)and any(e['pc']==0xb51098 for e in trace)
  assert all(any(e['pc']==pc for e in trace)for pc in (0xc23ab8,0xc21cdc))
  assert bytes(u.mem_read(PARAM,len(PARAMETERS)))==PARAMETERS
  live=bytes(u.mem_read(0x119f2cb,1))[0]
  result=dict(status='PASS',descriptor=descriptor,original_items=original_items,index=index,actual_menu=original_rows[index],
     native_route=routing,readback=readback,live=live,RAM_settings=list(u.mem_read(0x119299b,3)),trace=trace,
     conversion_reads=conversion_reads,modeled_sync=sync,refresh_stop=0x141cd64,
     fixture=dict(mode=36,selected_initial=0,global_pointers={'0x10c62b0':'0x120d8a0','0x119162c':'0x119f25c'},
                  optional_setter_diagnostics_disabled_at='0x121d626',actual_item_table_restored=True))
  if after:result['downstream']=after(u,readback[0])
  return result
 result=menu_fixture(image,b'',{},36,0,False,descriptor,True,0,work)
 gc.collect()
 return result


def capture_context(u,public):
 # Caller registers/context and capture+40 are declared test inputs. The original
 # native getter result supplies the byte; ETERNA/public18 is never injected.
 u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.mem_write(RAM,bytes(0x200));call(u,0x157a0fc,RAM)
 capture=RAM+0x7000;u.mem_write(capture+0x40,bytes([public]));u.mem_write(RAM+0xc000-0x35,b'\xa5')
 entries=[]
 def trace(uc,pc,size,data):entries.append(dict(pc=pc,args=registers(uc)))
 hooks=[u.hook_add(UC_HOOK_CODE,trace,begin=pc,end=pc)for pc in (0x1723b74,0x157ac60,0x157a5d8,CODE)]
 for reg,value in ((UC_ARM_REG_R4,capture),(UC_ARM_REG_R7,RAM),(UC_ARM_REG_FP,RAM+0xc000),(UC_ARM_REG_SP,RAM+0xe000)):u.reg_write(reg,value)
 try:u.emu_start(0x170c870,0x170c888,count=10000)
 finally:
  for h in hooks:u.hook_del(h)
 assert u.reg_read(UC_ARM_REG_PC)==0x170c888
 assert len([e for e in entries if e['pc']==0x157ac60])==1
 assert bytes(u.mem_read(RAM+0xc000-0x35,1))[0]==public
 return dict(status='PASS',input_from_native_getter=public,capture_fixture_address=capture+0x40,
             original_caller_block=[0x170c870,0x170c888],identity_adapter=0x1723b74,
             processing_context=RAM,processing_id=bytes(u.mem_read(RAM+0x52,1))[0],trace=entries,
             live_to_capture_bridge='UNVERIFIED: test fixture copies getter byte into capture+40; live native producer is not executed here')


def configure_context(u,mode,channel,adjustment):
 values={0x51:1,0x4f:adjustment,0x50:adjustment,0x66:adjustment,0x44:0,0x67:0,0xf7:0,0x8c:0,0x70:0}
 values.update([{}, {0x67:1}, {0x44:2}, {0x44:2,0x67:3}, {0x44:1,0x67:3}][mode])
 values.update({0xf7:1,0x8c:channel+2}if channel<3 else {0x70:channel-3})
 for off,value in values.items():u.mem_write(RAM+off,bytes([value]))
 return values


def body(u,public,mode=0,channel=0,adjustment=4,aggregate=False):
 bridge=capture_context(u,public);processing_id=bridge['processing_id'];inputs=configure_context(u,mode,channel,adjustment)
 branches=[];parameters=[];selected_records=[]
 watched=(0x1570438,0x1570470,0x1570498,0x156a17c,0x156a1a8,0x156a1c4)
 def trace(uc,pc,size,data):
  if pc in watched:branches.append(pc)
  elif pc==0xce35e4:parameters.append(uc.reg_read(UC_ARM_REG_R0))
  else:selected_records.append(dict(pc=pc,args=registers(uc)))
 hooks=[u.hook_add(UC_HOOK_CODE,trace,begin=pc,end=pc)for pc in (*watched,0xce35e4,0xc4d470,0xc4d4f4)]
 try:
  u.mem_write(RAM+0x2000,b'\xcc'*0x100);call(u,0x15703f8,RAM,RAM+0x2000,RAM+0x2040,RAM+0x2042)
  tone=bytes(u.mem_read(RAM+0x2000,56));bounds=bytes(u.mem_read(RAM+0x2040,4))
  call(u,0x156a140,RAM,1,RAM+0x2080);gain=bytes(u.mem_read(RAM+0x2080,44))
  assert bytes(u.mem_read(RAM+0x2038,8))==b'\xcc'*8 and bytes(u.mem_read(RAM+0x20ac,4))==b'\xcc'*4
  result=dict(tone=tone.hex(),bounds=bounds.hex(),gain=gain.hex())
  if aggregate:
   for off in (6,7,0x1d):u.mem_write(RAM+off,b'\x01')
   u.mem_write(RAM+0x40,struct.pack('<H',6));u.mem_write(RAM+0x9000,b'\xcc'*0x1684)
   call(u,0x1565c20,RAM+0x9000,RAM)
   assert bytes(u.mem_read(RAM+0x9000+0x1674,16))==b'\xcc'*16
   result['aggregate_sha256']=digest(bytes(u.mem_read(RAM+0x9000,0x1674)))
 finally:
  for h in hooks:u.hook_del(h)
 assert bytes(u.mem_read(RAM+0x52,1))[0]==processing_id
 return dict(bridge=bridge,context_fields=inputs,context_selector_not_reinitialized_after_bridge=True,
             calibration_input={hex(k):bytes(u.mem_read(PARAM+k,1))[0]for k in CALIB_KEYS},
             branch_PCs=branches,parameter_keys=parameters,selected_records=selected_records,
             tone_record_ids=[r['args'][0]for r in selected_records if r['pc']==0xc4d470],
             gain_record_ids=[r['args'][0]for r in selected_records if r['pc']==0xc4d4f4],outputs=result)


def main(smoke=False):
 image=IMAGE.read_bytes();stock=STOCK.read_bytes();assert digest(image)==EXPECTED_HASH
 donor=runtime('xh1-2.15',False)
 static=[dict(descriptor=d,items=menu_rows(image,d)[0],rows=menu_rows(image,d)[1])for d in DESCRIPTORS]
 candidate_rows=[];stock_rows=[];calibration=[];negative=[];mode_cases=[]
 flat=0xedaaac
 candidates=menu_rows(image,flat)[1]
 if smoke:candidates=[r for r in candidates if r['row']==5]
 # Menu→conversion→RAM write/readback executes for every actual flat row.
 for row in candidates:
  reference_holder={}
  baseline=routed(stock,flat,row['index'],lambda u,p:reference_holder.update(default=body(u,p,aggregate=True),development=development(u,p)))
  def downstream(u,public):
   record=body(u,public,aggregate=True)
   if row['row']==5:
    expected=reference_outputs(donor,True,18,0,0,4)
    assert {k:record['outputs'][k]for k in expected}==expected
    donor.reg_write(UC_ARM_REG_SP,RAM+0xe000)
    assert record['outputs']['aggregate_sha256']==digest(reference_aggregate(donor,True,18,4))
    assert record['bridge']['processing_id']==9
   else:assert record['outputs']==reference_holder['default']['outputs']
   dev=development(u,public);old_dev=reference_holder['development']
   if row['row']==5:assert dev['success']and int.from_bytes(dev['output'][0x21d:0x221],'little')==16
   else:assert dev==old_dev
   result=dict(default_body=record,stock_processing_id=reference_holder['default']['bridge']['processing_id'],
     development=dict(status='PASS',input_from_native_getter=public,
        native_selector=0x16e109c,success=dev['success'],development_id=int.from_bytes(dev['output'][0x21d:0x221],'little'),
        native_baseline_development_id=int.from_bytes(old_dev['output'][0x21d:0x221],'little'),
        handoff='UNVERIFIED: getter byte is copied into development capture+464 by declared fixture'))
   if row['row']==5 and not smoke:
    grid=[]
    for mode in range(5):
     for channel in range(6):
      for adjustment in (0,4,8):
       r=body(u,public,mode,channel,adjustment);expected=reference_outputs(donor,True,18,mode,channel,adjustment)
       assert r['outputs']==expected,(mode,channel,adjustment)
       grid.append(dict(mode=mode,channel=channel,adjustment=adjustment,output_sha256=digest(json.dumps(r['outputs'],sort_keys=True).encode()),
          processing_id=r['bridge']['processing_id'],tone_record_ids=r['tone_record_ids'],gain_record_ids=r['gain_record_ids'],
          branch_PCs=r['branch_PCs'],global_parameter_inputs=r['calibration_input'],profile_mode_context_fields=r['context_fields'],
          parameter_keys=sorted(set(r['parameter_keys'])),matches_donor_same_fixture=True))
    result['alias_grid']=grid
   if row['row']==5:
    for name,b5,f740,expected_tone,expected_gain in [('official_defaults',0,0,0x1570498,0x156a1c4),('first_forced',1,0,0x1570438,0x156a17c),('second_forced',0,1,0x1570470,0x156a1a8),('both_first_priority',1,1,0x1570438,0x156a17c),('nonboolean_falls_through',2,2,0x1570498,0x156a1c4)]:
     u.mem_write(PARAM+0xb5,bytes([b5]));u.mem_write(PARAM+0xf740,bytes([f740]));r=body(u,public)
     assert expected_tone in r['branch_PCs']and expected_gain in r['branch_PCs']
     if b5==1:
      assert r['tone_record_ids']==[PARAMETERS[0xf741]]and r['gain_record_ids']==[PARAMETERS[0xf02b]]
     elif f740==1:
      assert r['tone_record_ids']==[PARAMETERS[0xf742]]and r['gain_record_ids']==[PARAMETERS[0xf02c]]
     else:
      assert r['outputs']==reference_outputs(donor,True,18,0,0,4)
     calibration.append(dict(name=name,status='PASS',proof_scope='Native forced-branch/key/record selection only; donor-equivalence asserted only on the normal branch',
          provenance='Official DAT default parameter body; only B5/F740 explicitly varied for branch assay, not camera readiness',**r))
    u.mem_write(PARAM+0xb5,bytes([PARAMETERS[0xb5]]));u.mem_write(PARAM+0xf740,bytes([PARAMETERS[0xf740]]))
    assert bytes(u.mem_read(PARAM,len(PARAMETERS)))==PARAMETERS
   return result
  candidate=routed(image,flat,row['index'],downstream)
  assert candidate['readback']==baseline['readback']and candidate['live']==baseline['live']
  candidate_rows.append(candidate);stock_rows.append({k:v for k,v in baseline.items()if k!='downstream'})
  print('native menu row',row['row'],'public',candidate['readback'][0],'PASS',flush=True)
 # Both actually relabelled menus take their native ID5 entry; flat caption gap
 # remains visible and is never patched in this verifier.
 for descriptor in (0xeea334,0xebcdfc):
  r=next(r for r in menu_rows(image,descriptor)[1]if r['row']==5)
  candidate_rows.append(routed(image,descriptor,r['index']))
 # Alternative menu mode obeys the original visibility policy. No hidden row
 # is force-confirmed and the outer parent-menu callback is not fabricated.
 for descriptor in DESCRIPTORS:
  for mode in (32,36):
   result=menu_fixture(image,b'',{},mode,5,False,descriptor)
   baseline=menu_fixture(stock,b'',{},mode,5,False,descriptor)
   status=next(status for row,status in result if row==5)
   assert result==baseline and status==(3 if mode==32 else 0)
   mode_cases.append(dict(descriptor=descriptor,menu_mode=mode,actual_row=5,native_visibility_status=status,
       status='PASS',confirmation_attempted_in_this_visibility_assay=False,has_separate_routed_confirmation=mode==36,
       confirmation_scope='Separate MODE36 routed cases above'if mode==36 else'Hidden row: no forced confirmation',
       outer_parent_route='UNVERIFIED: bounded visibility collection stops before outer parent/menu callback'))
   gc.collect()
 # Every byte input outside the alias retains stock processing/development
 # fallback semantics; invalid inputs are not presumed to reject.
 def negative_body(u):
  for public in range(256):
   u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.mem_write(RAM,bytes(0x100));call(u,0x157ac60,RAM,public)
   context=bytes(u.mem_read(RAM,0x100));dev=development(u,public)
   negative.append(dict(public=public,processing_id=context[0x52],context_sha256=digest(context),
      development_success=dev['success'],development_id=int.from_bytes(dev['output'][0x21d:0x221],'little'),
      development_output_sha256=digest(dev['output']),development_registers_sha256=digest(struct.pack('<15I',*dev['registers'])),flags=dev['flags']))
  return None
 routed(stock,flat,0,lambda u,p:negative_body(u));old_negative=list(negative);negative.clear()
 routed(image,flat,0,lambda u,p:negative_body(u))
 for old,new in zip(old_negative,negative):
  if new['public']!=5:assert old==new,new['public']
 # Report every transition separately; no disconnected fixture is greenwashed.
 report=dict(scope=__doc__,image=str(IMAGE),image_sha256=digest(image),stock_sha256=digest(stock),image_modified=False,
   overall='PASS within bounded native stages; live capture/development producer and physical persistence/output bridges remain UNVERIFIED',
   counts=dict(candidate_routed_menus=len(candidate_rows),preserved_other_flat_profiles=0 if smoke else 14,
       alias_processing_grid=0 if smoke else 90,menu_mode_visibility=len(mode_cases),calibration_branches=len(calibration),
       selector_byte_inputs=256,unchanged_nonalias_selectors=255),
   smoke=smoke,actual_menus=static,conversion_row5=list(struct.unpack_from('<4I',image,0xe8bbb4+5*16)),
   transitions=[dict(name='actual menu/input packet→original conversion/dispatch→RAM setter/getter/live',status='PASS',cases=len(candidate_rows)),
    dict(name='live/getter RAM value→real capture-object producer+40',status='UNVERIFIED',reason='Declared getter-byte handoff fixture; original live producer is not executed'),
    dict(name='original caller170c870→identity1723b74→patched processing selector→tone/gain/aggregate',status='PASS',scope='Capture+40 is explicit fixture input from getter; no context reset after this native block'),
    dict(name='getter value→real development-capture+464 producer',status='UNVERIFIED',reason='Declared fixture handoff'),
    dict(name='actual patched development selector with nativegetter-derived input',status='PASS'),
    dict(name='durable storage/reboot and physical image output',status='UNVERIFIED')],
   candidate_menu_cases=candidate_rows,baseline_menu_cases=stock_rows,menu_mode_cases=mode_cases,calibration_cases=calibration,
   namespace_notes='Raw conversion row5 columns[5,4,5,10] are not processing-context enums. Stock context and development IDs below are native-execution results.',
   negative_inputs=dict(status='PASS',scope='Direct byte-valued selector fallback boundaries; invalid menu dispatch is UNVERIFIED',
      byte_inputs=256,preserved_except_alias=255,semantics='Compared original fallback/output/register/flag behavior, not blanket rejection',
      alias_stock=old_negative[5],alias_candidate=negative[5],records=negative),
   broad_processing_baseline='research/eterna-minimal-sd-verification.json',
   fixture_provenance=dict(parameter_body='official X-T2 DAT inverted bytes[0xc025c:0x10025c], not a per-camera calibration dump',parameter_body_sha256=digest(PARAMETERS),parameter_base=PARAM,RTOS_modeled_functions=['0xcf8b48','0xcf8b74'],refresh_stop='0x141cd64',capture_handoff='host fixture from native getter result',donor_reference='X-H1 public18 supplied only to reference machine'),
   limitations=['Flat0xedaaac caption remains SEPIA; only the other two descriptors were relabelled by delivered image.',
    'Synthetic menu state/mode and input packet, not physical buttons or rendered UI.', 'No autonomous boot, SD transfer, peripheral timing or calibration readiness fabricated/proven.'],
   source_sha256={str(p.relative_to(ROOT)):digest(p.read_bytes())for p in [Path(__file__),
      *[ROOT/'scripts'/name for name in ('verify_film_visibility.py','verify_film_confirmation_route.py','verify_film_routed_commit.py',
       'verify_development_selector_extension.py','verify_interpolated_profile_outputs.py','verify_native_parameter_builder.py',
       'verify_profile_selectors.py','verify_film_menu_navigation.py','firmware_analysis.py','build_eterna_minimal_sd.py','build_eterna_payload.py')]]},
   artifact_sha256={str(p.relative_to(ROOT)):digest(p.read_bytes())for p in (OUTPUT/'manifest.json',ROOT/'research/eterna-minimal-sd-verification.json')},
   firmware_provenance={model:dict(manifest_sha256=digest((ROOT/f'firmware/extracted/{model}/manifest.json').read_bytes()),
       stream_sha256={s['file']:digest((ROOT/f'firmware/extracted/{model}'/s['file']).read_bytes())for s in json.loads((ROOT/f'firmware/extracted/{model}/manifest.json').read_text())['streams']},
       calibration_body_sha256=digest((ROOT/f'firmware/extracted/{model}/inverted.bin').read_bytes()[(0x274 if model=='xh1-2.15'else 0x25c)+0xc0000:(0x274 if model=='xh1-2.15'else 0x25c)+0x100000]))for model in ('xt2-4.41','xh1-2.15')},
   repro_command='LIBUNICORN_PATH=$PWD/.toolchains/unicorn-tci UC_IGNORE_REG_BREAK=1 .venv/bin/python scripts/verify_eterna_minimal_menu_chain.py',hardware_verified=False)
 path=ROOT/('research/eterna-minimal-menu-chain-smoke.json'if smoke else'research/eterna-minimal-menu-chain-verification.json')
 path.write_text(json.dumps(report,indent=2)+'\n');print('Report',path,flush=True)
 print(json.dumps(dict(counts=report['counts'],image_sha256=report['image_sha256'],live_capture_bridge='UNVERIFIED',hardware_verified=False)),flush=True)
 return report


if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--smoke',action='store_true');main(parser.parse_args().smoke)
