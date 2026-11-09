"""Connect existing card-films to the ordinary X-T2 build, without a new loader.

AI-assisted original glue. Research candidate only: the immutable context
processing adapter deliberately declines card-recipe pointers. Card-menu/file
integration is not mutable processing or camera admission. Metadata overrides
are temporary; frozen prior candidates and sources remain intact.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from build_modular_candidate import ROOT,VENDOR,LIBS,sha
from prepare_film_parser import prepare as prepare_parser

INPUTS=ROOT/'card-films-inputs'
BASE=ROOT/'timer-build-unverified'
COMPONENT=ROOT/'film-loader-component-unverified'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'card-films-build-unverified')
    p.add_argument('--reservation-target',type=Path)
    a=p.parse_args();out=a.output.resolve();assert out!=BASE.resolve()
    assert sha((BASE/'mods.elf').read_bytes())=='06ab09771172acde5d7e330066ad4f8679083a751767f80701d225ee5e43b85d'
    prior=json.loads((COMPONENT/'build.json').read_text())
    for name,digest in prior['dependencies'].items():assert sha(Path(name).read_bytes())==digest,name
    INPUTS.mkdir(exist_ok=True)
    def copy(source,name):
        dest=INPUTS/name;dest.write_bytes(source.read_bytes());return dest
    for source,name in [
        (ROOT/'context-films-inputs/processing.c','processing.c'),
        (ROOT/'context-films-inputs/gain.generated.h','gain.generated.h'),
        (ROOT/'six-films-inputs/films.generated.c','films.generated.c'),
        (LIBS/'films/xt20/include/film_xt20.h','film_xt20.h'),
        (LIBS/'films/xt20/include/film_gen.h','film_gen.h'),
        (LIBS/'films/include/film_sims.h','film_sims.h'),
        (COMPONENT/'post.c','post.c')]:copy(source,name)
    changes={}
    for name in ['choice','cards']:
        source=LIBS/f'films/xpp/{name}.c';text=source.read_text()
        old='#define FILM 0x1d4u';assert text.count(old)==1
        text=text.replace(old,'#define FILM 0x1fcu')
        (INPUTS/f'{name}.c').write_text(text);changes[str(source)]=sha(source.read_bytes())
    binding=(ROOT/'six-films-inputs/film_binding.c').read_text()
    assert binding.count('#define EXTRA 6')==1
    (INPUTS/'film_binding.c').write_text(binding.replace('#define EXTRA 6','#define EXTRA 16'))
    bridge=(ROOT/'six-films-inputs/menu_bridge.c').read_text()
    assert bridge.count('XPP_MENU_TEXT(eterna_text,')==1
    (INPUTS/'menu_bridge.c').write_text(bridge.split('XPP_MENU_TEXT(eterna_text,')[0])
    parser=prepare_parser(LIBS/'film-storage/film_parse.c',INPUTS/'parser')
    cardmod=INPUTS/'card-films';cardmod.mkdir(exist_ok=True)
    (cardmod/'mod.json').write_text(json.dumps(dict(name='card-films',targets=['xt2-441'],
        sources=[os.path.relpath(VENDOR/'decomp/mods/card-films/xpp/register.c',cardmod)],
        libs=['film-storage'],description='Existing card-films integration; mutable processing remains unqualified.'),indent=2)+'\n')
    paths=[LIBS/n/'lib.json' for n in ['films/xt2-441-context','menu-stock-choices/xt2-441-six',
        'film-storage','menu/xt2-441','settings/xt2-441','cardio','lifetime','libc/xt2-441']]
    target=VENDOR/'decomp/mods/targets/xt2-441.json';paths.append(target)
    originals={path:path.read_bytes() for path in paths};metadata={}
    def modify(name,fn):
        path=LIBS/name/'lib.json';spec=json.loads(originals[path]);fn(spec,path.parent)
        metadata[path]=spec
    rel=lambda base,path:os.path.relpath(path,base)
    def films(spec,base):
        sources=[INPUTS/n for n in ['processing.c','films.generated.c','choice.c','cards.c','film_binding.c']]
        sources += [LIBS/'films'/n for n in ['film_user_table.c','xpp/film_labels.generated.c','xpp/film_sources.generated.c']]
        spec['sources']=[rel(base,s) for s in sources];spec['xpp']['include']=rel(base,INPUTS)
    modify('films/xt2-441-context',films)
    def menus(spec,base):
        old=rel(base,ROOT/'six-films-inputs/menu_bridge.c');assert old in spec['sources']
        spec['sources']=[rel(base,INPUTS/'menu_bridge.c') if s==old else s for s in spec['sources']]
    modify('menu-stock-choices/xt2-441-six',menus)
    def storage(spec,base):
        spec['sources']=['film_loader.c',rel(base,parser)]
        spec['libs']=['films/xt2-441-context','cardio','settings/xt2-441','lifetime']
        spec['xpp']=dict(sources=spec['sources'],libs=spec['libs'])
    modify('film-storage',storage)
    def ui(spec,base):spec['sources']=[rel(base,INPUTS/'post.c'),rel(base,LIBS/'menu/xpp/input.c')]
    modify('menu/xt2-441',ui)
    def settings(spec,base):spec['sources'].append(rel(base,LIBS/'settings/generated/film.c'))
    modify('settings/xt2-441',settings)
    def cardio(spec,base):spec['xpp']['sources']=[rel(base,COMPONENT/'cardio/cardio.c')]
    modify('cardio',cardio)
    def lifetime(spec,base):
        assert spec['xpp']['sources']==['lifetime.c','timer.c']
        spec['xpp']['sources'][1]=rel(base,ROOT/'timer-inputs/timer.c')
    modify('lifetime',lifetime)
    def libc(spec,base):spec['sources']=[rel(base,ROOT/'aeabi_loader_memory.c')]
    modify('libc/xt2-441',libc)
    native=json.loads((a.reservation_target or BASE/'target.json').read_text())
    native['symbols'].update(storage_media_ready=0x967490,storage_media_queue=0x9c3544,
        storage_send_request_packet=0x969f24,dispatch_current_task=0xceed8c,
        ui_next_event=0x14da7ac,ui_post_message=0xcf8da8,
        ui_screen_request=0x22e7364,ui_screen_request_send=0x15ca508)
    sys.path[:0]=[str(VENDOR),str(VENDOR/'decomp/tools')]
    import mod,mod_xpp
    from tools.sd_boot.xpp_mods import compose_card
    directories=[ROOT/'context-films-inputs'/n for n in ['film-sims','noise-reduction']]
    directories += [ROOT/'jpeg-max-inputs/jpeg-max',cardmod]
    run_original=mod_xpp._run
    def run_with_link_evidence(command,cwd):
        try:return run_original(command,cwd)
        except ValueError as error:
            if Path(command[0]).name.endswith('-ld'):
                # Save evidence before upstream removes its temporary directory.
                # Preserve the failure and all region/undefined-symbol checks.
                out.mkdir(parents=True,exist_ok=True)
                for name in ['mods.map','mods.ld']:
                    source=Path(cwd)/name
                    if source.exists():(out/('failed-'+name)).write_bytes(source.read_bytes())
                (out/'link-failure.json').write_text(json.dumps(dict(
                    status='FAILED',error=str(error),scope=__doc__,hardware_verified=False),indent=2)+'\n')
            raise
    try:
        mod_xpp._run=run_with_link_evidence
        for path,spec in metadata.items():path.write_text(json.dumps(spec,indent=2)+'\n')
        target.write_text(json.dumps(native,indent=2)+'\n')
        specs=[json.loads((d/'mod.json').read_text()) for d in directories]
        libs=mod_xpp.resolve_libraries(specs,'xt2-441')
        sources=[(LIBS/name/s).resolve() for name,spec in libs.items() for s in spec['sources']]
        sources += [(d/s).resolve() for d,spec in zip(directories,specs) for s in spec['sources']]
        assert len(sources)==len(set(sources))
        receipt=dict(scope=__doc__,source_sha256={str(s):sha(s.read_bytes()) for s in sources},
            metadata={str(p):s for p,s in metadata.items()},libraries=list(libs),
            generator_sha256=sha(Path(__file__).read_bytes()),target=native,
            card_processing_supported=False,hardware_verified=False)
        (INPUTS/'build-preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps(dict(stage='resolved',sources=len(sources),libraries=len(libs),mods=[s['name'] for s in specs])),flush=True)
        result=mod.build_xpp_mods(list(map(str,directories)),out,'xt2-441','reserved-native-prefix')
        (out/'preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
        assert all(r['available'] for r in result['availability'])
        (out/'target.json').write_bytes(target.read_bytes())
        roots={f'lib-{name}':str(LIBS/name) for name in libs}|{s['name']:str(d) for s,d in zip(specs,directories)}
        (out/'source-roots.json').write_text(json.dumps(roots,indent=2)+'\n')
        card=compose_card('xt2-441',out,Path(str(out)+'-card'))
        print(json.dumps(dict(elf_sha256=sha((out/'mods.elf').read_bytes()),regions=result['regions'],
            words=len(result['words']),accepted=card['accepted'],card_processing_supported=False)))
    finally:
        mod_xpp._run=run_original
        for path,data in originals.items():path.write_bytes(data)


if __name__=='__main__':main()
