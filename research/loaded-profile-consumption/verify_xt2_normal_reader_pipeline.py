"""Isolated route→unchanged reader→native file queue→private pipeline assay.
Adapter seam forwards public native FS calls, rather than completing them as
success stubs. Mode1 is retained; normal routing capability replaces stable-mode
premise only in this explicitly separate variant. No installed firmware/camera.
"""
import hashlib,json,shutil,struct,subprocess,tempfile
from pathlib import Path
from elftools.elf.elffile import ELFFile
from firmware_analysis import Firmware
ROOT=Path(__file__).resolve().parents[1]
SOURCES=['xt2_normal_route_prototype.c','xt2_normal_route_trampolines.S','xt2_normal_route_reader_variant.c','xt2_native_profile_reader.c','xt2_profile_container.c','xt2_profile_materialize.c','xt2_profile_stage.c','xt2_profile_pipeline.c']
def sha(b):return hashlib.sha256(b).hexdigest()
def build(d):
 flags=['--target=armv7-none-eabi','-marm','-march=armv7-a','-mfpu=none','-mfloat-abi=soft','-std=c11','-O2','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror','-I',str(ROOT/'firmware/research/profile-materializer-unverified')]
 objects=[]
 for n in SOURCES:
  out=d/(n+'.o');subprocess.run(['clang',*flags,*(['-DXT2_READER_TEST']if n=='xt2_native_profile_reader.c'else[]),'-c',str(ROOT/'scripts'/n),'-o',str(out)],check=True,capture_output=True);objects.append(str(out))
 ld=shutil.which('ld.lld')or str(sorted((ROOT/'.toolchains/rustup/toolchains').glob('*/lib/rustlib/*/bin/gcc-ld/ld.lld'))[0]);script=d/'linked.ld'
 script.write_text('ENTRY(xt2_reader_start)\nSECTIONS { . = 0x01280000; .text : { *(.text*) *(.rodata*) } . = 0x012a0000; .data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) } }')
 out=d/'linked.elf';subprocess.run([ld,'-T',str(script),'--no-undefined',*objects,'-o',str(out)],check=True,capture_output=True)
 with out.open('rb')as stream:
  e=ELFFile(stream);table=e.get_section_by_name('.symtab');assert all(s['st_shndx']!='SHN_UNDEF'for s in table.iter_symbols()if s.name)
  syms={s.name:s['st_value']for s in table.iter_symbols()};sections=[(s['sh_addr'],s.data(),s.name,s['sh_size'])for s in e.iter_sections()if s['sh_flags']&2 and s['sh_size']]
 return sections,syms,dict(elf_sha256=sha(out.read_bytes()),text_bytes=sum(n for a,b,k,n in sections if k=='.text'),bss_bytes=sum(n for a,b,k,n in sections if k=='.bss'),flags=flags,undefined_symbols=0,adapter_seam='XT2_READER_TEST only for unchanged reader TU; xr_test_* functions forward actualpublicFS in separate variant')

def assay(f,sections,syms,blob,manifest,error=False,*,prepared_observer=None):
 from verify_profile_selectors import machine,RAM,RETURN
 from unicorn import UC_HOOK_CODE,UC_PROT_READ,UC_PROT_EXEC
 from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
 # Helper is authored separately: original public open, ownedqueuecopy/dispatch,
 # descriptor/alias creation and cleanup; only explicit lowerFS/block+OS models.
 from xt2_native_profile_fs_fixture import NativeProfileFSFixture
 u=machine(f);actor=[230]
 def put(a,v):u.mem_write(a,struct.pack('<I',v&0xffffffff))
 def get(a):return struct.unpack('<I',u.mem_read(a,4))[0]
 def mapped(a,n):
  if not any(b<=a and a+n-1<=e for b,e,p in u.mem_regions()):u.mem_map(a,n)
 for a,n in [(0x1280000,0x10000),(0x12a0000,0x10000),(0x7a000,0x1000),(0x1189000,0x2000),(0x9c2000,0x2000),(0xac2000,0x2000),(0x9ae000,0x1000),(0xaae000,0x1000),(0x0b000000,0x10000),(0x0c000000,0x10000),(0x0f000000,0x1000)]:mapped(a,n)
 for a,b,k,n in sections:
  if k!='.bss':u.mem_write(a,b)
 u.mem_protect(0x1280000,0x10000,UC_PROT_READ|UC_PROT_EXEC)
 def current(_u,pc,size,data):u.reg_write(UC_ARM_REG_R0,actor[0]);u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
 u.hook_add(UC_HOOK_CODE,current,begin=0x57e20,end=0x57e20)
 for module,worker in ((0,39),(1,122)):
  tcb=RAM+0x7000+module*0x200;put(0x7a548+(worker-1)*4,tcb);put(tcb+0xcc,worker);put(tcb+0xe4,0x969fcc+module*0x100000)
 owner=RAM+0x6000;put(0x7a548+229*4,owner);put(owner+0xcc,230);put(owner+0xe4,syms['xt2_reader_service'])
 for stage,site in [('open',0x965250),('read',0x9682e4),('close',0x965780)]:
  for module in (0,1):
   pc=site+module*0x100000;target=syms[f'nr_{stage}_{"B"if module else"A"}'];off=target-pc-8
   assert not off%4 and -(1<<25)<=off<(1<<25);put(pc,0xea000000|((off>>2)&0xffffff))
 u.ctl_flush_tb()
 fixture=NativeProfileFSFixture(u,blob,module=0,scratch=0x0d000000,current_task_setter=lambda n:actor.__setitem__(0,n))
 if error:
  # Concrete helper knob must model lower data error, never public callback.
  fixture.read_error=0x114
 def call(name,*args):
  actor[0]=230
  for r,v in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):u.reg_write(r,v)
  u.reg_write(UC_ARM_REG_SP,RAM+0xe000);u.reg_write(UC_ARM_REG_LR,RETURN)
  u.emu_start(syms[name]if isinstance(name,str)else name,RETURN,count=2000000)
  assert u.reg_read(UC_ARM_REG_PC)==RETURN,(name,hex(u.reg_read(UC_ARM_REG_PC)))
  return u.reg_read(UC_ARM_REG_R0)
 native=[];callbacks=[];branches=[]
 def observe(_u,pc,size,data):
  native.append(hex(pc))
  if pc in [syms['nr_variant_opened'],syms['nr_variant_read_done'],syms['nr_variant_closed']]:
   assert not fixture.allocated
   callbacks.append(dict(entry=hex(pc),status=u.reg_read(UC_ARM_REG_R0),value=u.reg_read(UC_ARM_REG_R1),message_pool_released_before_callback=True))
  if pc in [0x96529c,0x968380,0x9657a0]:branches.append(hex(pc))
 for pc in [0xced3e0,0xced4b4,0xceda34,0xced554,0x959b5c,0x9682b0,0x959d34,0x96a140,0x96f32c,0x96529c,0x968380,0x9657a0,syms['nr_variant_opened'],syms['nr_variant_read_done'],syms['nr_variant_closed']]:u.hook_add(UC_HOOK_CODE,observe,begin=pc,end=pc)
 assert call('nr_variant_bind',0,230,owner,syms['xt2_reader_service'])==0
 assert call(0x958fbc,1)==0 and get(0x9ae8f4)==1
 path=RAM+0x1000;status=RAM+0x2000;u.mem_write(path,b'A:\\XT2PROF.BIN\0')
 # Numeric31 is required by unchanged reader source. The variant replaces its
 # adapter admission premise with installed forced-normal routing, not proof of
 # original NORMAL_FS_MODE_STABLE. Production reader remains failclosed.
 assert call('xt2_reader_start',path,31)==0
 states=[];transport=[]
 for _ in range(10):
  pending=fixture.pending;pending=len(pending)if not isinstance(pending,int)else pending
  if pending:
   op,caller,reply,n=struct.unpack('<HBBI',u.mem_read(fixture.pool,8))
   transport.append(dict(opcode=hex(op),caller=caller,reply_queue=reply,payload_bytes=n,modeword=get(0x9ae8f4)))
   fixture.drain_one_worker()
  assert get(0x9ae8f4)==1
  state=call('xt2_reader_service');states.append(state)
  if state in (7,8,9):break
 else:raise AssertionError('Reader did not terminate bounded nativequeue sequence')
 call('xt2_reader_status',status);words=struct.unpack('<9I',u.mem_read(status,36))
 assert get(0x9ae8f4)==1
 assert all(x in native for x in ['0xced3e0','0xced4b4','0xceda34','0xced554','0x959b5c','0x9682b0','0x959d34','0x96a140','0x96f32c']),(words,native,branches,callbacks,fixture.summary())
 assert branches==['0x96529c','0x968380','0x9657a0'] and len(callbacks)==3
 assert call('nr_phase')==6
 assert [(x['opcode'],x['payload_bytes'])for x in transport]==[('0x1389',80),('0x138a',28),('0x138c',40)]
 assert all(x['caller']==230 and x['reply_queue']==120 and x['modeword']==1 for x in transport)
 assert fixture.summary()['resources']==dict(alias_internal=0,alias_public=0,descriptor_id=0xffffffff,open_count=0,context_slot=0,reservation=0,pool_owned=0,queued=0)
 # drain_one_worker has returned after callback; only now may this explicit
 # owner operation discharge routing lifetime. Not invoked inside callbacks.
 assert call('nr_release_after_quiescence',1)==0
 result=dict(error_fixture=error,reader_states=states,reader_status=list(words),native_entries=native,forced_normal_branches=branches,callbacks=callbacks,modeword_retained=1,route_release_after_worker_return=True,filesystem=fixture.summary(),transport=transport,read_hook_header_contract="message+4 retains worker capacity80; actualqueued payload28 observed before receive/poolrelease")
 if error:
  assert state==9 and words[1]==9 and words[3]==0
  assert call('xt2_profile_pipeline_generation')==0
  result.update(pipeline_run=False,error_data_ineligible=True,normal_cleanup_after_completed_error=True)
 else:
  assert state==7 and words[1]==0 and words[5]==len(blob) and words[6]==0
  payload,hooks,manifest_addr,request=0x0b000000,0x0b008000,0x0c000000,0x0f000000
  u.mem_write(payload,b'\xa5'*0x4000);u.mem_write(hooks,b'\x5a'*348);u.mem_write(manifest_addr,manifest)
  u.mem_write(request,struct.pack('<7I',manifest_addr,len(manifest),0x1254000,payload,0x4000,hooks,348))
  assert call('xt2_profile_prepare',request)==0
  generation=call('xt2_profile_pipeline_generation');assert generation==1 and call('xt2_profile_candidate_eligible',request,generation)==1
  import xt2_profile_relocation as relocation
  from verify_xt2_profile_stage import expected_stage
  expected_payload,expected_hooks=relocation.materialize(manifest,0x1254000)
  got=bytes(u.mem_read(payload,0x4000));got_hooks=bytes(u.mem_read(hooks,348))
  assert got==expected_stage(expected_payload,blob)and got_hooks==expected_hooks
  result.update(pipeline_run=True,generation=generation,candidate_eligible=True,payload_sha256=sha(got),hooks_sha256=sha(got_hooks),original_container_sha256=sha(blob))
  # Optional observation only; defaults preserve the frozen assay behavior.
  # Caller owns any explicitly modeled isolated consumer boundary.
  if prepared_observer is not None:
   result['prepared_consumption']=prepared_observer(u,payload,hooks,0x1254000)
 return result

def main():
 blob=(ROOT/'firmware/research/data-container-unverified/custom.xt2p').read_bytes();manifest=(ROOT/'firmware/research/profile-materializer-unverified/runtime-template.reloc').read_bytes();f=Firmware('xt2-4.41',True)
 with tempfile.TemporaryDirectory(prefix='xt2-normal-reader-')as temp:
  sections,syms,compiled=build(Path(temp));cases=[assay(f,sections,syms,blob,manifest,error=e)for e in (False,True)]
 import sys,re
 helper_files=sorted({str(Path(m.__file__).resolve()) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and str(Path(m.__file__).resolve()).startswith(str(ROOT/'scripts')+'/') and Path(m.__file__).suffix=='.py'})
 headers={};pending=list(SOURCES)
 while pending:
  name=pending.pop();path=Path(name)if Path(name).is_absolute()else ROOT/'scripts'/name
  for h in re.findall(r'#include \"([^\"]+)\"',path.read_text()):
   candidates=[path.parent/h,ROOT/'scripts'/h,ROOT/'firmware/research/profile-materializer-unverified'/h]
   q=next(q for q in candidates if q.exists()).resolve()
   if str(q)not in headers:headers[str(q)]=sha(q.read_bytes());pending.append(str(q))
 report=dict(scope=__doc__,passed=True,compiled=compiled,local_python_helpers=[dict(path=p,sha256=sha(Path(p).read_bytes()))for p in helper_files],local_headers_and_schema=[dict(path=p,sha256=h)for p,h in sorted(headers.items())],cases=cases,sources=[dict(path='scripts/'+p,sha256=sha((ROOT/'scripts'/p).read_bytes()))for p in SOURCES+['xt2_normal_route_prototype.h','xt2_normal_route_reader_variant.h','verify_xt2_normal_reader_pipeline.py','xt2_native_profile_fs_fixture.py']],firmware=[dict(base=hex(b),sha256=sha(d))for b,d in f.units],container_sha256=sha(blob),manifest_sha256=sha(manifest),production_reader_owner_changed=False,activation=False,mounted_media=False,physical_camera=False,limitations=['One isolated moduleA normal-nativequeue integration with supplied mounted-context/backing entry and lowerdata/OS models; no cardmount or physicalread proof.','Productionreader mode contract remains unchanged and gate remains enabled outside this separate variant. Numeric31 is source ABI compatibility, not a claim that globalmode is stable0.','ActualnativeownerTCB/currenttask are explicit fixtures; six hooks are installed only inside isolated UC memory. Actualread payloadLength28 is observed in copiedqueuedblock; hook sees only retainedworkercapacity80.','Media/context/BSS teardown coordination and actual residentallocation/cache permissions remain unresolved.'],reproduction='LIBUNICORN_PATH="$PWD/.toolchains/unicorn-tci" UC_IGNORE_REG_BREAK=1 .venv/bin/python scripts/verify_xt2_normal_reader_pipeline.py')
 out=ROOT/'research/native-normal-reader-pipeline-verification.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(out),passed=True,cases=len(cases),text_bytes=compiled['text_bytes'])))
if __name__=='__main__':main()
