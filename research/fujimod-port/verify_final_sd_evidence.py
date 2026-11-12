"""Audit exact final ordinary/USB SD-test evidence without rerunning guest code.

This is bounded software qualification for hardware-test packaging. Physical
boot, display, capture, power-cycle, memory headroom and USB remain unverified.
All private evidence and source snapshots remain local.
"""
import argparse
import inspect
import json
import shutil
from pathlib import Path

from build_modular_candidate import ROOT, sha
from verify_common_controls_sdk_cardio import OWNERS
from verify_final_variant_sdk import ELFS
import verify_ordinary_platform_card as card

CASES = ['films', 'nr', 'jpeg', 'wb-import', 'custom-save', 'delivery', 'date',
         'dependencies', 'memory', 'overlay', 'aspect', 'icon-readers']
VARIANTS = {
    'ordinary': ('controls-lookup', 79, 130, 551864),
    'usb': ('controls-q-usb-lookup', 81, 131, 552496),
}


def main(output):
    assert not output.exists()
    output.mkdir(parents=True)
    pins, sources, variants = {}, {}, {}

    def pin(path):
        path = path.resolve()
        pins[str(path)] = sha(path.read_bytes())

    def read(path, digest=None, identity='elf_sha256'):
        path = ROOT / path if not Path(path).is_absolute() else Path(path)
        r = json.loads(path.read_text())
        if digest:
            assert r[identity] == digest, path
        assert not r.get('error') and not r.get('faults'), path
        if 'status' in r:
            assert 'PASS' in r['status'], path
        assert not r.get('hardware_verified', False), path
        pin(path)
        return r

    def frozen(name):
        r = read(name + '/freeze.json')
        for path, record in r['files'].items():
            digest = record['sha256'] if isinstance(record, dict) else record
            assert sha(Path(path).read_bytes()) == digest, path
            pin(Path(path))
        return r

    for variant, (prefix, count, words, footprint) in VARIANTS.items():
        build = ROOT / (prefix + '-build-unverified')
        repeat = ROOT / (prefix + '-rebuild-unverified')
        digest = sha((build / 'mods.elf').read_bytes())
        assert digest in ELFS and ELFS[digest] == (variant == 'usb')
        prep = read(build / 'preparation.json', digest)
        assert prep['usb_debug_selected'] == ELFS[digest]
        assert prep['logical_q_binding'] and prep['controls'] == 9
        assert len(prep['source_sha256']) == count
        for path, expected in prep['source_sha256'].items():
            assert sha(Path(path).read_bytes()) == expected, path
            sources[path] = expected
        for path in ['target.json', 'manifest.json', 'source-roots.json']:
            pin(build / path)
        manifest = json.loads((build / 'manifest.json').read_text())
        assert len(manifest['words']) == words
        assert len({w['address'] for w in manifest['words']}) == words
        region, = manifest['regions']
        assert region['size'] == footprint
        target = json.loads((build / 'target.json').read_text())
        reservation, = target['card_regions']
        assert int(reservation['address'], 0) == 0x1338000
        assert int(reservation['size'], 0) == 0x88000
        roots = json.loads((build / 'source-roots.json').read_text())
        assert sum(n.startswith('lib-') for n in roots) == 22
        repeated = {}
        for left, right, names in [(build, repeat, ['mods.elf', 'region.bin']),
                (Path(str(build) + '-card'), Path(str(repeat) + '-card'), ['ffboot.bin', 'ffsys.bin'])]:
            for name in names:
                raw = (left / name).read_bytes()
                assert raw == (right / name).read_bytes(), (variant, name)
                repeated[name] = dict(bytes=len(raw), sha256=sha(raw))
        # Retain the original correspondence engine, writing a fresh receipt.
        source = inspect.getsource(card.main)
        anchor = "(BUILD/'card-correspondence.json')"
        assert source.count(anchor) == 1
        source = source.replace(anchor, 'FINAL_CARD_RECEIPT')
        namespace = dict(vars(card), FINAL_CARD_RECEIPT=output / (variant + '-card.json'))
        exec(compile(source, str(__file__) + '::existing-card-correspondence', 'exec'), namespace)
        namespace['main'](build, words)
        pin(output / (variant + '-card.json'))

        functions = 'controls-lookup-functions-unverified' if variant == 'ordinary' else 'q-usb-full-functions-unverified'
        for case in CASES:
            a = read(f'{functions}/{case}/{case}-full-adapter.json', digest)
            assert a['case'] == case and a['words'] == words and a['init_count'] == 8
            for path in (ROOT / functions / case).rglob('*.json'):
                r = json.loads(path.read_text())
                if isinstance(r, dict) and 'elf_sha256' in r:
                    read(path, digest)
        films = read(f'{functions}/films/films/verification.json', digest)
        assert len(films['records']) == 356 and len(films['identity_checks']) == 99
        assert len(films['menus']) == 3 and len(films['captions']) == 6
        nr = read(f'{functions}/nr/nr/verification.json', digest)
        jpeg = read(f'{functions}/jpeg/jpeg/verification.json', digest)
        assert len(nr['register_cases']) == 43 and len(nr['menus']) == 3
        assert len(jpeg['cases']) == 33 and len(jpeg['menus']) == 3
        custom = read(f'{functions}/custom-save/verification.json', digest)
        assert len(custom['cases']) == 49 and custom['custom_record_count'] == 7
        imported = read(f'{functions}/wb-import/verification.json', digest)
        assert len(imported['cases']) == 6 and imported['primary_and_shadow_marker_coherent']
        assert len(read(f'{functions}/delivery/verification.json', digest)['cases']) == 8
        icons = read(f'{functions}/icon-readers/verification.json', digest)
        assert icons['stock_reader_comparisons'] == 19950 and icons['icon_patch_count'] == 22

        wb_folder = 'controls-lookup-wb-check-unverified' if variant == 'ordinary' else 'q-usb-lookup-wb-unverified'
        wb = read(wb_folder + '/verification.json', digest)
        assert len(wb['cases']) == 84 and len(wb['guard_cases']) == 2 and len(wb['reset_cases']) == 7
        ui_folder = 'controls-lookup-q-check-unverified' if variant == 'ordinary' else 'q-usb-lookup-controls-unverified'
        read(ui_folder + '/verification.json', digest)
        read(ui_folder + '/ui/verification.json', digest)
        dims = read(f'final-{variant}-dimensions-unverified/verification.json', digest)
        captions = read(f'final-{variant}-captions-unverified/verification.json', digest)
        assert len(dims['cases']) == 9 and dims['stock_detail_equal']
        assert len(captions['cases']) == 9
        screens = read(f'final-{variant}-screens-unverified/screens.json', digest)
        assert len(screens['cases']) == 30 and len(screens['stock']) == 15 and len(screens['visibility']) == 12

        commit_folder = 'controls-lookup-sdk-commit-unverified' if variant == 'ordinary' else 'final-usb-sdk-commit-unverified'
        commit = read(commit_folder + '/probe.json', digest)
        restore = read(f'final-{variant}-sdk-restore-unverified/probe.json', digest)
        readback = ROOT / commit_folder / 'settings-readback.json'
        assert sha(readback.read_bytes()) == restore['settings_readback_input_sha256']
        assert json.loads(readback.read_text()) == commit['expected_document'] == restore['expected_document']
        pin(readback)
        owners = next(s['full_owners_after_write'] for s in commit['stages'] if 'full_owners_after_write' in s)
        assert set(owners) == set(OWNERS)
        assert all(v['registered'] == 2 and v['completed'] == v['requested'] and v['failed'] == 0 for v in owners.values())
        fresh = next(s for s in restore['stages'] if 'full_owners_restored' in s)
        assert fresh['explicit_selection_setters'] == fresh['host_settings_decode_calls'] == 0
        assert set(fresh['full_owners_restored']) == set(OWNERS)
        assert all(v['registered'] == 2 and v['requested'] == v['completed'] == v['failed'] == 0 for v in fresh['full_owners_restored'].values())
        sdk = [commit, restore]
        for case in ['issue', 'capacity']:
            folder = 'controls-lookup-sdk-' + case + '-unverified' if variant == 'ordinary' else 'final-usb-sdk-' + case + '-unverified'
            r = read(folder + '/probe.json', digest)
            assert r['startup_owner_names'] == OWNERS
            result = r['contract_result']
            assert result['callbacks'] == result['active'] == result['actual_open_count'] == 0
            assert result['banks'] == [0] * 4
            if case == 'issue':
                assert result['job_state'] == 3 and result['status'] == 5
                assert result['explicit_caller_retry']['state'] == 2
            else:
                assert result['job_state'] == 2 and result['status'] == 0
                assert result['after_issue']['held_pool_blocks'] == 48
                assert result['after_issue']['unowned_post_not_retained']
                assert result['native_token_allocations_for_job'] == 1
            sdk.append(r)
        for case in ['pause', 'retry', 'mode']:
            r = read(f'final-{variant}-rec-{case}-unverified/probe.json', digest)
            assert r['exact_final_elf_sha256'] == digest and r['startup_owner_names'] == OWNERS
            sdk.append(r)
        capture_folder = 'controls-lookup-sdk-capture-unverified' if variant == 'ordinary' else 'q-usb-sdk-capture-unverified'
        capture = read(capture_folder + '/probe.json', digest)
        tail = capture['stages'][-1]
        assert tail['cropped_descriptor'][:5] == [6000, 1000, 0, 4000, 4000]
        assert tail['final_native_raf_pair'] == [1, 1] and tail['retired_saved_pointers'] == [0, 0]
        assert tail['main_source_missing'] and tail['stopped_before_hardware_programming']
        assert not capture['encoded_result'] and not capture['shot_ordering_qualified']
        sdk.append(capture)
        early = read(prefix + '-early-sdk-icons-unverified/probe.json', digest, 'common_elf_sha256')
        assert early['full_icon_closure_count'] == 20 and early['original_aspect_surround_cases'] == 12
        assert early['native_constructor_assertions_unchanged']
        sdk.append(early)
        recipe_folder = 'final-ordinary-sdk-recipe-unverified' if variant == 'ordinary' else 'q-usb-sdk-recipe-admission-unverified'
        recipe = read(recipe_folder + '/probe.json', digest)
        checked_folder = 'final-ordinary-sdk-recipe-check-unverified' if variant == 'ordinary' else 'q-usb-sdk-recipe-admission-check-unverified'
        checked = read(checked_folder + '/verification.json', digest)
        assert checked['report_sha256'] == sha((ROOT / recipe_folder / 'probe.json').read_bytes())
        assert checked['resources_retired'] and checked['native_recipe_files'] == 2
        sdk.append(recipe)
        lifecycle = ['final-ordinary-card-compaction-unverified', 'final-ordinary-card-native-unverified', 'final-ordinary-card-guard-unverified'] if variant == 'ordinary' else ['q-usb-card-compaction-unverified', 'q-usb-card-identity-native-unverified', 'q-usb-card-identity-guard-unverified']
        for folder in lifecycle:
            read(folder + '/verification.json', digest)
        nested = read(lifecycle[1] + '/nested-still-live/verification.json', digest)
        assert [s['readers'] for s in nested['stages']] == [1, 1, 2, 1, 0, 0, 0, 0]
        assert nested['publication_delta'] == 1
        for r in sdk:
            assert r['firmware_api_substitutions'] == r['host_registration_writes'] == r['host_vfp_enable_writes'] == 0
            assert r['native_core_count'] == 2 and not r['camera_tested']
        parent = frozen('controls-lookup-qualified-final-check-unverified' if variant == 'ordinary' else 'q-usb-extended-final-check-unverified')
        assert parent['elf_sha256'] == digest
        variants[variant] = dict(elf_sha256=digest,build=str(build),rebuild=str(repeat),
            sources=count,libraries=22,mods=14 if variant == 'ordinary' else 15,words=words,
            payload_bytes=footprint,reservation=[0x1338000,0x13c0000],spare_bytes=0x88000-footprint,
            reproducible=repeated,settings_readback_sha256=sha(readback.read_bytes()),
            consumes_fn_image_size=ELFS[digest],software_checks_passed=True,hardware_accepted=False)

    rec = read('final-rec-control-check-unverified/verification.json')
    assert set(rec['results']) == set(VARIANTS)
    for path, record in rec['reports'].items():
        assert sha(Path(path).read_bytes()) == record['sha256']
    # Source provenance history prevents later harmless wrapper edits from
    # retrospectively changing the checker identity of closed native runs.
    history = [ROOT / 'verify_final_variant_sdk.py', *sorted((ROOT / 'final-sdk-adapter-source-history').glob('*.py'))]
    hashes = {sha(p.read_bytes()) for p in history}
    for case in ['commit', 'restore', 'issue', 'capacity']:
        r = json.loads((ROOT / f'final-usb-sdk-{case}-unverified/probe.json').read_text())
        assert r['final_variant_adapter_sha256'] in hashes
    sources.update({str(p):sha(p.read_bytes()) for p in history})
    for name in ['verify_final_sd_evidence.py','verify_final_variant_detail.py','verify_ordinary_platform_card.py',
                 'verify_common_q_sdk_settings.py','verify_common_controls_sdk_settings.py',
                 'verify_common_controls_sdk_cardio.py','verify_final_rec_sdk.py']:
        p = ROOT / name
        sources[str(p)] = sha(p.read_bytes())
    snapshots = {}
    for i, (path, digest) in enumerate(sorted(sources.items())):
        dest = output / 'private-source-snapshot' / f'{i:04d}-{Path(path).name}'
        dest.parent.mkdir(exist_ok=True)
        shutil.copyfile(path, dest)
        assert sha(dest.read_bytes()) == digest
        snapshots[path] = dict(sha256=digest,snapshot=str(dest))
        pin(dest)
    result = dict(status='PASS',scope=__doc__,variants=variants,report_sha256=pins,
        source_snapshots=snapshots,checker_sha256=sha(Path(__file__).read_bytes()),
        software_package_gate=True,hardware_accepted=False,full_rom_boot=False,
        encoded_image=False,physical_power_cycle=False,physical_usb=False,
        limits=['Native function/SDK fixtures, not a complete camera emulator',
                'No developed source0 pixels, encoded JPEG/Exif output or physical shot',
                'No continuous capture epoch, physical cache/DMA/load or heap headroom proof',
                'No physical controls/display, SD boot, NAND/power-cycle or USB protocol proof',
                'Initial card-recipe load only; no selected runtime editor/refresh API',
                'Direct-action controls.function stays default; optional ninth direct-action persistence unselected'])
    (output / 'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',variants=2,reports=len(pins),sources=len(snapshots))))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args().output.resolve())
