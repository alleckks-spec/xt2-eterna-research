"""Compose completed WB, volatile USB and qualified dual-slot date-folders layers.

Inputs are existing qualified receipts, not regenerated derivatives. Every
shared source, library metadata and target field must agree. Symbols form a
conflict-checked union. The ordinary builder retains hook/preimage/SD conflict
checks and restores shared metadata even when a build fails. No camera access.
"""
import argparse
import copy
import json
import sys
from pathlib import Path
from build_modular_candidate import ROOT, VENDOR, LIBS, sha

BASE = ROOT / 'save-data-menu-native-build-unverified'
WB = ROOT / 'wb-usb-build-unverified'
USB = ROOT / 'date-folders-dual-stable-build-unverified'
BUILD = ROOT / 'wb-usb-date-build-unverified'


def merge(into, extra):
    for key, value in extra.items():
        assert key not in into or into[key] == value, ('conflicting owner', key)
        into[key] = copy.deepcopy(value)


def build(output):
    output = Path(output).resolve()
    assert not output.exists() and not Path(str(output) + '-card').exists()
    receipts = [json.loads((p / 'preparation.json').read_text()) for p in [BASE, WB, USB]]
    assert sha((BASE/'mods.elf').read_bytes()) == '892f6d3b5cafb9ac86c4f32e9a625220d58593a7b2c7c6310fcf739c46fe482e'
    assert sha((WB/'mods.elf').read_bytes()) == 'c4e87e6dff6031c9e67e1caec317480e52796ebc07acd3ea7bbeef0aa30d6353'
    assert sha((USB/'mods.elf').read_bytes()) == '0cbd4cb60b86c984a09c2809ef7faf265fe4a29eebd97bc36ac3ba6db79f0d87'
    frozen = json.loads((ROOT/'date-folders-dual-stable-qualified-final-unverified/freeze.json').read_text())
    for path, digest in frozen['files'].items(): assert sha(Path(path).read_bytes()) == digest, path
    metadata, expected, directories = {}, {}, []
    native = json.loads((BASE/'target.json').read_text())
    parents = {}
    for directory, receipt in zip([BASE, WB, USB], receipts):
        digest = sha((directory/'mods.elf').read_bytes())
        assert receipt['elf_sha256'] == digest
        parents[str(directory)] = dict(elf_sha256=digest, receipt_sha256=sha((directory/'preparation.json').read_bytes()))
        merge(metadata, receipt['metadata']); merge(expected, receipt['source_sha256'])
        for path in receipt['mod_directories']:
            if path not in directories: directories.append(path)
        target = json.loads((directory/'target.json').read_text())
        assert {k:v for k,v in target.items() if k!='symbols'} == {k:v for k,v in native.items() if k!='symbols'}
        merge(native['symbols'], target['symbols'])
    assert len(directories) == 8 and len(expected) == 42
    for path, digest in expected.items(): assert sha(Path(path).read_bytes()) == digest, path
    target = VENDOR/'decomp/mods/targets/xt2-441.json'
    metadata = {Path(path): spec for path,spec in metadata.items()}
    originals = {p:p.read_bytes() if p.exists() else None for p in [*metadata,target]}
    sys.path[:0] = [str(VENDOR), str(VENDOR/'decomp/tools')]
    import mod, mod_xpp
    from tools.sd_boot.xpp_mods import compose_card
    try:
        for path,spec in metadata.items(): path.write_text(json.dumps(spec,indent=2)+'\n')
        target.write_text(json.dumps(native,indent=2)+'\n')
        specs = [json.loads((Path(path)/'mod.json').read_text()) for path in directories]
        assert len({s['name'] for s in specs}) == len(specs)
        libraries = mod_xpp.resolve_libraries(specs,'xt2-441')
        sources = [(LIBS/name/f).resolve() for name,spec in libraries.items() for f in spec['sources']]
        sources += [(Path(d)/f).resolve() for d,s in zip(directories,specs) for f in s['sources']]
        assert len(sources) == len(set(sources)) == 42 and len(libraries) == 14
        assert {str(p):sha(p.read_bytes()) for p in sources} == expected
        result = mod.build_xpp_mods(directories,output,'xt2-441','reserved-native-prefix')
        assert all(row['available'] for row in result['availability']) and len(result['words']) == 81
        roots = {f'lib-{name}':str(LIBS/name) for name in libraries}
        roots.update({s['name']:d for s,d in zip(specs,directories)})
        (output/'source-roots.json').write_text(json.dumps(roots,indent=2)+'\n')
        (output/'target.json').write_bytes(target.read_bytes())
        receipt = dict(scope=__doc__,adaptation=receipts[1]['adaptation'],usb_adaptation=receipts[1]['usb_adaptation'],date_adaptation=receipts[2]['adaptation'],
            metadata={str(p):s for p,s in metadata.items()},source_sha256=expected,
            elf_sha256=sha((output/'mods.elf').read_bytes()),base_elf_sha256=receipts[0]['elf_sha256'],
            generator_sha256=sha(Path(__file__).read_bytes()),mod_directories=directories,parent_receipts=parents,
            shared_owners_unique=True,target_conflicts=False,physical_persistence_qualified=False)
        (output/'preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
        card = compose_card('xt2-441',output,Path(str(output)+'-card'))
    finally:
        for path,data in originals.items():
            if data is None: path.unlink(missing_ok=True)
            else: path.write_bytes(data)
    print(json.dumps(dict(elf_sha256=receipt['elf_sha256'],sources=len(sources),libraries=len(libraries),
        words=len(result['words']),regions=result['regions'],accepted=card['accepted'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=BUILD)
    build(parser.parse_args().output)
