"""Check the exact ordinary image's menu capacity using existing native setup.

The fixture initializes native UI state, not a complete camera boot. No physical
key scanner, display, shutdown or recovery result is claimed.
"""
import argparse
import json
from pathlib import Path
from elftools.elf.elffile import ELFFile
from verify_card_processing import sha
import verify_full_storage_guard as fixture


def make_machine(build):
    # The oldest processing fixture hardcodes the smaller four-mod region.
    # Reuse the existing full-image fixture, which takes the reservation from
    # this exact image's manifest. No instruction or API assertion changes.
    fixture.BUILD = build
    (u, s, call, api, clock, exceptions), evidence = fixture.fixture_machine(False)
    word = lambda address: int.from_bytes(u.mem_read(address, 4), 'little')
    # Match probe_fujimod_overlay.setup: register the native workers before
    # invoking the complete image's initializers (service enrollment uses them).
    for entry in [0xcec598, 0xcec634]:
        assert call(entry) == 0
    init = []
    for address in range(s['__xpp_init_start'], s['__xpp_init_end'], 4):
        entry = word(address)
        call(entry)
        init.append(hex(entry))
    assert word(s['film_choice_status']) == word(s['xpp_menu_stock_status']) == 0
    return (u, s, call, api, clock, init, exceptions), evidence


def main(build, output):
    (u, symbols, call, api, clock, init, exceptions), setup = make_machine(build)
    word = lambda address: int.from_bytes(u.mem_read(address, 4), 'little')
    call(symbols['menu_table_by_key'], 0x49, task=True)
    values = {name: word(symbols[name]) for name in
              ['xpp_menu_status', 'xpp_entries', 'item_entries', 'page_count']}
    # Several C translation units have a static `entries` array. Resolve the
    # menu's four-byte scalar explicitly rather than the fixture's name map.
    with (build/'mods.elf').open('rb') as stream:
        elf = ELFFile(stream)
        matches = [s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()
                   if s.name == 'entries' and s['st_size'] == 4]
    assert len(matches) == 1, matches
    values['entries'] = word(matches[0])
    assert values['xpp_menu_status'] == 0, values
    assert 0 < values['entries'] <= 24, values
    assert values['entries'] == values['xpp_entries'] + values['item_entries']
    assert values['page_count'] <= 4
    # This engine allocates distinct chooser/setup IDs for every entry and
    # starts pages at 0x7f40. Its actual selection must remain below that.
    assert 0x7f03 + 2 * (values['entries'] - 1) < 0x7f40
    assert not clock.errors
    result = dict(status='PASS', scope=__doc__, elf_sha256=sha((build/'mods.elf').read_bytes()),
                  native_menu=values, capacities=dict(entries=24, values=16, pages=4),
                  page_table_ids_disjoint=True, setup=setup, checker_sha256=sha(Path(__file__).read_bytes()),
                  menu_entries_scalar_address=hex(matches[0]),
                  hardware_verified=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(values), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    main(a.build, a.output)
