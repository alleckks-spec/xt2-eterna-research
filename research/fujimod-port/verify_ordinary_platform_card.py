"""Check correspondence between the ordinary ELF, region and delivered SD bytes.

Artifact integrity only: no SD transfer, firmware execution or camera acceptance.
"""
import hashlib
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parent
BUILD = ROOT/'ordinary-platform-build-unverified'
CARD = Path(str(BUILD)+'-card')


def main(build_directory=BUILD):
    BUILD=Path(build_directory)
    CARD=Path(str(BUILD)+'-card')
    manifest=json.loads((BUILD/'manifest.json').read_text())
    card=json.loads((CARD/'manifest.json').read_text())
    assert manifest['target']==card['firmware_id']=='xt2-441'
    assert manifest['words']==card['words'] and len(manifest['words'])==52
    assert len({word['address'] for word in manifest['words']})==52
    region,=manifest['regions']
    start=int(region['address'],0)
    payload=(BUILD/region['file']).read_bytes()
    assert len(payload)==region['size']
    assert hashlib.sha256(payload).hexdigest()==region['sha256']
    reconstructed=bytearray(len(payload))
    with (BUILD/'mods.elf').open('rb') as stream:
        elf=ELFFile(stream)
        for section in elf.iter_sections():
            address,size=int(section['sh_addr']),int(section['sh_size'])
            if not section['sh_flags']&2 or not size or not start<=address<start+len(payload):
                continue
            assert address+size<=start+len(payload)
            data=bytes(size) if section['sh_type']=='SHT_NOBITS' else section.data()
            reconstructed[address-start:address-start+size]=data
    assert reconstructed==payload
    with (CARD/'ffboot.bin').open('rb') as stream:
        stream.seek(start)
        assert stream.read(len(payload))==payload
        for word in manifest['words']:
            stream.seek(int(word['address'],0))
            assert stream.read(4)==struct.pack('<I',int(word['new'],0)),word
    verified={}
    for name,record in card['files'].items():
        path=CARD/name
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        assert path.stat().st_size==record['bytes'] and digest==record['sha256']
        verified[name]=record
    assert card['accepted'] is False
    report=dict(scope=__doc__,elf_sha256=hashlib.sha256((BUILD/'mods.elf').read_bytes()).hexdigest(),
        elf_region_equal=True,region_sd_equal=True,patched_sd_words=52,files=verified,
        input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                      [Path(__file__),BUILD/'manifest.json',CARD/'manifest.json']},
        accepted=False,hardware=False)
    (BUILD/'card-correspondence.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':
    main()
