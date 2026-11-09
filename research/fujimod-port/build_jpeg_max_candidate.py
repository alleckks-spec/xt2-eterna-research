"""Add the original JPEG Max XPP module to the checked six-film/NR inputs.

Private local upstream derivatives: do not publish generated C. Reuses ordinary
mod.build_xpp_mods and compose_card. No loader, service or architecture additions.
Build/link evidence only; capture, overlay lifetime and hardware remain open.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from build_modular_candidate import library, LIBS, ROOT, VENDOR, sha

INPUTS=ROOT/'jpeg-max-inputs'
BASE=ROOT/'context-films-build-unverified'


def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'jpeg-max-build-unverified')
    args=p.parse_args()
    INPUTS.mkdir(exist_ok=True)
    # Extend the previously checked source set; do not rerun baseline generators
    # or overwrite their build directories just to include another ordinary mod.
    freeze=json.loads((BASE/'freeze.json').read_text())
    for path,digest in freeze['source_sha256'].items():
        assert sha(Path(path).read_bytes())==digest,path
    sys.path[:0]=[str(VENDOR),str(VENDOR/'decomp/tools')]
    import mod_xpp
    import mod
    from tools.sd_boot.xpp_mods import compose_card
    upstream=VENDOR/'decomp/mods'
    jpeg=upstream/'jpeg-max/xpp/jpeg_max.c'
    quality=upstream/'lib/menu-stock-choices/quality/quality.c'
    raw=jpeg.read_bytes()
    assert git_blob(raw)=='ded6eb168bf845465062464851f10cb6553f95be'
    text=raw.decode();assert text.count('#define QUALITY 0x1cau')==1
    (INPUTS/'jpeg_max.c').write_text(text.replace('#define QUALITY 0x1cau','#define QUALITY 0x1f1u'))
    raw=quality.read_bytes()
    assert git_blob(raw)=='cb3a839b939dd9546eb3b8deefbf10e2a43fd95b'
    text=raw.decode();assert text.count('0x1ca')==3
    (INPUTS/'quality.c').write_text(text.replace('0x1ca','0x1f1'))
    locator=ROOT.parents[1]/'research/fujimod-xt2-jpeg-max-menu-bindings.json'
    found=json.loads(locator.read_text())
    assert found['property']==0x1f1
    rows={r['id']:r for r in found['rows']}
    target_path=upstream/'targets/xt2-441.json'
    original_target=target_path.read_bytes()
    target=json.loads(original_target)
    bindings={'metadata_prepare_tables':0x2a232e8}
    firmware=ROOT.parents[1]/'firmware/extracted/xt2-4.41'
    streams=json.loads((firmware/'manifest.json').read_text())['streams']
    storage={}
    def stock_read(address,size):
        for s in streams:
            base=s['inner_header']['base']
            if base<=address and address+size<=base+s['decoded_size']:
                if base not in storage:
                    data=(firmware/s['file']).read_bytes()
                    assert sha(data)==s['sha256']
                    storage[base]=data
                return storage[base][address-base:address-base+size]
        raise ValueError(f'Unmapped descriptor {address:#x}')
    for kind,ids in [('recmenu',[186,109]),('fn',[7]),('quickmenu',[77])]:
        for i,ident in enumerate(ids):
            row=rows[ident]
            assert sha(stock_read(row['address'],0x1c))==row['descriptor_sha256']
            bindings[f'{kind}_quality_'+('alt_table' if i else 'table')]=row['address']
            if i==0:
                bindings[f'{kind}_quality_rows']=row['rows']
                bindings[f'{kind}_quality_resources']=row['records']
    target['symbols'].update(bindings)
    candidate_target=json.dumps(target,indent=2)+'\n'
    (INPUTS/'xt2-441.json').write_text(candidate_target)
    library('menu-stock-choices/xt2-441-quality',[INPUTS/'quality.c'],
        ['menu-stock-choices/xt2-441-six'],LIBS/'menu-stock-choices/include')
    directory=INPUTS/'jpeg-max';directory.mkdir(exist_ok=True)
    spec=dict(name='jpeg-max',targets=['xt2-441'],sources=['../jpeg_max.c'],
        libs=['menu-stock-choices/xt2-441-quality'],
        description='Existing JPEG Max XPP implementation with X-T2 quality property and native bindings; capture unqualified.')
    (directory/'mod.json').write_text(json.dumps(spec,indent=2)+'\n')
    directories=[ROOT/'context-films-inputs'/n for n in ['film-sims','noise-reduction']]+[directory]
    specs=[json.loads((d/'mod.json').read_text()) for d in directories]
    libraries=mod_xpp.resolve_libraries(specs,'xt2-441')
    roots={f'lib-{name}':str(LIBS/name) for name in libraries}
    roots.update({s['name']:str(d) for s,d in zip(specs,directories)})
    sources=[(LIBS/n/s).resolve() for n,lib in libraries.items() for s in lib['sources']]
    sources += [(d/s).resolve() for spec,d in zip(specs,directories) for s in spec['sources']]
    assert len(sources)==len(set(sources))==23
    assert set(map(str,sources))==set(freeze['source_sha256'])|{str(INPUTS/'jpeg_max.c'),str(INPUTS/'quality.c')}
    receipt=dict(scope=__doc__,sources={str(s):sha(s.read_bytes()) for s in sources},
        source_roots=roots,target_sha256=sha(candidate_target.encode()),
        baseline_freeze_sha256=sha((BASE/'freeze.json').read_bytes()),
        native_table_check_sha256=sha((ROOT/'jpeg-max-native-check-unverified/verification.json').read_bytes()),
        generator_sha256=sha(Path(__file__).read_bytes()),hardware_verified=False)
    (INPUTS/'preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    # The frontend selects targets by name. Restore its prior metadata afterward;
    # preserve the exact candidate target beside the inputs for provenance.
    try:
        target_path.write_text(candidate_target)
        result=mod.build_xpp_mods(list(map(str,directories)),args.output,'xt2-441','reserved-native-prefix')
        assert all(r['available'] for r in result['availability'])
        assert len(result['words'])==63
        (args.output/'source-roots.json').write_text(json.dumps(roots,indent=2)+'\n')
        (args.output/'target.json').write_text(candidate_target)
        card=compose_card('xt2-441',args.output,Path(str(args.output)+'-card'))
    finally:
        target_path.write_bytes(original_target)
    print(json.dumps(dict(regions=result['regions'],words=len(result['words']),
        files=card['files'],accepted=card['accepted'])))


if __name__=='__main__':
    main()
