"""Build a volatile ETERNA first-trial image with the existing FujiMod composer.

Local authorized inputs required. Preserve the stock timer dispatcher exactly.
Retain the existing qualified heap/BSS placement and processing adapters.
Temporary target/library metadata is restored, including previously absent files.
"""
import argparse,json,sys
from pathlib import Path
from build_modular_candidate import ROOT,VENDOR,LIBS,sha
from prepare_single_eterna_candidate import prepare


def build(output, receipt=None):
    output=Path(output).resolve()
    assert not output.exists() and not Path(str(output)+'-card').exists()
    receipt=prepare() if receipt is None else receipt
    metadata={Path(k):v for k,v in receipt['metadata'].items()}
    target=VENDOR/'decomp/mods/targets/xt2-441.json'
    native=json.loads((ROOT/'timer-build-unverified/target.json').read_text())
    stock=(ROOT.parents[1]/'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    # This candidate has no timer users: do not alter any native timer routine.
    assert int.from_bytes(stock[0xcdfb04:0xcdfb08],'little')==0x1188000
    assert all((int(w['address'],0) if isinstance(w['address'],str) else w['address']) != 0xcdfb04
               for w in native['card_words'])
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
        result=mod.build_xpp_mods(list(map(str,directories)),output,'xt2-441','reserved-native-prefix')
        assert all(r['available'] for r in result['availability'])
        roots={f'lib-{name}':str(LIBS/name) for name in libs}|{s['name']:str(d) for s,d in zip(specs,directories)}
        (output/'source-roots.json').write_text(json.dumps(roots,indent=2)+'\n')
        (output/'target.json').write_bytes(target.read_bytes())
        receipt.update(source_sha256={str(s):sha(s.read_bytes()) for s in sources},
            libraries=list(libs),resolved_metadata={str(LIBS/n/'lib.json'):spec for n,spec in libs.items()},
            elf_sha256=sha((output/'mods.elf').read_bytes()),builder_sha256=sha(Path(__file__).read_bytes()))
        (output/'preparation.json').write_text(json.dumps(receipt,indent=2,default=str)+'\n')
        card=compose_card('xt2-441',output,Path(str(output)+'-card'))
        delivered=(Path(str(output)+'-card')/'ffboot.bin').read_bytes()
        assert delivered[0xcdfb04:0xcdfb08]==stock[0xcdfb04:0xcdfb08]
        assert len(result['words'])==45
    finally:
        for path,raw in originals.items():
            if raw is None:path.unlink(missing_ok=True)
            else:path.write_bytes(raw)
    print(json.dumps(dict(elf_sha256=receipt['elf_sha256'],sources=len(sources),libraries=len(libs),
        words=len(result['words']),regions=result['regions'],files=card['files'],accepted=card['accepted'])))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'single-eterna-build-unverified')
    a=p.parse_args();build(a.output)


if __name__=='__main__':main()
