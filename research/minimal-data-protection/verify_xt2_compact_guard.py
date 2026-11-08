"""Targeted compact-table coverage/early ARM verification, not full boot.

Original Codex-assisted source. Local pinned images/reports are required.
No unchanged late-wrapper or numeric grids are rerun.
"""
import json
import struct
from pathlib import Path
from build_xt2_minimal_protected import build, OUT, ROOT, compile_protected_guard
from build_xt2_delivery_probe import digest, require
from xt2_minimal_boot_guard import ENTRY, LIMIT, HOOK, checksum
from verify_xt2_minimal_protected_failures import early_cases


def main():
    image, meta, elf = build()
    require(image == (OUT/'ffboot.bin').read_bytes(), 'Delivered compact image differs')
    archive = ROOT/'research/minimal-protected-274de1d2-before-compact-guard'
    previous = (archive/'ffboot.bin').read_bytes()
    require(digest(previous) == '274de1d23e82c0a18a97d67b893a14961ceb18f75dd8a6b7fe440a38c362d6d3', 'Prior identity')
    require(len(image) == len(previous), 'Image size changed')
    require(image[:ENTRY] == previous[:ENTRY] and image[LIMIT:] == previous[LIMIT:],
            'Change outside the existing early guard')
    require(elf == (archive/'late.elf').read_bytes(), 'Late ELF changed')
    _, symbols = compile_protected_guard()
    ranges = meta['early_ranges']
    require(len(ranges) == 8 and LIMIT-ENTRY == 168, 'Guard/table size')
    expected = symbols['xt2_minimal_guard_expected']
    table = symbols['xt2_minimal_guard_ranges']
    require(struct.unpack_from('<16I', image, table) == tuple(x for r in ranges for x in r), 'Encoded table')
    require(struct.unpack_from('<I', image, expected-4)[0] == 0, 'Zero address terminator')
    require(expected == LIMIT-4, 'Expected value position')
    require(struct.unpack_from('<I', image, expected)[0] == checksum(image[a:a+n] for a,n in ranges), 'Checksum')
    stock = (ROOT/'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    require(digest(stock) == 'fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2', 'Stock identity')
    manifest = json.loads((ROOT/'firmware/research/eterna-minimal-sd-candidate/manifest.json').read_text())
    excluded = {HOOK+i for i in range(4)} | {expected+i for i in range(4)}
    def covered(a): return any(lo <= a < lo+n for lo,n in ranges)
    # Whole-image changed-byte coverage, not just a sample of hook addresses.
    changes = [i for i,(a,b) in enumerate(zip(stock,image)) if a != b]
    require(all(covered(a) or a in excluded for a in changes), 'Uncovered candidate change')
    functional_points = set()
    for edit in manifest['edits']:
        a = edit['address']; n = len(bytes.fromhex(edit['new']))
        require(all(covered(p) or p in excluded for p in range(a,a+n)), 'Original edit span uncovered')
        if (a != HOOK and a+n <= ENTRY) or a >= LIMIT:
            functional_points.update((a,a+n-1))
    points = {expected, meta['late_entry'], meta['late_end']-1, 0xCF8214, 0xCF8217}
    for a,n in ranges: points.update((a,a+n-1))
    points.update(functional_points)
    # Exercise the changed termination convention explicitly, plus table edges.
    points.update((table, table+7*8+4, expected-4, expected-1))
    mutations = [(table+8*i+4,struct.pack("<I",0)) for i in range(8)]
    mutations += [(table+8*i,struct.pack("<I",0)) for i in range(8)]
    mutations += [(table,struct.pack("<II",a,n)) for a,n in
                  [(0xFFFFFFF0,0x40),(0x2FFFFFC,4),(0xFFF10000,4)]]
    results = early_cases(image,meta,[None,*sorted(points),*mutations])
    prior = json.loads((archive/'local-build.json').read_text())
    old_ranges = prior['early_ranges']
    require(all(any(a <= lo and lo+n <= a+size for a,size in old_ranges) for lo,n in ranges),
            'Unexpected coverage outside prior policy')
    report = dict(image_sha256=digest(image), previous_image_sha256=digest(previous),
        guard_bytes=168, descriptor_count=8,
        early_checked_bytes=meta['early_checked_bytes'], previous_checked_bytes=prior['early_checked_bytes'],
        removed_bytes=prior['early_checked_bytes']-meta['early_checked_bytes'],
        all_candidate_changes_covered_except_trusted_entry_and_expected=True,
        original_edit_spans_covered=True, unchanged_outside_early_guard=True,
        late_elf_identical=True, late_native_evidence_inherited_not_rerun=True,
        prior_native_report='research/minimal-protected-prefix-verification.json',
        source_sha256={n:digest((ROOT/'scripts'/n).read_bytes()) for n in
            ['verify_xt2_compact_guard.py','xt2_minimal_compact_guard.S','xt2_minimal_boot_guard.py',
             'build_xt2_minimal_protected.py','verify_xt2_minimal_protected_failures.py']},
        early_cases=results, hardware_verified=False, full_boot=False,
        limits=['Host supplies image in RAM; no ROM transfer, cache timing, DMA or physical watchdog proof.',
                'Removed stock gap is no longer checked for incidental corruption; full stock image was never authenticated.',
                'FNV-1a32 is accidental corruption detection, not authentication or collision resistance.',
                'Entry branch and expected word remain trust boundaries, as before.',
                'A high-byte descriptor-length corruption exceeded the 8M instruction test budget at0x103124 without LED; immediate rejection is not proved. Valid in-RAM enlarged lengths can prolong hashing.'])
    (ROOT/'research/minimal-compact-guard-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('image_sha256','early_checked_bytes','removed_bytes','guard_bytes')}))
    print('Early cases:',len(results),'PASS; unchanged late/numeric grids not rerun')


if __name__ == '__main__': main()
