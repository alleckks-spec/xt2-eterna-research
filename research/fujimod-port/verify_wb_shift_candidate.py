"""Actual WB mod SAVE/cache reload/recall/edit on every slot and WB mode.

The exact ordinary artifact and full native callers execute without callback,
journal or hardware-apply success stubs. Cached journal readback is explicit;
physical NAND completion, reboot and photographic behavior remain unqualified.
"""
import argparse
import json
import struct
from pathlib import Path
from verify_wb_recall_edit_lifecycle import ROOT, BASE, SHADOW_DELTA, common, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT / 'wb-shift-coherent-build-unverified')
    parser.add_argument('--output', type=Path, default=ROOT / 'wb-shift-check-unverified/functional.json')
    args = parser.parse_args()
    receipt = json.loads((args.build / 'preparation.json').read_text())
    assert receipt['elf_sha256'] == sha((args.build / 'mods.elf').read_bytes())
    for name, digest in receipt['source_sha256'].items():
        assert sha(Path(name).read_bytes()) == digest, name
    common.BUILD = args.build
    (u, symbols, call, api, clock, init, exceptions), setup = common.fixture_machine(True)
    audit = json.loads((ROOT / 'wb-build-unverified/binding-audit-corrected.json').read_text())
    binding = audit['bindings']; reds = {int(key): value for key, value in audit['red_properties_by_setting_code'].items()}
    assert receipt['adaptation']['extension'] == dict(magic=0x84, red=0x85, blue=0x86,
        scope='declared native paths; not every unknown firmware writer')
    for index in range(7):
        u.mem_write(BASE + index * 256, bytes(256))
        call(0xbf5244, index, index, 1, task=True)
        u.mem_write(BASE + index * 256 + 0x87,
            bytes((index * 43 + offset + 23) % 256 for offset in range(121)))
    def get(prop, context=7):
        return call(binding['backup_get'], prop, 0, 0, context, task=True)
    def set_value(prop, value, context=7):
        call(binding['backup_set_explicit_context_body'], prop, value, 0, context, task=True)
        assert get(prop, context) == value
    def pair(mode):
        return [get(reds[mode]), get(reds[mode] + 13)]
    records = []
    for slot in range(7):
        for mode in range(12):
            record = BASE + slot * 256
            # Explicit old-slot input followed by the real native defaults
            # initializer. No eighth pseudo-record or successful NV stub.
            u.mem_write(record + 0x84, bytes(3))
            call(0xbf5244, slot, slot, 1, task=True)
            u.mem_write(binding['ui_info'] + binding['selected_slot_offset'], bytes([slot]))
            call(binding['custom_edit_load'], task=True)
            red, blue = (slot + mode + 2) % 19, (slot * 3 + mode * 2 + 5) % 19
            set_value(0x1cf, mode)
            set_value(reds[mode], red)
            set_value(reds[mode] + 13, blue)
            if mode == 8:
                set_value(0x1d0, 10)
            before = bytes(u.mem_read(BASE, 7 * 256))
            call(binding['custom_save'], task=True)
            after = bytes(u.mem_read(BASE, 7 * 256))
            assert bytes(u.mem_read(record + 0x84, 3)) == bytes([0xa5, red, blue]), (slot, mode)
            assert get(0x1cf, slot) == mode
            for index in range(7):
                low, high = index * 256, (index + 1) * 256
                if index != slot:
                    assert after[low:high] == before[low:high], (slot, mode, index)
                assert after[low + 0x87:high] == before[low + 0x87:high]
            # Read the bytes produced by the real native journal-cache writer.
            cached = 0x8005000
            u.mem_write(cached, b'\xa7' * 256)
            assert call(0xbbc8c8, cached, slot, task=True) == 0
            assert bytes(u.mem_read(cached, 256)) == bytes(u.mem_read(record + 4, 256))
            assert bytes(u.mem_read(cached + 0x80, 3)) == bytes([0xa5, red, blue])
            # Deliberate RAM corruption is a readback negative input: only
            # native cache read restores the saved marker and pair afterward.
            u.mem_write(record + 0x84, bytes(3))
            assert call(0xbbc8c8, record + 4, slot, task=True) == 0
            assert bytes(u.mem_read(record + 0x84, 3)) == bytes([0xa5, red, blue])
            set_value(reds[mode], (red + 7) % 19)
            set_value(reds[mode] + 13, (blue + 9) % 19)
            set_value(0x1cf, (mode + 1) % 12)
            call(binding['custom_recall'], slot, task=True)
            assert get(0x1cf) == mode and pair(mode) == [red, blue], (slot, mode, pair(mode))
            if mode == 8:
                assert get(0x1d0) == 10
            set_value(reds[mode], (red + 8) % 19)
            set_value(reds[mode] + 13, (blue + 11) % 19)
            call(binding['custom_edit_load'], task=True)
            assert get(0x1cf) == mode and pair(mode) == [red, blue], (slot, mode, pair(mode))
            assert bytes(u.mem_read(BASE + SHADOW_DELTA, 7 * 256)) == bytes(u.mem_read(BASE, 7 * 256))
            records.append(dict(raw_slot=slot, wb_setting_code=mode, pair=[red, blue],
                native_save=True, cached_marker_pair_equal=True, native_cache_reload=True,
                native_recall_restores_pair=True, native_edit_restores_pair=True,
                kelvin_restored=mode == 8, neighbors_unchanged=True,
                remaining_tail_canaries_preserved=True, native_shadow_snapshot_coherent=True,
                cached_record_sha256=sha(bytes(u.mem_read(cached, 256)))))
    # A native stock slot without this mod's marker must leave ordinary tuning
    # alone. A marked slot with invalid stored tuning retains upstream clamps.
    guard_cases = []
    slot = 0; record = BASE
    u.mem_write(binding['ui_info'] + binding['selected_slot_offset'], bytes([slot]))
    set_value(0x1cf, 3, slot)
    set_value(reds[3], 4); set_value(reds[3] + 13, 17)
    u.mem_write(record + 0x84, bytes([0, 255, 254]))
    call(binding['custom_recall'], slot, task=True)
    assert get(0x1cf) == 3 and pair(3) == [4, 17]
    guard_cases.append(dict(marker=0, stored_pair=[255, 254], actual_pair=pair(3), stock_tuning_preserved=True))
    u.mem_write(record + 0x84, bytes([0xa5, 255, 254]))
    call(binding['custom_recall'], slot, task=True)
    assert get(0x1cf) == 3 and pair(3) == [0, 0]
    guard_cases.append(dict(marker=0xa5, stored_pair=[255, 254], actual_pair=pair(3), upstream_clamp_preserved=True))
    reset_cases = []
    for slot in range(7):
        record = BASE + slot * 256
        mode, red, blue = (slot + 3) % 12, (slot + 6) % 19, (slot + 13) % 19
        u.mem_write(binding['ui_info'] + binding['selected_slot_offset'], bytes([slot]))
        call(binding['custom_edit_load'], task=True)
        set_value(0x1cf, mode); set_value(reds[mode], red); set_value(reds[mode] + 13, blue)
        call(binding['custom_save'], task=True)
        assert bytes(u.mem_read(record + 0x84, 3)) == bytes([0xa5, red, blue])
        # The real edit entry backs up the pre-edit ordinary image before
        # the WB hook applies this slot's pair. Native RESET must restore that
        # ordinary image while leaving the saved custom pair intact.
        previous_mode = (mode + 1) % 12
        set_value(0x1cf, previous_mode)
        set_value(reds[mode], 4); set_value(reds[mode] + 13, 17)
        call(binding['custom_edit_load'], task=True)
        assert get(0x1cf) == mode and pair(mode) == [red, blue]
        call(0x1543e4c, task=True)
        assert get(0x1cf) == previous_mode and pair(mode) == [4, 17]
        assert bytes(u.mem_read(record + 0x84, 3)) == bytes([0xa5, red, blue])
        call(binding['custom_edit_load'], task=True)
        default_mode = call(binding['backup_get'], 0x1cf, 0, 1, slot, task=True)
        call(0x1543ee4, task=True)
        assert get(0x1cf, slot) == default_mode
        assert bytes(u.mem_read(record + 0x84, 3)) == bytes([0xa5, red, blue])
        call(binding['custom_recall'], slot, task=True)
        assert get(0x1cf) == default_mode and pair(default_mode) == [red, blue]
        # Preserve upstream's documented defaults contract: its stock fields
        # reset; the prior mod pair remains until the next SAVE replaces it.
        call(binding['custom_edit_load'], task=True)
        set_value(reds[default_mode], 9); set_value(reds[default_mode] + 13, 9)
        call(binding['custom_save'], task=True)
        assert bytes(u.mem_read(record + 0x84, 3)) == bytes([0xa5, 9, 9])
        assert call(0xbbc8c8, 0x8005000, slot, task=True) == 0
        assert bytes(u.mem_read(0x8005080, 3)) == bytes([0xa5, 9, 9])
        call(0xbbc924, 0, task=True)
        u.mem_write(record + 0x84, bytes(3))
        call(0xbbc924, 1, task=True)
        assert bytes(u.mem_read(record + 0x84, 3)) == bytes([0xa5, 9, 9])
        reset_cases.append(dict(raw_slot=slot, reset_restores_pre_edit_mode=previous_mode,
            reset_preserves_saved_pair=[red, blue], defaults_native_mode=default_mode,
            defaults_preserves_pair_until_save=True, subsequent_save_cached_pair=[9, 9],
            native_bank_cancel_restores_coherent_tuple=True))
    assert not clock.errors
    result = dict(scope=__doc__, status='PASS', cases=records, guard_cases=guard_cases, reset_cases=reset_cases,
        elf_sha256=receipt['elf_sha256'], checker_sha256=sha(Path(__file__).read_bytes()),
        setup=setup, init_calls=init, native_vfp_exceptions=exceptions,
        actual_native_journal_cache_read_write=True, actual_full_native_callers=True,
        custom_record_count=7, physical_journal_io_verified=False, physical_buttons=False,
        full_reset_boot=False, hardware_verified=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status='PASS', cases=len(records), guards=len(guard_cases), elf=result['elf_sha256'])))


if __name__ == '__main__':
    main()
