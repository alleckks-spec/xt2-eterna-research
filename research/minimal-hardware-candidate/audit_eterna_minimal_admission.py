"""Freeze the available safety evidence; this does not execute a camera boot.

Original OpenAI Codex-assisted audit. Local vendor inputs are required and
are never copied into the public research repository.
"""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition):
    if not condition:
        raise ValueError("Static safety evidence mismatch")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def branch(image, address):
    word = struct.unpack_from('<I', image, address)[0]
    require(word >> 24 in (0xEA, 0xEB))
    delta = word & 0xFFFFFF
    if delta & 0x800000:
        delta -= 0x1000000
    return address + 8 + 4 * delta


def main():
    folder = ROOT / 'firmware/research/eterna-minimal-sd-candidate'
    image = (folder / 'ffboot.bin').read_bytes()
    stock = (ROOT / 'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    manifest = json.loads((folder / 'manifest.json').read_text())
    guard = json.loads((ROOT / 'research/eterna-minimal-boot-guard-verification.json').read_text())
    numeric = json.loads((ROOT / 'research/eterna-minimal-sd-verification.json').read_text())
    require(hashlib.sha256(image).hexdigest() == manifest['image_sha256'] == guard['image_sha256'] == 'c1aee308e0b6c54dfede3de4c48885223365b2b8e90c282c74d87a112d58fc10')
    prior = (ROOT / 'research/minimal-before-boot-guard/ffboot.bin').read_bytes()
    require(hashlib.sha256(prior).hexdigest() == numeric['image_sha256'] == '47a9376657501fec7805c0fa17b958dea2b100bfc13652d764a7b73401723751')
    # Evidence inheritance is allowed only outside the two actual guard edits.
    require(len(image) == len(prior) == len(stock) == 46505984)
    require(image[:0x103024] == prior[:0x103024])
    require(image[0x103028:0x1030F0] == prior[0x103028:0x1030F0])
    require(image[0x103198:] == prior[0x103198:])
    require(branch(image, 0x103024) == 0x1030F0)
    require(struct.unpack_from('<I', image, 0x20)[0] == 0x103000)
    sites = manifest['private_parameter_call_sites']
    require(len(sites) == 18)
    require(all(branch(image, a) in (0xDF7940, 0xDF7A80, 0xDF7AC0) for a in sites))
    layout = json.loads((ROOT / 'firmware/extracted/xt2-4.41/layout.json').read_text())
    spans = [(0x103000, 0x103200), (0x781000, 0x783A68), (0xDF7900, 0xDF7AD4)]
    overlaps = [(s['id'], lo, hi) for s in layout['sections'] for lo, hi in spans
                if s['bss_size'] and max(lo, s['bss_base']) < min(hi, s['bss_base'] + s['bss_size'])]
    require(not overlaps)
    sec = next(s for s in layout['sections'] if s['id'] == 2)
    require(sec['base'] + sec['initialized_size'] <= 0x781000 < 0x783A68 <= sec['base'] + sec['stored_extent'])
    recipes = json.loads((ROOT / 'upstream/fujimod/catalog/recovery/recipes.generated.json').read_text())
    if isinstance(recipes, dict):
        recipes = recipes['recipes']
    recipe = next(r for r in recipes if r['firmware_id'] == 'xt2-441')
    packaging = recipe['packaging']
    require(packaging['entry'] == packaging['load_address'] == 0)
    require(packaging['header_sha256'] == sha(folder / 'ffsys.bin'))
    require(recipe['plan']['size'] == len(image))
    # The carrier preserves the original general flash reader; it is not a
    # per-body read snapshot or an inhibit on controller program/erase commands.
    require(image[0xC58000:0xC5B000] == stock[0xC58000:0xC5B000])
    reports = ['eterna-minimal-sd-verification.json', 'eterna-minimal-stock-menu-verification.json',
               'eterna-minimal-boot-guard-verification.json', 'early-carrier-native-load-lifetime-audit.json',
               'native-flash-scratch-write-path.json', 'native-flash-program-readback.json',
               'native-flash-sector-erase.json', 'flash-cache-3ee-audit.json']
    sources = ['build_eterna_minimal_sd.py', 'eterna_ram_fixture.py', 'eterna_parameter_overlay.py',
               'eterna_development_selector.py', 'xt2_minimal_boot_guard.S', 'xt2_minimal_boot_guard.py',
               'verify_xt2_minimal_boot_guard.py', 'audit_eterna_minimal_admission.py']
    output = dict(schema=1, date='2026-11-08', decision='HOLD: do not offer this candidate for hardware testing yet',
                  candidate_files={p.name: dict(size=p.stat().st_size, sha256=sha(p))
                                   for p in sorted(folder.iterdir()) if p.is_file()},
                  static_checks=dict(entry_vector_to_existing_led=True, guard_branch=True,
                                     private_call_destinations_checked=18, declared_bss_overlaps=overlaps,
                                     data_within_raw_allocation=True, recipe_packaging_matches=True,
                                     numeric_body_byte_identical_to_tested_prior=True,
                                     stock_flash_driver_preserved=True),
                  evidence_sha256={n: sha(ROOT / 'research' / n) for n in reports},
                  source_sha256={n: sha(ROOT / 'scripts' / n) for n in sources},
                  limitations=['Static bounds/branches do not establish ROM delivery, dynamic ownership or cache permissions.',
                               'Historical flash runs use synthetic erased stores; not this candidate full boot or a complete persistence inventory.',
                               'No rollback, per-body NV backup/restore or physical power-off recovery is established.'],
                  original_rom_transfer=False, full_boot=False, hardware_verified=False)
    target = ROOT / 'research/eterna-minimal-safety-freeze.json'
    target.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
