"""Exact WB composition: delivered memory edits and related report pins.

Reuse the existing native BSS/heap/map-argument checker with this artifact's
reservation. Actual map installation, full boot and physical NAND/SD remain
outside these bounded checks. Numeric and native reports are validated only
for this exact ELF; older artifact reports are not transferred.
"""
import argparse
import inspect
import json
from pathlib import Path
import verify_minimal_memory as memory
import verify_full_storage_guard as fixture

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT / 'wb-shift-coherent-build-unverified')
    parser.add_argument('--output', type=Path, default=ROOT / 'wb-shift-coherent-check-unverified')
    args = parser.parse_args(); args.output.mkdir(exist_ok=True)
    fixture.BUILD = args.build
    def machine():
        (u, symbols, call, api, clock, exceptions), setup = fixture.fixture_machine(False)
        return (u, symbols, call, clock, exceptions), setup
    manifest = json.loads((args.build / 'manifest.json').read_text())
    target = json.loads((args.build / 'target.json').read_text())
    base_target = json.loads((ROOT / 'save-data-menu-native-build-unverified/target.json').read_text())
    assert target['card_regions'] == base_target['card_regions']
    assert target['card_words'] == base_target['card_words']
    region, = manifest['regions']; start = int(region['address'], 0)
    assert start == 0x1380000 and region['size'] == 246144 and len(manifest['words']) == 76
    source = inspect.getsource(memory.main)
    namespace = dict(vars(memory), machine=machine, BUILD=args.build, OUT=args.output,
        START=start, END=0x13c0000)
    source = source.replace('def main():', 'def verify_memory():', 1)
    exec(compile(source, str(Path(memory.__file__)) + '::exact-wb-reservation', 'exec'), namespace)
    namespace['verify_memory']()
    sha = fixture.sha; digest = sha((args.build / 'mods.elf').read_bytes())
    pins = {}
    functional = json.loads((args.output / 'functional.json').read_text())
    assert functional['status'] == 'PASS' and functional['elf_sha256'] == digest
    assert len(functional['cases']) == 84 and len(functional['guard_cases']) == 2 and len(functional['reset_cases']) == 7
    imported = json.loads((args.output / 'import-fixed.json').read_text())
    assert imported['status'] == 'PASS' and imported['elf_sha256'] == digest and len(imported['cases']) == 6
    assert imported['primary_and_shadow_marker_coherent'] is True
    assert all(row['native_bank_cancel_markers'] == [0] * 7 for row in imported['cases'])
    control_path = ROOT / 'wb-shift-check-unverified/import-primary-only-control.json'
    control = json.loads(control_path.read_text())
    assert control['expected_stale_shadow_control'] and control['old_marker_reactivated_by_bank_cancel']
    assert all(row['native_bank_cancel_markers'] == [0xa5] * 7 for row in control['cases'])
    for path in [args.output / 'functional.json', args.output / 'import-fixed.json', control_path,
                 ROOT / 'wb-shift-coherent-menu-check-unverified/verification.json',
                 ROOT / 'wb-shift-coherent-dependencies-unverified/verification.json']:
        record = json.loads(path.read_text())
        if path != control_path:
            assert record['elf_sha256'] == digest
        pins[str(path)] = sha(path.read_bytes())
    numeric = ROOT / 'wb-shift-coherent-regressions-unverified'
    films, nr, jpeg = [json.loads((numeric / name / 'verification.json').read_text()) for name in ['films', 'nr', 'jpeg']]
    assert all(record['elf_sha256'] == digest for record in [films, nr, jpeg])
    assert len(films['records']) == 356 and len(films['identity_checks']) == 99
    assert len(nr['register_cases']) == 43 and len(nr['menus']) == 3
    assert len(jpeg['cases']) == 33 and len(jpeg['menus']) == 3
    for name in ['films', 'nr', 'jpeg']:
        path = numeric / name / 'verification.json'; pins[str(path)] = sha(path.read_bytes())
    result = dict(scope=__doc__, status='PASS', elf_sha256=digest,
        checker_sha256=sha(Path(__file__).read_bytes()), original_memory_checker_sha256=sha(Path(memory.__file__).read_bytes()),
        adapted_memory_checker_sha256=sha(source.encode()), related_report_sha256=pins,
        original_reservation_card_words_unchanged=True, reservation_bytes=0x40000,
        actual_payload_bytes=region['size'], spare_reserved_bytes=0x40000 - region['size'],
        full_boot=False, physical_nand=False, hardware_verified=False)
    (args.output / 'integration.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status='PASS', elf=digest, related_reports=len(pins), reserved_spare=16000)))


if __name__ == '__main__':
    main()
