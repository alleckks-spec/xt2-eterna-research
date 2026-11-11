"""Rerun the frozen final SDK settings probes on an explicit ordinary composition.

Only artifact/output paths and the verified ELF identity are adapted. Native
mount, task/IRQ scheduling, storage callbacks, assertions and JSON fixture
contract remain those of the original final probes. No runtime is introduced.
Defaults retain the original 892f artifact and prior readback input; output is
separate, and original sources/reports are never rewritten.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
from build_modular_candidate import ROOT


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=ROOT/'save-data-menu-native-build-unverified')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--case',choices=['commit','restore'],required=True)
    parser.add_argument('--settings-readback',type=Path,default=ROOT/'sdk-native-fs-settings-commit-unverified/settings-readback.json')
    parser.add_argument('--save-data-nondefault',action='store_true',help='Also qualify native DATE FOLDERS on and FORMAT CARD NAME off persistence')
    args=parser.parse_args()
    assert not (args.output/'probe.json').exists(), 'Preserve prior reports; choose a fresh output'
    receipt=json.loads((args.build/'preparation.json').read_text())
    manifest=json.loads((args.build/'manifest.json').read_text())
    raw=(args.build/'mods.elf').read_bytes(); digest=sha(raw)
    assert digest==receipt['elf_sha256']
    for name,h in receipt['source_sha256'].items():assert sha(Path(name).read_bytes())==h,name
    if args.case=='commit':import probe_sdk_native_fs_settings_commit as original
    else:import probe_sdk_native_fs_settings_restore as original
    source=inspect.getsource(original.main)
    anchors={"        build=ROOT/'save-data-menu-native-build-unverified'":"        build=COMPOSED_BUILD",
        "        assert hashlib.sha256(raw).hexdigest()=='892f6d3b5cafb9ac86c4f32e9a625220d58593a7b2c7c6310fcf739c46fe482e'":
        '        assert hashlib.sha256(raw).hexdigest()==COMPOSED_ELF'}
    if args.case=='restore':anchors["    saved=(ROOT/'sdk-native-fs-settings-commit-unverified/settings-readback.json').read_bytes()"]='    saved=COMPOSED_READBACK.read_bytes()'
    if args.save_data_nondefault:
        if args.case=='commit':
            old="        assert word(owner+92)==1\n        stages.append(dict(settings_commit="
            new="""        assert word(owner+92)==1
        save_owner=symbols['save_data_settings']
        assert word(save_owner+92)==0
        assert execute_smp_call(0x154b700,0x7f01,0)==0
        assert execute_smp_call(0x154b700,0x7f03,1)==0
        assert word(symbols['save_data_date_folders'])==1 and word(symbols['save_data_date_card_name'])==0
        assert word(save_owner+92)==2
        stages.append(dict(native_save_data_properties=['0x7f01','0x7f03'],date_folders=1,date_card_name=0,requested=2))
        stages.append(dict(settings_commit="""
            assert source.count(old)==1;source=source.replace(old,new)
            old="            if word(owner+96)==word(owner+92) and word(owner+92):break"
            assert source.count(old)==1
            source=source.replace(old,"            if word(owner+96)==word(owner+92) and word(owner+92) and word(save_owner+96)==word(save_owner+92):break")
            old="        assert word(owner+92)==word(owner+96)==1 and word(owner+100)==0"
            assert source.count(old)==1
            source=source.replace(old,old+"\n        assert word(save_owner+92)==word(save_owner+96)==2 and word(save_owner+100)==0\n        stages.append(dict(save_data_completed=2,save_data_failed=0))")
            old="        assert produced['stock_choices']['current']['values']==[dict(setting='film_simulation',value='eterna')]"
            assert source.count(old)==1
            source=source.replace(old,old+"\n        assert produced['save_data']==dict(date_folders=True,date_card_name=False)")
        else:
            old="    assert hashlib.sha256(saved).hexdigest()=='82daddf400b7e2dcb6db80d61c4d67a059c25286f291a243bb889cf2e566316c'"
            anchors[old]="    assert json.loads(saved)==dict(save_data=dict(date_folders=True,date_card_name=False),stock_choices=dict(current=dict(values=[dict(setting='film_simulation',value='eterna')])))"
            old="        assert word(symbols['x70_stock_choices_restored'])==1"
            assert source.count(old)==1
            source=source.replace(old,old+"\n        assert word(symbols['save_data_date_folders'])==1 and word(symbols['save_data_date_card_name'])==0\n        save_owner=symbols['save_data_settings']\n        assert word(save_owner+92)==word(save_owner+96)==word(save_owner+100)==0\n        stages.append(dict(native_save_data_restored=True,date_folders=1,date_card_name=0,explicit_selection_setters=0,host_settings_decode_calls=0))")
    for old,new in anchors.items():assert source.count(old)==1,old;source=source.replace(old,new)
    source=source.replace('def main():','def execute():',1)
    namespace=dict(vars(original),OUT=args.output,COMPOSED_BUILD=args.build,COMPOSED_ELF=digest,COMPOSED_READBACK=args.settings_readback)
    exec(compile(source,str(Path(original.__file__))+'::composed-artifact','exec'),namespace)
    try:namespace['execute']()
    finally:
        if (args.output/'probe.json').exists():
            report=json.loads((args.output/'probe.json').read_text())
            report.update(artifact_adapter_scope=__doc__,elf_sha256=digest,save_data_nondefault=args.save_data_nondefault,
                checker_sha256=sha(Path(__file__).read_bytes()),original_checker_sha256=sha(Path(original.__file__).read_bytes()),
                adapted_checker_sha256=sha(source.encode()),original_probe_source=str(Path(original.__file__)),
                settings_readback_input_sha256=sha(args.settings_readback.read_bytes()) if args.case=='restore' else None,
                artifact_manifest_sha256=sha((args.build/'manifest.json').read_bytes()))
            (args.output/'probe.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
