"""Bind the reduced artifact, actual test results and removal decisions.

Integrity/evidence audit only; does not rerun ARM or certify a camera.
No firmware bytes or private source excerpts belong in the public result.
"""
import hashlib
import json
from pathlib import Path
from verify_ordinary_platform_card import main as correspondence

ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parents[1]
BUILD=ROOT/'single-eterna-build-unverified'
REBUILD=ROOT/'single-eterna-rebuild-unverified'
OUT=ROOT/'single-eterna-check-unverified'


def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(path.read_text())


def main():
    prep=read(BUILD/'preparation.json');manifest=read(BUILD/'manifest.json')
    old=read(ROOT/'minimal-build-unverified/manifest.json')
    assert len(manifest['words'])==45 and len(prep['source_sha256'])==19
    for mapping in [prep['inputs'],prep['source_outputs'],prep['source_sha256']]:
        for name,digest in mapping.items():assert sha(Path(name).read_bytes())==digest,name
    assert prep['builder_sha256']==sha((ROOT/'build_single_eterna_candidate.py').read_bytes())
    assert prep['single_generator_sha256']==sha((ROOT/'prepare_single_eterna_candidate.py').read_bytes())
    digest=sha((BUILD/'mods.elf').read_bytes());assert digest==prep['elf_sha256']
    correspondence(BUILD,45)
    prior={int(w['address'],0):w for w in old['words']}
    current={int(w['address'],0):w for w in manifest['words']}
    removed=sorted(set(prior)-set(current))
    assert removed==[0xcdfb04,0x156d348,0x1570668] and not set(current)-set(prior)
    image=(Path(str(BUILD)+'-card')/'ffboot.bin').read_bytes()
    stock=(WORKSPACE/'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    assert image[0xcdf570:0xcdfb08]==stock[0xcdf570:0xcdfb08]
    code=Path(prep['processing_source']).read_text()
    assert 'PROFILE_RECIPE' not in code and 'PROFILE_MAGIC' not in code
    assert 'static const struct xt20_film_recipe *volatile latched' not in code
    assert 'chroma_armed[4]' not in code
    recipes=Path(next(p for p in prep['source_sha256'] if Path(p).name=='films.generated.c'))
    assert sha(recipes.read_bytes())==sha((ROOT/'generated/films.generated.c').read_bytes())
    artifacts={}
    for name in ['mods.elf','region.bin','ffboot.bin','ffsys.bin']:
        suffix='-card' if name.startswith('ff') else ''
        raw=(Path(str(BUILD)+suffix)/name).read_bytes()
        assert raw==(Path(str(REBUILD)+suffix)/name).read_bytes(),name
        artifacts[name]=sha(raw)
    reports={name:read(OUT/name) for name in ['runtime.json','still.json','memory.json',
        'placement-ablations.json','chroma-adapter.json','processing/processing-verification-tci.json']}
    reports['storage']=read(BUILD/'storage-audit.json')
    for name,report in reports.items():assert report['elf_sha256']==digest,name
    assert reports['runtime.json']['profile_tail_sentinels_untouched']
    assert reports['runtime.json']['unexpected_storage_or_timer_requests']==[]
    assert reports['still.json']['profile_tail_write_events']==[]
    assert reports['still.json']['four_groups_equal_linked_recipe']
    assert reports['still.json']['stock_before_after_equal']
    assert reports['memory.json']['reserved_payload_preserved']
    assert reports['placement-ablations.json']['original_bss_clear_erases_reserved_payload']
    assert reports['placement-ablations.json']['original_heap_allows_crossing']
    assert not reports['chroma-adapter.json']['nested_call_changes_output']
    control=read(OUT/'chroma-upstream-control.json')
    assert control['nested_call_changes_output']
    assert control['elf_sha256']==sha((ROOT/'single-eterna-chroma-control-unverified/mods.elf').read_bytes())
    processing=reports['processing/processing-verification-tci.json']
    assert len(processing['records'])==117
    for record in processing['records']:
        for key in ['equal_stock','equal_reference','equal_donor','pass_check']:
            if key in record:assert record[key],record
    assert not processing['interleaving']['changed']
    assert processing['interleaving']['nested_native_chroma_unchanged']
    assert reports['storage']['linked_blocked_definitions']==[]
    files={Path(p) for p in prep['source_sha256']}|{Path(p) for p in prep['inputs']}|{Path(p) for p in prep['source_outputs']}
    files.update(ROOT/n for n in ['build_single_eterna_candidate.py','prepare_single_eterna_candidate.py',
        'verify_single_eterna_candidate.py','verify_single_eterna_runtime.py','verify_single_eterna_still.py',
        'verify_single_eterna_chroma.py','audit_single_eterna_package.py','verify_minimal_memory.py',
        'verify_minimal_processing.py','verify_minimal_runtime.py','verify_processing.py','audit_minimal_storage.py'])
    for spec in prep['resolved_metadata'].values():
        for directory in [spec['interface'],*spec.get('includes',[])]:files.update(Path(directory).resolve().rglob('*.h'))
    for folder in [BUILD,Path(str(BUILD)+'-card'),OUT]:files.update(folder.rglob('*.json'))
    files.discard(OUT/'package-audit.json')
    result=dict(scope=__doc__,status='PASS: reduced single-ETERNA artifact and evidence',elf_sha256=digest,
        reproducible_artifacts=artifacts,source_files=19,delivery_words=45,processing_cases=117,
        removed_stock_edit_addresses=list(map(hex,removed)),profile_tail_writes=False,
        native_timer_dispatcher_unchanged=True,rgb_curve_hooks_excluded=True,
        retained_placement_protection='Original BSS clear erases payload; original heap admits overlap.',
        retained_chroma_adapter='Original per-core mechanism fails supplied same-core nested call.',
        full_boot=False,hardware_verified=False,accepted=False,persistence_supported=False,
        freeze_sha256={str(p.resolve()):sha(p.read_bytes()) for p in sorted(files)})
    (OUT/'package-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='freeze_sha256'}))


if __name__=='__main__':main()
