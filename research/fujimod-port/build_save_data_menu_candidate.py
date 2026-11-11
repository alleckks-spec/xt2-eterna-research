"""Build the existing XPP SAVE DATA item engine on the five-mod X-T2 candidate.

Replace the prior stock-choice-only bridge with the selected upstream item
closure, retaining its one owner per hook. All other sources and services stay
pinned; target and library metadata are temporary and restored. AI-assisted.
"""
import argparse
import copy
import json
import os
import shutil
import sys
from pathlib import Path
from build_modular_candidate import ROOT,VENDOR,LIBS,sha
from prepare_save_data_menu import prepare,INPUTS

BASE=ROOT/'volume-name-rebuild-unverified'
BUILD=ROOT/'save-data-menu-build-unverified'


def build(output):
    output=Path(output).resolve()
    assert not output.exists() and not Path(str(output)+'-card').exists()
    adaptation=prepare()
    base=json.loads((BASE/'preparation.json').read_text())
    assert sha((BASE/'mods.elf').read_bytes())=='58eab0e9177c61d00b689b4bd08ae3c52cb7215975266f7bc93d6462d0c3affa'
    metadata={Path(p):copy.deepcopy(s) for p,s in base['metadata'].items()}
    replacements={ROOT/'card-films-inputs/menu_bridge.c':INPUTS/'menu_entries.c',ROOT/'caption_bridge.c':INPUTS/'caption_bridge.c'}
    found=[]
    for path,spec in metadata.items():
        for i,source in enumerate(spec.get('sources',[])):
            original=(path.parent/source).resolve()
            if original in replacements:
                spec['sources'][i]=os.path.relpath(replacements[original],path.parent);found.append(original)
    assert set(found)==set(replacements) and len(found)==2
    for source,digest in base['source_sha256'].items():assert sha(Path(source).read_bytes())==digest,source
    target=VENDOR/'decomp/mods/targets/xt2-441.json'
    native=json.loads((BASE/'target.json').read_text());native['symbols'].update(adaptation['symbols'])
    directories=list(map(Path,base['mod_directories']))
    originals={p:p.read_bytes() if p.exists() else None for p in [*metadata,target]}
    sys.path[:0]=[str(VENDOR),str(VENDOR/'decomp/tools')]
    import mod,mod_xpp
    from tools.sd_boot.xpp_mods import compose_card
    original_run=mod_xpp._run
    def retain_failed_map(command,work):
        try:return original_run(command,work)
        except ValueError:
            for name in ['mods.map','mods.ld']:
                if (Path(work)/name).exists():shutil.copyfile(Path(work)/name,output/('failed-'+name))
            raise
    try:
        for path,spec in metadata.items():path.write_text(json.dumps(spec,indent=2)+'\n')
        target.write_text(json.dumps(native,indent=2)+'\n')
        specs=[json.loads((d/'mod.json').read_text()) for d in directories]
        libraries=mod_xpp.resolve_libraries(specs,'xt2-441')
        sources=[(LIBS/n/s).resolve() for n,spec in libraries.items() for s in spec['sources']]
        sources += [(d/s).resolve() for d,spec in zip(directories,specs) for s in spec['sources']]
        assert len(sources)==len(set(sources))==37
        assert set(map(str,sources))==(set(base['source_sha256'])-set(map(str,replacements)))|set(map(str,replacements.values()))
        mod_xpp._run=retain_failed_map
        result=mod.build_xpp_mods(list(map(str,directories)),output,'xt2-441','reserved-native-prefix')
        assert all(row['available'] for row in result['availability'])
        assert len(result['words'])==72
        roots={f'lib-{n}':str(LIBS/n) for n in libraries}|{s['name']:str(d) for s,d in zip(specs,directories)}
        (output/'source-roots.json').write_text(json.dumps(roots,indent=2)+'\n')
        (output/'target.json').write_bytes(target.read_bytes())
        receipt=dict(scope=__doc__,adaptation=adaptation,metadata={str(p):s for p,s in metadata.items()},
            source_sha256={str(s):sha(s.read_bytes()) for s in sources},
            elf_sha256=sha((output/'mods.elf').read_bytes()),base_elf_sha256=sha((BASE/'mods.elf').read_bytes()),
            generator_sha256=sha(Path(__file__).read_bytes()),mod_directories=list(map(str,directories)))
        (output/'preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
        card=compose_card('xt2-441',output,Path(str(output)+'-card'))
    finally:
        mod_xpp._run=original_run
        for path,data in originals.items():
            if data is None:path.unlink(missing_ok=True)
            else:path.write_bytes(data)
    print(json.dumps(dict(elf_sha256=receipt['elf_sha256'],sources=len(sources),libraries=len(libraries),
        words=len(result['words']),regions=result['regions'],accepted=card['accepted'])))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=BUILD)
    build(parser.parse_args().output)
