"""Rebuild the frozen four-mod X-T2 configuration with its dispatcher stack fix.

Only the native dispatcher literal changes. All 33 C sources and the existing
14-library graph are pinned to the earlier card-processing receipt. Temporary
metadata is restored. This is software evidence, not a complete port or camera
qualification. Upstream analog: Taylor Chapman and Claude, x70view PR #470;
the X-T2 literal and stack effect were independently qualified by the earlier
minimal-candidate dispatcher assay.
"""
import argparse
import copy
import json
import sys
from pathlib import Path
from build_modular_candidate import ROOT, VENDOR, LIBS, sha

BASE = ROOT / 'card-processing-build-unverified'
BUILD = ROOT / 'full-timer-build-unverified'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BUILD)
    args = parser.parse_args()
    assert sha((BASE / 'mods.elf').read_bytes()) == '208845640d4745ff9384911b2f0f38459f830fa87d29adce7c42674d532e9b69'
    base = json.loads((BASE / 'preparation.json').read_text())
    metadata = {Path(path): copy.deepcopy(spec) for path, spec in base['metadata'].items()}
    for path, digest in base['source_sha256'].items():
        assert sha(Path(path).read_bytes()) == digest, path
    target = VENDOR / 'decomp/mods/targets/xt2-441.json'
    native = json.loads((BASE / 'target.json').read_text())
    stock = (ROOT.parents[1] / 'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    assert sha(stock) == 'fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    assert int.from_bytes(stock[0xcdfb04:0xcdfb08], 'little') == 0x1188000
    assert all((int(row['address'], 0) if isinstance(row['address'], str) else row['address']) != 0xcdfb04
               for row in native['card_words'])
    native['card_words'].append(dict(name='X-T2 timer callback AAPCS stack alignment',
        address=0xcdfb04, old=0x1188000, new=0x1187ffc))
    directories = [ROOT / 'context-films-inputs' / name for name in ['film-sims', 'noise-reduction']]
    directories += [ROOT / 'jpeg-max-inputs/jpeg-max', ROOT / 'card-films-inputs/card-films']
    originals = {path: path.read_bytes() if path.exists() else None for path in [*metadata, target]}
    sys.path[:0] = [str(VENDOR), str(VENDOR / 'decomp/tools')]
    import mod, mod_xpp
    from tools.sd_boot.xpp_mods import compose_card
    try:
        for path, spec in metadata.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(spec, indent=2) + '\n')
        target.write_text(json.dumps(native, indent=2) + '\n')
        specs = [json.loads((directory / 'mod.json').read_text()) for directory in directories]
        libs = mod_xpp.resolve_libraries(specs, 'xt2-441')
        sources = [(LIBS / name / source).resolve() for name, spec in libs.items() for source in spec['sources']]
        sources += [(directory / source).resolve() for directory, spec in zip(directories, specs) for source in spec['sources']]
        assert len(sources) == len(set(sources)) == 33 and len(libs) == 14
        assert {str(path): sha(path.read_bytes()) for path in sources} == base['source_sha256']
        result = mod.build_xpp_mods(list(map(str, directories)), args.output, 'xt2-441', 'reserved-native-prefix')
        assert all(row['available'] for row in result['availability'])
        assert len(result['words']) == 67
        roots = {f'lib-{name}': str(LIBS / name) for name in libs}
        roots.update({spec['name']: str(directory) for spec, directory in zip(specs, directories)})
        (args.output / 'source-roots.json').write_text(json.dumps(roots, indent=2) + '\n')
        (args.output / 'target.json').write_bytes(target.read_bytes())
        receipt = dict(base, scope=__doc__, metadata={str(path): spec for path, spec in metadata.items()},
            base_elf_sha256=sha((BASE / 'mods.elf').read_bytes()),
            generator_sha256=sha(Path(__file__).read_bytes()),
            elf_sha256=sha((args.output / 'mods.elf').read_bytes()),
            upstream_analog=dict(pr='https://github.com/justjake/x70view/pull/470',
                commit='e007961f2a9ad32b96f1136433f91b4ab2597270'),
            dispatcher_literal=dict(address=0xcdfb04, old=0x1188000, new=0x1187ffc), hardware_verified=False)
        (args.output / 'preparation.json').write_text(json.dumps(receipt, indent=2) + '\n')
        card = compose_card('xt2-441', args.output, Path(str(args.output) + '-card'))
    finally:
        for path, data in originals.items():
            if data is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(data)
    print(json.dumps(dict(elf_sha256=receipt['elf_sha256'], regions=result['regions'],
        words=len(result['words']), accepted=card['accepted'])))


if __name__ == '__main__':
    main()
