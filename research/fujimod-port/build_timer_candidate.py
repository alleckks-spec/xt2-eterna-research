"""Rebuild the existing three ordinary X-T2 mods with one corrected timer source.

AI-assisted original builder. Local authorized upstream/generated inputs and
ordinary FujiMod toolchain required. Temporary metadata is restored afterward;
baseline artifacts stay intact. No extra mod/service or hardware acceptance.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from build_modular_candidate import ROOT,VENDOR,LIBS,sha
from prepare_timer_restart import prepare

BASE=ROOT/'jpeg-max-build-unverified'
INPUTS=ROOT/'timer-inputs'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'timer-build-unverified')
    args=p.parse_args();assert args.output.resolve()!=BASE.resolve()
    freeze=json.loads((BASE/'freeze.json').read_text())
    for name,expected in freeze['source_sha256'].items():assert sha(Path(name).read_bytes())==expected,name
    assert sha((BASE/'mods.elf').read_bytes())=='8bea01979955b1e751643cb1201975adc553e9efe2eafa5ef327fdc990c013eb'
    timer=prepare(LIBS/'lifetime/timer.c',INPUTS)
    sys.path[:0]=[str(VENDOR),str(VENDOR/'decomp/tools')]
    import mod_xpp,mod
    from tools.sd_boot.xpp_mods import compose_card
    directories=[ROOT/'context-films-inputs'/n for n in ['film-sims','noise-reduction']]+[ROOT/'jpeg-max-inputs/jpeg-max']
    target=VENDOR/'decomp/mods/targets/xt2-441.json';lifetime=LIBS/'lifetime/lib.json'
    originals={p:p.read_bytes() for p in [target,lifetime]}
    metadata=json.loads(originals[lifetime]);sources=metadata['xpp']['sources']
    assert sources==['lifetime.c','timer.c']
    sources[1]=os.path.relpath(timer,lifetime.parent)
    try:
        lifetime.write_text(json.dumps(metadata,indent=2)+'\n')
        target.write_bytes((BASE/'target.json').read_bytes())
        specs=[json.loads((d/'mod.json').read_text()) for d in directories]
        libs=mod_xpp.resolve_libraries(specs,'xt2-441')
        all_sources=[(LIBS/name/s).resolve() for name,spec in libs.items() for s in spec['sources']]
        all_sources += [(d/s).resolve() for d,spec in zip(directories,specs) for s in spec['sources']]
        expected=(set(freeze['source_sha256'])-{str((LIBS/'lifetime/timer.c').resolve())})|{str(timer.resolve())}
        assert set(map(str,all_sources))==expected
        assert len(all_sources)==len(set(all_sources))==23 and len(libs)==13
        result=mod.build_xpp_mods(list(map(str,directories)),args.output,'xt2-441','reserved-native-prefix')
        assert all(r['available'] for r in result['availability']) and len(result['words'])==63
        roots={f'lib-{name}':str(LIBS/name) for name in libs}|{s['name']:str(d) for s,d in zip(specs,directories)}
        (args.output/'source-roots.json').write_text(json.dumps(roots,indent=2)+'\n')
        (args.output/'target.json').write_bytes(target.read_bytes())
        receipt=dict(scope=__doc__,source_sha256={str(s):sha(s.read_bytes()) for s in all_sources},
            temporary_lifetime_metadata=metadata,target_sha256=sha(target.read_bytes()),
            generator_sha256=sha(Path(__file__).read_bytes()),baseline_elf_sha256=sha((BASE/'mods.elf').read_bytes()),
            preparation_sha256=sha((INPUTS/'preparation.json').read_bytes()),hardware_verified=False)
        (args.output/'preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
        card=compose_card('xt2-441',args.output,Path(str(args.output)+'-card'))
    finally:
        for path,data in originals.items():path.write_bytes(data)
    print(json.dumps(dict(elf_sha256=sha((args.output/'mods.elf').read_bytes()),
        regions=result['regions'],words=len(result['words']),files=card['files'],accepted=card['accepted'])))


if __name__=='__main__':main()
