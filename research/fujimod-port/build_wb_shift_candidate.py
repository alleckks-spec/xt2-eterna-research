"""Add the existing custom-WB pair mod to the pinned native-menu composition.

No new service or format. All prior 37 sources and the memory reservation stay
pinned; linker/preimage/conflict checks remain those of the ordinary builder.
This six-mod candidate is separate from other compatibility configurations.
"""
import argparse
import copy
import json
import sys
from pathlib import Path
from build_modular_candidate import ROOT, VENDOR, LIBS, sha
from prepare_wb_shift_candidate import prepare, BASE

BUILD = ROOT / 'wb-shift-coherent-build-unverified'


def build(output):
    output = Path(output).resolve()
    assert not output.exists() and not Path(str(output) + '-card').exists()
    directory, adaptation = prepare()
    base = json.loads((BASE / 'preparation.json').read_text())
    metadata = {Path(path): copy.deepcopy(spec) for path, spec in base['metadata'].items()}
    for path, digest in base['source_sha256'].items():
        assert sha(Path(path).read_bytes()) == digest, path
    target = VENDOR / 'decomp/mods/targets/xt2-441.json'
    native = json.loads((BASE / 'target.json').read_text())
    for name, address in adaptation['symbols'].items():
        assert name not in native['symbols'] or native['symbols'][name] == address, name
        native['symbols'][name] = address
    directories = [*map(Path, base['mod_directories']), directory]
    originals = {path: path.read_bytes() if path.exists() else None for path in [*metadata, target]}
    sys.path[:0] = [str(VENDOR), str(VENDOR / 'decomp/tools')]
    import mod, mod_xpp
    from tools.sd_boot.xpp_mods import compose_card
    try:
        for path, spec in metadata.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(spec, indent=2) + '\n')
        target.write_text(json.dumps(native, indent=2) + '\n')
        specs = [json.loads((path / 'mod.json').read_text()) for path in directories]
        libraries = mod_xpp.resolve_libraries(specs, 'xt2-441')
        sources = [(LIBS / name / filename).resolve() for name, spec in libraries.items() for filename in spec['sources']]
        sources += [(path / filename).resolve() for path, spec in zip(directories, specs) for filename in spec['sources']]
        assert len(sources) == len(set(sources)) == 38
        expected = dict(base['source_sha256'])
        expected[str((directory / 'wb_shift.c').resolve())] = adaptation['source_sha256']
        assert {str(path): sha(path.read_bytes()) for path in sources} == expected
        result = mod.build_xpp_mods(list(map(str, directories)), output, 'xt2-441', 'reserved-native-prefix')
        assert all(row['available'] for row in result['availability'])
        assert len(result['words']) == 76
        roots = {f'lib-{name}': str(LIBS / name) for name in libraries}
        roots.update({spec['name']: str(path) for spec, path in zip(specs, directories)})
        (output / 'source-roots.json').write_text(json.dumps(roots, indent=2) + '\n')
        (output / 'target.json').write_bytes(target.read_bytes())
        receipt = dict(scope=__doc__, adaptation=adaptation, metadata={str(path): spec for path, spec in metadata.items()},
            source_sha256=expected, elf_sha256=sha((output / 'mods.elf').read_bytes()),
            base_elf_sha256=base['elf_sha256'], generator_sha256=sha(Path(__file__).read_bytes()),
            mod_directories=list(map(str, directories)), physical_persistence_qualified=False)
        (output / 'preparation.json').write_text(json.dumps(receipt, indent=2) + '\n')
        card = compose_card('xt2-441', output, Path(str(output) + '-card'))
    finally:
        for path, data in originals.items():
            if data is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(data)
    print(json.dumps(dict(elf_sha256=receipt['elf_sha256'], sources=len(sources), libraries=len(libraries),
        words=len(result['words']), regions=result['regions'], accepted=card['accepted'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BUILD)
    build(parser.parse_args().output)
