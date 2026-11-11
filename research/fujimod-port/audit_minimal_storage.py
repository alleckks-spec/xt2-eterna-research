"""Audit mod-owned storage reachability in the final volatile X-T2 ELF.

Original AI-assisted artifact check. Absolute symbols alone are linker bindings,
not executed imports. Check live definitions, direct branches and aligned native
API pointer words in allocated sections, together with pinned selected sources.
This is not a whole-firmware call-graph proof or a camera timing measurement.
"""
import argparse
import hashlib
import io
import json
import re
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parent
BLOCKED = re.compile(r'^(?:storage_|software_timer_|x70_cardio_|x70_timer_|x70_settings_(?:start|tick|request_save)|cb_(?:open|read|write|seek|close|list))')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit(build):
    build = Path(build).resolve()
    elf_raw = (build/'mods.elf').read_bytes()
    elf = ELFFile(io.BytesIO(elf_raw))
    syms = list(elf.get_section_by_name('.symtab').iter_symbols())
    target = json.loads((build/'target.json').read_text())
    bindings = {n:int(v,0) if isinstance(v,str) else v for n,v in target['symbols'].items() if BLOCKED.match(n)}
    addresses = {}
    for name,address in bindings.items():
        addresses.setdefault(address,[]).append(name)
    live = [s.name for s in syms if BLOCKED.match(s.name) and isinstance(s['st_shndx'],int) and
            elf.get_section(s['st_shndx'])['sh_flags'] & 2 and s['st_value']]
    assert not live, ('linked mod-owned storage/timer implementation',live)
    branches = []
    pointers = []
    decoder = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for section in elf.iter_sections():
        if not section['sh_flags'] & 2 or section['sh_type']=='SHT_NOBITS':
            continue
        raw = section.data()
        base = section['sh_addr']
        if section['sh_flags'] & 4:
            # Disassemble each aligned instruction independently: literal pools
            # do not prematurely stop the scan or hide a later function.
            for offset in range(0,len(raw)-3,4):
                for pc,size,mnemonic,operands in decoder.disasm_lite(raw[offset:offset+4],base+offset):
                    if re.fullmatch(r'b(?:l|lx)?(?:eq|ne|hs|lo|mi|pl|vs|vc|hi|ls|ge|lt|gt|le|al)?',mnemonic) and operands.startswith('#'):
                        destination = int(operands[1:],0)
                        if destination in addresses:
                            branches.append(dict(site=hex(pc),names=addresses[destination]))
        for offset in range((-base)%4,len(raw)-3,4):
            value = struct.unpack_from('<I',raw,offset)[0]
            if value in addresses:
                pointers.append(dict(section=section.name,site=hex(base+offset),names=addresses[value]))
    assert not branches, ('native storage/timer branches',branches)
    assert not pointers, ('native storage/timer pointer words',pointers)
    prep = json.loads((build/'preparation.json').read_text())
    assert prep['elf_sha256'] == sha(elf_raw), 'receipt is for another ELF'
    source_hashes = prep['source_sha256']
    for path,digest in source_hashes.items():
        assert sha(Path(path).read_bytes()) == digest,path
    selected = {Path(p).name:Path(p) for p in source_hashes if Path(p).parent.name=='minimal-inputs'}
    stock = selected['stock_choices.c'].read_text()
    start = selected['start.c'].read_text()
    choice = selected['film_choice.c'].read_text()
    assert 'x70_settings_request_save(' not in stock
    assert 'x70_settings_start(' not in stock and 'x70_settings_start(' not in start
    assert 'x70_settings_apply_stock(FILM, PROVIA);' in choice
    assert '#define PROVIA 0u' in choice and '#define FILM 0x1fcu' in choice
    assert 'stored != PROVIA' in choice
    # A development-card selector using stored enum18..23 is not selected here.
    assert 'stored == 18' not in choice and 'stored - 18' not in choice
    binding = selected['film_binding.c'].read_text()
    assert 'CSAVE_FSIM_TBL' in binding  # explicit source explanation of exclusion
    hook_declarations = [line.strip() for line in binding.splitlines() if line.startswith('X70_HOOK_WORD(')]
    assert len(hook_declarations)==8
    assert all('csave' not in s.lower() for s in hook_declarations)
    result = dict(scope=__doc__,status='PASS: no mod-owned storage/timer path linked',
        elf_sha256=sha(elf_raw), absolute_native_bindings=bindings,
        linked_blocked_definitions=live, direct_native_storage_timer_branches=branches,
        native_storage_timer_pointer_words=pointers,
        selected_sources_verified=len(source_hashes), settings_start_calls=0, settings_save_requests=0,
        stored_film_choice_base='PROVIA, native value 0; ETERNA key32 remains RAM state',
        custom_setting_editor_bound=False, film_list_word_hooks=len(hook_declarations),
        source_and_build_limits=[
            'Fn/Q/IQ bindings use native stock choices; no C1-C7 ETERNA snapshot support.',
            'Power-off and C1-C7 native serializers are not exhaustively executed here.',
            'Stock JPEG/other firmware SD writes are unaffected and still require hardware testing.',
            'No claim of X-T2 capture-safe admission for the larger card-backed build.',
            'Aligned pointer scan plus direct-branch scan is not a general indirect-call proof.'
        ], hardware_verified=False,checker_sha256=sha(Path(__file__).read_bytes()))
    output = build/'storage-audit.json'
    output.write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=ROOT/'minimal-build-unverified')
    args=parser.parse_args()
    result=audit(args.build)
    print(json.dumps({k:result[k] for k in ('status','elf_sha256','selected_sources_verified')}))
