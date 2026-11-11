"""Pin independent reruns to the exact bounded recorded-callback cardio composition.

Report integrity and declared native-function/software-board evidence only.
No report from either parent artifact is promoted to combined execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--build',type=Path,default=ROOT/'cardio-task-issue-build-unverified')
 p.add_argument('--reports',type=Path,default=ROOT/'cardio-task-issue-check-unverified')
 a=p.parse_args();digest=sha(a.build/'mods.elf');pins={}
 def read(path):
  d=json.loads(path.read_text());assert d['elf_sha256']==digest,path
  assert not d.get('error') and not d.get('faults'),path
  if 'status' in d:assert 'PASS' in d['status'],path
  pins[str(path)]=sha(path);return d
 functional=read(a.reports/'functional.json');assert len(functional['cases'])==84 and len(functional['guard_cases'])==2 and len(functional['reset_cases'])==7
 imported=read(a.reports/'import-fixed.json');assert len(imported['cases'])==6 and imported['primary_and_shadow_marker_coherent']
 assert all(r['native_bank_cancel_markers']==[0]*7 for r in imported['cases'])
 read(a.reports/'usb.json')
 serialized=read(a.reports/'custom-slot-film.json');assert len(serialized['cases'])==49 and serialized['custom_record_count']==7
 delivery=read(a.reports/'delivery.json');assert delivery['delivery_words']==81 and len(delivery['exact_elf_native_reports'])==21
 for relative in ['adapter.json','native/verification.json','transitions/verification.json','menu/date/verification.json','menu/volume/verification.json']:
  read(ROOT/'cardio-task-issue-folders-check-unverified'/relative)
 read(ROOT/'cardio-task-issue-dependencies-unverified/verification.json')
 numeric=ROOT/'cardio-task-issue-regressions-unverified'
 films,nr,jpeg=[read(numeric/name/'verification.json') for name in ['films','nr','jpeg']]
 assert len(films['records'])==356 and len(films['identity_checks'])==99
 assert len(nr['register_cases'])==43 and len(nr['menus'])==3
 assert len(jpeg['cases'])==33 and len(jpeg['menus'])==3
 read(numeric/'memory.json')
 nondefault_commit=read(ROOT/'cardio-task-issue-sdk-commit-unverified/probe.json')
 nondefault_restore=read(ROOT/'cardio-task-issue-sdk-restore-unverified/probe.json')
 for record in [nondefault_commit,nondefault_restore]:
  assert record['save_data_nondefault'] and record['firmware_api_substitutions']==record['host_registration_writes']==record['host_vfp_enable_writes']==0
 merged=next(s for s in nondefault_commit['stages'] if 'settings_content' in s)
 assert merged['settings_content']['save_data']==dict(date_folders=True,date_card_name=False)
 assert any(s.get('save_data_completed')==2 and s['save_data_failed']==0 for s in nondefault_commit['stages'])
 restored_owner=next(s for s in nondefault_restore['stages'] if s.get('native_save_data_restored'))
 assert restored_owner==dict(native_save_data_restored=True,date_folders=1,date_card_name=0,explicit_selection_setters=0,host_settings_decode_calls=0)
 readback2=ROOT/'cardio-task-issue-sdk-commit-unverified/settings-readback.json'
 assert sha(readback2)==nondefault_restore['settings_readback_input_sha256'];pins[str(readback2)]=sha(readback2)
 delivery_cases=read(a.reports/'recorded-delivery.json');assert len(delivery_cases['cases'])==8 and not delivery_cases['native_storage_calls']
 fixed=read(ROOT/'cardio-task-contract-fixed-retirement-unverified/probe.json')
 retired=fixed['contract_result']
 assert retired['job_state']==3 and retired['status']==5 and retired['banks']==[0]*4 and retired['active']==retired['callbacks']==retired['actual_open_count']==retired['stale']==0
 assert retired['retirement_stable_after_polls']==3
 retried=retired['explicit_caller_retry']
 assert retried['state']==2 and retried['status']==0 and retried['generation_after']==retried['generation_before']+1
 assert retried['active']==retried['callbacks']==retried['actual_open_count']==0
 assert retired['fault_applied'][0]['task']==39 and 'restored_at_callback' in retired['fault_applied'][0]
 assert any(e['pc']=='0xced4b4' and e['task']==34 for e in fixed['contract_trace'])
 assert not any(e['pc']=='0xced4b4' and e['task']==39 for e in fixed['contract_trace'])
 old_path=ROOT/'cardio-task-contract-original-transient-unverified/probe.json';old=json.loads(old_path.read_text())
 assert old['error'] is None and old['elf_sha256']=='18d06d6afe79b67dba7d9fae33ed0586d5d941a4ec40122502b8bc5d85f331d0'
 stuck=old['contract_result'];assert stuck['job_state']==1 and stuck['status']==0 and stuck['banks'].count(1)==1 and stuck['callbacks']==0 and stuck['stale']==stuck['actual_open_count']==1
 assert any(e['pc']=='0xced4b4' and e['task']==39 for e in old['contract_trace'])
 pins[str(old_path)]=sha(old_path)
 receipt=json.loads((a.build/'preparation.json').read_text());assert receipt['shared_owners_unique'] and not receipt['target_conflicts']
 manifest=json.loads((a.build/'manifest.json').read_text());region,=manifest['regions']
 assert region['size']==249288 and len(manifest['words'])==81
 result=dict(scope=__doc__,status='PASS',elf_sha256=digest,checker_sha256=sha(Path(__file__)),
  related_report_sha256=pins,words=81,sources=42,reservation_bytes=262144,payload_bytes=region['size'],spare_bytes=262144-region['size'],
  genuine_native_settings_commit_and_fresh_board_restore=True,recorded_issue_refusal_retirement_and_caller_retry=True,automatic_lost_queue_retry=False,full_rom_boot=False,physical_nand=False,physical_sd=False,hardware_verified=False)
 (a.reports/'integration.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(status='PASS',elf=digest,reports=len(pins))))

if __name__=='__main__':main()
