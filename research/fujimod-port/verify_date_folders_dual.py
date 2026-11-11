"""Verify actual A/B date candidates, native arbitration and counter ownership.

Native post-enumeration catalog/status inputs are explicit. No completed mount,
positive filesystem result, capture or physical storage operation is claimed.
Original AI-assisted checker using existing platform/native function fixtures.
"""
import argparse
import json
import struct
from pathlib import Path
from probe_date_folders_dual import run_case,ROOT,CONTEXT,B_CONTEXT,CONTEXT_BYTES
from verify_ordinary_platform_card import main as verify_card
from build_modular_candidate import sha


def main(build,output):
    output.mkdir(exist_ok=True);verify_card(build,76);cases=[]
    definitions=[
        ('new-day',101,100,1001,1,{},['102_1111\\DSCF2001','101_1111\\DSCF1001','102_1111\\DSCF2001']),
        ('both-continue',101,100,1001,1,dict(asuffix='_1111',bsuffix='_1111'),['101_1111\\DSCF1002','100_1111\\DSCF0002','101_1111\\DSCF1002']),
        ('a-continue',101,100,1001,1,dict(asuffix='_1111'),['101_1111\\DSCF1002','101_1111\\DSCF1001','101_1111\\DSCF1002']),
        ('b-newer-folder',100,102,1,2001,{},['101_1111\\DSCF1001','103_1111\\DSCF3001','103_1111\\DSCF3001']),
        ('b-larger-file',100,100,1,99,dict(asuffix='_1111',bsuffix='_1111'),['100_1111\\DSCF0002','100_1111\\DSCF0100','100_1111\\DSCF0100']),
    ]
    for name,af,bf,an,bn,options,wanted in definitions:
        actual=run_case(build,af,bf,an,bn,enabled=True,**options)
        for index,result in enumerate(actual['results']):
            assert result['name'].endswith(wanted[index//2]),(name,result,wanted)
            assert result['counter_bytes_before']==result['counter_bytes_after'],(name,result)
        actual['case']=name;cases.append(actual)
    edges=[]
    for name,nums,options,wanted in [
        ('empty',(0,0,0,0),dict(initial_pair=(100,0)),['100_1111\\DSCF0001']*3),
        ('invalid-month',(101,100,1001,1),dict(calendar=(26,13,11,0,0,0)),['101_FUJI\\DSCF1002','100_FUJI\\DSCF0002','101_FUJI\\DSCF1002']),
        ('invalid-day',(101,100,1001,1),dict(calendar=(26,11,0,0,0,0)),['101_FUJI\\DSCF1002','100_FUJI\\DSCF0002','101_FUJI\\DSCF1002']),
        ('capacity',(999,999,9999,9999),dict(expected_errors={0x41:6,0x42:6,0xffffffff:6}),None),
    ]:
        actual=run_case(build,*nums,enabled=True,**options);actual['case']=name
        for index,result in enumerate(actual['results']):
            assert result['counter_bytes_before']==result['counter_bytes_after']
            if wanted:assert result['name'].endswith(wanted[index//2]),(name,result)
            else:assert result['status']==6 and result['name'] is None
        edges.append(actual)
    refusals=[]
    for owner in ['a','b']:
        actual=run_case(build,101,100,1001,1,enabled=True,refusal_owner=owner)
        assert all(r['counter_bytes_before']==r['counter_bytes_after'] for r in actual['results'])
        assert any(r['status']==1 and r['counter_writes'] for r in actual['results'])
        refusals.append(actual)
    stock=[]
    base=ROOT/'save-data-menu-native-build-unverified'
    for af,bf,an,bn in [(100,100,1,1),(100,101,1,1001),(102,100,2001,1),(100,100,1,99)]:
        expected=run_case(base,af,bf,an,bn)
        actual=run_case(build,af,bf,an,bn,enabled=False)
        for e,a in zip(expected['results'],actual['results']):
            for key in ['status','name','counter_bytes_after','candidate_a','candidate_b']:assert e[key]==a[key],(key,e,a)
        stock.append(dict(inputs=[af,bf,an,bn],full_native_outputs_original_equal=True))
    report=dict(scope=__doc__,status='PASS',elf_sha256=sha((build/'mods.elf').read_bytes()),
        cases=cases,edges=edges,refusals=refusals,off_stock=stock,framewalk=False,per_owner_contexts=True,
        producer_counter_pair_restored=True,post_capture_counter_owner_changed=False,
        physical_storage=False,full_mount=False,full_boot=False,hardware_verified=False,
        checker_sha256=sha(Path(__file__).read_bytes()),
        native_fixture_sha256=sha((ROOT/'probe_date_folders_dual.py').read_bytes()),
        constructor_fixture_sha256=sha((ROOT/'probe_date_folders_native.py').read_bytes()))
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',native_date_calls=48,capacity_calls=6,refusal_calls=12,off_stock_calls=24,elf_sha256=report['elf_sha256'])))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.build,a.output)
