"""Pin native storage integration reports to reproducible ordinary SD artifacts.

Artifact correspondence and prior-check result integrity only. Does not promote
the declared native fixtures to a physical filesystem, capture or camera result.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import verify_ordinary_platform_card as card_check


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--rebuild', type=Path, required=True)
    parser.add_argument('--reports', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.build / 'manifest.json').read_text())
    receipt = json.loads((args.build / 'preparation.json').read_text())
    word_count = len(manifest['words'])
    assert word_count > 0
    # Keep the earlier artifact's correspondence report immutable. Reuse the
    # existing verifier, changing only its output destination for this stage.
    card_source = inspect.getsource(card_check.main)
    destination = "(BUILD/'card-correspondence.json')"
    assert card_source.count(destination) == 1
    card_source = card_source.replace(destination, 'CARD_REPORT_PATH')
    card_source = card_source.replace('def main(', 'def verify_artifact(', 1)
    namespace = dict(vars(card_check), CARD_REPORT_PATH=args.reports / 'card-correspondence.json')
    exec(compile(card_source, str(Path(card_check.__file__)) + '::stage-report-destination', 'exec'), namespace)
    namespace['verify_artifact'](args.build, word_count)
    digest = sha((args.build / 'mods.elf').read_bytes())
    assert digest == receipt['elf_sha256']
    for name, expected in receipt['source_sha256'].items():
        assert sha(Path(name).read_bytes()) == expected, name
    repeated = {}
    for directory, rebuilt, names in [
        (args.build, args.rebuild, ['mods.elf', 'region.bin']),
        (Path(str(args.build) + '-card'), Path(str(args.rebuild) + '-card'), ['ffboot.bin', 'ffsys.bin'])]:
        for name in names:
            data = (directory / name).read_bytes()
            assert data == (rebuilt / name).read_bytes(), name
            repeated[name] = dict(bytes=len(data), sha256=sha(data))
    with (Path(str(args.build) + '-card') / 'ffboot.bin').open('rb') as stream:
        stream.seek(0xcdfb04)
        assert int.from_bytes(stream.read(4), 'little') == 0x1187ffc
    required = ['callbacks.json', 'dispatch-original.json', 'dispatch-fixed.json',
        'processing/verification.json', 'file/valid.json', 'file/invalid-json.json', 'file/read-error.json',
        'write/verification.json']
    required += ['restore/' + name + '/valid.json' for name in
        ['eterna', 'classic_neg', 'bleach_bypass', 'nostalgic_neg', 'reala_ace', 'neutral', 'card_1']]
    required += ['restore/eterna/invalid-json.json', 'restore/eterna/read-error.json']
    from elftools.elf.elffile import ELFFile
    with (args.build / 'mods.elf').open('rb') as stream:
        symbols = {symbol.name for symbol in ELFFile(stream).get_section_by_name('.symtab').iter_symbols()}
    has_save_data = 'save_data_settings' in symbols
    if has_save_data:
        required += ['restore/eterna/save-data-0-' + str(value) + '/valid.json' for value in [0, 1]]
        required += ['write-save-data-0-0/verification.json']
    if 'xpp_menu_setup_options' in symbols:
        required += ['restore/eterna/save-data-0-1/menu-owner-flow/valid.json']
    evidence = {}
    for name in required:
        path = args.reports / name
        report = json.loads(path.read_text())
        assert report['status'].startswith('PASS') and report['elf_sha256'] == digest, name
        assert not report.get('faults') and not report.get('error'), name
        evidence[name] = sha(path.read_bytes())
    callback = json.loads((args.reports / 'callbacks.json').read_text())
    assert len(callback['cases']) == 24 and callback['full_ordinary_elf'] is True
    for original in [False, True]:
        name = 'dispatch-original.json' if original else 'dispatch-fixed.json'
        report = json.loads((args.reports / name).read_text())
        assert report['original_stack_control'] == original
        assert all(int(sp, 0) % 8 == (4 if original else 0) for sp in report['callback_sp'])
    if 'xpp_menu_setup_options' in symbols:
        owner = json.loads((args.reports / required[-1]).read_text())['native_save_data_menu_owner']
        assert owner['supplied_ui_mode'] == 3 and owner['host_menu_open_writes'] == 0
        assert owner['native_file_requests_while_menu_open'] == []
        assert len(owner['native_file_requests_after_close']) == 1
        assert owner['failed_after_close']['failed'] == 3 and owner['failed_after_close']['completed'] == 0
        assert owner['initial_film'] == owner['final_film'] == 32
    result = dict(scope=__doc__, status='PASS', elf_sha256=digest,
        reproduced=repeated, delivery_words=word_count, source_count=len(receipt['source_sha256']),
        regions=manifest['regions'], exact_elf_native_reports=evidence,
        artifact_checker_sha256=sha(Path(card_check.__file__).read_bytes()),
        artifact_checker_output_adapter_sha256=sha(card_source.encode()),
        checker_sha256=sha(Path(__file__).read_bytes()),
        adapter_sha256=sha(Path(__file__).with_name('verify_full_storage_guard.py').read_bytes()),
        accepted=False, hardware_verified=False)
    (args.reports / 'delivery.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status='PASS', elf=digest, reports=len(required), reproduced=repeated)))


if __name__ == '__main__':
    main()
