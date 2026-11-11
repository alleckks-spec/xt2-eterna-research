"""Replace only cardio with the bounded PR471 recorded-issue backport.

Keep the qualified eight-mod composition and ordinary composer; all41other
source inputs and target memory operands are pinned. Shared metadata is restored.
Native original stuck-job and positive SDK controls gate the replacement.
"""
import argparse
import copy
import json
import os
import sys
from pathlib import Path
from build_modular_candidate import ROOT, VENDOR, LIBS, sha
BASE = ROOT / 'wb-usb-date-build-unverified'
from prepare_cardio_task_issue import prepare

BUILD = ROOT / 'cardio-task-issue-build-unverified'
INPUTS = ROOT / 'cardio-task-issue-inputs'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BUILD)
    args = parser.parse_args()
    base = json.loads((BASE / 'preparation.json').read_text())
    assert sha((BASE / 'mods.elf').read_bytes()) == base['elf_sha256']
    for name, fault in [('cardio-task-contract-original-unverified',True),('cardio-task-contract-positive-unverified',False)]:
        report=json.loads((ROOT/name/'probe.json').read_text())
        assert report['error'] is None and report['elf_sha256']==base['elf_sha256'] and report['negative_media_status_input']==fault
        state=report['contract_result']
        assert state['job_state']==(1 if fault else 2) and state['callbacks']==0
    old = ROOT / 'full-storage-guard-inputs/cardio.c'
    source, adaptation = prepare()
    for path, digest in base['source_sha256'].items():
        assert sha(Path(path).read_bytes()) == digest, path
    metadata = {Path(path): copy.deepcopy(spec) for path, spec in base['metadata'].items()}
    replacements = 0
    for path, spec in metadata.items():
        for selection in [spec, spec.get('xpp', {})]:
            for index, name in enumerate(selection.get('sources', [])):
                if (path.parent / name).resolve() == old.resolve():
                    selection['sources'][index] = os.path.relpath(source, path.parent)
                    replacements += 1
    assert replacements == 1
    target = VENDOR / 'decomp/mods/targets/xt2-441.json'
    native = json.loads((BASE / 'target.json').read_text())
    directories = list(map(Path, base['mod_directories']))
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
        sources = [(LIBS / name / filename).resolve() for name, spec in libs.items() for filename in spec['sources']]
        sources += [(directory / filename).resolve() for directory, spec in zip(directories, specs) for filename in spec['sources']]
        assert len(sources) == len(set(sources)) == 42 and len(libs) == 14
        expected = dict(base['source_sha256'])
        del expected[str(old.resolve())]
        expected[str(source.resolve())] = sha(source.read_bytes())
        assert {str(path): sha(path.read_bytes()) for path in sources} == expected
        result = mod.build_xpp_mods(list(map(str, directories)), args.output, 'xt2-441', 'reserved-native-prefix')
        assert all(row['available'] for row in result['availability'])
        assert len(result['words']) == 81
        roots = {f'lib-{name}': str(LIBS / name) for name in libs}
        roots.update({spec['name']: str(directory) for spec, directory in zip(specs, directories)})
        (args.output / 'source-roots.json').write_text(json.dumps(roots, indent=2) + '\n')
        (args.output / 'target.json').write_bytes(target.read_bytes())
        receipt = dict(base, scope=__doc__, metadata={str(path): spec for path, spec in metadata.items()},
            source_sha256=expected, base_elf_sha256=base['elf_sha256'],
            generator_sha256=sha(Path(__file__).read_bytes()),
            elf_sha256=sha((args.output / 'mods.elf').read_bytes()),
            cardio_task_issue=adaptation, hardware_verified=False)
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
