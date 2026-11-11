"""Build the X-T20 FAT32 format-label hook and save_data codec for X-T2.

Reuse the existing five-mod builder and native reservation. This stage keeps
the upstream FORMAT CARD NAME declaration but does not supply the missing
X-T2 general mod-menu engine. Settings.JSN loading and the formatter boundary
can be checked separately; physical formatting and menu operation are open.
Private upstream inputs remain local. Original integration glue, AI-assisted.
"""
import argparse
import copy
import hashlib
import json
import os
import shutil
import re
import struct
import sys
from pathlib import Path
from build_modular_candidate import ROOT, VENDOR, LIBS, sha

BASE = ROOT / 'full-storage-guard-build-unverified'
INPUTS = ROOT / 'volume-name-inputs'
BUILD = ROOT / 'volume-name-build-unverified'
RESERVATION = ROOT / 'volume-name-reservation-unverified'
PIN = '9d22f1b41c70c20407158e699f2583ac4907ff16'
PINS = {
    'save-data/save_data.c': '6b9e829722c60327ea3ad70033e75e634f3da18d',
    'save-data/include/x70_save_data.h': 'a4ad2288f1ea6b7480fa2c64e89e065602a2a868',
    'menu-save-data/xpp/save_data.c': 'a28740309dfe36aa48ce6e4f2fe58d1eb0e93fe9',
    'menu-save-data/xpp/include/x70_menu_save_data.h': '20498bf55f53f2ddb57a3e5051b6da82dc87d792',
    'settings/generated/save_data.h': 'bdf6c7f4318a26617608024123bf5dc3eed059cf',
    'settings/generated/save_data.c': '52025528c2732cc0e883a788113673e8e6e87452',
}


def prepare():
    stock = (ROOT.parents[1]/'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    assert sha(stock) == 'fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    pins = [(0xc69d60, 0x168, '7235605c2d2e0019d3f936a83c8cc356694818800beb36ea5d82d378fcbdddc7'),
            (0xc7f868, 0x10, 'fab99704a5815b8cc1e7be824ce471a9e66962fac2d88cf0167001b1d479c3e5')]
    for address, size, digest in pins:
        assert sha(stock[address:address+size]) == digest
    for relative, blob in PINS.items():
        data = (LIBS / relative).read_bytes()
        assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == blob, relative
    source = VENDOR / 'decomp/mods/sd-volume-name/xpp/volume_name.c'
    blob = source.read_bytes()
    assert hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest() == '9598bc3883576ab7c1d0e3b4c77b0558dc06c4fe'
    original = source.read_text()
    old = 'XPP_ENTRY_HOOK(card_write_pages, card_write_pages_hook, 0xe92d4870);'
    assert original.count(old) == 1
    INPUTS.mkdir(exist_ok=True)
    adapted = INPUTS / 'volume_name.c'
    adapted.write_text(original.replace(old, 'XPP_ENTRY_HOOK(card_write_pages, card_write_pages_hook, 0xe92d4ff0);'))
    sources = [adapted, LIBS / 'save-data/save_data.c', LIBS / 'settings/generated/save_data.c',
               LIBS / 'menu-save-data/xpp/save_data.c']
    includes = [LIBS / 'save-data/include', LIBS / 'menu-save-data/xpp/include']
    specification = dict(name='sd-volume-name', targets=['xt2-441'],
        description='X-T2 FAT32 format-label boundary and original save_data codec; general mod-menu engine pending.',
        sources=[os.path.relpath(p, INPUTS) for p in sources],
        include=[os.path.relpath(p, INPUTS) for p in includes],
        libs=['settings/xt2-441', 'xpp-settings/xt2-441', 'menu/xt2-441'])
    (INPUTS / 'mod.json').write_text(json.dumps(specification, indent=2) + '\n')
    return dict(upstream_pin=PIN, upstream_blob_pins=PINS,
        volume_source_sha256=sha(source.read_bytes()),
        native_boundaries=[dict(address=a, size=n, sha256=h) for a,n,h in pins],
        native_symbols=dict(card_write_pages=0xc69d60, calendar_read=0xc7f868),
        adaptation='Only hook preimage changes; native X-T2 count/buffer ABI checked independently.',
        menu_declaration_retained=True, general_mod_menu_engine_present=False,
        hardware_verified=False)


def resize(native):
    """Reuse the existing 32 KiB heap-suffix reservation after a measured link."""
    failed = ROOT/'volume-name-guard-footprint-unverified/failed-mods.map'
    matches = re.findall(r'(0x[0-9a-f]+)\s+__x70mod_region_end =',failed.read_text())
    assert len(matches) == 1
    region, = native['card_regions']
    old_start = int(region['address'],0)
    end = old_start + int(region['size'],0)
    footprint = int(matches[0],16) - old_start
    assert (old_start,end,footprint) == (0x1388000,0x13c0000,229736)
    size = (footprint + 0x7fff) & ~0x7fff
    start = end - size
    assert (start,size) == (0x1380000,0x40000)
    previous = ROOT/'card-films-reservation-unverified'
    proposal = json.loads((previous/'proposal.json').read_text())
    code = bytearray((previous/'reservation.bin').read_bytes())
    assert sha(code) == proposal['shim']['sha256']
    assert proposal['heap']['start'] < start < old_start < end
    shim = proposal['shim']['address']
    def mov16(base,value): return base | ((value&0xf000)<<4) | (value&0xfff)
    changes = {0xcf45c4:mov16(0xe3003000,start&0xffff),0xcf45c8:mov16(0xe3403000,start>>16),
               0xcf8200:mov16(0xe3000000,start&0xffff),0xcf8204:mov16(0xe3400000,start>>16),
               shim+28:(start-proposal['bss']['start'])//4}
    words = {w['address']:w for w in native['card_words']}
    assert struct.unpack_from('<I',code,28)[0] == (old_start-proposal['bss']['start'])//4
    for a,v in changes.items(): words[a]['new'] = v
    for row in proposal['edits']:
        if row['address'] in changes: row['new'] = changes[row['address']]
    struct.pack_into('<I',code,28,changes[shim+28])
    region.update(address=hex(start),size=hex(size),
        status='Existing reservation resized to measured37-source footprint; hardware workload headroom unproved.')
    proposal['region'].update(start=start,end=end,bytes=size,current_loaded_bytes=footprint,remaining_before_stack=size-footprint)
    proposal['heap'].update(new_end=start,new_capacity=start-proposal['heap']['start'])
    proposal['bss']['prefix_bytes']=start-proposal['bss']['start']
    proposal['shim']['sha256']=sha(code)
    proposal['status']='Measured37-source reservation; bounded checks required'
    proposal['inputs']={str(p.resolve()):sha(p.read_bytes()) for p in
        [Path(__file__),failed,BASE/'target.json',previous/'proposal.json',previous/'reservation.bin']}
    RESERVATION.mkdir(exist_ok=True)
    (RESERVATION/'proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
    (RESERVATION/'reservation.bin').write_bytes(code)
    (RESERVATION/'target.json').write_text(json.dumps(native,indent=2)+'\n')
    return proposal


def build(output, *, measure_only=False):
    output = Path(output).resolve()
    assert not output.exists() and not Path(str(output) + '-card').exists()
    adaptation = prepare()
    base = json.loads((BASE / 'preparation.json').read_text())
    metadata = {Path(p): copy.deepcopy(s) for p,s in base['metadata'].items()}
    for source,digest in base['source_sha256'].items():
        assert sha(Path(source).read_bytes()) == digest, source
    target = VENDOR / 'decomp/mods/targets/xt2-441.json'
    native = json.loads((BASE / 'target.json').read_text())
    native['symbols'].update(adaptation['native_symbols'])
    if not measure_only:
        adaptation['reservation']=resize(native)
    assert any(int(w['address']) == 0xcdfb04 and int(w['new']) == 0x1187ffc for w in native['card_words'])
    directories = [ROOT/'context-films-inputs'/n for n in ['film-sims','noise-reduction']]
    directories += [ROOT/'jpeg-max-inputs/jpeg-max', ROOT/'card-films-inputs/card-films', INPUTS]
    originals = {p:p.read_bytes() if p.exists() else None for p in [*metadata,target]}
    sys.path[:0] = [str(VENDOR), str(VENDOR/'decomp/tools')]
    import mod, mod_xpp
    from tools.sd_boot.xpp_mods import compose_card
    original_run = mod_xpp._run
    def retain_failed_map(command, work):
        try:
            return original_run(command, work)
        except ValueError:
            if Path(work, 'mods.map').exists():
                shutil.copyfile(Path(work,'mods.map'), output/'failed-mods.map')
                shutil.copyfile(Path(work,'mods.ld'), output/'failed-mods.ld')
            raise
    try:
        for path,spec in metadata.items(): path.write_text(json.dumps(spec,indent=2)+'\n')
        target.write_text(json.dumps(native,indent=2)+'\n')
        specs = [json.loads((d/'mod.json').read_text()) for d in directories]
        libraries = mod_xpp.resolve_libraries(specs,'xt2-441')
        sources = [(LIBS/n/s).resolve() for n,spec in libraries.items() for s in spec['sources']]
        sources += [(d/s).resolve() for d,spec in zip(directories,specs) for s in spec['sources']]
        assert len(sources) == len(set(sources)) == 37
        mod_xpp._run = retain_failed_map
        result = mod.build_xpp_mods(list(map(str,directories)),output,'xt2-441','reserved-native-prefix')
        assert all(row['available'] for row in result['availability'])
        assert len(result['words']) == 68
        roots = {f'lib-{n}':str(LIBS/n) for n in libraries}|{s['name']:str(d) for s,d in zip(specs,directories)}
        (output/'source-roots.json').write_text(json.dumps(roots,indent=2)+'\n')
        (output/'target.json').write_bytes(target.read_bytes())
        receipt = dict(scope=__doc__,adaptation=adaptation,metadata={str(p):s for p,s in metadata.items()},
            source_sha256={str(s):sha(s.read_bytes()) for s in sources},
            elf_sha256=sha((output/'mods.elf').read_bytes()),base_elf_sha256=sha((BASE/'mods.elf').read_bytes()),
            generator_sha256=sha(Path(__file__).read_bytes()),mod_directories=list(map(str,directories)))
        (output/'preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
        card = compose_card('xt2-441',output,Path(str(output)+'-card'))
    finally:
        mod_xpp._run = original_run
        for path,data in originals.items():
            if data is None: path.unlink(missing_ok=True)
            else: path.write_bytes(data)
    print(json.dumps(dict(elf_sha256=receipt['elf_sha256'],sources=len(sources),libraries=len(libraries),
        words=len(result['words']),regions=result['regions'],accepted=card['accepted'])))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=BUILD)
    parser.add_argument('--measure-only',action='store_true')
    arguments=parser.parse_args()
    build(arguments.output,measure_only=arguments.measure_only)
