"""Build a volatile ETERNA first-trial image with the existing FujiMod composer.

Local authorized inputs required. The only added stock edit aligns the X-T2
software timer dispatcher stack. No loader, profile format or emulator is added.
Temporary target/library metadata is restored, including previously absent files.
"""
import argparse,json,sys
from pathlib import Path
from build_modular_candidate import ROOT,VENDOR,LIBS,sha
from prepare_minimal_candidate import prepare


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'minimal-build-unverified');a=p.parse_args()
    receipt=prepare();metadata={Path(k):v for k,v in receipt['metadata'].items()}
    target=VENDOR/'decomp/mods/targets/xt2-441.json'
    native=json.loads((ROOT/'timer-build-unverified/target.json').read_text())
    stock=(ROOT.parents[1]/'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    # X-T2 dispatcher loads the literal then pushes a saved outer SP word.
    assert int.from_bytes(stock[0xcdfb04:0xcdfb08],'little')==0x1188000
    native['card_words'].append(dict(name='X-T2 timer callback AAPCS stack alignment',
        address=0xcdfb04,old=0x1188000,new=0x1187ffc))
    assert (0x1187ffc-4)%8==0 and 0x1187000<0x1187ffc<0x1188000
    originals={p:p.read_bytes() if p.exists() else None for p in [*metadata,target]}
    sys.path[:0]=[str(VENDOR),str(VENDOR/'decomp/tools')]
    import mod,mod_xpp
    from tools.sd_boot.xpp_mods import compose_card
    try:
        for path,spec in metadata.items():
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(spec,indent=2)+'\n')
        target.write_text(json.dumps(native,indent=2)+'\n')
        directories=list(map(Path,receipt['mod_directories']))
        specs=[json.loads((d/'mod.json').read_text()) for d in directories]
        libs=mod_xpp.resolve_libraries(specs,'xt2-441')
        sources=[(LIBS/name/s).resolve() for name,spec in libs.items() for s in spec['sources']]
        sources += [(d/s).resolve() for d,spec in zip(directories,specs) for s in spec['sources']]
        assert len(sources)==len(set(sources)) and len(directories)==1
        result=mod.build_xpp_mods(list(map(str,directories)),a.output,'xt2-441','reserved-native-prefix')
        assert all(r['available'] for r in result['availability'])
        roots={f'lib-{name}':str(LIBS/name) for name in libs}|{s['name']:str(d) for s,d in zip(specs,directories)}
        (a.output/'source-roots.json').write_text(json.dumps(roots,indent=2)+'\n')
        (a.output/'target.json').write_bytes(target.read_bytes())
        receipt.update(source_sha256={str(s):sha(s.read_bytes()) for s in sources},
            libraries=list(libs),resolved_metadata={str(LIBS/n/'lib.json'):spec for n,spec in libs.items()},
            elf_sha256=sha((a.output/'mods.elf').read_bytes()),builder_sha256=sha(Path(__file__).read_bytes()))
        (a.output/'preparation.json').write_text(json.dumps(receipt,indent=2,default=str)+'\n')
        card=compose_card('xt2-441',a.output,Path(str(a.output)+'-card'))
    finally:
        for path,raw in originals.items():
            if raw is None:path.unlink(missing_ok=True)
            else:path.write_bytes(raw)
    print(json.dumps(dict(elf_sha256=receipt['elf_sha256'],sources=len(sources),libraries=len(libs),
        words=len(result['words']),regions=result['regions'],files=card['files'],accepted=card['accepted'])))

if __name__=='__main__':main()
