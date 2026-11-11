"""Verify the full timer package delta, exact-ELF evidence and fresh rebuild.

The timer literal lives in native SD code, outside mods.elf. Numeric processing
reports remain evidence for the identical ELF only; they do not qualify timer
scheduling or capture admission. The two new dispatcher reports qualify their
declared production callback/mode0 boundary separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_full_timer_candidate import BASE, BUILD, ROOT
from verify_ordinary_platform_card import main as verify_card


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=BUILD)
    parser.add_argument('--rebuild', type=Path, default=ROOT / 'full-timer-rebuild-unverified')
    parser.add_argument('--output', type=Path, default=ROOT / 'full-timer-check-unverified/package.json')
    args = parser.parse_args()
    verify_card(args.build, 67)
    base_card, card, rebuilt_card = map(lambda path: Path(str(path) + '-card'), [BASE, args.build, args.rebuild])
    elf = (args.build / 'mods.elf').read_bytes()
    assert elf == (BASE / 'mods.elf').read_bytes() == (args.rebuild / 'mods.elf').read_bytes()
    assert (args.build / 'region.bin').read_bytes() == (BASE / 'region.bin').read_bytes()
    manifest = json.loads((args.build / 'manifest.json').read_text())
    previous = json.loads((BASE / 'manifest.json').read_text())
    added = [row for row in manifest['words'] if row not in previous['words']]
    assert len(added) == 1 and all(row in manifest['words'] for row in previous['words'])
    assert int(added[0]['address'], 0) == 0xcdfb04
    assert int(added[0]['old'], 0) == 0x1188000 and int(added[0]['new'], 0) == 0x1187ffc
    original = bytearray((base_card / 'ffboot.bin').read_bytes())
    assert int.from_bytes(original[0xcdfb04:0xcdfb08], 'little') == 0x1188000
    original[0xcdfb04:0xcdfb08] = (0x1187ffc).to_bytes(4, 'little')
    assert original == (card / 'ffboot.bin').read_bytes()
    assert (base_card / 'ffsys.bin').read_bytes() == (card / 'ffsys.bin').read_bytes()
    reproduced = {}
    for directory, other, names in [(args.build, args.rebuild, ['mods.elf', 'region.bin']),
                                    (card, rebuilt_card, ['ffboot.bin', 'ffsys.bin'])]:
        for name in names:
            data = (directory / name).read_bytes()
            assert data == (other / name).read_bytes(), name
            reproduced[name] = dict(bytes=len(data), sha256=sha(data))
    reports = {}
    for name in ['dispatch-original', 'dispatch-fixed']:
        path = args.output.parent / (name + '.json')
        report = json.loads(path.read_text())
        assert report['status'] == 'PASS' and report['elf_sha256'] == sha(elf)
        assert report['original_stack_control'] == (name == 'dispatch-original')
        reports[str(path)] = sha(path.read_bytes())
    inherited = {}
    for relative in ['card-processing-check-unverified/verification.json',
                     'card-processing-regressions-unverified/nr/verification.json',
                     'card-processing-regressions-unverified/jpeg/verification.json',
                     'card-still-native-check-unverified/verification.json']:
        path = ROOT / relative
        report = json.loads(path.read_text())
        assert report['elf_sha256'] == sha(elf), path
        inherited[str(path)] = sha(path.read_bytes())
    region, = manifest['regions']
    native = json.loads((args.build / 'target.json').read_text())
    assert native['card_regions'] == json.loads((BASE / 'target.json').read_text())['card_regions']
    receipt = json.loads((args.build / 'preparation.json').read_text())
    assert receipt['source_sha256'] == json.loads((BASE / 'preparation.json').read_text())['source_sha256']
    result = dict(scope=__doc__, status='PASS', elf_sha256=sha(elf),
        reproduced=reproduced, old_elf_and_region_byte_equal=True, native_sd_delta_words=1,
        native_sd_delta_address=hex(0xcdfb04), delivery_words=67,
        exact_elf_reports_reused=inherited, new_dispatch_reports=reports,
        source_count=len(receipt['source_sha256']), unchanged_region=region,
        unchanged_reservation=True, accepted=False, hardware_verified=False,
        checker_sha256=sha(Path(__file__).read_bytes()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
