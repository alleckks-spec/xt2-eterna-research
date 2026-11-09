"""Rebuild the same ordinary four mods with two guarded native API bindings.

AI-assisted original glue. Reuse the frozen33-source selections and reservation.
Only two private C derivatives and their header change. Metadata is restored;
this is an unaccepted research image, not complete native-lifetime/camera proof.
"""
import argparse
import copy
import json
import os
import sys
from pathlib import Path
from build_modular_candidate import ROOT,VENDOR,LIBS,sha
from prepare_card_processing import prepare,BASE,INPUTS


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'card-processing-build-unverified');a=p.parse_args()
    assert sha((BASE/'mods.elf').read_bytes())=='db56c69c993a30e9fbdfb024ad766e005234b50f76684082b29683a526dd3754'
    adaptation=prepare();base=json.loads((BASE/'preparation.json').read_text())
    metadata={Path(path):copy.deepcopy(spec) for path,spec in base['metadata'].items()}
    variant=LIBS/'films/xt2-441-context/lib.json'
    for name in ['processing.c','cards.c']:
        old=os.path.relpath(ROOT/'card-films-inputs'/name,variant.parent)
        assert metadata[variant]['sources'].count(old)==1
        metadata[variant]['sources']=[os.path.relpath(INPUTS/name,variant.parent) if s==old else s for s in metadata[variant]['sources']]
    target=VENDOR/'decomp/mods/targets/xt2-441.json'
    native=json.loads((BASE/'target.json').read_text());native['symbols'].update(adaptation['target_symbols'])
    originals={path:path.read_bytes() for path in [*metadata,target]}
    directories=[ROOT/'context-films-inputs'/n for n in ['film-sims','noise-reduction']]
    directories += [ROOT/'jpeg-max-inputs/jpeg-max',ROOT/'card-films-inputs/card-films']
    sys.path[:0]=[str(VENDOR),str(VENDOR/'decomp/tools')]
    import mod,mod_xpp
    from tools.sd_boot.xpp_mods import compose_card
    try:
        for path,spec in metadata.items():path.write_text(json.dumps(spec,indent=2)+'\n')
        target.write_text(json.dumps(native,indent=2)+'\n')
        specs=[json.loads((d/'mod.json').read_text()) for d in directories]
        libs=mod_xpp.resolve_libraries(specs,'xt2-441')
        sources=[(LIBS/name/s).resolve() for name,spec in libs.items() for s in spec['sources']]
        sources += [(d/s).resolve() for d,spec in zip(directories,specs) for s in spec['sources']]
        assert len(sources)==len(set(sources))==33 and len(libs)==14
        changed={str((ROOT/'card-films-inputs'/n).resolve()):str((INPUTS/n).resolve()) for n in ['processing.c','cards.c']}
        assert set(map(str,sources))==(set(base['source_sha256'])-set(changed))|set(changed.values())
        for source in sources:
            if str(source) in base['source_sha256']:assert sha(source.read_bytes())==base['source_sha256'][str(source)],source
        print(json.dumps(dict(stage='resolved',sources=33,libraries=14)),flush=True)
        result=mod.build_xpp_mods(list(map(str,directories)),a.output,'xt2-441','reserved-native-prefix')
        assert all(r['available'] for r in result['availability'])
        roots={f'lib-{name}':str(LIBS/name) for name in libs}|{spec['name']:str(d) for spec,d in zip(specs,directories)}
        (a.output/'source-roots.json').write_text(json.dumps(roots,indent=2)+'\n')
        (a.output/'target.json').write_bytes(target.read_bytes())
        receipt=dict(scope=__doc__,source_sha256={str(s):sha(s.read_bytes()) for s in sources},
            metadata={str(path):spec for path,spec in metadata.items()},adaptation=adaptation,
            generator_sha256=sha(Path(__file__).read_bytes()),elf_sha256=sha((a.output/'mods.elf').read_bytes()),
            card_recipe_reads_enabled=True,hardware_verified=False)
        (a.output/'preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
        card=compose_card('xt2-441',a.output,Path(str(a.output)+'-card'))
        print(json.dumps(dict(elf_sha256=receipt['elf_sha256'],regions=result['regions'],words=len(result['words']),accepted=card['accepted'])))
    finally:
        for path,data in originals.items():path.write_bytes(data)


if __name__=='__main__':main()
