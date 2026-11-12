"""Verify one PR308 reuse boundary against immutable X-T2 code/native reports.

Uses local selected upstream metadata and existing native SDK reports. Validates
the offline update-backed flash control separately from runtime callback
publication. No flash result, firmware table or private source is emitted.
"""
import argparse
import hashlib
import json
from pathlib import Path
from firmware_analysis import Firmware

ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parents[1]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def verify(output):
    output=Path(output);assert not output.exists();output.mkdir()
    inputs=ROOT/'ff80-upstream-inputs'
    ref_path=inputs/'reuse-refs-2026-11-12.json';refs=json.loads(ref_path.read_text())
    assert refs['pr308']['head_sha']=='6d189457bf14e9894b917fbd62e4479eea8eb2ff'
    assert refs['pr308']['state']=='open'and refs['pr308']['draft']is False
    assert refs['pr308']['fujimod_gitlink']=='b4314dd650e3ff57755250cb6315636d817b8ff1'
    flash_path=inputs/'xt2-flash-480aded0.json';flash=json.loads(flash_path.read_text())
    assert flash['firmware_id']=='xt2-441'and flash['transport']=='xpp-cmd-callback'
    assert flash['window']==dict(address=0xf0000000,size=0x4000000)
    native=Firmware('xt2-4.41',True)
    update_path=WORKSPACE/native.manifest['source'];update=update_path.read_bytes()
    assert sha(update)==native.manifest['sha256']
    control=flash['control'];start=flash['update_image']['dat_offset']+control['offset']
    control_bytes=bytes(b^flash['update_image']['xor']for b in update[start:start+control['size']])
    assert len(control_bytes)==control['size']==32768 and sha(control_bytes)==control['sha256']
    bulk_path=WORKSPACE/'.toolchains/fujimod-944d5c8-source/catalog/firmware/xt2/4.41/bulk.generated.json'
    bulk=json.loads(bulk_path.read_text());assert bulk['firmware_id']=='xt2-441'
    checks=[]
    for row in bulk['code_checks']:
        assert sha(native.read(row['address'],row['size']))==row['sha256'],row['name']
        checks.append(dict(name=row['name'],address=hex(row['address']),size=row['size'],sha256=row['sha256']))
    assert bulk['window']['size']==524288 and bulk['source']['tag']==0x133
    assert native.word(0x1975b28)==0x15e6888
    assert native.word(0x16fddd4)==native.word(0x16fbe78)==0x1e0c180
    assert sha(native.read(0x1586470,16))=='5750a61d999fe7f3887809ef161c7c6697b9ea10e793589c0dc05c94891b3dd6'
    reports=[];pins={str(ref_path):sha(ref_path.read_bytes()),str(flash_path):sha(flash_path.read_bytes()),str(bulk_path):sha(bulk_path.read_bytes())}
    probe=ROOT/'probe_sdk_native_usb_callback.py'
    for number in [2,3,4]:
        path=ROOT/f'sdk-native-usb-callback-{number}-unverified/probe.json';r=json.loads(path.read_text())
        assert r['error']is None and r['class_number']==number
        assert r['adapter_sha256']==sha(probe.read_bytes())
        assert r['hardware_verified']is False and r['usb_transactions']==0 and r['flash_readback']is False
        assert r['firmware_api_substitutions']==r['host_registration_writes']==r['host_vfp_enable_writes']==0
        result=r['stages'][-1]
        assert result['class_number']==number and result['stop']=='0x1586480'
        assert result['context']=='0x1d215f0'and result['host_callback_table_writes']is False
        assert result['caller_scratch']==dict(base='0x10000000',bytes=65536)
        assert result['native_buffer']==dict(base='0x5522000',bytes=0x3320000)
        assert result['stopped_before_posting_class_message']is True
        assert result['slot_word']==('0x15e6888'if number==3 else '0x0')
        if number==3:
            assert result['published_table']=='0x1e0c180'and result['slot_at_offset12']=='0x1e0c18c'
            assert result['native_factory_copy_matches']is True
        pins[str(path)]=sha(path.read_bytes());reports.append(result)
    report=dict(scope=__doc__,status='PASS',checker_sha256=sha(Path(__file__).read_bytes()),
        probe_sha256=sha(probe.read_bytes()),upstream_refs=refs,stock_update_sha256=native.manifest['sha256'],
        input_report_sha256=pins,immutable_bulk_code_checks=checks,native_class_results=reports,
        offline_update_control_matches=True,native_callback_publication_qualified=True,
        outer_usb_mode_selection_qualified=False,jig_admission_qualified=False,
        usb_readback_qualified=False,flash_backup_qualified=False,hardware_verified=False,
        mod_candidate_changed=False)
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',native_classes=3,bulk_code_checks=len(checks),
        boundary='native class3 callback publication; no USB transaction or flash backup')))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'usb-callback-reuse-check-unverified')
    verify(p.parse_args().output)
