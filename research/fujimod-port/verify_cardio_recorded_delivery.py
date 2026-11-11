"""Per-bank error delivery and abandoned-request retirement after actual polling.

Callback error arguments are explicit bounded-function inputs. No successful
storage response is synthesized. Before polling the callback only records;
after polling error publication/stale retirement occurs once. Genuine SDK
callback/task and successful filesystem evidence is checked separately.
"""
import argparse
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
import verify_full_storage_guard as fixture
from verify_cardio_native_worker import Assay,RAM


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 fixture.BUILD=a.build
 (u,s,call,api,clock,init,exceptions),setup=fixture.fixture_machine(True)
 m=Assay.__new__(Assay);m.u=u;m.symbols=s;m.clock=clock;m.presence(True)
 job=RAM+0x4000;folder=RAM+0x3000;name=RAM+0x3100
 u.mem_write(folder,b'FUJIMOD\0');u.mem_write(name,b'TEST.JSN\0')
 seen=[]
 u.hook_add(UC_HOOK_CODE,lambda uc,pc,size,data:seen.append(hex(pc)),begin=0xced3e0,end=0xced668)
 cases=[]
 def state():return dict(job=m.word(job),status=m.word(job+8),active=m.word(s['x70_cardio_active']),callbacks=m.word(s['callbacks']),banks=[m.word(s['bank_state']+n*4) for n in range(4)],stale=m.word(s['x70_cardio_stale']),deferred=m.word(s['x70_cardio_deferred']),overlap=m.word(s['x70_cardio_deferred_overlap']),dropped=m.word(s['x70_cardio_deferred_dropped']))
 for abandoned in [False,True]:
  for index in range(4):
   u.mem_write(job,bytes(256));assert m.api('x70_cardio_begin',job,2,folder,name)==0
   bank=next(n for n in range(4) if m.word(s['bank_job']+n*4)==job and m.word(s['bank_state']+n*4)==1)
   m.api('x70_callback_issued')
   if abandoned:m.api('x70_cardio_abandon',job)
   before=state();assert before['callbacks']==1
   m.api('cb_open_read_'+str(bank),5,0)
   recorded=state();assert recorded['callbacks']==1 and recorded['job']==before['job'] and recorded['status']==before['status']
   assert recorded['deferred']==before['deferred']+1 and recorded['banks'][bank]==before['banks'][bank]
   m.api('x70_cardio_busy');delivered=state()
   assert delivered['callbacks']==delivered['active']==0 and delivered['banks']==[0]*4
   assert delivered['job']==3
   if abandoned:assert delivered['stale']==before['stale']+1
   else:assert delivered['status']==5 and delivered['stale']==before['stale']
   for repeat in range(3):m.api('x70_cardio_busy')
   assert state()==delivered and not seen
   assert delivered['overlap']==delivered['dropped']==0
   cases.append(dict(bank=bank,abandoned=abandoned,before=before,recorded=recorded,delivered=delivered,extra_poll_count=3))
 assert all({c['bank'] for c in cases if c['abandoned']==v}==set(range(4)) for v in [False,True])
 a.output.parent.mkdir(exist_ok=True)
 report=dict(scope=__doc__,status='PASS',elf_sha256=fixture.sha((a.build/'mods.elf').read_bytes()),cases=cases,setup=setup,init_calls=init,native_vfp_exceptions=exceptions,native_storage_calls=seen,checker_sha256=fixture.sha(Path(__file__).read_bytes()),hardware_verified=False)
 a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status='PASS',cases=len(cases))))


if __name__=='__main__':main()
