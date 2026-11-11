"""Validate completed minimal-candidate evidence and reproducibility without ARM reruns.

Local evidence receipt only. Does not compose SD images or certify hardware.
Records selected sources, headers, tools and reports; excludes firmware contents.
"""
import json,hashlib
from pathlib import Path
from elftools.elf.elffile import ELFFile
from verify_ordinary_platform_card import main as correspondence

ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parents[1]
BUILD=ROOT/'minimal-build-unverified'
REBUILD=ROOT/'minimal-rebuild-unverified'
CHECK=ROOT/'minimal-check-unverified'

def sha(b):return hashlib.sha256(b).hexdigest()
def read(path):return json.loads(path.read_text())

def main():
    prep=read(BUILD/'preparation.json');manifest=read(BUILD/'manifest.json')
    assert len(manifest['words'])==48 and len(prep['source_sha256'])==19
    assert [m['name'] for m in manifest['mods'] if not m['name'].startswith('lib-')]==['film-sims']
    for mapping in [prep['inputs'],prep['source_outputs'],prep['source_sha256']]:
        for name,digest in mapping.items():assert sha(Path(name).read_bytes())==digest,name
    assert sha((ROOT/'build_minimal_candidate.py').read_bytes())==prep['builder_sha256']
    elf_hash=sha((BUILD/'mods.elf').read_bytes());assert elf_hash==prep['elf_sha256']
    correspondence(BUILD,48)
    reproducible={}
    for name in ['mods.elf','region.bin']:
        digest=sha((BUILD/name).read_bytes());assert sha((REBUILD/name).read_bytes())==digest
        reproducible[name]=digest
    for name in ['ffboot.bin','ffsys.bin']:
        digest=sha((Path(str(BUILD)+'-card')/name).read_bytes())
        assert sha((Path(str(REBUILD)+'-card')/name).read_bytes())==digest
        reproducible[name]=digest
    reports={name:read(CHECK/name) for name in ['runtime.json','still.json','memory.json','timer-fixed.json','timer-original.json']}
    reports['storage']=read(BUILD/'storage-audit.json')
    reports['processing']=read(CHECK/'processing/processing-verification-tci.json')
    for name,report in reports.items():
        assert report['elf_sha256']==elf_hash,name
        assert not report.get('hardware_verified',False)
        if 'checker_sha256' in report:
            checker={'runtime.json':'verify_minimal_runtime.py','still.json':'verify_minimal_still.py',
                'memory.json':'verify_minimal_memory.py','timer-fixed.json':'verify_timer_dispatch.py',
                'timer-original.json':'verify_timer_dispatch.py','storage':'audit_minimal_storage.py'}.get(name)
            if checker:assert sha((ROOT/checker).read_bytes())==report['checker_sha256'],name
    assert reports['runtime.json']['unexpected_storage_or_timer_requests']==[]
    assert reports['still.json']['four_groups_equal_linked_recipe'] and reports['still.json']['stock_before_after_equal']
    assert reports['still.json']['same_profile_reused_without_host_clear'] and reports['still.json']['stock_return_clears_recipe_tag']
    assert reports['memory.json']['reserved_payload_preserved']
    assert reports['timer-fixed.json']['stack']['callback_sp']==['0x1187ff8']
    assert reports['timer-original.json']['stack']['callback_sp']==['0x1187ffc']
    assert len(reports['processing']['records'])==117
    assert reports['storage']['linked_blocked_definitions']==[]
    sections=[]
    with (BUILD/'mods.elf').open('rb') as stream:
        elf=ELFFile(stream)
        for sec in elf.iter_sections():
            if sec['sh_flags']&2 and sec['sh_size'] and sec.name not in ['.x70mod.hooks','.x70mod.strings']:
                assert 0x1390000<=sec['sh_addr']<sec['sh_addr']+sec['sh_size']<=0x13c0000
                sections.append(dict(name=sec.name,address=hex(sec['sh_addr']),bytes=sec['sh_size'],nobits=sec['sh_type']=='SHT_NOBITS'))
    files=set(Path(p) for p in prep['source_sha256'])|set(Path(p) for p in prep['inputs'])|set(Path(p) for p in prep['source_outputs'])
    for spec in prep['resolved_metadata'].values():
        for interface in [spec['interface'],*spec.get('includes',[])]:files.update(Path(interface).resolve().rglob('*.h'))
    files.update((ROOT/'vendor/x70view/decomp/mods/include').glob('*.h'))
    files.update(BUILD/n for n in ['mods.elf','region.bin','manifest.json','preparation.json','target.json','source-roots.json','storage-audit.json','card-correspondence.json'])
    files.update(p for p in CHECK.rglob('*.json') if p.name!='package-audit.json')
    files.update(Path(str(BUILD)+'-card')/n for n in ['manifest.json','ffboot.bin','ffsys.bin'])
    files.update(ROOT/n for n in ['prepare_minimal_candidate.py','build_minimal_candidate.py','verify_minimal_runtime.py','verify_minimal_processing.py','verify_minimal_memory.py','verify_minimal_still.py','verify_timer_dispatch.py','audit_minimal_storage.py','audit_minimal_package.py','verify_card_films_menu.py'])
    files.update(ROOT/'vendor/x70view'/n for n in ['decomp/tools/mod.py','decomp/tools/mod_xpp.py','decomp/tools/build_toolchain.py','tools/sd_boot/xpp_mods.py','decomp/mods/targets/xt2-441-api.h'])
    files.update(WORKSPACE/n for n in ['.toolchains/fujimod-944d5c8-source/bindings/python/python/fujimod/_native.abi3.so','.toolchains/unicorn-tci/libunicorn.2.dylib'])
    freeze={str(p.resolve()):sha(p.read_bytes()) for p in files if p.is_file()}
    result=dict(scope=__doc__,status='PASS: final artifact and evidence; hardware unverified',
        elf_sha256=elf_hash,reproducible_artifacts=reproducible,sections=sections,source_files=19,
        delivery_words=48,processing_cases=117,native_menu_lists=3,native_still_groups=4,
        freeze_sha256=freeze,full_boot=False,camera_available=False,hardware_verified=False)
    (CHECK/'package-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','elf_sha256','reproducible_artifacts','sections']}))

if __name__=='__main__':main()
