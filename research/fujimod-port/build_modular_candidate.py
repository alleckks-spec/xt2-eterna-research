"""Wire the checked X-T2 slice through ordinary mod/library dependencies.

Intermediate immutable-film + NR scope only. Reuses upstream libc/lifetime/cardio
unchanged, with target-specific metadata for already adapted source selections.
No new loader, service, firmware feature or camera qualification. AI-assisted.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from build_ordinary_platform_candidate import prepare, ROOT, VENDOR, sha

STAGE=ROOT/'modular-inputs'
LIBS=VENDOR/'decomp/mods/lib'
GENERATOR=Path(__file__).name


def relative(base,path):
    return os.path.relpath(path,base)


def library(name,sources,dependencies,interface):
    directory=LIBS/name
    directory.mkdir(parents=True,exist_ok=True)
    path=directory/'lib.json'
    if path.exists():assert json.loads(path.read_text()).get('port_generator')==GENERATOR,path
    specification=dict(description='X-T2 4.41 selection of existing checked sources; intermediate scope.',
        targets=['xt2-441'],sources=[relative(directory,p) for p in sources],libs=dependencies,
        xpp=dict(include=relative(directory,interface)),port_generator=GENERATOR)
    path.write_text(json.dumps(specification,indent=2)+'\n')
    return path


def prepare_modules():
    prepare()  # existing target, native bindings and reservation; no compilation
    STAGE.mkdir(exist_ok=True)
    created=[]
    def lib(name,sources,deps,interface):
        created.append(library(name,sources,deps,interface))
    lib('libc/xt2-441',[ROOT/'aeabi_memory.c'],['libc'],LIBS/'libc/include')
    lib('settings/xt2-441',[LIBS/'settings'/p for p in
        ['settings.c','json.c','generated/stock_choice_storage.generated.c']],
        ['cardio','libc/xt2-441','lifetime'],LIBS/'settings/include')
    lib('xpp-settings/xt2-441',[ROOT/'reserved-gnu-candidate-unverified/start.c'],
        ['settings/xt2-441','xpp-hook'],LIBS/'xpp-settings/include')
    lib('resources/xt2-441',[],[],LIBS/'resources/include')
    lib('menu/xt2-441',[],['xpp-hook'],LIBS/'menu/xpp/include')
    lib('menu-stock-choices/xt2-441',[
        ROOT/'reserved-gnu-candidate-unverified/stock_rows.c',
        LIBS/'menu-stock-choices/stock_choices.c',ROOT/'menu_bridge.c',ROOT/'caption_bridge.c'],
        ['settings/xt2-441','xpp-settings/xt2-441','xpp-hook','resources/xt2-441','menu/xt2-441'],
        LIBS/'menu-stock-choices/include')
    lib('films/xt2-441',[ROOT/p for p in ['generated/processing.c','generated/films.generated.c',
        'menu-generated/film_choice.c','menu-generated/film_binding.c']],
        ['menu-stock-choices/xt2-441'],ROOT/'generated')
    selections={
        'film-sims':dict(sources=[ROOT/'native_services_enrollment.c'],libs=['films/xt2-441']),
        'noise-reduction':dict(sources=[ROOT/'nr-candidate-unverified'/p for p in
            ['noise_reduction.c','noise_binding.c']],libs=['menu-stock-choices/xt2-441']),
    }
    directories=[]
    for name,spec in selections.items():
        directory=STAGE/name;directory.mkdir(exist_ok=True)
        path=directory/'mod.json'
        path.write_text(json.dumps(dict(name=name,targets=['xt2-441'],
            sources=[relative(directory,p) for p in spec['sources']],libs=spec['libs'],
            description='Existing checked X-T2 adaptation, intermediate immutable-film/NR scope.'),indent=2)+'\n')
        directories.append(directory);created.append(path)
    sys.path[:0]=[str(VENDOR),str(VENDOR/'decomp/tools')]
    import mod_xpp
    specs=[json.loads((p/'mod.json').read_text()) for p in directories]
    libraries=mod_xpp.resolve_libraries(specs,'xt2-441')
    roots={f'lib-{name}':str(LIBS/name) for name in libraries}
    roots.update({name:str(directory) for name,directory in zip(selections,directories)})
    sources=[]
    for name,libspec in libraries.items():
        sources += [(LIBS/name/p).resolve() for p in libspec['sources']]
    for directory,spec in zip(directories,specs):
        sources += [(directory/p).resolve() for p in spec['sources']]
    checked=json.loads((ROOT/'reserved-gnu-candidate-unverified/build.json').read_text())
    expected={(ROOT/p).resolve() for p in checked['source_sha256'] if Path(p).suffix in ('.c','.S')}
    assert len(sources)==len(set(sources))==21,(len(sources),len(set(sources)))
    assert set(sources)==expected,dict(extra=list(map(str,set(sources)-expected)),missing=list(map(str,expected-set(sources))))
    receipt=dict(scope=__doc__,mod_directories=list(map(str,directories)),source_roots=roots,
        libraries=list(libraries),sources={str(p):sha(p.read_bytes()) for p in sources},
        metadata={str(p):sha(p.read_bytes()) for p in created} |
            {str(LIBS/name/'lib.json'):sha((LIBS/name/'lib.json').read_bytes()) for name in libraries},
        generator_sha256=sha(Path(__file__).read_bytes()),camera_verified=False)
    (STAGE/'preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return directories,roots


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'modular-build-unverified')
    args=parser.parse_args()
    directories,roots=prepare_modules()
    if args.prepare_only:
        print('Resolved two mods and ordinary shared dependencies; exactly21 checked C sources, no duplicates.')
        return
    import mod
    from tools.sd_boot.xpp_mods import compose_card
    result=mod.build_xpp_mods(list(map(str,directories)),args.output,'xt2-441','reserved-native-prefix')
    assert all(row['available'] for row in result['availability'])
    (args.output/'source-roots.json').write_text(json.dumps(roots,indent=2)+'\n')
    card=compose_card('xt2-441',args.output,Path(str(args.output)+'-card'))
    print(json.dumps(dict(mods=result['mods'],card=card['files'],accepted=card['accepted'])))


if __name__=='__main__':main()
