"""Apply the existing bounded NR assay to the exact ordinary-builder ELF.

Source/calibration/manual-init/transport boundaries are those of the assay.
No ordinary build is substituted and no full boot, SD transfer or camera claim.
"""
import json
from pathlib import Path
from elftools.elf.elffile import ELFFile
from build_resident_reservation import ROOT, START, END, sha

BUILD = ROOT/'ordinary-platform-build-unverified'
CARD = Path(str(BUILD)+'-card')
OUT = ROOT/'ordinary-platform-nr-check-unverified'


def load(build_directory=BUILD, expected_words=52):
    BUILD=Path(build_directory)
    CARD=Path(str(BUILD)+'-card')
    source_roots=json.loads((BUILD/'source-roots.json').read_text()) if (BUILD/'source-roots.json').exists() else None
    path = BUILD/'manifest.json'
    manifest = json.loads(path.read_text())
    assert manifest['target']=='xt2-441' and manifest['mode']=='image'
    assert len(manifest['words'])==expected_words
    assert manifest['toolchain']=='arm-gnu-13.2-armv7a'
    region, = manifest['regions']
    assert int(region['address'],0)==START and region['size']<=END-START
    payload=(BUILD/region['file']).read_bytes()
    assert len(payload)==region['size'] and sha(payload)==region['sha256']
    card=json.loads((CARD/'manifest.json').read_text())
    assert card['accepted'] is False and card['words']==manifest['words']
    sources={}
    for unit in manifest['mods']:
        for record in unit['sources']:
            base=Path(source_roots[unit['name']]) if source_roots is not None else ROOT/'ordinary-platform-inputs'
            source=(base/record['file']).resolve()
            assert source.is_relative_to(ROOT)
            assert sha(source.read_bytes())==record['sha256'],source
            sources[str(source.relative_to(ROOT))]=record['sha256']
    elf_path=BUILD/'mods.elf'
    with elf_path.open('rb') as stream:
        elf=ELFFile(stream)
        sections=[(int(section['sh_addr']),section.data(),section.name,int(section['sh_size']))
                  for section in elf.iter_sections() if section['sh_flags']&2 and section['sh_size']]
        symbols={symbol.name:int(symbol['st_value']) for symbol in
                 elf.get_section_by_name('.symtab').iter_symbols() if symbol.name}
    report=dict(elf_sha256=sha(elf_path.read_bytes()),compiler=manifest['toolchain'],
        edits=[dict(address=int(word['address'],0),expected=int(word['old'],0),value=int(word['new'],0))
               for word in manifest['words']],source_sha256=sources,
        dependency_sha256={str(p):sha(p.read_bytes()) for p in [Path(__file__),path,
            CARD/'manifest.json',ROOT/'ordinary-platform-inputs/preparation.json']})
    if source_roots is not None:
        report['dependency_sha256'][str(BUILD/'source-roots.json')]=sha((BUILD/'source-roots.json').read_bytes())
    return sections,symbols,report


if __name__=='__main__':
    from verify_nr_candidate import verify
    OUT.mkdir(exist_ok=True)
    verify(build_function=load,output=OUT,resident_region=(START,END),
           binding_audit=ROOT/'nr-candidate-unverified/binding-audit.json',
           artifact_files=[BUILD/'manifest.json',BUILD/'mods.elf',BUILD/'region.bin',CARD/'manifest.json'])
    path=OUT/'verification.json';report=json.loads(path.read_text())
    report['scope']=__doc__+'\n'+report['scope']
    path.write_text(json.dumps(report,indent=2)+'\n')
